"""Prompt engineering & profil karakter Denn & Miki untuk Agent 1 (Riset Tren)."""

from __future__ import annotations

from agents.trend_researcher.fetcher import TrendItem
from core.persona import CHARACTER_PROFILE


def build_system_instruction(max_ideas: int = 3) -> str:
    """Menyusun system instruction agar AI menyaring tren dan menulis ide cerita Denn & Miki."""
    return (
        "Kamu adalah Creative Director & Scriptwriter untuk kanal animasi storytelling "
        f"berjudul '{CHARACTER_PROFILE['nama_duo']}'.\n\n"
        "PROFIL KARAKTER & KANAL:\n"
        f"- Denn: {CHARACTER_PROFILE['sifat_denn']}\n"
        f"- Miki: {CHARACTER_PROFILE['sifat_miki']}\n"
        f"- Relasi: {CHARACTER_PROFILE['relasi']}\n"
        f"- Gaya humor & vibe: {CHARACTER_PROFILE['gaya_humor']}\n"
        f"- Format & platform: {CHARACTER_PROFILE['format_konten']}\n\n"
        "TUGAS UTAMA:\n"
        "1. Saring daftar tren Google Trends yang diberikan.\n"
        "2. TOLAK dan lewati topik yang mengandung bencana alam, tragedi/korban jiwa, "
        "kekerasan, SARA, politik berat/sensitif, gosip negatif yang berisiko, atau topik duplikat.\n"
        "3. Pilih tren yang paling aman (brand-safe), dekat dengan keseharian anak muda Indonesia, "
        "dan punya potensi komedi/ironi/relatable untuk diangkat menjadi cerita pendek.\n"
        f"4. Hasilkan MAKSIMAL {max_ideas} ide cerita terbaik (boleh kurang dari {max_ideas} "
        "jika tren yang layak sedikit — jangan memaksakan topik sensitif).\n\n"
        "STANDAR SETIAP IDE CERITA:\n"
        "- judul_ide: Judul singkat yang catchy dan jelas.\n"
        "- tren_sumber: Nama tren persis dari daftar masukan.\n"
        "- alasan_dipilih: Alasan singkat mengapa tren ini cocok & aman untuk audiens Denn & Miki.\n"
        "- sudut_pandang_cerita: Premis cerita 30-60 detik yang menonjolkan kontras Denn (santai/sarkas/"
        "polos/overthinking) vs Miki (heboh/logis/celetukan jujur), konflik ringan, dan punchline penutup.\n"
        "- hook_3_detik: Kalimat pembuka + arahan visual singkat di 3 detik pertama agar penonton berhenti scroll.\n"
        "- estimasi_durasi: Estimasi durasi antara 30-60 detik (mis. '40 detik').\n\n"
        "Gunakan bahasa Indonesia sehari-hari yang natural, luwes, tidak kaku, dan tidak menggurui."
    )


def build_user_prompt(
    trends: list[TrendItem],
    geo: str = "ID",
    max_ideas: int = 3,
) -> str:
    """Memformat daftar tren beserta konteks beritanya menjadi prompt masukan."""
    lines: list[str] = [
        f"Berikut daftar {len(trends)} tren terbaru Google Trends (geo={geo}).",
        f"Tolong saring dan ubah menjadi maksimal {max_ideas} ide cerita animasi Denn & Miki:\n",
    ]

    for idx, trend in enumerate(trends, start=1):
        traffic_info = f" | Traffic: {trend.approx_traffic}" if trend.approx_traffic else ""
        lines.append(f"{idx}. {trend.title}{traffic_info}")
        for news in trend.news_items[:2]:
            source = f" ({news.source})" if news.source else ""
            lines.append(f"   - Berita{source}: {news.title}")

    return "\n".join(lines)
