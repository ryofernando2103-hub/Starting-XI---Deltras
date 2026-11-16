"""Menyiapkan data/players.json dari data/squad_source.json + assets/photos/.

Jalankan ulang setiap ada perubahan roster, nama, atau foto:
    python3 scripts/prep_players.py
"""
import base64
import io
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# Nama pendek yang tampil di kartu lapangan (per nomor punggung).
SHORT = {21: 'Havidz', 29: 'Reimas', 33: 'Rohim', 81: 'Rafi', 3: 'Nirwanto', 4: 'Taher',
         13: 'Idris', 15: 'A. Dwi', 16: 'Raditya', 17: 'Usemahu', 26: 'Marckho', 31: 'Deo',
         35: 'Reza', 45: 'Ibrohim', 5: 'Qadri', 6: 'Mandacingi', 8: 'Ananta', 14: 'Hariono',
         19: 'Pellu', 22: 'Ichasan', 28: 'Gading', 87: 'Shulton', 9: 'Irman', 10: 'Mochine',
         11: 'Wigi', 18: 'Martinus', 20: 'Aulia', 23: 'Hamdi', 25: 'Ketut', 27: 'Rafly',
         30: 'Nathan', 32: 'Aqila', 77: 'Lopez'}

# Koreksi nama lengkap dari sumber.
NAME_FIX = {32: 'Aqila Agustian'}

# Di deltrasfc.com, foto #35 dan #45 adalah file yang identik, jadi keduanya
# ditampilkan dengan inisial sampai ada foto yang benar.
NO_PHOTO = {35, 45}


def tidy(name):
    name = re.sub(r'\s+', ' ', name).strip().title()
    name = re.sub(r'^([A-Z]) ', r'\1. ', name)
    return re.sub(r' ([A-Z])$', r' \1.', name)


def photo_uri(num):
    path = ROOT / 'assets' / 'photos' / f'{num}.png'
    if num in NO_PHOTO or not path.exists():
        return None
    im = Image.open(path).convert('RGBA').resize((121, 147), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=78, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


def main():
    src = json.loads((ROOT / 'data' / 'squad_source.json').read_text(encoding='utf8'))
    out = []
    for p in src:
        n = p['number']
        out.append(dict(id=n, num=n, name=NAME_FIX.get(n, tidy(p['name'])), short=SHORT[n],
                        pos=p['position'], age=p['age'], country=p['country'], photo=photo_uri(n)))
    (ROOT / 'data' / 'players.json').write_text(
        json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    print(f'{len(out)} pemain ditulis ke data/players.json')


if __name__ == '__main__':
    main()
