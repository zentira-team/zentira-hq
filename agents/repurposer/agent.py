"""Orkestrasi Agent 2: Repurposer 3 Platform (TikTok, IG Reels, YT Shorts)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from agents.repurposer.prompts import build_system_instruction, build_user_prompt
from core.formatter import timestamp_wib
from core.gemini_client import GeminiClient


class VideoBrief(BaseModel):
    """Masukan ringkasan 1 video untuk di-repurpose ke 3 platform."""

    ringkasan: str
    judul_kerja: str = ""
    cta_tambahan: str = ""
    catatan_gaya: str = ""


class PlatformCopy(BaseModel):
    """Draf publikasi lengkap untuk satu platform video pendek."""

    judul: str = Field(description="Judul video atau teks cover sesuai karakter platform")
    caption: str = Field(description="Caption atau deskripsi siap tempel")
    hashtags: list[str] = Field(
        default_factory=list,
        description="Daftar hashtag diawali tanda # tanpa spasi",
    )
    pinned_comment: str = Field(
        description="Draf komentar yang disematkan untuk memancing interaksi"
    )


class _LLMPlatformCopy(BaseModel):
    """Skema internal untuk Gemini agar hashtag tertulis lengkap dipisah spasi."""

    judul: str = Field(description="Judul video atau teks cover sesuai karakter platform")
    caption: str = Field(description="Caption atau deskripsi siap tempel")
    hashtags: str = Field(
        description=(
            "Baris berisi 4 sampai 6 hashtag relevan dipisah spasi (khusus IG Reels 5-8, "
            "YouTube Shorts 3-5 termasuk #Shorts), contoh: "
            "'#DennMiki #AnimasiIndonesia #Storytelling #KomediRelatable #CuacaEkstrem'"
        )
    )
    pinned_comment: str = Field(
        description="Draf komentar yang disematkan untuk memancing interaksi"
    )


class RepurposeOutput(BaseModel):
    """Skema JSON terstruktur dari Gemini untuk Agent 2."""

    catatan_strategi: str = Field(
        description="Ringkasan singkat perbedaan pendekatan antar 3 platform"
    )
    tiktok: _LLMPlatformCopy
    instagram_reels: _LLMPlatformCopy
    youtube_shorts: _LLMPlatformCopy


class RepurposeReport(BaseModel):
    """Laporan akhir Agent 2 yang siap ditampilkan, disimpan, atau dikirim ke Telegram."""

    waktu_dibuat: str
    ringkasan_sumber: str
    catatan_strategi: str
    tiktok: PlatformCopy
    instagram_reels: PlatformCopy
    youtube_shorts: PlatformCopy


def _normalize_hashtags(
    tags: list[str] | str, ensure_shorts: bool = False
) -> list[str]:
    """Merapikan hashtag (dari string atau list) agar selalu diawali # dan bebas duplikat."""
    raw_items: list[str]
    if isinstance(tags, str):
        raw_items = re.split(r"[\s,]+", tags.strip())
    else:
        raw_items = []
        for item in tags:
            raw_items.extend(re.split(r"[\s,]+", item.strip()))

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_tag in raw_items:
        # Pisahkan jika beberapa hashtag menempel seperti "#A#B"
        parts = [p for p in raw_tag.split("#") if p.strip()]
        for part in parts:
            cleaned = re.sub(r"\s+", "", part.strip())
            if not cleaned:
                continue
            formatted = f"#{cleaned}"
            key = formatted.casefold()
            if key not in seen:
                seen.add(key)
                normalized.append(formatted)

    if ensure_shorts and "#shorts" not in seen:
        normalized.insert(0, "#Shorts")

    return normalized


def _normalize_platform_copy(
    copy: _LLMPlatformCopy | PlatformCopy, ensure_shorts: bool = False
) -> PlatformCopy:
    return PlatformCopy(
        judul=copy.judul.strip(),
        caption=copy.caption.strip(),
        hashtags=_normalize_hashtags(copy.hashtags, ensure_shorts=ensure_shorts),
        pinned_comment=copy.pinned_comment.strip(),
    )


class RepurposerAgent:
    """Agent 2 untuk mengubah 1 ringkasan video menjadi paket 3 platform."""

    def __init__(self, gemini_client: GeminiClient) -> None:
        self.gemini_client = gemini_client

    def run(self, brief: VideoBrief) -> RepurposeReport:
        """Menjalankan proses adaptasi copywriting untuk TikTok, IG Reels, dan YT Shorts."""
        summary = brief.ringkasan.strip()
        if not summary:
            raise ValueError(
                "Ringkasan video tidak boleh kosong. Masukkan isi/cerita singkat videonya terlebih dahulu."
            )

        system_instruction = build_system_instruction()
        user_prompt = build_user_prompt(
            ringkasan=summary,
            judul_kerja=brief.judul_kerja,
            cta_tambahan=brief.cta_tambahan,
            catatan_gaya=brief.catatan_gaya,
        )
        raw_output = self.gemini_client.generate_structured(
            prompt=user_prompt,
            response_schema=RepurposeOutput,
            system_instruction=system_instruction,
            temperature=0.75,
        )

        return RepurposeReport(
            waktu_dibuat=timestamp_wib(),
            ringkasan_sumber=summary,
            catatan_strategi=raw_output.catatan_strategi.strip(),
            tiktok=_normalize_platform_copy(raw_output.tiktok),
            instagram_reels=_normalize_platform_copy(raw_output.instagram_reels),
            youtube_shorts=_normalize_platform_copy(
                raw_output.youtube_shorts, ensure_shorts=True
            ),
        )

    def _format_platform_section(self, heading: str, copy: PlatformCopy) -> list[str]:
        hashtag_line = " ".join(copy.hashtags) if copy.hashtags else "-"
        return [
            f"## {heading}",
            f"- **Judul / Cover:** {copy.judul}",
            f"- **Caption / Deskripsi:**\n{copy.caption}",
            f"- **Hashtag:** {hashtag_line}",
            f"- **Pinned Comment:** {copy.pinned_comment}",
            "",
        ]

    def format_report(self, report: RepurposeReport) -> str:
        """Memformat hasil repurpose menjadi Markdown siap salin untuk 3 platform."""
        lines: list[str] = [
            "# Paket Konten 3 Platform — Denn & Miki",
            f"Waktu: {report.waktu_dibuat}",
            f"Strategi adaptasi: {report.catatan_strategi}",
            "",
        ]
        lines.extend(self._format_platform_section("1. TikTok", report.tiktok))
        lines.extend(
            self._format_platform_section("2. Instagram Reels", report.instagram_reels)
        )
        lines.extend(
            self._format_platform_section("3. YouTube Shorts", report.youtube_shorts)
        )
        return "\n".join(lines).rstrip()
