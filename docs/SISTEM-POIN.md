# Sistem poin Starting XI Deltras

Aturan poin mengikuti gaya Fantasy Premier League (FPL). Berlaku **mulai laga Deltras vs Persela (21 November 2026)**, termasuk laga I.League Cup.

## Poin pemain per laga

| Kejadian | Poin |
|---|---|
| Gol: kiper atau bek / gelandang / penyerang | +6 / +5 / +4 |
| Assist | +3 |
| Clean sheet (≥ 60 menit): kiper atau bek / gelandang | +4 / +1 |
| Tiap 3 penyelamatan (kiper) | +1 |
| Penalti diselamatkan | +5 |
| Tiap 2 kebobolan (kiper atau bek) | −1 |
| Penalti gagal | −2 |
| Kartu kuning / merah | −1 / −3 |
| Gol bunuh diri | −2 |

- **Kebobolan** dihitung saat pemain berada di lapangan (`gc`). Jika tidak tersedia, memakai total kebobolan tim di laga itu.
- **Clean sheet** hanya untuk pemain yang bermain minimal 60 menit dan timnya tidak kebobolan selama ia di lapangan.
- **Bermain saja tidak menambah poin.** Poin hanya datang dari performa: pemain yang bermain tanpa kontribusi apa pun mendapat 0, dan bisa minus karena kebobolan atau kartu.

## Poin coach per laga

- Jumlah poin 11 pemain **starting XI** yang tercatat saat deadline (2 jam sebelum kick-off).
- Poin **kapten dikali 2**.
- **Cadangan tidak dihitung.**
- **Total poin** = jumlah poin semua laga. Peringkat diurutkan dari total poin.

## Riwayat perubahan

- 17 Nov 2026: sempat memakai "Rating Starting XI" (rating 3,0–10,0 dari banyak statistik). Hasilnya terlalu besar, misalnya total pemain laga vs Persela 44 poin padahal Deltras kalah 0–3.
- 22 Nov 2026: dikembalikan ke aturan gaya FPL di atas. Laga vs Persela dihitung ulang dengan aturan ini.
- 22 Nov 2026: poin main (+1 di bawah 60 menit, +2 minimal 60 menit) dihapus. Poin hanya dari performa.

## Tempat rumus di kode

- `pointsOf()` di `src/template.html`: tampilan di website.
- `points_of()` di `scripts/update_stats.py`: poin yang dikirim robot ke database untuk peringkat.

Keduanya harus selalu sama. Setelah mengubah rumus, jalankan robot dengan `--force` (atau tombol *Run workflow* di GitHub Actions) supaya poin di database ikut dihitung ulang.
