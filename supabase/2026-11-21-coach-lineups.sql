-- Tambahan 21 Nov 2026: susunan coach bisa dilihat dari peringkat.
-- Jalankan sekali di Supabase: SQL Editor -> New query -> tempel semua -> Run.
-- Aman dijalankan ulang. Isi yang sama juga sudah ada di schema.sql.

-- ---------- Susunan coach di peringkat (hanya laga yang sudah lewat deadline) ----------
create or replace function public.coach_lineups(uid uuid)
returns table (tanggal date, data jsonb, pts jsonb, total int)
language sql stable security definer set search_path = '' as $$
  select h.tanggal, h.data,
    coalesce((
      select jsonb_object_agg(pp.num::text, pp.points)
      from public.player_points pp
      where pp.tanggal = h.tanggal
        and ((h.data->'xi') @> to_jsonb(pp.num) or (h.data->'bench') @> to_jsonb(pp.num))
    ), '{}'::jsonb),
    (
      select sum(pp.points * case when x.v::int = (h.data->>'cap')::int then 2 else 1 end)::int
      from jsonb_array_elements_text(h.data->'xi') as x(v)
      join public.player_points pp on pp.tanggal = h.tanggal and pp.num = x.v::int
      where x.v is not null
    )
  from public.lineup_history h
  join public.fixtures f on f.tanggal = h.tanggal
  where h.user_id = uid
    and f.kickoff - interval '2 hours' <= now()
  order by h.tanggal desc;
$$;
grant execute on function public.coach_lineups(uuid) to anon, authenticated;
