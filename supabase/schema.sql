-- =====================================================================
-- Starting XI Deltras: skema database Supabase
-- Jalankan sekali di Supabase: SQL Editor -> New query -> tempel semua -> Run.
-- Aman dijalankan ulang (idempotent).
-- =====================================================================

-- ---------- Profil coach ----------
create table if not exists public.profiles (
  id          uuid primary key references auth.users on delete cascade,
  coach_name  text not null default 'Coach' check (char_length(coach_name) between 1 and 28),
  created_at  timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, coach_name)
  values (new.id, left(coalesce(nullif(new.raw_user_meta_data->>'full_name', ''),
                                nullif(new.raw_user_meta_data->>'name', ''),
                                nullif(split_part(new.email, '@', 1), ''), 'Coach'), 28))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- Jadwal (diisi robot statistik) ----------
create table if not exists public.fixtures (
  tanggal       date primary key,
  kandang       text not null,
  tamu          text not null,
  kickoff       timestamptz not null,
  skor_kandang  int,
  skor_tamu     int
);

-- Susunan dikunci dari deadline (2 jam sebelum kick-off) sampai 2 jam setelah kick-off.
create or replace function public.lineup_locked()
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.fixtures f
    where now() >= f.kickoff - interval '2 hours' and now() < f.kickoff + interval '2 hours'
  );
$$;

-- ---------- Susunan aktif tiap coach ----------
-- data = {"rows":[4,3,3], "xi":[11 nomor/null], "bench":[<=10 nomor/null], "cap":n, "vice":n, "pos":{}}
create or replace function public.valid_lineup(d jsonb)
returns boolean language plpgsql immutable set search_path = '' as $$
declare nums int[];
begin
  if jsonb_typeof(d->'xi') <> 'array' or jsonb_array_length(d->'xi') <> 11 then return false; end if;
  if jsonb_typeof(d->'bench') <> 'array' or jsonb_array_length(d->'bench') > 10 then return false; end if;
  if jsonb_typeof(d->'rows') <> 'array' then return false; end if;
  select array_agg(v::int) into nums
  from (select jsonb_array_elements(d->'xi') as v union all select jsonb_array_elements(d->'bench')) s
  where jsonb_typeof(v) = 'number';
  -- tidak boleh ada pemain ganda (mencegah poin dobel)
  if nums is not null and cardinality(nums) <> (select count(distinct x) from unnest(nums) x) then return false; end if;
  -- kapten & wakil harus ada di starting XI
  if jsonb_typeof(d->'cap') = 'number' and not (d->'xi') @> jsonb_build_array(d->'cap') then return false; end if;
  if jsonb_typeof(d->'vice') = 'number' and not (d->'xi') @> jsonb_build_array(d->'vice') then return false; end if;
  return true;
exception when others then
  return false;
end $$;

create table if not exists public.lineups (
  user_id     uuid primary key default auth.uid() references auth.users on delete cascade,
  data        jsonb not null check (public.valid_lineup(data)),
  updated_at  timestamptz not null default now()
);

-- ---------- Riwayat susunan per laga (dicatat otomatis saat deadline) ----------
create table if not exists public.lineup_history (
  tanggal  date not null references public.fixtures on delete cascade,
  user_id  uuid not null references auth.users on delete cascade,
  data     jsonb not null,
  primary key (tanggal, user_id)
);

create table if not exists public.snapshot_log (
  tanggal  date primary key references public.fixtures on delete cascade,
  taken_at timestamptz not null default now()
);

-- ---------- Poin pemain per laga (diisi robot statistik) ----------
create table if not exists public.player_points (
  tanggal  date not null references public.fixtures on delete cascade,
  num      int  not null,
  points   int  not null,
  primary key (tanggal, num)
);

