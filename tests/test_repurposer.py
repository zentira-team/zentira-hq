"""Unit test offline untuk Agent 2 (Repurposer 3 Platform)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.repurposer.agent import (
    RepurposeOutput,
    RepurposerAgent,
    VideoBrief,
    _LLMPlatformCopy,
)
from main import _resolve_video_summary


class FakeRepurposeGeminiClient:
    """Mock GeminiClient untuk menguji Agent 2 tanpa API call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[RepurposeOutput],
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> RepurposeOutput:
        self.calls.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction or "",
            }
        )
        return RepurposeOutput(
            catatan_strategi="TikTok dibuat lebih punchy, IG Reels mendorong share DM, YT Shorts ramah pencarian.",
            tiktok=_LLMPlatformCopy(
                judul="Overthinking Notif BMKG 😭",
                caption="Baru gerimis 3 tetes, si Denn udah siap evakuasi. Tim Denn atau tim Miki?",
                hashtags="DennMiki #dennmiki #AnimasiIndonesia #KomediRelatable",
                pinned_comment="Jujur, kalian pernah bawa jas hujan eh malah panas terik ga?",
            ),
            instagram_reels=_LLMPlatformCopy(
                judul="Drama Notif BMKG vs Realita Cuaca",
                caption="Kirim ke temen lo yang panikan tiap denger ramalan hujan padahal cuma mendung doang.",
                hashtags="#AnimasiIndonesia #DennMiki ReelsLucu",
                pinned_comment="Miki: 'Den, mantelnya buat mandi uap ya?'",
            ),
            youtube_shorts=_LLMPlatformCopy(
                judul="Ketika Denn Panik Baca Notif BMKG | Denn & Miki",
                caption="Denn langsung pakai jas hujan 3 lapis di kafe gara-gara notif BMKG. Subscribe biar ga ketinggalan episode selanjutnya!",
                hashtags="AnimasiLucu #DennMiki",
                pinned_comment="Kalau di kota kalian sekarang beneran hujan apa cuma PHP doang?",
            ),
        )


class TestRepurposerAgent(unittest.TestCase):
    def test_repurposer_builds_three_platforms_and_normalizes_hashtags(self) -> None:
        fake_client = FakeRepurposeGeminiClient()
        agent = RepurposerAgent(gemini_client=fake_client)  # type: ignore[arg-type]

        brief = VideoBrief(
            ringkasan="Denn overthinking soal notif BMKG hujan lebat, Miki nyindir logis.",
            judul_kerja="Jas Hujan 3 Lapis",
            cta_tambahan="Cek keranjang kuning untuk payung lipat anti badai.",
        )
        report = agent.run(brief)

        self.assertEqual(len(fake_client.calls), 1)
        self.assertIn("Denn", fake_client.calls[0]["system_instruction"])
        self.assertIn("Miki", fake_client.calls[0]["system_instruction"])
        self.assertIn("payung lipat", fake_client.calls[0]["prompt"])

        # Hashtag deduplikasi + format #
        self.assertEqual(
            report.tiktok.hashtags,
            ["#DennMiki", "#AnimasiIndonesia", "#KomediRelatable"],
        )
        self.assertEqual(
            report.instagram_reels.hashtags,
            ["#AnimasiIndonesia", "#DennMiki", "#ReelsLucu"],
        )
        # YouTube Shorts wajib punya #Shorts
        self.assertIn("#Shorts", report.youtube_shorts.hashtags)

        formatted = agent.format_report(report)
        self.assertIn("## 1. TikTok", formatted)
        self.assertIn("## 2. Instagram Reels", formatted)
        self.assertIn("## 3. YouTube Shorts", formatted)
        self.assertIn("Pinned Comment", formatted)

    def test_repurposer_rejects_empty_summary(self) -> None:
        fake_client = FakeRepurposeGeminiClient()
        agent = RepurposerAgent(gemini_client=fake_client)  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            agent.run(VideoBrief(ringkasan="   "))
        self.assertEqual(len(fake_client.calls), 0)

    def test_cli_resolve_summary_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "ringkasan.txt"
            file_path.write_text("Denn ketiduran pas trailer film akhirnya rilis.", encoding="utf-8")
            args = SimpleNamespace(summary=None, file=str(file_path))
            self.assertEqual(
                _resolve_video_summary(args),
                "Denn ketiduran pas trailer film akhirnya rilis.",
            )


if __name__ == "__main__":
    unittest.main()
