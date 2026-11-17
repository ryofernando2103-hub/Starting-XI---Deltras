# Sistem poin: Rating Tata Tim

ileague.id tidak menyediakan rating pemain, jadi **rating dihitung sendiri dari statistik laga**.
Ini rating buatan Tata Tim, bukan rating resmi. Berlaku **mulai laga Deltras vs Persela (21 November 2026)**.

## 1. Rating pemain (3,0 sampai 10,0)

Mulai dari **6,0**, lalu ditambah atau dikurangi:

| Kejadian | Bobot |
|---|---|
| Gol | +1,4 (FW), +1,6 (MF), +2,0 (DF dan GK) |
| Assist | +1,0 |
| Peluang tercipta | +0,25 |
| Tembakan tepat sasaran / melenceng | +0,15 / −0,05 |
| Dribel sukses | +0,12 |
| Tekel | +0,15 |
| Blok | +0,15 |
| Intersep | +0,10 |
| Sapuan | +0,06 (GK, DF), +0,04 (lainnya) |
| Rebut bola | +0,05 |
| Umpan | +0,012 tiap umpan, maksimal +0,6 |
| Pelanggaran dibuat / diterima | −0,08 / +0,04 |
| Penyelamatan kiper | +0,25 tiap penyelamatan, maksimal +2,0 |
| Kebobolan saat pemain di lapangan | −0,35 (GK), −0,20 (DF), −0,08 (MF) |
| Clean sheet (main ≥ 60 menit) | +0,8 (GK), +0,6 (DF), +0,25 (MF) |
| Gol bunuh diri | −1,2 |
| Hasil tim: menang / seri / kalah | +0,3 / 0 / −0,2 |

Pemain yang bermain kurang dari 45 menit: selisih dari 6,0 dikalikan (menit ÷ 45), sehingga pemain pengganti
semenit tidak bisa mendapat rating ekstrem. Hasil dibulatkan ke satu desimal.

**Kartu tidak masuk rating**, supaya tidak terpotong dua kali. Kartu dikurangkan langsung dari poin.

## 2. Rating menjadi poin

```
poin = poin main
     + dibulatkan((rating − 6,0) × 2,5)
     − kartu kuning × 1
     − kartu merah  × 3
     + penalti diselamatkan × 5
     − penalti gagal × 2
```

- Poin main: **+1** bila main kurang dari 60 menit, **+2** bila 60 menit atau lebih.
- Pembulatan: ke atas pada .5 (misalnya 2,5 menjadi 3).
- Penalti gagal dan diselamatkan tidak ada di ileague.id; isi lewat `data/overrides.json`.

| Rating | Poin dari rating |
|---|---|
| 5,0 | −2 |
| 6,0 | 0 |
| 7,0 | +3 |
| 8,0 | +5 |
| 9,0 | +8 |

## 3. Poin tim

Poin satu laga = jumlah poin **11 pemain starting XI** yang tercatat saat deadline.
**Kapten dikali 2.** Cadangan tidak dihitung. Total poin = jumlah poin semua laga.

## 4. Kalibrasi

Diuji pada 48 penampilan pemain Deltras di tiga laga (24 Oktober, 31 Oktober, 7 November 2026):
rating terendah 5,9, rata-rata 6,8, tertinggi 8,7; poin 0 sampai 9, rata-rata 3,4.
Bobot masih bisa disesuaikan setelah beberapa laga, misalnya bila kiper terasa dirugikan.

## 5. Di mana rumusnya

Rumus yang sama ditulis di dua tempat dan **harus selalu identik**:

- `ratingOf` dan `pointsOf` di `src/template.html` (menampilkan poin di website)
- `rating_of` dan `points_of` di `scripts/update_stats.py` (mengisi tabel `player_points` untuk peringkat)

Keduanya telah dibandingkan pada 3.048 kasus dengan selisih nol. Setelah mengubah satu, ubah yang lain dan bandingkan lagi.
