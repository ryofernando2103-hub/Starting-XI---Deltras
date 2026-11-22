"""Membuat favicon dan ikon aplikasi dari lambang di logo Seputar Deltras.

    python3 scripts/make_icons.py

Hasil di public/: favicon.ico, icon-192.png, icon-512.png, apple-touch-icon.png, site.webmanifest
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RED = (180, 27, 22, 255)


def crest():
    im = Image.open(ROOT / 'assets' / 'logo' / 'seputar-deltras.png').convert('RGBA')
    part = im.crop((int(im.width * 0.68), 0, im.width, im.height))
    return part.crop(part.getbbox())


def icon(size, rounded):
    c = crest()
    bg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    mask = Image.new('L', (size, size), 0)
    r = int(size * 0.22) if rounded else 0
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=255)
    bg.paste(Image.new('RGBA', (size, size), RED), (0, 0), mask)
    box = int(size * 0.78)
    c.thumbnail((box, box), Image.LANCZOS)
    bg.alpha_composite(c, ((size - c.width) // 2 + int(size * 0.01), (size - c.height) // 2))
    return bg


def main():
    out = ROOT / 'public'
    icon(512, True).save(out / 'icon-512.png')
    icon(192, True).save(out / 'icon-192.png')
    icon(180, False).convert('RGB').save(out / 'apple-touch-icon.png')   # iOS membulatkan sudut sendiri
    icon(256, True).save(out / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    (out / 'site.webmanifest').write_text(json.dumps({
        'name': 'Starting XI Deltras', 'short_name': 'Starting XI',
        'start_url': '/', 'display': 'standalone',
        'background_color': '#F2F2F4', 'theme_color': '#B41B16',
        'icons': [{'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}],
    }, indent=2) + '\n')
    print('ikon dibuat di public/')


if __name__ == '__main__':
    main()
