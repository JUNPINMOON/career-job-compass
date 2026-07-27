create table if not exists public.personalized_snapshots (
  user_id uuid primary key references auth.users(id) on delete cascade,
  generated_at timestamptz not null,
  preference_digest text,
  job_data_as_of date,
  snapshot jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.personalized_snapshots enable row level security;

grant select, insert, update, delete on table public.personalized_snapshots to authenticated;

create policy "personalized_snapshots_select_own"
on public.personalized_snapshots for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "personalized_snapshots_insert_own"
on public.personalized_snapshots for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "personalized_snapshots_update_own"
on public.personalized_snapshots for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "personalized_snapshots_delete_own"
on public.personalized_snapshots for delete
to authenticated
using ((select auth.uid()) = user_id);
