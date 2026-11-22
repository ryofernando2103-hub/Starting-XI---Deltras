# Sistem poin Starting XI Deltras

Berlaku **mulai laga Deltras vs Persela (21 November 2026)**, termasuk laga I.League Cup.

## 1. Rating Starting XI

Tiap pemain yang bermain mendapat rating **3,0–10,0** (bukan rating resmi). Rating mulai dari 6,0, lalu naik atau turun dari statistik laga:

- **Naik:** gol (bobot lebih besar untuk bek dan kiper), assist, peluang tercipta, tembakan tepat sasaran, dribel, tekel, intersep, blok, sapuan, rebut bola, umpan, dilanggar, penyelamatan (kiper), clean sheet, tim menang.
- **Turun:** kebobolan (terutama kiper dan bek), tembakan melenceng, pelanggaran, gol bunuh diri, tim kalah.
- Pemain yang bermain kurang dari 45 menit mendapat perubahan yang lebih kecil (sebanding dengan menitnya).
- **Kartu tidak masuk rating**; kartu dihitung terpisah di poin.

## 2. Dari rating ke poin

| Rating pemain di laga itu | Poin |
|---|---|
| di bawah 7,0 (bermain) | 1 |
| 7,0 – 7,9 | 2 |
| 8,0 – 8,9 | 3 |
| 9,0 – 10 | 5 |
| Kartu kuning | tidak mengurangi |
| Kartu merah | −2 |

Pemain yang tidak bermain mendapat 0. Poin pemain **tidak pernah minus** (paling kecil 0).

## 3. Poin coach per laga

- Jumlah poin 11 pemain **starting XI** yang tercatat saat deadline (2 jam sebelum kick-off).
- Poin **kapten dikali 2**.
- **Cadangan tidak dihitung.**
- **Total poin** = jumlah poin semua laga. Peringkat diurutkan dari total poin.

## Riwayat perubahan

- 17 Nov 2026: poin = poin main + (rating − 6,0) × 2,5. Hasilnya terlalu besar (total pemain vs Persela 44).
- 22 Nov 2026: sempat kembali ke aturan gaya FPL, lalu tanpa poin main. Hasilnya minus (total pemain vs Persela −4).
- 22 Nov 2026: **tangga rating** seperti di atas. Total pemain vs Persela 18 poin.

## Tempat rumus di kode

- `ratingOf()`, `ratingPts()`, `pointsOf()` di `src/template.html`: tampilan di website.
- `rating_of()`, `rating_points()`, `points_of()` di `scripts/update_stats.py`: poin yang dikirim robot ke database untuk peringkat.

Keduanya harus selalu sama. Setelah mengubah rumus, jalankan robot dengan `--force` (atau tombol *Run workflow* di GitHub Actions) supaya poin di database ikut dihitung ulang.
