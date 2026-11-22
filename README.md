# Starting XI Deltras

Website untuk menyusun starting XI **Deltras FC** bergaya Fantasy Premier League, dibuat untuk **Seputar Deltras**. Pengguna memilih formasi, menempatkan 11 pemain dan 7 cadangan, menunjuk kapten, lalu membagikan susunannya sebagai gambar PNG.

Halaman ini berupa satu file HTML mandiri. Semua data, foto, dan logo tertanam di dalamnya, jadi tidak perlu server.

- `public/index.html`: versi web, dihosting di Vercel (`vercel.json` mengarahkan Vercel ke folder `public`).
- `dist/index.html`: versi artifact claude.ai.

## Struktur

| Path | Isi |
|---|---|
| `src/template.html` | Kode halaman (HTML, CSS, JS) dengan placeholder `__PLAYERS__`, `__LOGO__`, `__MATCHES__` |
| `data/squad_source.json` | Data skuad mentah: nama dan posisi dari deltrasfc.com, usia dan negara dari ileague.id |
| `data/players.json` | Data pemain siap pakai beserta foto (dibuat oleh `prep_players.py`) |
| `data/fixtures.json` | Jadwal dan hasil laga Deltras (dari ileague.id) |
| `data/teams.json` | Nama tim dan file logo |
| `data/matches.json` | Statistik per laga untuk menghitung poin |
| `assets/photos/` | Foto asli pemain per nomor punggung |
| `assets/logo/` | Logo Seputar Deltras |
| `assets/teams/` | Logo tim peserta (RANS sementara dari ileague.id) |
| `scripts/prep_players.py` | Membuat `data/players.json` (nama pendek, koreksi nama, kompres foto) |
| `scripts/build.py` | Merakit `dist/index.html` |
| `public/index.html` | Hasil akhir untuk website (Vercel) |
| `dist/index.html` | Hasil akhir untuk artifact claude.ai |

## Membangun ulang

Perlu Python 3 dan Pillow (`pip install pillow`).

```bash
python3 scripts/prep_players.py   # hanya jika roster, nama, atau foto berubah
python3 scripts/build.py
```

## Login & peringkat (Supabase)

Login (Google atau tautan email), susunan tersimpan online, riwayat per laga, dan tab Peringkat aktif setelah
`data/supabase.json` diisi Project URL dan anon key. Skema database ada di `supabase/schema.sql`.
Langkah lengkap: [docs/SETUP-LOGIN.md](docs/SETUP-LOGIN.md).

## Statistik otomatis dari ileague.id

Robot `scripts/update_stats.py` berjalan otomatis lewat GitHub Actions (`.github/workflows/update-stats.yml`) tiap jam pukul 16.17–06.17 WIB. Robot hanya menghubungi ileague.id bila ada laga Deltras dalam 3 hari terakhir yang skor atau statistiknya belum tercatat.

Yang dilakukan robot:
1. Membaca daftar laga di halaman klub Deltras untuk memperbarui tanggal, jam, stadion, dan skor di `data/fixtures.json`.
2. Untuk laga yang selesai **mulai 21 November 2026 (vs Persela)**, membaca halaman detail laga: susunan pemain, pergantian (untuk menit bermain), gol lawan (untuk kebobolan), dan kartu merah.
3. Mengambil statistik tiap pemain Deltras yang bermain: gol, assist, penyelamatan, kartu kuning, dan gol bunuh diri.
4. Menulis `data/matches.json`, membangun ulang halaman, lalu menyimpan ke GitHub. Vercel menerbitkan ulang otomatis.

Pemain dicocokkan lewat nomor punggung. Pemain yang belum ada di skuad dilewati dan dicatat di log Actions.

Menjalankan manual:

```bash
python3 scripts/update_stats.py --dry-run                              # lihat hasil tanpa menulis
python3 scripts/update_stats.py --dry-run --from 2026-09-01 --force    # uji pada laga lama
```

Robot juga bisa dijalankan dari tab **Actions → Perbarui statistik laga → Run workflow** di GitHub.

### Koreksi manual

Penalti gagal (`pm`) dan penalti yang diselamatkan (`ps`) belum tersedia di ileague, dan data ileague bisa saja keliru. Tulis koreksi di `data/overrides.json`; isinya menimpa hasil robot:

```json
{
  "2026-11-21": {
    "pemain": {
      "10": {"pm": 1},
      "29": {"ps": 1, "sv": 5}
    }
  }
}
```

Nilai `null` untuk seorang pemain menghapusnya dari laga itu.

## Menambah poin dari laga secara manual

