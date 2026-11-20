"""Unit test offline untuk Agent 6: Manajer (Orchestrator)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agents.finance_admin import FinanceStore, ReminderDraftOutput
from agents.lead_hunter import LeadStore
from agents.orchestrator import (
    DelegatedTask,
    ManagerOrchestratorAgent,
    OrchestratorPlan,
)
from agents.repurposer.agent import RepurposeOutput, _LLMPlatformCopy
from agents.trend_researcher import StoryIdea, TrendAnalysisOutput, TrendItem


class FakeOrchestratorGeminiClient:
    """Mock GeminiClient untuk menguji perencanaan & delegasi Manajer tanpa API call."""

    def __init__(self, plan: OrchestratorPlan) -> None:
        self.plan = plan
        self.calls: list[str] = []

    def generate_structured(
        self,
        prompt: str,
        response_schema: type,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ):
        self.calls.append(response_schema.__name__)
        if response_schema is OrchestratorPlan:
            return self.plan
        if response_schema is TrendAnalysisOutput:
            return TrendAnalysisOutput(
                ringkasan_filter="1 tren dipilih.",
                ide_cerita=[
                    StoryIdea(
                        judul_ide="Floatee Panas Terik",
                        tren_sumber="cuaca panas",
                        alasan_dipilih="Relatable anak muda.",
                        sudut_pandang_cerita="Denn kepanasan, Miki kasih Floatee.",
                        hook_3_detik="Denn meleleh di kafe!",
                        estimasi_durasi="40 detik",
                    )
                ],
            )
        if response_schema is RepurposeOutput:
            return RepurposeOutput(
                catatan_strategi="Adaptasi 3 platform untuk Floatee.",
                tiktok=_LLMPlatformCopy(
                    judul="Floatee Bikin Adem!",
                    caption="Akhirnya tayang juga kolab Denn & Miki x Floatee!",
                    hashtags="#DennMiki #Floatee #AnimasiIndonesia #Komedi",
                    pinned_comment="Varian Floatee favorit kalian yang mana?",
                ),
                instagram_reels=_LLMPlatformCopy(
                    judul="Denn & Miki x Floatee",
                    caption="Share ke temen lu yang gampang kepanasan!",
                    hashtags="#DennMiki #Floatee #ReelsLucu #AnimasiLokal",
                    pinned_comment="Miki: 'Dingin banget ini mah!'",
                ),
                youtube_shorts=_LLMPlatformCopy(
                    judul="Denn & Miki x Floatee: Bikin Adem Seketika",
                    caption="Tonton kolaborasi Denn & Miki bareng Floatee!",
                    hashtags="#Shorts #DennMiki #Floatee #Animasi",
                    pinned_comment="Udah pernah cobain Floatee belum guys?",
                ),
            )
        if response_schema is ReminderDraftOutput:
            return ReminderDraftOutput(
                pesan_pengingat="Halo Tim Floatee, terima kasih sudah ACC! Berikut format pelunasan Rp1.500.000.",
                catatan_nada="Hangat dan profesional.",
            )
        raise AssertionError(f"Skema tidak terduga: {response_schema}")


class TestManagerOrchestrator(unittest.TestCase):
    def test_floatee_command_delegates_to_repurposer_and_finance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fin_store = FinanceStore(file_path=tmp / "finance.json")
            fin_store.add_invoice(
                klien="Floatee",
                proyek="Endorse Video TikTok+IG",
                total_harga=3_000_000,
                dp=1_500_000,
                sumber="konten",
                jatuh_tempo="2026-11-28",
            )
            plan = OrchestratorPlan(
                ringkasan_rencana="Menugaskan Repurposer membuat caption tayang dan Keuangan membuat tagihan pelunasan Floatee.",
                tugas=[
                    DelegatedTask(
                        target_agent="repurpose",
                        action="repurpose_video",
                        ringkasan_tugas="Siapkan paket judul, caption, hashtag, dan pinned comment Floatee.",
                        alasan_delegasi="Video baru ACC dan siap tayang.",
                        judul_kerja="Endorse Floatee Denn & Miki",
                        ringkasan="Video endorse animasi Denn & Miki untuk brand minuman Floatee sudah ACC.",
                        klien="Floatee",
                    ),
                    DelegatedTask(
                        target_agent="finance",
                        action="finance_bill",
                        ringkasan_tugas="Buat format pesan WA tagihan pelunasan untuk Floatee.",
                        alasan_delegasi="Bos minta tagih pelunasan Floatee.",
                        klien="Floatee",
                    ),
                ],
            )
            events: list[tuple[str, str]] = []
            agent = ManagerOrchestratorAgent(
                gemini_client=FakeOrchestratorGeminiClient(plan),  # type: ignore[arg-type]
                lead_store=LeadStore(file_path=tmp / "leads.json"),
                finance_store=fin_store,
                on_agent_event=lambda aid, ev, _msg: events.append((aid, ev)),
            )

            report = agent.run("Floatee baru ACC, siapin buat tayang dan tagih pelunasan")
            self.assertEqual(len(report.hasil_delegasi), 2)
            self.assertTrue(all(r.berhasil for r in report.hasil_delegasi))
            self.assertEqual(
                [r.target_agent for r in report.hasil_delegasi], ["repurpose", "finance"]
            )
            self.assertIn(("repurpose", "working"), events)
            self.assertIn(("repurpose", "done"), events)
            self.assertIn(("finance", "working"), events)
            self.assertIn(("finance", "done"), events)

            md = agent.format_report(report)
            self.assertIn("Floatee", md)
            self.assertIn("REPURPOSE", md)
            self.assertIn("FINANCE", md)

    def test_trend_to_repurpose_auto_chaining_and_ad_hoc_billing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            plan = OrchestratorPlan(
                ringkasan_rencana="Cari tren, teruskan ide #1 ke Repurposer, lalu buat format tagihan ad-hoc.",
                tugas=[
                    DelegatedTask(
                        target_agent="trend",
                        action="trend_research",
                        ringkasan_tugas="Ambil tren Indonesia.",
                        alasan_delegasi="Diminta bos.",
                    ),
                    DelegatedTask(
                        target_agent="repurpose",
                        action="repurpose_video",
                        ringkasan_tugas="Ubah ide #1 jadi paket 3 platform.",
                        alasan_delegasi="Otomatis dari ide tren.",
                        ringkasan="",
                    ),
                    DelegatedTask(
                        target_agent="finance",
                        action="finance_bill",
                        ringkasan_tugas="Buat format tagihan Brand Baru.",
                        alasan_delegasi="Tagihan belum di database.",
                        klien="Brand Baru",
                    ),
                ],
            )
            agent = ManagerOrchestratorAgent(
                gemini_client=FakeOrchestratorGeminiClient(plan),  # type: ignore[arg-type]
                lead_store=LeadStore(file_path=tmp / "leads.json"),
                finance_store=FinanceStore(file_path=tmp / "finance.json"),
                trend_fetcher=lambda _g, _m: [TrendItem(title="cuaca panas")],
            )

            report = agent.run("Cari tren, bikin captionnya, dan tagih Brand Baru")
            self.assertEqual(len(report.hasil_delegasi), 3)
            self.assertTrue(all(r.berhasil for r in report.hasil_delegasi))
            self.assertIn("Format Tagihan Pelunasan — Brand Baru", report.hasil_delegasi[2].output_markdown)

            with self.assertRaises(ValueError):
                agent.run("   ")


if __name__ == "__main__":
    unittest.main()
