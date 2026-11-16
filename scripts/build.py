"""Merakit dist/index.html dari src/template.html + data + logo.

    python3 scripts/build.py

dist/index.html adalah file yang dipublikasikan sebagai artifact.
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


def main():
    tpl = (ROOT / 'src' / 'template.html').read_text(encoding='utf8')
    players = (ROOT / 'data' / 'players.json').read_text(encoding='utf8').strip()
    matches = json.loads((ROOT / 'data' / 'matches.json').read_text(encoding='utf8'))
    html = (tpl.replace('__PLAYERS__', players)
               .replace('__LOGO__', logo_uri())
               .replace('__MATCHES__', json.dumps(matches, ensure_ascii=False, separators=(',', ':'))))
    for token in ('__PLAYERS__', '__LOGO__', '__MATCHES__'):
        assert token not in html, token
    out = ROOT / 'dist' / 'index.html'
    out.write_text(html, encoding='utf8')
    print(f'dist/index.html ditulis ({out.stat().st_size // 1024} KB, {len(matches)} laga)')


if __name__ == '__main__':
    main()
