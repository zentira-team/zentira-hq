"""Knowledge base Rate Card & FAQ untuk Agent 5 (Asisten CS).

Anda bisa mengedit template di bawah langsung, ATAU membuat file Markdown sendiri di:
`data/rate_card.md` (otomatis diprioritaskan jika file tersebut ada).
"""

from __future__ import annotations

from pathlib import Path

from core.config import PROJECT_ROOT
from core.persona import CHARACTER_PROFILE, WEB_SERVICE_PROFILE

DEFAULT_RATE_CARD_FILE = PROJECT_ROOT / "data" / "rate_card.md"

DEFAULT_RATE_CARD_AND_FAQ = f"""
=== 1. LAYANAN ENDORSE KONTEN ANIMASI ({CHARACTER_PROFILE['nama_duo']}) ===
Profil Kanal:
- Karakter: {CHARACTER_PROFILE['nama_duo']} ({CHARACTER_PROFILE['relasi']})
- Format: {CHARACTER_PROFILE['format_konten']}
- Gaya: {CHARACTER_PROFILE['gaya_humor']}

Paket Layanan Endorse (Contoh Template — silakan sesuaikan angka di data/rate_card.md):
- Paket A (Single Platform): 1 video animasi storytelling 30-60 detik di 1 platform pilihan (TikTok / IG Reels / YT Shorts) -> [Isi Harga Paket A di data/rate_card.md]
- Paket B (Mirroring 3 Platform): 1 video animasi ditayangkan di TikTok + IG Reels + YT Shorts sekaligus -> [Isi Harga Paket B di data/rate_card.md]
- Add-on Opsional: Link di bio / Keranjang Kuning / Boost Ads (spark ads code) / revisi ekstra -> [Konfirmasi sesuai kebutuhan]

FAQ Endorse:
- Alur pengerjaan: Terima brief & DP 50% -> Draft konsep & skrip (maks. 2 hari kerja) -> Approval skrip -> Produksi animasi (3-5 hari kerja) -> Preview -> Pelunasan 50% -> Tayang sesuai jadwal.
- Revisi: Gratis 2x revisi minor pada tahap skrip/storyboard, dan 1x revisi minor (teks/audio/warna) setelah animasi jadi. Perubahan konsep total setelah animasi berjalan dikenakan biaya tambahan.
- Syarat Konten: Produk harus aman/legal (tidak menerima judi online, pinjol ilegal, atau konten SARA).

=== 2. LAYANAN JASA PEMBUATAN WEBSITE UMKM ===
Profil Layanan:
- Nama: {WEB_SERVICE_PROFILE['nama_layanan']}
- Fokus: {WEB_SERVICE_PROFILE['fokus_layanan']}
- Keunggulan: {WEB_SERVICE_PROFILE['keunggulan']}

Paket Website UMKM (Contoh Template — silakan sesuaikan angka di data/rate_card.md):
- Paket Starter (Landing Page 1 Halaman): Profil usaha, galeri foto, tombol order langsung ke WhatsApp, integrasi Google Maps, tampilan mobile-friendly -> [Isi Harga Paket Starter di data/rate_card.md]
- Paket Katalog UMKM: Landing page + halaman katalog produk/menu interaktif yang mudah diperbarui + tombol order WA per item -> [Isi Harga Paket Katalog di data/rate_card.md]
- Paket Custom: Fitur khusus sesuai permintaan usaha -> [Estimasi setelah diskusi kebutuhan]

FAQ Website UMKM:
- Estimasi pengerjaan: 3-7 hari kerja setelah materi (logo, foto produk, daftar harga/menu) lengkap.
- Domain & Hosting: Bisa dibantu pendaftaran domain (.com / .id / .my.id) dan hosting; rincian biaya perpanjangan tahunan disampaikan transparan sejak awal.
- Pembayaran: DP 50% di awal pengerjaan, pelunasan 50% saat website siap tayang/online.
- Revisi & Garansi: Termasuk 2x revisi desain minor sebelum launch + panduan singkat cara penggunaan.
""".strip()


def load_rate_card_and_faq(custom_file: Path | None = None) -> str:
    """Memuat teks Rate Card & FAQ dari file kustom (atau data/rate_card.md), fallback ke default."""
    candidate = custom_file or DEFAULT_RATE_CARD_FILE
    if candidate.is_file():
        content = candidate.read_text(encoding="utf-8").strip()
        if content:
            return content
    if custom_file is not None and not custom_file.is_file():
        raise ValueError(f"File rate card/FAQ tidak ditemukan: {custom_file}")
    return DEFAULT_RATE_CARD_AND_FAQ