-- ---------- Row Level Security ----------
alter table public.profiles       enable row level security;
alter table public.fixtures       enable row level security;
alter table public.lineups        enable row level security;
alter table public.lineup_history enable row level security;
alter table public.snapshot_log   enable row level security;
alter table public.player_points  enable row level security;

drop policy if exists "profil sendiri dibaca"   on public.profiles;
drop policy if exists "profil sendiri diubah"   on public.profiles;
create policy "profil sendiri dibaca" on public.profiles for select to authenticated using (id = auth.uid());
create policy "profil sendiri diubah" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists "jadwal publik" on public.fixtures;
create policy "jadwal publik" on public.fixtures for select to anon, authenticated using (true);

drop policy if exists "poin publik" on public.player_points;
create policy "poin publik" on public.player_points for select to anon, authenticated using (true);

drop policy if exists "susunan sendiri dibaca"  on public.lineups;
drop policy if exists "susunan sendiri dibuat"  on public.lineups;
drop policy if exists "susunan sendiri diubah"  on public.lineups;
create policy "susunan sendiri dibaca" on public.lineups for select to authenticated using (user_id = auth.uid());
create policy "susunan sendiri dibuat" on public.lineups for insert to authenticated
  with check (user_id = auth.uid() and not public.lineup_locked());
create policy "susunan sendiri diubah" on public.lineups for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid() and not public.lineup_locked());

drop policy if exists "riwayat sendiri dibaca" on public.lineup_history;
create policy "riwayat sendiri dibaca" on public.lineup_history for select to authenticated using (user_id = auth.uid());
-- snapshot_log: tanpa policy = hanya fungsi & service role.

-- ---------- Pencatatan susunan saat deadline ----------
create or replace function public.snapshot_due_lineups()
returns int language plpgsql security definer set search_path = '' as $$
declare f record; n int := 0;
begin
  for f in
    select x.tanggal from public.fixtures x
    where x.kickoff - interval '2 hours' <= now()
      and x.kickoff > now() - interval '3 days'
      and not exists (select 1 from public.snapshot_log s where s.tanggal = x.tanggal)
  loop
    insert into public.lineup_history (tanggal, user_id, data)
      select f.tanggal, l.user_id, l.data from public.lineups l
      on conflict do nothing;
    insert into public.snapshot_log (tanggal) values (f.tanggal);
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.snapshot_due_lineups() from public, anon, authenticated;

-- ---------- Peringkat ----------
create or replace function public.leaderboard(lim int default 100)
returns table (peringkat bigint, user_id uuid, coach_name text, poin bigint, laga bigint)
language sql stable security definer set search_path = '' as $$
  with per as (
    select h.user_id, h.tanggal,
      coalesce((
        select sum(pp.points * case when x.v::int = (h.data->>'cap')::int then 2 else 1 end)
        from jsonb_array_elements_text(h.data->'xi') as x(v)
        join public.player_points pp on pp.tanggal = h.tanggal and pp.num = x.v::int
        where x.v is not null
      ), 0) as pts
    from public.lineup_history h
    where exists (select 1 from public.player_points p where p.tanggal = h.tanggal)
  )
  select rank() over (order by sum(per.pts) desc), p.id, p.coach_name, sum(per.pts)::bigint, count(*)::bigint
  from per join public.profiles p on p.id = per.user_id
  group by p.id, p.coach_name
  order by 4 desc, 3 asc
  limit greatest(1, least(lim, 500));
$$;
grant execute on function public.leaderboard(int) to anon, authenticated;
grant execute on function public.lineup_locked() to anon, authenticated;

-- ---------- Jadwal otomatis pencatatan (pg_cron, tiap 5 menit) ----------
-- @cron-begin
create extension if not exists pg_cron;
select cron.unschedule('tata-tim-snapshot') where exists (select 1 from cron.job where jobname = 'tata-tim-snapshot');
select cron.schedule('tata-tim-snapshot', '*/5 * * * *', 'select public.snapshot_due_lineups()');
-- @cron-end
