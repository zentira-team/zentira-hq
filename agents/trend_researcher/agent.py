"""Orkestrasi Agent 1: Riset Tren Indonesia menjadi ide cerita Denn & Miki."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, Field

from agents.trend_researcher.fetcher import TrendItem, fetch_google_trends
from agents.trend_researcher.prompts import (
    build_system_instruction,
    build_user_prompt,
)
from core.formatter import timestamp_wib
from core.gemini_client import GeminiClient


class StoryIdea(BaseModel):
    """Satu ide cerita animasi Denn & Miki hasil penyaringan tren."""

    judul_ide: str = Field(description="Judul singkat ide cerita animasi")
    tren_sumber: str = Field(description="Topik tren asal dari Google Trends")
    alasan_dipilih: str = Field(
        description="Alasan tren ini relatable dan aman untuk diangkat"
    )
    sudut_pandang_cerita: str = Field(
        description="Premis, dinamika dialog Denn vs Miki, dan punchline akhir"
    )
    hook_3_detik: str = Field(
        description="Kalimat pembuka dan aksi visual di 3 detik pertama"
    )
    estimasi_durasi: str = Field(
        default="45 detik",
        description="Perkiraan durasi video antara 30-60 detik",
    )


class TrendAnalysisOutput(BaseModel):
    """Skema respons JSON terstruktur dari Gemini untuk Agent 1."""

    ringkasan_filter: str = Field(
        description="Ringkasan singkat proses penyaringan tren dan topik yang dilewati"
    )
    ide_cerita: list[StoryIdea] = Field(
        default_factory=list,
        description="Daftar maksimal 3 ide cerita terpilih",
    )


class TrendReport(BaseModel):
    """Laporan akhir Agent 1 yang siap ditampilkan atau dikirim ke Telegram."""

    geo: str
    waktu_riset: str
    total_tren_dipindai: int
    ringkasan_filter: str
    ide_cerita: list[StoryIdea] = Field(default_factory=list)


class TrendResearcherAgent:
    """Agent 1 untuk mengambil tren Indonesia dan mengubahnya menjadi maks. 3 ide cerita."""

    def __init__(
        self,
        gemini_client: GeminiClient | None,
        geo: str = "ID",
        max_items: int = 20,
        max_ideas: int = 3,
        fetcher: Callable[[str, int], list[TrendItem]] = fetch_google_trends,
    ) -> None:
        self.gemini_client = gemini_client
        self.geo = geo.upper()
        self.max_items = max(1, max_items)
        self.max_ideas = max(1, min(3, max_ideas))
        self.fetcher = fetcher

    def run(self) -> TrendReport:
        """Menjalankan alur lengkap: ambil tren -> saring AI -> kembalikan laporan."""
        trends = self.fetcher(self.geo, self.max_items)
        waktu_riset = timestamp_wib()

        if not trends:
            return TrendReport(
                geo=self.geo,
                waktu_riset=waktu_riset,
                total_tren_dipindai=0,
                ringkasan_filter="Tidak ada tren yang ditemukan dari feed Google Trends RSS saat ini.",
                ide_cerita=[],
            )

        if self.gemini_client is None:
            raise ValueError(
                "GeminiClient diperlukan untuk menyaring tren menjadi ide cerita."
            )

        system_instruction = build_system_instruction(max_ideas=self.max_ideas)
        user_prompt = build_user_prompt(
            trends=trends, geo=self.geo, max_ideas=self.max_ideas
        )
        analysis = self.gemini_client.generate_structured(
            prompt=user_prompt,
            response_schema=TrendAnalysisOutput,
            system_instruction=system_instruction,
            temperature=0.7,
        )

        return TrendReport(
            geo=self.geo,
            waktu_riset=waktu_riset,
            total_tren_dipindai=len(trends),
            ringkasan_filter=analysis.ringkasan_filter,
            ide_cerita=analysis.ide_cerita[: self.max_ideas],
        )

    def format_report(self, report: TrendReport) -> str:
        """Memformat TrendReport menjadi teks Markdown rapi untuk terminal/Telegram."""
        lines: list[str] = [
            f"# Riset Tren Denn & Miki ({report.geo})",
            f"Waktu: {report.waktu_riset}",
            f"Total tren dipindai: {report.total_tren_dipindai}",
            f"Ringkasan filter: {report.ringkasan_filter}",
            "",
        ]

        if not report.ide_cerita:
            lines.append(
                "Belum ada ide cerita yang lolos filter aman/relatable pada pemindaian kali ini."
            )
            return "\n".join(lines)

        lines.append(f"## {len(report.ide_cerita)} Ide Cerita Terpilih")
        for idx, idea in enumerate(report.ide_cerita, start=1):
            lines.extend(
                [
                    "",
                    f"### {idx}. {idea.judul_ide}",
                    f"- **Tren Sumber:** {idea.tren_sumber}",
                    f"- **Estimasi Durasi:** {idea.estimasi_durasi}",
                    f"- **Alasan Dipilih:** {idea.alasan_dipilih}",
                    f"- **Hook 3 Detik Pertama:** {idea.hook_3_detik}",
                    f"- **Sudut Pandang Cerita (Denn & Miki):** {idea.sudut_pandang_cerita}",
                ]
            )

        return "\n".join(lines)
