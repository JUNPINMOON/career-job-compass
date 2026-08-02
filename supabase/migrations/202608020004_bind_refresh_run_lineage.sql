-- Bind every published snapshot to one claimed refresh attempt.
--
-- This migration deliberately keeps the existing PostgREST RPC signatures so
-- the installed Windows worker can be upgraded independently.  The database
-- owns the lease, immutable terminal payload hash, and canonical publication
-- binding; callers cannot overwrite those fields with stale JSON.

alter table private.refresh_worker_config
  add column if not exists worker_id uuid;

update private.refresh_worker_config
set worker_id = extensions.gen_random_uuid()
where worker_id is null;

alter table private.refresh_worker_config
  alter column worker_id set default extensions.gen_random_uuid(),
  alter column worker_id set not null;

alter table public.refresh_runs
  add column if not exists attempt_count integer not null default 0,
  add column if not exists worker_id uuid,
  add column if not exists lease_expires_at timestamptz,
  add column if not exists heartbeat_at timestamptz,
  add column if not exists preference_digest text,
  add column if not exists liked_count integer not null default 0,
  add column if not exists disliked_count integer not null default 0,
  add column if not exists row_count integer not null default 0,
  add column if not exists model_version text not null default 'preference-ranker-v5',
  add column if not exists terminal_payload_hash text;

alter table public.refresh_runs
  add constraint refresh_runs_attempt_count_nonnegative
    check (attempt_count >= 0),
  add constraint refresh_runs_count_binding_valid
    check (
      liked_count >= 0
      and disliked_count >= 0
      and row_count = liked_count + disliked_count
    ),
  add constraint refresh_runs_digest_format
    check (preference_digest is null or preference_digest ~ '^[0-9a-f]{64}$'),
  add constraint refresh_runs_model_version_nonempty
    check (length(btrim(model_version)) > 0),
  add constraint refresh_runs_terminal_hash_state
    check (
      (state in ('pending', 'running') and terminal_payload_hash is null)
      or (state in ('succeeded', 'failed') and terminal_payload_hash is not null)
    ) not valid;

create index if not exists refresh_runs_claimable_lease_idx
on public.refresh_runs (requested_at, lease_expires_at)
where state in ('pending', 'running');

create unique index if not exists refresh_runs_id_user_id_key
on public.refresh_runs (id, user_id);

-- Any running row created before this migration did not have a lease.  Mark it
-- immediately recoverable instead of leaving it permanently unclaimable.
update public.refresh_runs
set lease_expires_at = clock_timestamp() - interval '1 second'
where state = 'running' and lease_expires_at is null;

alter table public.personalized_snapshots
  add column if not exists source_run_id uuid,
  add column if not exists source_attempt_count integer,
  add column if not exists liked_count integer,
  add column if not exists disliked_count integer,
  add column if not exists row_count integer,
  add column if not exists model_version text;

alter table public.personalized_snapshots
  add constraint personalized_snapshots_source_run_owner_fk
    foreign key (source_run_id, user_id)
    references public.refresh_runs (id, user_id),
  add constraint personalized_snapshots_source_binding_valid
    check (
      source_run_id is null
      or (
        source_attempt_count is not null
        and source_attempt_count > 0
        and liked_count is not null
        and disliked_count is not null
        and row_count is not null
        and liked_count >= 0
        and disliked_count >= 0
        and row_count = liked_count + disliked_count
        and preference_digest ~ '^[0-9a-f]{64}$'
        and length(btrim(model_version)) > 0
      )
    ) not valid;

create unique index if not exists personalized_snapshots_source_run_id_key
on public.personalized_snapshots (source_run_id)
where source_run_id is not null;

create or replace function private.refresh_model_version()
returns text
language sql
immutable
security definer
set search_path = ''
as $$
  select 'preference-ranker-v5'::text;
$$;

revoke all on function private.refresh_model_version() from public, anon, authenticated;

create or replace function private.refresh_worker_identity(candidate text)
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select config.worker_id
  from private.refresh_worker_config as config
  where config.singleton
    and length(coalesce(candidate, '')) between 40 and 256
    and extensions.crypt(candidate, config.secret_hash) = config.secret_hash;
$$;

revoke all on function private.refresh_worker_identity(text) from public, anon, authenticated;

