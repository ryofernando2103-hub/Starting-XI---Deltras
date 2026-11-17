# Mengaktifkan login & peringkat (Supabase)

Website tetap berjalan tanpa login sampai langkah-langkah ini selesai. Setelah `data/supabase.json` diisi,
tombol **Masuk** dan tab **Peringkat** muncul otomatis.

## 1. Buat proyek Supabase
1. Buka https://supabase.com, masuk dengan akun GitHub.
2. **New project** → nama `tata-tim-deltras`, region **Southeast Asia (Singapore)**, buat kata sandi database (simpan sendiri).

## 2. Pasang skema database
1. Di proyek: **SQL Editor → New query**.
2. Tempel seluruh isi `supabase/schema.sql`, lalu **Run**. Aman dijalankan ulang.

Skema ini membuat tabel profil, susunan, riwayat susunan per laga, poin pemain, aturan keamanan (Row Level Security),
fungsi peringkat, dan jadwal otomatis (pg_cron, tiap 5 menit) yang mencatat susunan semua coach saat deadline.

## 3. Alamat website
**Authentication → URL Configuration**
- **Site URL**: `https://startingxi-deltras.vercel.app`
- **Redirect URLs**: tambahkan `https://startingxi-deltras.vercel.app/**`

## 4. Login Google
1. https://console.cloud.google.com → buat project → **APIs & Services → OAuth consent screen**: tipe *External*, isi nama aplikasi
   "Starting XI Deltras" dan email kontak, lalu **Publish app**.
2. **Credentials → Create credentials → OAuth client ID** → tipe *Web application*.
   **Authorized redirect URI**: `https://<ID-PROYEK>.supabase.co/auth/v1/callback`
   (alamat persisnya tertera di Supabase: **Authentication → Providers → Google**).
3. Salin **Client ID** dan **Client secret** ke **Supabase → Authentication → Providers → Google**, aktifkan, simpan.

## 5. Login email (opsional)
Pengirim email bawaan Supabase dibatasi sangat sedikit email per jam, tidak cukup untuk umum.
Untuk dibuka ke publik, pasang SMTP sendiri (misalnya Resend, ada paket gratis) di
**Project Settings → Authentication → SMTP Settings**. Sampai itu, sarankan pengguna memakai Google.

## 6. Sambungkan website
**Project Settings → API**, salin:
- **Project URL**
- **anon public key**

Keduanya memang dirancang untuk dipasang di website (keamanan dijaga oleh Row Level Security), jadi boleh
dikirim ke Claude untuk diisi ke `data/supabase.json`.

## 7. Sambungkan robot statistik (rahasia)
Robot mengirim jadwal dan poin pemain ke Supabase untuk menghitung peringkat. Ini butuh **service_role key**,
yang **rahasia**: jangan dikirim lewat chat dan jangan ditaruh di kode.

GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
- `SUPABASE_URL` = Project URL
- `SUPABASE_SERVICE_KEY` = service_role key (Project Settings → API)

Lalu **Actions → Perbarui statistik laga → Run workflow** sekali, supaya jadwal masuk ke database.
Tanpa jadwal di database, susunan tidak bisa dikunci dan dicatat saat deadline.

## Catatan
- Poin peringkat dihitung mulai laga vs Persela (21 November 2026).
- Susunan terkunci dari deadline (2 jam sebelum kick-off) sampai 2 jam setelah kick-off.
- Login menyimpan email pengguna: siapkan halaman Kebijakan Privasi sebelum dibuka untuk umum.
