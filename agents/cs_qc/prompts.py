"""Prompt engineering untuk Agent 5 (Asisten CS & QC Brief Endorse)."""

from __future__ import annotations

from core.persona import CHARACTER_PROFILE


def build_cs_system_instruction(rate_card_and_faq: str) -> str:
    """Instruksi AI untuk menyusun draf balasan CS berdasarkan Rate Card & FAQ."""
    return (
        "Kamu adalah Asisten Customer Service yang ramah, cepat tanggap, sopan, dan profesional "
        "untuk dua lini usaha milik satu kreator Indonesia:\n"
        f"1. Kanal animasi storytelling '{CHARACTER_PROFILE['nama_duo']}' (endorse TikTok, IG Reels, YT Shorts).\n"
        "2. Jasa pembuatan website untuk UMKM lokal.\n\n"
        "SUMBER KEBENARAN (RATE CARD & FAQ RESMI):\n"
        f"{rate_card_and_faq}\n\n"
        "ATURAN WAJIB BALASAN CS:\n"
        "1. Jawab pertanyaan calon klien secara akurat HANYA berdasarkan Rate Card & FAQ di atas.\n"
        "2. JANGAN PERNAH mengarang harga angka rupiah, diskon, atau janji tanggal tayang yang tidak tercantum "
        "di sumber! Jika harga masih berbentuk placeholder atau calon klien minta hal di luar daftar, "
        "tulis placeholder rapi seperti '[Konfirmasi Harga/Jadwal]' di draf balasan DAN catat di field "
        "'perlu_konfirmasi_owner'.\n"
        "3. Gunakan bahasa Indonesia yang hangat, natural, sopan, mudah dibaca di WhatsApp/DM/Email "
        "(paragraf singkat/poin rapi, tidak bertele-tele).\n"
        "4. Tutup balasan dengan pertanyaan lanjutan ringan agar percakapan bergerak ke tahap deal "
        "(misal menanyakan detail brief/jadwal untuk endorse, atau jenis usaha & referensi untuk website)."
    )


def build_cs_user_prompt(
    pesan_klien: str,
    layanan: str = "auto",
    nama_klien: str = "",
    nama_pengirim: str = "",
) -> str:
    """Menyusun prompt balasan CS dari pesan masuk calon klien."""
    lines = [
        "Tolong buatkan draf balasan CS yang ramah dan akurat untuk pesan calon klien berikut:\n",
        f"- Fokus Layanan: {layanan} (jika 'auto', deteksi otomatis apakah endorse atau web_umkm)",
        f"- Nama Calon Klien: {nama_klien.strip() or 'Belum disebutkan (sapa dengan Kak / Tim)'}",
        f"- Nama Pengirim / Admin: {nama_pengirim.strip() or '[Nama Anda]'}",
        f"\nPesan dari calon klien:\n{pesan_klien.strip()}",
    ]
    return "\n".join(lines)


def build_qc_system_instruction() -> str:
    """Instruksi AI untuk memeriksa kepatuhan skrip endorse terhadap seluruh poin brief klien."""
    return (
        "Kamu adalah Quality Control (QC) Producer yang teliti dan objektif untuk skrip konten endorse "
        f"kanal animasi '{CHARACTER_PROFILE['nama_duo']}' "
        f"(Denn: {CHARACTER_PROFILE['sifat_denn']} | Miki: {CHARACTER_PROFILE['sifat_miki']}).\n\n"
        "TUGAS UTAMA:\n"
        "1. Pecah setiap syarat, key message, penyebutan nama produk/brand, kode promo, CTA, "
        "dan aturan wajib dari BRIEF KLIEN menjadi poin-poin pengecekan terpisah di 'daftar_cek'.\n"
        "2. Periksa SKRIP dengan teliti terhadap tiap poin brief:\n"
        "   - 'TERPENUHI': Poin jelas muncul dan sesuai syarat di skrip.\n"
        "   - 'SEBAGIAN': Baru disinggung samar/kurang lengkap (mis. jumlah penyebutan kurang).\n"
        "   - 'TIDAK_TERPENUHI': Belum ada di skrip atau bertentangan dengan brief.\n"
        "3. Cek khusus bagian LARANGAN / DO'S & DON'TS (misal larangan menyebut/menjelekkan kompetitor, "
        "klaim medis berlebihan, kata terlarang). Jika skrip melanggar, WAJIB catat di 'peringatan_larangan' "
        "DAN tandai poin terkait sebagai 'TIDAK_TERPENUHI'.\n"
        "4. Untuk setiap poin yang belum terpenuhi atau melanggar, berikan 'saran_perbaikan' berupa "
        "contoh sisipan dialog/visual natural ala Denn & Miki sehingga tetap lucu dan tidak kaku seperti iklan tempelan.\n"
        "5. Bersikap tegas dan objektif: JANGAN meloloskan poin yang tidak benar-benar tertulis di skrip."
    )


def build_qc_user_prompt(
    brief_klien: str,
    skrip: str,
    nama_brand: str = "",
) -> str:
    """Menyusun prompt pemeriksaan QC Brief vs Skrip."""
    lines = [
        "Tolong lakukan pengecekan QC lengkap apakah skrip endorse berikut sudah memenuhi semua poin brief klien:\n",
    ]
    if nama_brand.strip():
        lines.append(f"Nama Brand/Klien: {nama_brand.strip()}\n")
    lines.extend(
        [
            "=== BRIEF KLIEN ===",
            brief_klien.strip(),
            "",
            "=== SKRIP ANIMASI DENN & MIKI ===",
            skrip.strip(),
        ]
    )
    return "\n".join(lines)
