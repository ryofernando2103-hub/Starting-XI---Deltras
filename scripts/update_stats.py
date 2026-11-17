"""Robot statistik: memperbarui jadwal, skor, dan statistik pemain Deltras dari ileague.id.

    python3 scripts/update_stats.py              # jalan normal (dipakai GitHub Actions)
    python3 scripts/update_stats.py --dry-run    # hanya tampilkan hasil, tidak menulis file
    python3 scripts/update_stats.py --dry-run --from 2026-09-01 --force   # uji pada laga lama

Yang diperbarui:
- data/fixtures.json : tanggal, jam, stadion, dan skor tiap laga
- data/matches.json  : statistik mentah per pemain untuk laga yang sudah selesai,
                       mulai START_DATE (poin dihitung sejak laga vs Persela).
                       Rating dan poin dihitung dari statistik ini (rating_of / points_of).
Koreksi manual bisa ditulis di data/overrides.json dan akan menimpa hasil robot.
"""
import argparse
import datetime as dt
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://www.ileague.id'
CLUB_URL = BASE + '/clubs/single/PEGADAIAN_CHAMPIONSHIP_2026-27/DELTRAS_FC'
START_DATE = '2026-11-21'          # poin dihitung mulai laga ini
WIB = dt.timezone(dt.timedelta(hours=7))
UA = 'Mozilla/5.0 (compatible; StartingXIDeltras/1.0)'

# Nama tim di ileague -> kunci di data/teams.json
TEAM_KEY = {
    'PSBS BIAK': 'psbs', 'DELTRAS FC': 'deltras', 'PS BARITO PUTERA': 'barito', 'RANS NUSANTARA FC': 'rans',
    'PERSIBA BALIKPAPAN': 'persiba', 'PERSELA LAMONGAN': 'persela', 'PERSIS SOLO': 'persis',
    'KENDAL TORNADO FC': 'kendal', 'DE RED FC': 'dered', 'PERSIPURA JAYAPURA': 'persipura',
}
MONTHS = {'januari': 1, 'january': 1, 'februari': 2, 'february': 2, 'maret': 3, 'march': 3, 'april': 4,
          'mei': 5, 'may': 5, 'juni': 6, 'june': 6, 'juli': 7, 'july': 7, 'agustus': 8, 'august': 8,
          'september': 9, 'oktober': 10, 'october': 10, 'november': 11, 'desember': 12, 'december': 12}


