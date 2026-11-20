# Multi-Agent AI (Denn & Miki + Jasa Website UMKM)

Sistem Multi-Agent AI berbasis Python yang ringan, bersih, dan modular menggunakan Google Gemini API (`google-genai`, model default `gemini-3.5-flash` dengan fallback otomatis `gemini-3.8-flash`).

## Status Pengembangan
- **Tahap 1 (Aktif):** **Agent 1 — Riset Tren** (`agents/trend_researcher/`)
  - Mengambil tren terbaru Indonesia dari Google Trends RSS gratis.
  - Menyaring topik aman & *relatable* dengan `gemini-3.5-flash` (fallback otomatis `gemini-3.8-flash`).
  - Mengubahnya menjadi maksimal 3 ide cerita animasi **Denn & Miki** lengkap dengan sudut pandang cerita dan *hook* 3 detik pertama.
- **Tahap 2 (Aktif):** **Agent 2 — Repurposer 3 Platform** (`agents/repurposer/`)
  - Mengubah ringkasan 1 video menjadi draf judul, caption, hashtag, dan *pinned comment* khusus untuk TikTok, Instagram Reels, dan YouTube Shorts (termasuk dukungan CTA/endorse opsional).
- **Tahap 3 (Aktif):** **Agent 3 — Lead Hunter UMKM** (`agents/lead_hunter/`)
  - Mengelola daftar prospek UMKM lokal yang belum punya website (`data/leads.json`, mendukung tambah, filter, ubah status, hapus, dan impor CSV).
  - Pencarian prospek UMKM lokal otomatis gratis via OpenStreetMap (`leads discover`).
  - Membuat draf pesan penawaran personal (WhatsApp, DM Instagram, atau Email) lengkap dengan pesan *follow-up* H+3.
- **Tahap 4 (Aktif):** **Agent 4 — Admin Keuangan & Pengingat** (`agents/finance_admin/`)
  - Mencatat pemasukan/pengeluaran per lini usaha (`konten`, `web_umkm`, `umum`) dan ringkasan kas (`data/finance.json`).
  - Melacak status DP/pelunasan klien, pengingat jatuh tempo, draf pesan penagihan WA sopan, serta kalkulator bagi hasil sederhana.