-- Rotating the protected secret also rotates the worker identity.  Existing
-- leases then fail closed instead of silently accepting the new credential.
create or replace function private.set_refresh_worker_secret(candidate text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if length(coalesce(candidate, '')) < 40 then
    raise exception 'worker secret must contain at least 40 characters';
  end if;

  insert into private.refresh_worker_config (
    singleton,
    secret_hash,
    worker_id,
    updated_at
  ) values (
    true,
    extensions.crypt(candidate, extensions.gen_salt('bf', 12)),
    extensions.gen_random_uuid(),
    clock_timestamp()
  )
  on conflict (singleton) do update
  set
    secret_hash = excluded.secret_hash,
    worker_id = excluded.worker_id,
    updated_at = excluded.updated_at;
end;
$$;

revoke all on function private.set_refresh_worker_secret(text) from public, anon, authenticated;

create or replace function private.initialize_refresh_run()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  requested_at_value timestamptz := clock_timestamp();
  liked_count_value integer;
  disliked_count_value integer;
  model_version_value text := private.refresh_model_version();
begin
  if new.user_id is distinct from auth.uid() then
    raise exception 'refresh run user must match the authenticated user';
  end if;

  select
    count(*) filter (where sentiment = 'liked'),
    count(*) filter (where sentiment = 'not_for_me')
  into liked_count_value, disliked_count_value
  from public.job_preferences
  where user_id = new.user_id;

  new.state := 'pending';
  new.requested_at := requested_at_value;
  new.started_at := null;
  new.finished_at := null;
  new.updated_at := requested_at_value;
  new.attempt_count := 0;
  new.worker_id := null;
  new.lease_expires_at := null;
  new.heartbeat_at := null;
  new.preference_digest := null;
  new.liked_count := liked_count_value;
  new.disliked_count := disliked_count_value;
  new.row_count := liked_count_value + disliked_count_value;
  new.model_version := model_version_value;
  new.terminal_payload_hash := null;
  new.status := jsonb_build_object(
    'state', 'pending',
    'startedAt', requested_at_value,
    'updatedAt', requested_at_value,
    'currentStage', jsonb_build_object(
      'id', 'queued',
      'labelKo', '안전한 작업 큐에서 엔진 연결 대기',
      'position', 0,
      'total', 10
    ),
    'stages', '[]'::jsonb,
    'attemptCount', 0,
    'preferenceSummary', jsonb_build_object(
      'likedCount', liked_count_value,
      'dislikedCount', disliked_count_value,
      'rowCount', liked_count_value + disliked_count_value,
      'digest', null
    ),
    'refreshBinding', jsonb_build_object(
      'runId', new.id,
      'userId', new.user_id,
      'preferenceDigest', null,
      'likedCount', liked_count_value,
      'dislikedCount', disliked_count_value,
      'rowCount', liked_count_value + disliked_count_value,
      'modelVersion', model_version_value
    )
  );
  return new;
end;
$$;

create or replace function private.enforce_refresh_run_terminal_immutability()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if old.state in ('succeeded', 'failed')
     and row(new.*) is distinct from row(old.*) then
    raise exception 'terminal refresh publication is immutable' using errcode = '55000';
  end if;
  return new;
end;
$$;

revoke all on function private.enforce_refresh_run_terminal_immutability()
from public, anon, authenticated;

drop trigger if exists enforce_refresh_run_terminal_immutability on public.refresh_runs;
create trigger enforce_refresh_run_terminal_immutability
before update on public.refresh_runs
for each row execute function private.enforce_refresh_run_terminal_immutability();

create or replace function public.claim_refresh_run(worker_secret text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  claimed public.refresh_runs%rowtype;
  preference_rows jsonb;
  liked_count_value integer;
  disliked_count_value integer;
  claim_time timestamptz := clock_timestamp();
  active_worker_id uuid;
  recovering boolean := false;
  preference_summary jsonb;
  refresh_binding jsonb;
  claimed_status jsonb;
begin
  active_worker_id := private.refresh_worker_identity(worker_secret);
  if active_worker_id is null then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;

  select run.*
  into claimed
  from public.refresh_runs as run
  where run.state = 'pending'
     or (
       run.state = 'running'
       and run.lease_expires_at is not null
       and run.lease_expires_at <= claim_time
     )
  order by run.requested_at, run.id
  for update skip locked
  limit 1;

  if claimed.id is null then
    return null;
  end if;

  recovering := claimed.state = 'running';

  select
    coalesce(
      jsonb_agg(
        jsonb_build_object(
          'userId', preference.user_id,
          'jobId', preference.job_id,
          'sentiment', preference.sentiment,
          'reasons', preference.reasons,
          'note', preference.note,
          'jobSnapshot', jsonb_build_object(
            'title', coalesce(preference.job_snapshot->>'title', ''),
            'company', coalesce(preference.job_snapshot->>'company', ''),
            'location', coalesce(preference.job_snapshot->>'location', ''),
            'sectors', coalesce(preference.job_snapshot->'sectors', '[]'::jsonb),
            'source', coalesce(preference.job_snapshot->>'source', ''),
            'url', coalesce(preference.job_snapshot->>'url', '')
          ),
          'updatedAt', preference.updated_at
        ) order by preference.updated_at, preference.job_id
      ),
      '[]'::jsonb
    ),
    count(*) filter (where preference.sentiment = 'liked'),
    count(*) filter (where preference.sentiment = 'not_for_me')
  into preference_rows, liked_count_value, disliked_count_value
  from public.job_preferences as preference
  where preference.user_id = claimed.user_id;

  preference_summary := jsonb_build_object(
    'likedCount', liked_count_value,
    'dislikedCount', disliked_count_value,
    'rowCount', liked_count_value + disliked_count_value,
    'digest', null
  );
  refresh_binding := jsonb_build_object(
    'runId', claimed.id,
    'userId', claimed.user_id,
    'preferenceDigest', null,
    'likedCount', liked_count_value,
    'dislikedCount', disliked_count_value,
    'rowCount', liked_count_value + disliked_count_value,
    'modelVersion', claimed.model_version
  );
  claimed_status := coalesce(claimed.status, '{}'::jsonb) || jsonb_build_object(
    'state', 'running',
    'updatedAt', claim_time,
    'attemptCount', claimed.attempt_count + 1,
    'preferenceSummary', preference_summary,
    'refreshBinding', refresh_binding,
    'currentStage', case
      when recovering then jsonb_build_object(
        'id', 'worker_reclaimed',
        'labelKo', '만료된 작업을 안전하게 다시 연결',
        'position', 0,
        'total', 10
      )
      else jsonb_build_object(
        'id', 'worker_claimed',
        'labelKo', '로컬 엔진이 작업을 인수',
        'position', 0,
        'total', 10
      )
    end
  );

  update public.refresh_runs
  set
    state = 'running',
    status = claimed_status,
    started_at = coalesce(claimed.started_at, claim_time),
    finished_at = null,
    updated_at = claim_time,
    attempt_count = claimed.attempt_count + 1,
    worker_id = active_worker_id,
    heartbeat_at = claim_time,
    lease_expires_at = claim_time + interval '5 minutes',
    preference_digest = null,
    liked_count = liked_count_value,
    disliked_count = disliked_count_value,
    row_count = liked_count_value + disliked_count_value,
    terminal_payload_hash = null
  where id = claimed.id
  returning * into claimed;

  return jsonb_build_object(
    'runId', claimed.id,
    'userId', claimed.user_id,
    'attemptCount', claimed.attempt_count,
    'workerId', claimed.worker_id,
    'leaseExpiresAt', claimed.lease_expires_at,
    'modelVersion', claimed.model_version,
    'lineage', refresh_binding,
    'status', claimed.status,
    'preferences', preference_rows
  );
end;
$$;

create or replace function public.publish_refresh_run(
  worker_secret text,
  run_id uuid,
  run_status jsonb,
  personalized_snapshot jsonb default null
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  claimed public.refresh_runs%rowtype;
  active_worker_id uuid;
  publish_time timestamptz := clock_timestamp();
  next_state text;
  incoming_summary jsonb;
  incoming_binding jsonb;
  snapshot_stats jsonb;
  snapshot_summary jsonb;
  snapshot_binding jsonb;
  normalized_summary jsonb;
  normalized_binding jsonb;
  normalized_status jsonb;
  normalized_snapshot jsonb;
  incoming_digest text;
  effective_digest text;
  incoming_liked_count integer;
  incoming_disliked_count integer;
  incoming_row_count integer;
  model_version_count integer;
  distinct_model_version_count integer;
  observed_model_version text;
  generated_at_value timestamptz;
  job_data_as_of_value date;
  terminal_hash text;
begin
  active_worker_id := private.refresh_worker_identity(worker_secret);
  if active_worker_id is null then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;
  if run_status is null or jsonb_typeof(run_status) <> 'object' then
    raise exception 'refresh status must be an object';
  end if;

  next_state := run_status->>'state';
  if next_state not in ('running', 'succeeded', 'failed') then
    raise exception 'invalid refresh state';
  end if;

  select run.*
  into claimed
  from public.refresh_runs as run
  where run.id = run_id
  for update;

  if claimed.id is null then
    return false;
  end if;

  if claimed.state in ('succeeded', 'failed') then
    terminal_hash := encode(
      extensions.digest(
        convert_to(
          jsonb_build_object(
            'runId', run_id,
            'status', run_status,
            'snapshot', personalized_snapshot
          )::text,
          'UTF8'
        ),
        'sha256'
      ),
      'hex'
    );
    if claimed.state = next_state
       and claimed.terminal_payload_hash = terminal_hash then
      return true;
    end if;
    raise exception 'terminal refresh publication is immutable' using errcode = '55000';
  end if;

  if claimed.state <> 'running' then
    return false;
  end if;
  if claimed.worker_id is distinct from active_worker_id then
    raise exception 'refresh lease belongs to a different worker' using errcode = '42501';
  end if;
  if claimed.lease_expires_at is null or claimed.lease_expires_at <= publish_time then
    raise exception 'refresh lease expired' using errcode = '55000';
  end if;

  incoming_summary := run_status->'preferenceSummary';
  if incoming_summary is null or jsonb_typeof(incoming_summary) <> 'object' then
    raise exception 'refresh preference summary is required';
  end if;
  if coalesce(incoming_summary->>'likedCount', '') !~ '^[0-9]+$'
     or coalesce(incoming_summary->>'dislikedCount', '') !~ '^[0-9]+$'
     or coalesce(incoming_summary->>'rowCount', '') !~ '^[0-9]+$' then
    raise exception 'refresh preference counts are invalid';
  end if;

  incoming_liked_count := (incoming_summary->>'likedCount')::integer;
  incoming_disliked_count := (incoming_summary->>'dislikedCount')::integer;
  incoming_row_count := (incoming_summary->>'rowCount')::integer;
  if incoming_liked_count <> claimed.liked_count
     or incoming_disliked_count <> claimed.disliked_count
     or incoming_row_count <> claimed.row_count
     or incoming_row_count <> incoming_liked_count + incoming_disliked_count then
    raise exception 'refresh preference counts do not match the claimed run';
  end if;

  incoming_digest := nullif(incoming_summary->>'digest', '');
  if incoming_digest is not null and incoming_digest !~ '^[0-9a-f]{64}$' then
    raise exception 'refresh preference digest is invalid';
  end if;
  if claimed.preference_digest is not null
     and incoming_digest is not null
     and incoming_digest <> claimed.preference_digest then
    raise exception 'refresh preference digest does not match the claimed run';
  end if;
  effective_digest := coalesce(claimed.preference_digest, incoming_digest);
  if next_state = 'succeeded' and effective_digest is null then
    raise exception 'successful refresh requires a preference digest';
  end if;

  if run_status ? 'refreshBinding'
     and jsonb_typeof(run_status->'refreshBinding') <> 'object' then
    raise exception 'refresh binding must be an object';
  end if;
  incoming_binding := coalesce(run_status->'refreshBinding', '{}'::jsonb);

  if nullif(incoming_binding->>'runId', '') is not null
     and incoming_binding->>'runId' <> run_id::text then
    raise exception 'refresh binding run id mismatch';
  end if;
  if nullif(incoming_binding->>'userId', '') is not null
     and incoming_binding->>'userId' <> claimed.user_id::text then
    raise exception 'refresh binding user id mismatch';
  end if;
  if nullif(incoming_binding->>'preferenceDigest', '') is not null
     and incoming_binding->>'preferenceDigest' is distinct from effective_digest then
    raise exception 'refresh binding preference digest mismatch';
  end if;
  if nullif(incoming_binding->>'modelVersion', '') is not null
     and incoming_binding->>'modelVersion' <> claimed.model_version then
    raise exception 'refresh binding model version mismatch';
  end if;
  if incoming_binding ? 'likedCount'
     and incoming_binding->>'likedCount' <> claimed.liked_count::text then
    raise exception 'refresh binding liked count mismatch';
  end if;
  if incoming_binding ? 'dislikedCount'
     and incoming_binding->>'dislikedCount' <> claimed.disliked_count::text then
    raise exception 'refresh binding disliked count mismatch';
  end if;
  if incoming_binding ? 'rowCount'
     and incoming_binding->>'rowCount' <> claimed.row_count::text then
    raise exception 'refresh binding row count mismatch';
  end if;

  normalized_summary := jsonb_build_object(
    'likedCount', claimed.liked_count,
    'dislikedCount', claimed.disliked_count,
    'rowCount', claimed.row_count,
    'digest', effective_digest
  );
  normalized_binding := jsonb_build_object(
    'runId', claimed.id,
    'userId', claimed.user_id,
    'preferenceDigest', effective_digest,
    'likedCount', claimed.liked_count,
    'dislikedCount', claimed.disliked_count,
    'rowCount', claimed.row_count,
    'modelVersion', claimed.model_version
  );
  normalized_status := run_status || jsonb_build_object(
    'state', next_state,
    'updatedAt', publish_time,
    'attemptCount', claimed.attempt_count,
    'preferenceSummary', normalized_summary,
    'refreshBinding', normalized_binding
  );

  if next_state = 'running' then
    if personalized_snapshot is not null then
      raise exception 'running refresh cannot publish a snapshot';
    end if;
    update public.refresh_runs
    set
      status = normalized_status,
      updated_at = publish_time,
      heartbeat_at = publish_time,
      lease_expires_at = publish_time + interval '5 minutes',
      preference_digest = effective_digest
    where id = claimed.id;
    return true;
  end if;

  terminal_hash := encode(
    extensions.digest(
      convert_to(
        jsonb_build_object(
          'runId', run_id,
          'status', run_status,
          'snapshot', personalized_snapshot
        )::text,
        'UTF8'
      ),
      'sha256'
    ),
    'hex'
  );

  if next_state = 'failed' then
    if personalized_snapshot is not null then
      raise exception 'failed refresh cannot publish a snapshot';
    end if;
    update public.refresh_runs
    set
      state = 'failed',
      status = normalized_status,
      finished_at = coalesce(
        nullif(run_status->>'finishedAt', '')::timestamptz,
        publish_time
      ),
      updated_at = publish_time,
      heartbeat_at = publish_time,
      lease_expires_at = null,
      preference_digest = effective_digest,
      terminal_payload_hash = terminal_hash
    where id = claimed.id;
    return true;
  end if;

  if personalized_snapshot is null
     or jsonb_typeof(personalized_snapshot) <> 'object' then
    raise exception 'successful refresh requires a snapshot object';
  end if;
  snapshot_stats := personalized_snapshot->'stats';
  if snapshot_stats is null or jsonb_typeof(snapshot_stats) <> 'object' then
    raise exception 'successful snapshot stats are required';
  end if;
  snapshot_summary := snapshot_stats->'preferenceSummary';
  if snapshot_summary is null or jsonb_typeof(snapshot_summary) <> 'object' then
    raise exception 'successful snapshot preference summary is required';
  end if;
  if snapshot_summary->>'digest' is distinct from effective_digest
     or snapshot_summary->>'likedCount' <> claimed.liked_count::text
     or snapshot_summary->>'dislikedCount' <> claimed.disliked_count::text
     or snapshot_summary->>'rowCount' <> claimed.row_count::text then
    raise exception 'snapshot preference binding does not match the claimed run';
  end if;

  if snapshot_stats ? 'refreshBinding'
     and jsonb_typeof(snapshot_stats->'refreshBinding') <> 'object' then
    raise exception 'snapshot refresh binding must be an object';
  end if;
  snapshot_binding := coalesce(snapshot_stats->'refreshBinding', '{}'::jsonb);
  if snapshot_binding->>'runId' is distinct from run_id::text
     or snapshot_binding->>'preferenceDigest' is distinct from effective_digest then
    raise exception 'snapshot run or preference digest mismatch';
  end if;
  if nullif(snapshot_binding->>'userId', '') is not null
     and snapshot_binding->>'userId' <> claimed.user_id::text then
    raise exception 'snapshot user id mismatch';
  end if;
  if nullif(snapshot_binding->>'modelVersion', '') is not null
     and snapshot_binding->>'modelVersion' <> claimed.model_version then
    raise exception 'snapshot model version mismatch';
  end if;
  if snapshot_binding ? 'likedCount'
     and snapshot_binding->>'likedCount' <> claimed.liked_count::text then
    raise exception 'snapshot liked count mismatch';
  end if;
  if snapshot_binding ? 'dislikedCount'
     and snapshot_binding->>'dislikedCount' <> claimed.disliked_count::text then
    raise exception 'snapshot disliked count mismatch';
  end if;
  if snapshot_binding ? 'rowCount'
     and snapshot_binding->>'rowCount' <> claimed.row_count::text then
    raise exception 'snapshot row count mismatch';
  end if;

  if jsonb_typeof(personalized_snapshot->'jobs') <> 'array' then
    raise exception 'successful snapshot jobs must be an array';
  end if;
  select
    count(*),
    count(distinct versions.model_version),
    min(versions.model_version)
  into
    model_version_count,
    distinct_model_version_count,
    observed_model_version
  from (
    select nullif(job.value#>>'{personalization,modelVersion}', '') as model_version
    from jsonb_array_elements(personalized_snapshot->'jobs') as job(value)
    union all
    select nullif(job.value#>>'{preferenceDiscovery,modelVersion}', '') as model_version
    from jsonb_array_elements(personalized_snapshot->'jobs') as job(value)
  ) as versions
  where versions.model_version is not null;

  if model_version_count = 0
     or distinct_model_version_count <> 1
     or observed_model_version <> claimed.model_version then
    raise exception 'snapshot model version does not match the claimed run';
  end if;

  normalized_snapshot := jsonb_set(
    personalized_snapshot,
    '{stats}',
    snapshot_stats || jsonb_build_object('refreshBinding', normalized_binding),
    true
  );
  generated_at_value := nullif(personalized_snapshot->>'generatedAt', '')::timestamptz;
  if generated_at_value is null then
    raise exception 'successful snapshot generatedAt is required';
  end if;
  job_data_as_of_value := coalesce(
    nullif(personalized_snapshot#>>'{stats,jobDataAsOf}', '')::date,
    nullif(personalized_snapshot->>'dataAsOf', '')::date
  );

  insert into public.personalized_snapshots (
    user_id,
    generated_at,
    preference_digest,
    job_data_as_of,
    snapshot,
    updated_at,
    source_run_id,
    source_attempt_count,
    liked_count,
    disliked_count,
    row_count,
    model_version
  ) values (
    claimed.user_id,
    generated_at_value,
    effective_digest,
    job_data_as_of_value,
    normalized_snapshot,
    publish_time,
    claimed.id,
    claimed.attempt_count,
    claimed.liked_count,
    claimed.disliked_count,
    claimed.row_count,
    claimed.model_version
  )
  on conflict (user_id) do update
  set
    generated_at = excluded.generated_at,
    preference_digest = excluded.preference_digest,
    job_data_as_of = excluded.job_data_as_of,
    snapshot = excluded.snapshot,
    updated_at = excluded.updated_at,
    source_run_id = excluded.source_run_id,
    source_attempt_count = excluded.source_attempt_count,
    liked_count = excluded.liked_count,
    disliked_count = excluded.disliked_count,
    row_count = excluded.row_count,
    model_version = excluded.model_version;

  update public.refresh_runs
  set
    state = 'succeeded',
    status = normalized_status,
    finished_at = coalesce(
      nullif(run_status->>'finishedAt', '')::timestamptz,
      publish_time
    ),
    updated_at = publish_time,
    heartbeat_at = publish_time,
    lease_expires_at = null,
    preference_digest = effective_digest,
    terminal_payload_hash = terminal_hash
  where id = claimed.id;

  return true;
end;
$$;

grant execute on function public.claim_refresh_run(text) to anon, authenticated;
grant execute on function public.publish_refresh_run(text, uuid, jsonb, jsonb)
to anon, authenticated;
