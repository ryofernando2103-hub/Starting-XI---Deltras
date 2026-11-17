# Rencana V2: Starting XI Deltras Online

**Tujuan:** siapa pun bisa membuka Starting XI Deltras dari HP, masuk dengan akun Google atau email, menyimpan susunan tim secara online, mengumpulkan poin tiap laga Deltras, dan bersaing di papan peringkat.

Tampilan V1 (desain merah-hitam, lapangan gaya FPL, kartu pemain, gambar share 2:3) **dipakai ulang**. Yang berubah adalah apa yang ada di belakangnya.

---

## 1. Apa yang berubah dari V1

| | V1 (sekarang) | V2 |
|---|---|---|
| Akses | Tautan artifact claude.ai | Website sendiri, contoh `startingxi.seputardeltras.com` |
| Penyimpanan susunan | Browser masing-masing | Akun pengguna (database online) |
| Poin | Poin musim dijumlah, berlaku untuk susunan apa pun | Poin **per pekan**, hanya dari susunan yang dikunci sebelum kick-off |
| Peringkat | Tidak ada | Peringkat global, per pekan, dan liga mini |
| Input statistik | Dikirim ke Claude, lalu halaman diterbitkan ulang | **Panel admin**: tim Seputar Deltras mengisi sendiri dari HP |
| Roster | Diubah lewat kode | Diubah dari panel admin |

---

## 2. Arsitektur

```
 HP pengguna ──► Website (Vercel / Cloudflare Pages)
                    │  halaman statis + JavaScript
                    ▼
               Supabase
                 ├─ Auth: login Google + email (tautan masuk)
                 ├─ Postgres: pemain, pekan, susunan, statistik, poin
                 ├─ Row Level Security: tiap coach hanya bisa mengubah datanya sendiri
                 └─ Storage: foto pemain
```

**Kenapa pilihan ini:**
- **Supabase** menyediakan login, database, dan penyimpanan foto dalam satu layanan. Paket gratisnya cukup untuk awal: ribuan pengguna aktif dan database ratusan MB. Batas pastinya perlu dicek di halaman harga Supabase saat mendaftar.
- **Vercel atau Cloudflare Pages** bisa meng-hosting gratis langsung dari repo GitHub ini. Tiap push ke `main` otomatis terbit.
- Frontend memakai **Vite + TypeScript tanpa framework berat**, karena kode V1 sudah vanilla JS dan bisa dipindah hampir apa adanya. Halamannya tetap ringan di HP dengan sinyal lemah.

**Biaya perkiraan:** Rp0 untuk hosting dan database selama masih dalam batas gratis, ditambah domain jika belum punya (biasanya beberapa ratus ribu rupiah per tahun). Catatan: proyek Supabase gratis bisa dijeda otomatis jika tidak ada aktivitas sekitar seminggu, misalnya saat libur kompetisi. Mengaktifkannya lagi cukup satu klik, atau naik ke paket berbayar saat ramai.

---

## 3. Mekanisme permainan

### Pekan (gameweek)
- Satu **pekan = satu laga Deltras** di Pegadaian Championship.
- Tiap pekan punya **deadline**, usulannya **2 jam sebelum kick-off**. Setelah deadline, susunan dikunci dan disalin sebagai susunan resmi pekan itu.
- Coach yang tidak mengubah susunan otomatis memakai susunan pekan sebelumnya.

### Poin
- Aturan poin sama dengan V1 (lihat README).
- **Poin pekan** = poin 11 starter pada laga itu, dengan poin kapten dikali 2.
- **Wakil kapten** otomatis menjadi kapten jika kapten tidak bermain.
- **Pergantian otomatis** (fase 3): starter yang tidak bermain diganti cadangan yang bermain, mengikuti urutan bangku.
- **Total poin** = jumlah poin semua pekan.

### Agar tidak semua orang memilih XI yang sama
Karena semua pemain berasal dari satu klub dan tanpa harga, susunan "terbaik" cepat terlihat sama. Pembedanya:
1. **Batas perubahan:** 3 perubahan pemain gratis per pekan, dan tiap perubahan tambahan dikurangi 4 poin. Ganti kapten dan formasi bebas.
2. **Chip sekali semusim:** *Kapten ×3* dan *Bangku Ikut Dihitung*.
3. **Pemilihan kapten** tetap menjadi keputusan terpenting tiap pekan.