def get(url, post=False, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=b'' if post else None, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf8', 'ignore')
        except Exception as e:  # jaringan putus: coba lagi dengan jeda
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def minute(s):
    """'90+4' -> 90, '45(1)' -> 45, '72' -> 72"""
    m = re.match(r'\d+', s or '')
    return int(m.group(0)) if m else None


def stadium(s):
    return ' '.join(w if w.isdigit() else w.capitalize() for w in s.split())


# ---------- 1. daftar laga dari halaman klub ----------
def parse_fixtures(page):
    s = page.index('id="fixtures"')
    seg = page[s:s + 400000]
    parts = re.split(r'<div align="left" style="margin-top:10px" class="col-md-12">', seg)[1:]
    out = []
    for p in parts:
        d, mon, y = p.split('</div>')[0].strip().split()
        date = dt.date(int(y), MONTHS[mon.lower()], int(d)).isoformat()
        teams = [t.strip().upper() for t in re.findall(r'class="club-fixture-team">([^<]+)<', p)]
        if len(teams) < 2 or teams[0] not in TEAM_KEY or teams[1] not in TEAM_KEY:
            print('  ! tim tidak dikenal, dilewati:', teams, file=sys.stderr)
            continue
        sc = text(re.search(r'club-fixture-score".*?</td>', p, re.S).group(0).split('>', 1)[1])
        fin = re.match(r'FT\s*(\d+)\s*:\s*(\d+)', sc)
        tm = re.search(r'(\d{1,2}:\d{2})', sc)
        std = re.findall(r'<td style="border:0" width="23%" align="left">\s*(.*?)\s*</td>', p, re.S)
        url = re.search(r'href="([^"]+/result/detail/[^"]+)"', p)
        out.append({'tanggal': date, 'kandang': TEAM_KEY[teams[0]], 'tamu': TEAM_KEY[teams[1]],
                    'jam': None if fin else (tm.group(1) if tm else None),
                    'skor_kandang': int(fin.group(1)) if fin else None,
                    'skor_tamu': int(fin.group(2)) if fin else None,
                    'stadion': stadium(text(std[0])) if std else '', 'url': url.group(1) if url else None})
    return out


# ---------- 2. susunan & kejadian dari halaman laga ----------
ICON = re.compile(r'<i class="([^"]+)"([^>]*)></i>\s*\'?\s*(\d+(?:\+\d+)?(?:\(\d+\))?)?')


def parse_lineup(page, deltras_home):
    s = page.index('<div class="tab-pane" id="lineup">')
    e = page.index('<div class="tab-pane"', s + 40)
    sides = page[s:e].split('<td class="noborder" style="border-top-color: white;border-top-color: white;">')
    if len(sides) != 2:
        raise ValueError('struktur daftar pemain berubah')
    result = {}
    for side_i, part in enumerate(sides):
        ours = (side_i == 0) == deltras_home
        bench = False
        for tok in re.finditer(r'<h4><b>([^<]+)</b></h4>|<a onclick="statistikPemain\((\d+),(\d+)\)"[^>]*>(.*?)</a>', part, re.S):
            if tok.group(1):
                bench = 'pengganti' in tok.group(1).lower()
                continue
            jadwal, pid, inner = tok.group(2), tok.group(3), tok.group(4)
            before = part[max(0, tok.start() - 260):tok.start()]
            after = part[tok.end():tok.end() + 120]
            num = re.search(r'<span[^>]*btn-xs[^>]*>\s*(\d+)\s*</span>\s*$', before) or re.match(r'\s*<span[^>]*btn-xs[^>]*>\s*(\d+)', after)
            ev = {'goal': [], 'in': None, 'out': None, 'yellow': [], 'red': None}
            for cls, attrs, mn in ICON.findall(inner):
                m = minute(mn)
                if 'futbol' in cls:
                    ev['goal'].append(m)
                elif 'refresh' in cls:
                    if '12CA20' in attrs.upper():
                        ev['in'] = m
                    else:
                        ev['out'] = m
                elif 'yellow' in attrs:
                    ev['yellow'].append(m)
                elif 'red' in attrs:
                    ev['red'] = m
            key = 'deltras' if ours else 'lawan'
            result.setdefault(key, []).append({'jadwal': jadwal, 'pid': pid, 'num': int(num.group(1)) if num else None,
                                               'nama': text(re.sub(r'<span.*?</span>|<p.*?</p>', ' ', inner, flags=re.S)),
                                               'cadangan': bench, **ev})
    return result


def played_window(p):
    """(menit masuk, menit keluar) atau None bila tidak bermain."""
    start = 0 if not p['cadangan'] else p['in']
    if start is None:
        return None
    end = 90
    if p['out'] is not None and (p['cadangan'] or p['out'] < 90):
        end = min(90, p['out'])
    if p['red'] is not None:
        end = min(end, p['red'])
    return start, max(start, end)


# ---------- 3. statistik per pemain ----------
# label ileague -> kunci pendek yang dipakai website (lihat ratingOf di src/template.html)
LABELS = [('FOULED', 'fd'), ('FOUL', 'fl'), ('YELLOW CARD', 'yc'), ('PASSING', 'pa'), ('ASSIST', 'a'),
          ('CREATE CHANCE', 'cc'), ('DRIBBLE SUCCESS', 'dr'), ('BLOCK', 'bl'), ('CLEARANCE', 'cl'),
          ('INTERCEPT', 'ic'), ('TACKLE', 'tk'), ('BALL RECOVERY', 'rb'), ('OWN GOAL', 'og'),
          ('SHOOT OFF TARGET', 'sof'), ('SHOOT ON TARGET', 'sot'), ('GOAL CONCIDED', 'gc_ileague'),
          ('GOAL', 'g'), ('SAVES', 'sv')]


def player_stats(jadwal, pid):
    t = text(get(f'{BASE}/result/get_statistikpemain/{jadwal}/{pid}', post=True))
    out = {}
    for label, k in LABELS:
        m = re.search(r'(?<![A-Z] )\b' + re.escape(label) + r'\s+(\d+)', t)
        if m:
            out[k] = int(m.group(1))
    return out


def match_stats(fx, page, squad):
    deltras_home = fx['kandang'] == 'deltras'
    lu = parse_lineup(page, deltras_home)
    conceded = fx['skor_tamu'] if deltras_home else fx['skor_kandang']
    opp_goals = sorted(m for p in lu.get('lawan', []) for m in p['goal'] if m is not None)
    pemain, warn = {}, []
    for p in lu.get('deltras', []):
        win = played_window(p)
        if win is None:
            continue
        if p['num'] not in squad:
            warn.append(f"#{p['num']} {p['nama']} tidak ada di skuad, dilewati")
            continue
        st = player_stats(p['jadwal'], p['pid'])
        time.sleep(0.6)
        a, b = win
        gc = sum(1 for m in opp_goals if a <= m <= b) if len(opp_goals) == conceded else None
        row = {'m': max(1, b - a)}
        for k in ('g', 'a', 'sv', 'yc', 'og', 'pa', 'cc', 'sot', 'sof', 'dr', 'tk', 'bl', 'ic', 'cl', 'rb', 'fl', 'fd'):
            if st.get(k):
                row[k] = st[k]
        if not row.get('g') and p['goal']:
            row['g'] = len(p['goal'])
        if not row.get('yc') and p['yellow']:
            row['yc'] = len(p['yellow'])
        if p['red'] is not None:
            row['rc'] = 1
        row['gc'] = gc if gc is not None else (st.get('gc_ileague') if st.get('gc_ileague') is not None else conceded)
        pemain[str(p['num'])] = row
    return {'tanggal': fx['tanggal'], 'kebobolan': conceded, 'sumber': 'ileague.id', 'pemain': pemain}, warn


def merge_override(entry, ov):
    o = ov.get(entry['tanggal'])
    if not o:
        return entry
    if 'kebobolan' in o:
        entry['kebobolan'] = o['kebobolan']
    for num, vals in (o.get('pemain') or {}).items():
        if vals is None:
            entry['pemain'].pop(num, None)
        else:
            entry['pemain'].setdefault(num, {}).update(vals)
    return entry


def needs_network(fixtures, matches, start, force):
    if force:
        return True
    now = dt.datetime.now(WIB)
    done = {m['tanggal'] for m in matches}
    for f in fixtures:
        ko = dt.datetime.fromisoformat(f['tanggal'] + 'T' + (f['jam'] or '19:00') + ':00+07:00')
        recent = ko - dt.timedelta(hours=1) <= now <= ko + dt.timedelta(days=3)
        if recent and (f['skor_kandang'] is None or (f['tanggal'] >= start and f['tanggal'] not in done)):
            return True
    return False


# ---------- 4. poin & sinkron ke Supabase (untuk peringkat) ----------
RW_GOAL = {'FW': 1.4, 'MF': 1.6, 'DF': 2.0, 'GK': 2.0}
RW_CONC = {'GK': .35, 'DF': .2, 'MF': .08, 'FW': 0}
RW_CS = {'GK': .8, 'DF': .6, 'MF': .25, 'FW': 0}
RW_CLR = {'GK': .06, 'DF': .06, 'MF': .04, 'FW': .04}


def floor_half(x):
    return math.floor(x + .5)


def rating_of(pos, s, ga, res):
    """Rating Starting XI 3,0-10,0. Sama persis dengan ratingOf() di src/template.html."""
    m = s.get('m', 0)
    if not m:
        return None
    gc = s['gc'] if s.get('gc') is not None else (ga or 0)
    d = s.get('g', 0) * RW_GOAL[pos] + s.get('a', 0) * 1
    d += s.get('cc', 0) * .25 + s.get('sot', 0) * .15 - s.get('sof', 0) * .05
    d += s.get('dr', 0) * .12 + s.get('tk', 0) * .15 + s.get('ic', 0) * .1 + s.get('bl', 0) * .15
    d += s.get('cl', 0) * RW_CLR[pos] + s.get('rb', 0) * .05 + min(.6, s.get('pa', 0) * .012)
    d -= s.get('fl', 0) * .08
    d += s.get('fd', 0) * .04
    if pos == 'GK':
        d += min(2, s.get('sv', 0) * .25)
    d -= gc * RW_CONC[pos]
    if m >= 60 and gc == 0:
        d += RW_CS[pos]
    d -= s.get('og', 0) * 1.2
    d += .3 if res > 0 else -.2 if res < 0 else 0
    d *= min(1, m / 45)
    return math.floor(min(10, max(3, 6 + d)) * 10 + .5) / 10


def points_of(pos, s, ga, res=0):
    """Poin = poin main + (rating - 6,0) x 2,5, dikurangi kartu. Sama dengan pointsOf() di website."""
    m = s.get('m', 0)
    if not m:
        return 0
    rt = rating_of(pos, s, ga, res)
    return ((2 if m >= 60 else 1) + floor_half((rt - 6) * 2.5) - s.get('yc', 0) - s.get('rc', 0) * 3
            + s.get('ps', 0) * 5 - s.get('pm', 0) * 2)


def result_of(fixtures, date):
    for f in fixtures:
        if f['tanggal'] == date and f['skor_kandang'] is not None:
            us, th = (f['skor_kandang'], f['skor_tamu']) if f['kandang'] == 'deltras' else (f['skor_tamu'], f['skor_kandang'])
            return (us > th) - (us < th)
    return 0


def sb_headers(key):
    """Kunci baru (sb_secret_...) bukan JWT: kirim hanya lewat 'apikey'. Kunci lama (JWT) juga lewat Authorization."""
    # Supabase menolak kunci rahasia bila User-Agent tampak seperti browser (Mozilla/...), jadi pakai identitas robot.
    h = {'apikey': key, 'Content-Type': 'application/json',
         'Prefer': 'resolution=merge-duplicates,return=minimal', 'User-Agent': 'starting-xi-deltras-robot/1.0'}
    if key.count('.') == 2:   # bentuk JWT, mis. service_role lama
        h['Authorization'] = f'Bearer {key}'
    return h


def sb_upsert(table, rows, conflict):
    url, key = os.environ.get('SUPABASE_URL', '').strip().rstrip('/'), os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
    if not rows:
        return
    req = urllib.request.Request(f'{url}/rest/v1/{table}?on_conflict={conflict}', data=json.dumps(rows).encode(),
                                 method='POST', headers=sb_headers(key))
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf8', 'ignore')[:500]
        hint = ''
        if e.code in (401, 403):
            hint = (' | Petunjuk: kunci SUPABASE_SERVICE_KEY ditolak. Pastikan itu kunci rahasia (sb_secret_... atau '
                    'service_role), disalin utuh, dan SUPABASE_URL berbentuk https://<id>.supabase.co tanpa garis miring.')
        print(f'Supabase menolak permintaan ke tabel {table}: HTTP {e.code} {body}{hint}', file=sys.stderr)
        raise SystemExit(1)


def sync_supabase(fixtures, matches):
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_SERVICE_KEY'):
        print('Supabase belum diatur (SUPABASE_URL / SUPABASE_SERVICE_KEY), sinkron dilewati.')
        return
    pos = {p['num']: p['pos'] for p in json.loads((ROOT / 'data' / 'players.json').read_text(encoding='utf8'))}
    sb_upsert('fixtures', [{'tanggal': f['tanggal'], 'kandang': f['kandang'], 'tamu': f['tamu'],
                            'kickoff': f['tanggal'] + 'T' + (f['jam'] or '19:00') + ':00+07:00',
                            'skor_kandang': f['skor_kandang'], 'skor_tamu': f['skor_tamu']} for f in fixtures], 'tanggal')
    pts = [{'tanggal': m['tanggal'], 'num': int(n), 'points': points_of(pos[int(n)], s, m.get('kebobolan'), result_of(fixtures, m['tanggal']))}
           for m in matches if m['tanggal'] >= START_DATE for n, s in m['pemain'].items() if int(n) in pos]
    sb_upsert('player_points', pts, 'tanggal,num')
    print(f'Supabase: {len(fixtures)} jadwal, {len(pts)} poin pemain disinkronkan.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--from', dest='start', default=START_DATE)
    ap.add_argument('--force', action='store_true', help='tetap periksa ileague walau tidak ada laga baru')
    args = ap.parse_args()

    fx_path, mt_path, ov_path = ROOT / 'data' / 'fixtures.json', ROOT / 'data' / 'matches.json', ROOT / 'data' / 'overrides.json'
    fixtures = json.loads(fx_path.read_text(encoding='utf8'))
    matches = json.loads(mt_path.read_text(encoding='utf8'))
    overrides = json.loads(ov_path.read_text(encoding='utf8')) if ov_path.exists() else {}
    squad = {p['num'] for p in json.loads((ROOT / 'data' / 'players.json').read_text(encoding='utf8'))}

    if not needs_network(fixtures, matches, args.start, args.force):
        print('Tidak ada laga yang perlu diperiksa sekarang.')
        return

    print('Mengambil jadwal dari ileague.id ...')
    remote = parse_fixtures(get(CLUB_URL))
    by_pair = {(f['kandang'], f['tamu']): f for f in remote}
    new_fixtures = []
    for f in fixtures:
        r = by_pair.get((f['kandang'], f['tamu']))
        if not r:
            new_fixtures.append(f)
            continue
        nf = {k: r[k] for k in ('tanggal', 'jam', 'kandang', 'tamu', 'skor_kandang', 'skor_tamu', 'stadion')}
        if nf['jam'] is None and f['tanggal'] == nf['tanggal']:
            nf['jam'] = f['jam']   # ileague tidak lagi menampilkan jam setelah laga selesai
        new_fixtures.append(nf)
    changed_fx = new_fixtures != fixtures

    done = {m['tanggal'] for m in matches}
    added = []
    for f in sorted(by_pair.values(), key=lambda x: x['tanggal']):
        if f['tanggal'] < args.start or f['skor_kandang'] is None or not f['url']:
            continue
        if f['tanggal'] in done and not args.force:
            continue
        print(f"Membaca laga {f['tanggal']} {f['kandang']} {f['skor_kandang']}-{f['skor_tamu']} {f['tamu']} ...")
        page = get(f['url'])
        if 'id="lineup"' not in page or 'statistikPemain' not in page:
            print('  susunan pemain belum tersedia, dicoba lagi nanti')
            continue
        entry, warn = match_stats(f, page, squad)
        for w in warn:
            print('  !', w)
        if not entry['pemain']:
            print('  statistik pemain belum tersedia, dicoba lagi nanti')
            continue
        added.append(merge_override(entry, overrides))

    pos_of = {p['num']: p for p in json.loads((ROOT / 'data' / 'players.json').read_text(encoding='utf8'))}
    for e in added:
        res = result_of(new_fixtures, e['tanggal'])
        print(f"\n== {e['tanggal']} (kebobolan {e['kebobolan']}, hasil {'menang' if res > 0 else 'kalah' if res < 0 else 'seri'}) ==")
        for num, row in sorted(e['pemain'].items(), key=lambda x: int(x[0])):
            pl = pos_of.get(int(num))
            rt = rating_of(pl['pos'], row, e['kebobolan'], res) if pl else None
            pt = points_of(pl['pos'], row, e['kebobolan'], res) if pl else None
            print(f"  #{num:>2} {pl['short'] if pl else '?':<11} rating {rt}  poin {pt}  {row}")

    if args.dry_run:
        print('\n[dry-run] tidak ada file yang ditulis. Jadwal berubah:', changed_fx)
        return
    sync_supabase(new_fixtures, [m for m in matches if m['tanggal'] not in {e['tanggal'] for e in added}] + added)
    if changed_fx:
        fx_path.write_text(json.dumps(new_fixtures, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
        print('fixtures.json diperbarui')
    if added:
        keep = [m for m in matches if m['tanggal'] not in {e['tanggal'] for e in added}]
        mt_path.write_text(json.dumps(sorted(keep + added, key=lambda m: m['tanggal']), ensure_ascii=False, indent=1) + '\n', encoding='utf8')
        print(f'matches.json diperbarui ({len(added)} laga)')
    if not changed_fx and not added:
        print('Tidak ada perubahan.')


if __name__ == '__main__':
    main()
