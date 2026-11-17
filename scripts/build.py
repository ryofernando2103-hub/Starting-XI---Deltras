"""Merakit halaman dari src/template.html + data + logo.

    python3 scripts/build.py

Hasil:
- dist/index.html    untuk artifact claude.ai (tanpa kerangka dokumen)
- public/index.html  dokumen HTML lengkap untuk hosting web (Vercel)
"""
import base64
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def logo_uri():
    im = Image.open(ROOT / 'assets' / 'logo' / 'seputar-deltras.png').convert('RGBA')
    im = im.crop(im.getbbox())
    h = 96
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=90, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


def team_logo_uri(path):
    if path.suffix == '.svg':
        return 'data:image/svg+xml;base64,' + base64.b64encode(path.read_bytes()).decode()
    im = Image.open(path).convert('RGBA')
    im = im.crop(im.getbbox())
    im.thumbnail((160, 160), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=88, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


SUPABASE_LIB = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>'


def main():
    tpl = (ROOT / 'src' / 'template.html').read_text(encoding='utf8')
    players = (ROOT / 'data' / 'players.json').read_text(encoding='utf8').strip()
    matches = json.loads((ROOT / 'data' / 'matches.json').read_text(encoding='utf8'))
    fixtures = json.loads((ROOT / 'data' / 'fixtures.json').read_text(encoding='utf8'))
    teams = json.loads((ROOT / 'data' / 'teams.json').read_text(encoding='utf8'))
    teams = {k: {'nama': v['nama'], 'pendek': v['pendek'],
                 'logo': team_logo_uri(ROOT / 'assets' / 'teams' / v['logo'])} for k, v in teams.items()}
    compact = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    html = (tpl.replace('__PLAYERS__', players)
               .replace('__FIXTURES__', compact(fixtures))
               .replace('__TEAMS__', compact(teams))
               .replace('__LOGO__', logo_uri())
               .replace('__MATCHES__', json.dumps(matches, ensure_ascii=False, separators=(',', ':'))))
    for token in ('__PLAYERS__', '__LOGO__', '__MATCHES__', '__FIXTURES__', '__TEAMS__'):
        assert token not in html, token
    # Login online (Supabase) hanya untuk versi web; artifact claude.ai tidak bisa menghubungi server luar.
    sbc = json.loads((ROOT / 'data' / 'supabase.json').read_text(encoding='utf8'))
    sb_on = bool(sbc.get('url') and sbc.get('anon_key'))
    web_html = (html.replace('<!--SUPABASE_LIB-->', SUPABASE_LIB if sb_on else '')
                    .replace('__SUPABASE__', compact({'url': sbc['url'], 'key': sbc['anon_key']} if sb_on else {}))
                    .replace('__LIVE__', 'true'))  # /api/live hanya ada di Vercel
    html = html.replace('<!--SUPABASE_LIB-->', '').replace('__SUPABASE__', '{}').replace('__LIVE__', 'false')
    out = ROOT / 'dist' / 'index.html'
    out.write_text(html, encoding='utf8')
    # Versi web: bagian sebelum <div class="app"> (title, font, style) masuk ke <head>.
    head, body = web_html.split('<div class="app">', 1)
    web = ('<!doctype html>\n<html lang="id">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
           '<meta name="theme-color" content="#B41B16">\n'
           '<meta name="description" content="Susun starting XI Deltras FC versimu, lalu bagikan ke sesama Deltamania.">\n'
           '<style>html{padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}'
           'body{margin:0}img{max-width:100%}</style>\n'
           + head + '</head>\n<body>\n<div class="app">' + body + '\n</body>\n</html>\n')
    (ROOT / 'public').mkdir(exist_ok=True)
    (ROOT / 'public' / 'index.html').write_text(web, encoding='utf8')
    print(f'dist/index.html ditulis ({out.stat().st_size // 1024} KB, {len(matches)} laga); login online: {"aktif" if sb_on else "belum diatur"}')


if __name__ == '__main__':
    main()