### Peringkat
- **Global:** total poin semua coach.
- **Per pekan:** siapa terbaik pekan ini, bagus untuk konten Instagram Seputar Deltras.
- **Liga mini:** coach membuat liga dengan kode undangan, misalnya untuk korwil Deltamania atau grup WA.

---

## 4. Halaman

| Halaman | Isi |
|---|---|
| **Beranda** | Pekan aktif, hitung mundur deadline, poin pekan lalu, peringkatmu |
| **Masuk** | Tombol Google dan email (tanpa password) |
| **Start XI** | Editor susunan V1, ditambah tombol *Simpan Susunan* dan status "Terkunci" setelah deadline |
| **Poin** | Riwayat per pekan: susunan saat itu dan poin tiap pemain |
| **Peringkat** | Global, per pekan, dan liga mini |
| **Liga** | Buat atau gabung liga dengan kode |
| **Pemain** | Daftar 33 pemain dengan poin dan statistik musim |
| **Profil** | Nama coach dan nama tim |
| **Admin** (khusus tim Seputar Deltras) | Atur jadwal pekan, input statistik laga, kelola roster dan foto, umumkan hasil |

Gambar share ditambah **peringkat** dan **poin pekan**, misalnya "Peringkat 12 dari 840 coach".

---

## 5. Struktur data (Supabase / Postgres)

```
profiles        id (= akun login), nama_coach, nama_tim, peran ('coach' | 'admin'), dibuat
players         nomor (PK), nama, nama_pendek, posisi, usia, negara, foto_url, aktif
gameweeks       id, nomor_pekan, lawan, kandang, kickoff, deadline, status ('akan' | 'terkunci' | 'selesai')
lineups         coach_id, gameweek_id, formasi, xi[11], bangku[7], kapten, wakil, posisi_bebas, chip, disimpan
                PK (coach_id, gameweek_id)
player_stats    gameweek_id, nomor, menit, gol, assist, kebobolan, penyelamatan,
                penalti_selamat, penalti_gagal, kuning, merah, bunuh_diri, poin
gw_scores       coach_id, gameweek_id, poin, potongan_transfer, peringkat
leagues         id, nama, kode_undangan, pemilik
league_members  league_id, coach_id
```

**Aturan keamanan (Row Level Security):**
- Coach hanya bisa membuat atau mengubah susunan **miliknya sendiri**, dan hanya **sebelum deadline**. Ini dicek di database, bukan cuma di tampilan.
- Susunan coach lain baru bisa dilihat **setelah deadline**, seperti di FPL.
- Hanya akun berperan `admin` yang bisa mengubah pemain, jadwal, dan statistik.
- Poin dihitung oleh fungsi di database saat admin menekan *Selesaikan Pekan*, jadi tidak bisa dimanipulasi dari browser.

---

## 6. Tahapan

| Fase | Isi | Perkiraan |
|---|---|---|
| **1. MVP** | Login, simpan susunan online, pekan dan deadline, panel admin input statistik, poin per pekan, peringkat global | 1–2 minggu |
| **2. Komunitas** | Liga mini, riwayat poin, profil, gambar share dengan peringkat, halaman pemain | 1 minggu |
| **3. Strategi** | Batas perubahan, chip, wakil kapten dan pergantian otomatis | 1 minggu |
| **4. Pemanis** | Notifikasi deadline (email/WA), pemain terbaik pekan ini, statistik musim | menyusul |

**Peluncuran yang disarankan:** uji tertutup dengan 10–20 orang selama 1–2 pekan laga sebelum dibuka untuk umum.

---

## 7. Yang perlu disiapkan pemilik proyek

1. **Akun Supabase** dan **akun Vercel** (atau Cloudflare). Daftar memakai akun GitHub ini. Claude tidak bisa membuat akun atas nama Anda.
2. **Domain**: subdomain dari domain Seputar Deltras yang sudah ada, atau domain baru.
3. **Siapa admin**: akun yang boleh input statistik dan mengubah roster.
4. **Jadwal laga** Deltras musim ini: bisa diambil dari ileague.id lalu dicek.
5. **Kebijakan privasi**: login menyimpan email pengguna, jadi perlu halaman kebijakan privasi singkat sesuai UU Pelindungan Data Pribadi. Draf bisa disiapkan.
6. **Keputusan aturan main**: deadline, batas perubahan, chip, dan hadiah (jika ada).
