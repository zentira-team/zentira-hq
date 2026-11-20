# Panduan Deploy Zentira HQ Online 100% Gratis via Render.com (Tanpa Kartu Kredit)

Karena Hugging Face Spaces sekarang mewajibkan paket PRO untuk Docker, opsi **100% GRATIS tanpa kartu kredit** terbaik untuk menjalankan Python + FastAPI + Kantor 3D **Zentira HQ** adalah **Render.com** (server region **Singapore** biar kencang dari Indonesia!).

Begitu live, kamu bisa membuka **Zentira HQ** dari HP di sekolah (kuota seluler/Wi-Fi) walau PC di rumah mati total.

---

## Langkah 1 — Upload Proyek ke GitHub (Gratis, Buat Repo Private)
1. Buka https://github.com/new (daftar/login akun GitHub gratis).
2. Isi:
   - **Repository name:** `zentira-hq`
   - **Visibility:** pilih **`Private`** *(aman, hanya kamu yang bisa melihat kodenya)*
3. Klik **Create repository**, lalu klik **uploading an existing file** dan upload file/folder berikut dari `d:\multi agent ai`:
   - `main.py`, `requirements.txt`, `render.yaml`, `Dockerfile`, `.dockerignore`
   - Folder `core/`
   - Folder `agents/`
   - Folder `office/`
   - **JANGAN PERNAH upload:** `.env`, `.venv/`, `__pycache__/`, `.agents/`, `outputs/`, `ai-riset-tren/`
4. Klik **Commit changes**.

---

## Langkah 2 — Deploy Gratis di Render.com (Tanpa Kartu Kredit)
1. Buka https://dashboard.render.com/register → login cepat pakai tombol **GitHub** (tidak perlu kartu kredit!).
2. Di dashboard Render, klik **+ New** → pilih **Web Service**.
3. Pilih repo GitHub **`zentira-hq`** yang baru dibuat → klik **Connect**.
4. Isi pengaturan berikut (kalau tidak otomatis terbaca):
   - **Name:** `zentira-hq`
   - **Region:** **`Singapore (Southeast Asia)`** *(paling cepat dari Indonesia)*
   - **Language / Runtime:** **`Python 3`**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py office --host 0.0.0.0 --port $PORT --no-browser`
   - **Instance Type:** pilih **`Free ($0/month)`**
5. Scroll ke bawah ke bagian **Environment Variables** → tambahkan satu per satu:

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.11.9` |
| `GEMINI_API_KEY` | *(tempel API key Gemini kamu dari `.env`)* |
| `GROQ_API_KEY` | *(tempel API key Groq kamu `gsk_...` dari `.env`)* |
| `OFFICE_PASSWORD` | *(buat password rahasia kamu sendiri untuk login dari HP!)* |
| `CUSTOM_AGENT_NAMES` | `manager=Denn,trend=ucok,repurpose=ali,leads=Lido,finance=Fina,cs=Caca` |

6. Klik **Deploy Web Service** → tunggu ~2–3 menit sampai status berubah **`Live`** (hijau)!

---

## Langkah 3 — Buka di HP & Jadikan Ikon Aplikasi
1. Salin alamat link di pojok kiri atas Render, contohnya: `https://zentira-hq.onrender.com`.
2. Buka link itu di Chrome/Safari HP → masukkan **`OFFICE_PASSWORD`** → langsung masuk ke kantor 3D **Zentira HQ**!
3. **Jadikan seperti aplikasi di HP:**
   - **Android Chrome:** klik `⋮` → **Tambahkan ke layar utama (Add to Home screen)**
   - **iPhone Safari:** klik ikon Share → **Add to Home Screen**

---

## Catatan Penting Paket Gratis Render + Tips Anti-Tidur
- **Tidur saat sepi 15 menit:** kalau baru pertama buka setelah >15 menit tidak dipakai, tunggu ~30–50 detik sampai kantornya bangun otomatis (setelah bangun langsung mulus).
- **Tips Backup Data:** karena server gratis bisa restart sewaktu-waktu, klik dropdown **`● Kantor: Masuk ⌄`** → **`Backup`** setelah mencatat kas/prospek penting (tersimpan 1 file `.json` kecil di HP). Kalau data sempat kosong, klik **`Restore`** untuk mengembalikan semuanya dalam 1 detik.
- **Endpoint Health Check sudah siap:** `https://zentira-hq.onrender.com/api/health` (bisa dipakai kalau suatu saat kamu mau pasang ping gratis seperti cron-job.org saat jam sekolah supaya tidak perlu tunggu 30 detik bangun).
