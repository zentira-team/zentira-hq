"""Prompt engineering untuk Agent 3 (Lead Hunter UMKM — draf penawaran personal)."""

from __future__ import annotations

from agents.lead_hunter.storage import Lead
from core.persona import WEB_SERVICE_PROFILE


def build_system_instruction() -> str:
    """Menyusun instruksi AI untuk menulis pesan penawaran jasa website yang personal & sopan."""
    return (
        "Kamu adalah Business Development & Copywriter B2B khusus UMKM Indonesia "
        f"untuk '{WEB_SERVICE_PROFILE['nama_layanan']}'.\n\n"
        "PROFIL LAYANAN:\n"
        f"- Fokus layanan: {WEB_SERVICE_PROFILE['fokus_layanan']}\n"
        f"- Keunggulan: {WEB_SERVICE_PROFILE['keunggulan']}\n"
        f"- Gaya komunikasi: {WEB_SERVICE_PROFILE['gaya_komunikasi']}\n\n"
        "PRINSIP MENULIS PESAN PENAWARAN (WAJIB DIPATUHI):\n"
        "1. PERSONAL, BUKAN SPAM: Sebut nama usaha, jenis bisnis/kota, serta detail observasi spesifik "
        "dari catatan agar pemilik usaha merasa pesan ini benar-benar ditulis khusus untuk mereka.\n"
        "2. BAHASA MEMBUMI: Hindari istilah IT yang rumit (seperti responsive UI, SEO on-page, CMS, hosting stack). "
        "Ganti dengan manfaat nyata yang dipahami pemilik UMKM (misal: menu/katalog rapi di HP, "
        "pelanggan tinggal klik langsung masuk WhatsApp, gampang dicari di Google).\n"
        "3. RINGKAS SESUAI SALURAN:\n"
        "   - whatsapp: 3-4 paragraf pendek, mudah dibaca di layar HP tanpa bikin malas baca.\n"
        "   - instagram: Lebih singkat & santai (2-3 paragraf pendek ala DM Instagram).\n"
        "   - email: Sertakan baris 'Subjek:' di baris pertama diikuti isi email yang rapi dan sopan.\n"
        "4. SOFT CTA (TANPA MEMAKSA): Akhiri dengan pertanyaan ringan yang gampang dijawab "
        "(misal menawarkan kirim contoh tampilan singkat gratis dulu jika berkenan).\n"
        "5. Siapkan juga draf 'pesan_followup' singkat & ramah untuk dikirim 3 hari kemudian jika belum ada balasan."
    )


def build_user_prompt(
    lead: Lead,
    penawaran_khusus: str = "",
    nama_pengirim: str = "",
) -> str:
    """Menyusun konteks lengkap satu prospek UMKM untuk dibuatkan draf pesan."""
    status_web = (
        "Sudah punya website (potensi upgrade/redesign)"
        if lead.punya_website
        else "Belum punya website"
    )
    lines = [
        "Tolong buatkan strategi pendekatan, draf pesan penawaran utama, draf follow-up, "
        "dan tips pengiriman untuk prospek UMKM berikut:\n",
        f"- Nama Usaha: {lead.nama_usaha}",
        f"- Kategori: {lead.kategori}",
        f"- Kota/Lokasi: {lead.kota or '-'}",
        f"- Saluran Kontak Target: {lead.saluran}",
        f"- Kontak: {lead.kontak or '-'}",
        f"- Status Website: {status_web}",
        f"- Catatan Observasi: {lead.catatan or 'Belum ada catatan khusus.'}",
    ]
    if nama_pengirim.strip():
        lines.append(f"- Nama Pengirim: {nama_pengirim.strip()}")
    else:
        lines.append("- Nama Pengirim: [Nama Anda] (gunakan placeholder rapi agar mudah diganti)")
    if penawaran_khusus.strip():
        lines.append(f"- Penawaran / Promo Khusus yang ingin disampaikan: {penawaran_khusus.strip()}")
    return "\n".join(lines)
