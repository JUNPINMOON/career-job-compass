create extension if not exists pgcrypto with schema extensions;

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table if not exists private.refresh_worker_config (
  singleton boolean primary key default true check (singleton),
  secret_hash text not null,
  updated_at timestamptz not null default now()
);

revoke all on table private.refresh_worker_config from public, anon, authenticated;

create table if not exists public.refresh_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  state text not null default 'pending' check (state in ('pending', 'running', 'succeeded', 'failed')),
  status jsonb not null default '{}'::jsonb,
  requested_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  updated_at timestamptz not null default now()
);

create unique index if not exists refresh_runs_one_active_per_user
on public.refresh_runs (user_id)
where state in ('pending', 'running');

alter table public.refresh_runs enable row level security;

revoke all on table public.refresh_runs from anon;
revoke all on table public.refresh_runs from authenticated;
grant select on table public.refresh_runs to authenticated;
grant insert (user_id) on table public.refresh_runs to authenticated;

create policy "Users read their own refresh runs"
on public.refresh_runs
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Users request their own refresh runs"
on public.refresh_runs
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create or replace function private.initialize_refresh_run()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  liked_count integer;
  disliked_count integer;
begin
  if new.user_id is distinct from auth.uid() then
    raise exception 'refresh run user must match the authenticated user';
  end if;

  select
    count(*) filter (where sentiment = 'liked'),
    count(*) filter (where sentiment = 'not_for_me')
  into liked_count, disliked_count
  from public.job_preferences
  where user_id = new.user_id;

  new.state := 'pending';
  new.requested_at := now();
  new.started_at := null;
  new.finished_at := null;
  new.updated_at := now();
  new.status := jsonb_build_object(
    'state', 'pending',
    'startedAt', new.requested_at,
    'updatedAt', new.requested_at,
    'currentStage', jsonb_build_object(
      'id', 'queued',
      'labelKo', '안전한 작업 큐에서 엔진 연결 대기',
      'position', 0,
      'total', 10
    ),
    'stages', '[]'::jsonb,
    'preferenceSummary', jsonb_build_object(
      'likedCount', liked_count,
      'dislikedCount', disliked_count,
      'rowCount', liked_count + disliked_count
    )
  );
  return new;
end;
$$;

drop trigger if exists initialize_refresh_run on public.refresh_runs;
create trigger initialize_refresh_run
before insert on public.refresh_runs
for each row execute function private.initialize_refresh_run();

create or replace function private.refresh_worker_secret_matches(candidate text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select
    length(coalesce(candidate, '')) between 40 and 256
    and exists (
      select 1
      from private.refresh_worker_config
      where singleton
        and extensions.crypt(candidate, secret_hash) = secret_hash
    );
$$;

revoke all on function private.refresh_worker_secret_matches(text) from public, anon, authenticated;

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
  insert into private.refresh_worker_config (singleton, secret_hash, updated_at)
  values (true, extensions.crypt(candidate, extensions.gen_salt('bf', 12)), now())
  on conflict (singleton) do update
  set secret_hash = excluded.secret_hash, updated_at = excluded.updated_at;
end;
$$;

revoke all on function private.set_refresh_worker_secret(text) from public, anon, authenticated;

create or replace function public.claim_refresh_run(worker_secret text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  claimed public.refresh_runs%rowtype;
  preference_rows jsonb;
begin
  if not private.refresh_worker_secret_matches(worker_secret) then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;

  select *
  into claimed
  from public.refresh_runs
  where state = 'pending'
  order by requested_at
  for update skip locked
  limit 1;

  if claimed.id is null then
    return null;
  end if;

  update public.refresh_runs
  set
    state = 'running',
    started_at = now(),
    updated_at = now(),
    status = jsonb_set(
      jsonb_set(status, '{state}', '"running"'::jsonb, true),
      '{updatedAt}', to_jsonb(now()), true
    )
  where id = claimed.id
  returning * into claimed;

  select coalesce(jsonb_agg(jsonb_build_object(
    'userId', user_id,
    'jobId', job_id,
    'sentiment', sentiment,
    'reasons', reasons,
    'note', note,
    'jobSnapshot', jsonb_build_object(
      'title', coalesce(job_snapshot->>'title', ''),
      'company', coalesce(job_snapshot->>'company', ''),
      'location', coalesce(job_snapshot->>'location', ''),
      'sectors', coalesce(job_snapshot->'sectors', '[]'::jsonb),
      'source', coalesce(job_snapshot->>'source', ''),
      'url', coalesce(job_snapshot->>'url', '')
    ),
    'updatedAt', updated_at
  ) order by updated_at), '[]'::jsonb)
  into preference_rows
  from public.job_preferences
  where user_id = claimed.user_id;

  return jsonb_build_object(
    'runId', claimed.id,
    'userId', claimed.user_id,
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
  next_state text;
  owner_id uuid;
begin
  if not private.refresh_worker_secret_matches(worker_secret) then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;
  next_state := run_status->>'state';
  if next_state not in ('running', 'succeeded', 'failed') then
    raise exception 'invalid refresh state';
  end if;

  update public.refresh_runs
  set
    state = next_state,
    status = run_status,
    updated_at = now(),
    started_at = coalesce(started_at, nullif(run_status->>'startedAt', '')::timestamptz, now()),
    finished_at = case
      when next_state in ('succeeded', 'failed') then coalesce(nullif(run_status->>'finishedAt', '')::timestamptz, now())
      else null
    end
  where id = run_id and state in ('running', next_state)
  returning user_id into owner_id;

  if owner_id is null then
    return false;
  end if;

  if next_state = 'succeeded' and personalized_snapshot is not null then
    insert into public.personalized_snapshots (
      user_id,
      generated_at,
      preference_digest,
      job_data_as_of,
      snapshot,
      updated_at
    ) values (
      owner_id,
      (personalized_snapshot->>'generatedAt')::timestamptz,
      personalized_snapshot#>>'{stats,preferenceSummary,digest}',
      coalesce(
        nullif(personalized_snapshot#>>'{stats,jobDataAsOf}', '')::date,
        nullif(personalized_snapshot->>'dataAsOf', '')::date
      ),
      personalized_snapshot,
      now()
    )
    on conflict (user_id) do update
    set
      generated_at = excluded.generated_at,
      preference_digest = excluded.preference_digest,
      job_data_as_of = excluded.job_data_as_of,
      snapshot = excluded.snapshot,
      updated_at = excluded.updated_at;
  end if;

  return true;
end;
$$;

grant execute on function public.claim_refresh_run(text) to anon, authenticated;
grant execute on function public.publish_refresh_run(text, uuid, jsonb, jsonb) to anon, authenticated;

drop policy if exists "personalized_snapshots_insert_own" on public.personalized_snapshots;
drop policy if exists "personalized_snapshots_update_own" on public.personalized_snapshots;
drop policy if exists "personalized_snapshots_delete_own" on public.personalized_snapshots;
revoke insert, update, delete on table public.personalized_snapshots from authenticated;
