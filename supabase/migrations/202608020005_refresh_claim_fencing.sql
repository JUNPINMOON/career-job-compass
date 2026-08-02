-- Fence every refresh attempt with a server-issued opaque token.
--
-- Only a SHA-256 verifier is retained in the database.  The clear token is
-- returned once to the claimant and must accompany heartbeats and every
-- progress/terminal publication.  The old publication signature remains for
-- PostgREST compatibility, but it fails closed instead of bypassing fencing.

alter table public.refresh_runs
  add column if not exists claim_token_hash text;

alter table public.refresh_runs
  add constraint refresh_runs_claim_token_hash_format
    check (claim_token_hash is null or claim_token_hash ~ '^[0-9a-f]{64}$')
    not valid;

create or replace function private.refresh_claim_token_hash(candidate text)
returns text
language sql
immutable
security definer
set search_path = ''
as $$
  select case
    when length(coalesce(candidate, '')) between 32 and 256 then
      encode(
        extensions.digest(convert_to(candidate, 'UTF8'), 'sha256'),
        'hex'
      )
    else null
  end;
$$;

revoke all on function private.refresh_claim_token_hash(text)
from public, anon, authenticated;

-- Preserve the previously validated implementations behind names that cannot
-- be invoked through PostgREST.  The wrappers below add attempt fencing while
-- retaining the existing public claim and publication argument signatures.
alter function public.claim_refresh_run(text)
  rename to claim_refresh_run_unfenced_legacy;

alter function public.publish_refresh_run(text, uuid, jsonb, jsonb)
  rename to publish_refresh_run_unfenced_legacy;

revoke all on function public.claim_refresh_run_unfenced_legacy(text)
from public, anon, authenticated;

revoke all on function public.publish_refresh_run_unfenced_legacy(text, uuid, jsonb, jsonb)
from public, anon, authenticated;

create or replace function public.claim_refresh_run(worker_secret text)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  claimed_payload jsonb;
  clear_claim_token text;
  token_hash text;
  claimed_row_count integer;
begin
  -- The legacy function authenticates, locks, and claims the row.  Its row
  -- lock remains held until this outer RPC transaction commits.
  claimed_payload := public.claim_refresh_run_unfenced_legacy(worker_secret);
  if claimed_payload is null then
    return null;
  end if;

  clear_claim_token := extensions.gen_random_uuid()::text;
  token_hash := private.refresh_claim_token_hash(clear_claim_token);
  if token_hash is null then
    raise exception 'server failed to create a refresh claim token';
  end if;

  update public.refresh_runs as claimed_run
  set claim_token_hash = token_hash
  where claimed_run.id = (claimed_payload->>'runId')::uuid
    and claimed_run.user_id = (claimed_payload->>'userId')::uuid
    and claimed_run.worker_id = (claimed_payload->>'workerId')::uuid
    and claimed_run.state = 'running'
    and claimed_run.lease_expires_at > clock_timestamp();

  get diagnostics claimed_row_count = row_count;
  if claimed_row_count <> 1 then
    raise exception 'refresh claim fencing failed' using errcode = '55000';
  end if;

  return claimed_payload || jsonb_build_object('claimToken', clear_claim_token);
end;
$$;

revoke all on function public.claim_refresh_run(text) from public;
grant execute on function public.claim_refresh_run(text) to anon, authenticated;

create or replace function public.heartbeat_refresh_run(
  worker_secret text,
  run_id uuid,
  user_id uuid,
  claim_token text
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  active_worker_id uuid;
  presented_token_hash text;
  heartbeat_time timestamptz := clock_timestamp();
  updated_row_count integer;
begin
  active_worker_id := private.refresh_worker_identity(worker_secret);
  if active_worker_id is null then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;

  presented_token_hash := private.refresh_claim_token_hash(claim_token);
  if presented_token_hash is null then
    return false;
  end if;

  update public.refresh_runs as run
  set
    heartbeat_at = heartbeat_time,
    updated_at = heartbeat_time,
    lease_expires_at = heartbeat_time + interval '5 minutes'
  where run.id = heartbeat_refresh_run.run_id
    and run.user_id = heartbeat_refresh_run.user_id
    and run.state = 'running'
    and run.worker_id = active_worker_id
    and run.claim_token_hash = presented_token_hash
    and run.lease_expires_at > heartbeat_time;

  get diagnostics updated_row_count = row_count;
  return updated_row_count = 1;
end;
$$;

revoke all on function public.heartbeat_refresh_run(text, uuid, uuid, text) from public;
grant execute on function public.heartbeat_refresh_run(text, uuid, uuid, text)
to anon, authenticated;

create or replace function public.publish_refresh_run_fenced(
  worker_secret text,
  run_id uuid,
  user_id uuid,
  claim_token text,
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
  presented_token_hash text;
  checked_at timestamptz := clock_timestamp();
begin
  active_worker_id := private.refresh_worker_identity(worker_secret);
  if active_worker_id is null then
    raise exception 'worker authentication failed' using errcode = '42501';
  end if;

  presented_token_hash := private.refresh_claim_token_hash(claim_token);
  if presented_token_hash is null then
    return false;
  end if;

  select run.*
  into claimed
  from public.refresh_runs as run
  where run.id = publish_refresh_run_fenced.run_id
    and run.user_id = publish_refresh_run_fenced.user_id
  for update;

  if claimed.id is null then
    return false;
  end if;
  if claimed.worker_id is distinct from active_worker_id
     or claimed.claim_token_hash is distinct from presented_token_hash then
    return false;
  end if;

  -- An active lease is mandatory while the attempt can still mutate state.
  -- For a terminal row, the same token may retry the exact terminal payload so
  -- a lost HTTP response can be resolved by the legacy idempotency hash check.
  if claimed.state = 'running' then
    if claimed.lease_expires_at is null
       or claimed.lease_expires_at <= checked_at then
      return false;
    end if;
  elsif claimed.state not in ('succeeded', 'failed') then
    return false;
  end if;

  return public.publish_refresh_run_unfenced_legacy(
    publish_refresh_run_fenced.worker_secret,
    publish_refresh_run_fenced.run_id,
    publish_refresh_run_fenced.run_status,
    publish_refresh_run_fenced.personalized_snapshot
  );
end;
$$;

revoke all on function public.publish_refresh_run_fenced(
  text, uuid, uuid, text, jsonb, jsonb
) from public;
grant execute on function public.publish_refresh_run_fenced(
  text, uuid, uuid, text, jsonb, jsonb
) to anon, authenticated;

-- Compatibility sentinel: clients still calling the old signature receive an
-- explicit error, never an unfenced write.  The function stays discoverable so
-- mixed-version deployments fail loudly instead of silently dropping updates.
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
begin
  raise exception 'claim token is required; use publish_refresh_run_fenced'
    using errcode = '42501';
end;
$$;

revoke all on function public.publish_refresh_run(text, uuid, jsonb, jsonb) from public;
grant execute on function public.publish_refresh_run(text, uuid, jsonb, jsonb)
to anon, authenticated;
