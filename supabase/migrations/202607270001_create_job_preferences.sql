create table if not exists public.job_preferences (
  user_id uuid not null references auth.users (id) on delete cascade,
  job_id text not null,
  sentiment text not null check (sentiment in ('liked', 'not_for_me')),
  reasons text[] not null default '{}',
  note text not null default '' check (char_length(note) <= 2000),
  job_snapshot jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, job_id)
);

alter table public.job_preferences enable row level security;

revoke all on table public.job_preferences from anon;
grant select, insert, update, delete on table public.job_preferences to authenticated;

create policy "Users read their own job preferences"
on public.job_preferences
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "Users create their own job preferences"
on public.job_preferences
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "Users update their own job preferences"
on public.job_preferences
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "Users delete their own job preferences"
on public.job_preferences
for delete
to authenticated
using ((select auth.uid()) = user_id);