- **Tahap 5 (Aktif):** **Agent 5 — Asisten CS & QC Brief** (`agents/cs_qc/`)
  - Membuat draf balasan calon klien (endorse & website UMKM) berbasis Rate Card & FAQ (`agents/cs_qc/knowledge.py` atau kustom di `data/rate_card.md`).
  - Memeriksa kelengkapan poin brief klien & larangan (*don'ts*) pada skrip endorse Denn & Miki lengkap dengan saran revisi dialog.
- **Kantor Virtual 3D Voxel (Aktif):** (`office/` + `buka_kantor.bat`)
  - Ruangan studio 3D Voxel interaktif (Three.js + FastAPI) dengan 5 karakter voxel beranimasi yang terhubung langsung ke seluruh Agent 1–5 secara *real-time*, bisa dikendalikan dari PC maupun HP dalam 1 Wi-Fi.
- **Tahap Selanjutnya:** Telegram Bot & jadwal otomatis harian GitHub Actions.

## Cara Membuka Kantor Virtual 3D Voxel (Tanpa Terminal!)

- **Cara Termudah:** Klik 2x file `buka_kantor.bat` di folder proyek ini → server menyala dan browser PC otomatis terbuka ke `http://127.0.0.1:8000`.
- **Lewat Terminal:**
  ```powershell
  .\.venv\Scripts\python.exe main.py office
  ```
- **Kontrol dari HP (1 Wi-Fi):** Klik tombol **📱 Akses HP** di pojok kanan atas Kantor 3D (atau lihat alamat `http://192.168.x.x:8000` di jendela terminal), lalu buka link tersebut di browser HP Anda.

## Setup Lokal (Windows PowerShell + Python 3.11)

1. Aktifkan virtual environment `.venv`:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(Jika PowerShell memblokir aktivasi script, Anda bisa langsung memakai `.\.venv\Scripts\python.exe` tanpa aktivasi.)*

2. Jika belum menginstal library:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Isi API key Gemini pada file `.env`:
   - Buka `.env` (dibuat dari `.env.example`)
   - Ganti `GEMINI_API_KEY=...` dengan API key dari [Google AI Studio](https://aistudio.google.com/apikey).

## Cara Menjalankan Agent 1 (Riset Tren)

- Uji ambil tren mentah dari Google Trends Indonesia (gratis, tanpa Gemini API):
  ```powershell
  .\.venv\Scripts\python.exe main.py trend --fetch-only --max-items 5
  ```

- Jalankan Agent 1 lengkap (riset tren + ide cerita Denn & Miki):
  ```powershell
  .\.venv\Scripts\python.exe main.py trend
  ```

- Jalankan Agent 1 dan simpan hasilnya ke folder `outputs/`:
  ```powershell
  .\.venv\Scripts\python.exe main.py trend --save
  ```

## Cara Menjalankan Agent 2 (Repurposer 3 Platform)

- Langsung masukkan ringkasan lewat argumen `--summary`:
  ```powershell
  .\.venv\Scripts\python.exe main.py repurpose --summary "Denn overthinking baca notif BMKG hujan lebat sampai pakai jas hujan 3 lapis di kafe, lalu Miki nyindir pas hujannya cuma 3 tetes."
  ```

- Dengan catatan CTA / endorse dan simpan ke folder `outputs/`:
  ```powershell
  .\.venv\Scripts\python.exe main.py repurpose --summary "..." --cta "Cek link di bio buat promo payung lipat!" --save
  ```

- Membaca ringkasan dari file teks/Markdown (atau ketik interaktif tanpa `--summary`):
  ```powershell
  .\.venv\Scripts\python.exe main.py repurpose --file ringkasan.txt --save
  ```

## Cara Menjalankan Agent 3 (Lead Hunter UMKM)

- **Cari prospek UMKM lokal otomatis** (gratis via OpenStreetMap, otomatis saring usaha tanpa website & skip jaringan besar):
  ```powershell
  .\.venv\Scripts\python.exe main.py leads discover --keyword "kopi" --city "Bandung" --limit 10
  # Tambahkan --save-leads agar langsung masuk ke data/leads.json:
  .\.venv\Scripts\python.exe main.py leads discover --keyword "bengkel" --city "Bekasi" --radius-km 5 --limit 10 --save-leads
  ```

- Tambah prospek UMKM manual:
  ```powershell
  .\.venv\Scripts\python.exe main.py leads add --name "Kedai Kopi Sudut" --category "Kafe" --city "Bandung" --contact "08123456789" --channel whatsapp --notes "Rating Google Maps 4.9, menu cuma ada di highlight IG"
  ```

- Lihat daftar prospek (atau filter khusus yang belum punya website / status tertentu):
  ```powershell
  .\.venv\Scripts\python.exe main.py leads list --no-web
  .\.venv\Scripts\python.exe main.py leads list --status baru
  ```

- Buat draf pesan penawaran personal pakai Gemini (opsional `--save` dan `--mark-contacted`):
  ```powershell
  .\.venv\Scripts\python.exe main.py leads pitch --id 1 --offer "Gratis contoh tampilan halaman depan dulu" --save
  ```

- Perbarui status prospek atau impor banyak prospek dari CSV:
  ```powershell
  .\.venv\Scripts\python.exe main.py leads status --id 1 --status tertarik --notes "Minta dikirim estimasi harga"
  .\.venv\Scripts\python.exe main.py leads import --csv daftar_umkm.csv
  ```

## Cara Menjalankan Agent 4 (Admin Keuangan & Pengingat)

- Catat pemasukan / pengeluaran:
  ```powershell
  .\.venv\Scripts\python.exe main.py finance tx-add --type masuk --amount 1500000 --category endorse --stream konten --notes "Endorse TikTok Denn & Miki"
  .\.venv\Scripts\python.exe main.py finance tx-add --type keluar --amount 250000 --category hosting --stream web_umkm --notes "Domain + hosting klien"
  ```

- Catat tagihan klien (DP otomatis tercatat ke kas) & catat pelunasan:
  ```powershell
  .\.venv\Scripts\python.exe main.py finance invoice-add --client "Kedai Kopi Sudut" --project "Website Katalog" --total 2000000 --dp 1000000 --due 2026-11-28
  .\.venv\Scripts\python.exe main.py finance invoice-pay --id 1 --amount 1000000 --notes "Pelunasan via BCA"
  ```

- Ringkasan kas, cek pengingat jatuh tempo, draf WA pengingat sopan, dan kalkulator bagi hasil:
  ```powershell
  .\.venv\Scripts\python.exe main.py finance summary --month 2026-11
  .\.venv\Scripts\python.exe main.py finance remind --days 7
  .\.venv\Scripts\python.exe main.py finance remind-draft --id 1 --bank "BCA 123456 a.n. Nama Anda"
  .\.venv\Scripts\python.exe main.py finance split --amount 2000000 --cost 200000 --shares "Saya:60,Partner:40"
  ```

## Cara Menjalankan Agent 5 (Asisten CS & QC Brief)

- Lihat isi Rate Card & FAQ aktif (buat file `data/rate_card.md` bila ingin mengganti dengan daftar harga asli Anda):
  ```powershell
  .\.venv\Scripts\python.exe main.py cs rate-card
  ```

- Buat draf balasan calon klien berdasarkan Rate Card & FAQ:
  ```powershell
  .\.venv\Scripts\python.exe main.py cs reply --message "Halo kak, mau tanya paket endorse 3 platform Denn & Miki dan estimasi pengerjaannya ya?"
  ```

- Audit QC skrip endorse terhadap poin brief klien (bisa lewat teks langsung atau `--brief-file` & `--script-file`):
  ```powershell
  .\.venv\Scripts\python.exe main.py cs qc --brand "Es Teh Segar" --brief "1. Sebut nama brand 2x. 2. Highlight melati asli. 3. Sebut kode promo DENNMIKI10." --script "Denn kepanasan, Miki kasih Es Teh Segar..."
  ```

## Kustomisasi Karakter Denn & Miki & Jasa Web UMKM
Ubah kamus `CHARACTER_PROFILE` dan `WEB_SERVICE_PROFILE` di file `core/persona.py` untuk menyesuaikan profil IP Denn & Miki serta jasa pembuatan website UMKM Anda.

## Menjalankan Unit Test Offline
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