1. Isi skor laga di `data/fixtures.json` (`skor_kandang`, `skor_tamu`) dan kosongkan `jam` menjadi `null`.
2. Tambahkan statistik laga ke `data/matches.json`. Kunci `tanggal` harus sama dengan tanggal di `fixtures.json`, dan kunci `pemain` adalah nomor punggung. Pemain yang tidak bermain tidak perlu ditulis.
3. Jalankan `build.py`.

```json
[
  {
    "tanggal": "2026-11-21",
    "kebobolan": 1,
    "pemain": {
      "10": {"m": 90, "g": 2, "pa": 14, "tk": 1},
      "29": {"m": 90, "sv": 4, "pa": 18, "gc": 1},
      "11": {"m": 65, "yc": 1, "gc": 0}
    }
  }
]
```

Kunci statistik per pemain:

| Kode | Arti | Kode | Arti |
|---|---|---|---|
| `m` | menit bermain | `pa` | umpan |
| `g` / `a` | gol / assist | `cc` | peluang tercipta |
| `sv` | penyelamatan (kiper) | `sot` / `sof` | tembakan tepat sasaran / melenceng |
| `gc` | kebobolan saat pemain di lapangan (kosong = kebobolan laga) | `dr` | dribel sukses |
| `yc` / `rc` | kartu kuning / merah | `tk` / `bl` | tekel / blok |
| `og` | gol bunuh diri | `ic` / `cl` | intersep / sapuan |
| `ps` / `pm` | penalti diselamatkan / gagal | `rb` | rebut bola |
| | | `fl` / `fd` | pelanggaran dibuat / diterima |

## Sistem poin: tangga Rating Starting XI

Rincian ada di [docs/SISTEM-POIN.md](docs/SISTEM-POIN.md). Tiap pemain mendapat **Rating Starting XI** (3,0–10,0, bukan rating resmi) dari statistik laga: gol, assist, peluang, tembakan, dribel, tekel, intersep, blok, sapuan, umpan, penyelamatan, kebobolan, clean sheet, hasil tim, dan pelanggaran. Rating lalu diubah menjadi poin:

| Rating pemain di laga itu | Poin |
|---|---|
| di bawah 7,0 (bermain) | 1 |
| 7,0 – 7,9 | 2 |
| 8,0 – 8,9 | 3 |
| 9,0 – 10 | 5 |
| Kartu kuning | tidak mengurangi |
| Kartu merah | −2 |

Pemain yang tidak bermain mendapat 0. Poin pemain **tidak pernah minus** (paling kecil 0).

**Poin tim** satu laga = jumlah poin 11 pemain starting XI yang tercatat saat deadline, poin **kapten ×2**. Cadangan tidak dihitung. Dihitung **mulai laga Deltras vs Persela (21 November 2026)**, termasuk laga I.League Cup.

Rumus ada di dua tempat yang harus selalu sama: `ratingOf`/`pointsOf` di `src/template.html` (tampilan) dan `rating_of`/`points_of` di `scripts/update_stats.py` (peringkat di database). Ubah keduanya sekaligus.

## Kunci dan simpan susunan

- Susunan **terkunci otomatis 2 jam sebelum kick-off** dan terbuka lagi 2 jam setelah kick-off. Selama terkunci tidak ada yang bisa mengubah susunan, dan database menolak penulisan susunan (aturan di `supabase/schema.sql`, bukan hanya di tampilan).
- Saat deadline, server mencatat susunan semua coach sebagai riwayat laga itu (pencatat otomatis tiap 5 menit).
- Penulisan ke database dibuat hemat: perubahan ditampung 20 detik, hanya dikirim bila isinya berubah dari yang terakhir tersimpan, dikirim langsung saat tab disembunyikan atau deadline kurang dari 2 menit lagi, dan bisa dipaksa lewat tombol "Simpan sekarang". Peringkat di-cache 60 detik di browser.

Susunan tercatat di browser pengguna saat halaman dibuka setelah deadline lewat. Laga sebelum pengguna pertama kali membuka halaman ditandai "Tidak ikut".

## Catatan data

- Ada 33 pemain Senior Team (Pegadaian Championship 2026/27).
- Nomor 32 dikoreksi menjadi **Aqila Agustian**. Di sumber tertulis "Aqil A" dan "Agustian".
- Foto **#35 Reza Wili** dan **#45 Ibrohim** di deltrasfc.com adalah file yang identik, jadi keduanya tampil dengan inisial. Taruh foto yang benar di `assets/photos/` lalu hapus nomornya dari `NO_PHOTO` di `prep_players.py`.
- Posisi mengikuti kategori klub (GK/DF/MF/FW), tanpa posisi rinci seperti bek kiri.
- Usia diambil November 2026 dan perlu diperbarui tiap musim.
- Susunan pengguna tersimpan di browser masing-masing (`localStorage`). Belum ada login atau papan peringkat.
