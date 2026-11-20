"""Unit test offline untuk Agent 5 (Asisten CS & QC Brief Endorse)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agents.cs_qc import (
    BriefQCOutput,
    CSQCAgent,
    CSReplyOutput,
    QCCheckItem,
    load_rate_card_and_faq,
)


class FakeCSQCGeminiClient:
    """Mock GeminiClient untuk menguji mode CS Reply & QC Brief tanpa API call."""

    def __init__(self, qc_output: BriefQCOutput | None = None) -> None:
        self.calls: list[dict[str, str]] = []
        self._qc_output = qc_output

    def generate_structured(
        self,
        prompt: str,
        response_schema: type,
        system_instruction: str | None = None,
        temperature: float = 0.5,
    ):
        self.calls.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction or "",
                "schema": response_schema.__name__,
            }
        )
        if response_schema is CSReplyOutput:
            return CSReplyOutput(
                kategori_klien="endorse",
                ringkasan_kebutuhan="Menanyakan rate card endorse 3 platform dan estimasi pengerjaan.",
                draf_balasan=(
                    "Halo Kak! Terima kasih sudah menghubungi Denn & Miki. "
                    "Kami tersedia Paket B (mirroring TikTok, IG Reels, dan YT Shorts) dengan alur DP 50%."
                ),
                perlu_konfirmasi_owner=["Isi nominal harga Paket B di data/rate_card.md"],
                langkah_lanjut="Minta brief produk dan target tanggal tayang dari brand.",
            )
        if self._qc_output is not None:
            return self._qc_output
        return BriefQCOutput(
            # Sengaja dikembalikan LOLOS meski ada 1 item TIDAK_TERPENUHI untuk menguji safeguard Python
            status_keseluruhan="LOLOS",
            daftar_cek=[
                QCCheckItem(
                    poin_brief="Sebut nama brand Es Teh Segar minimal 2x",
                    status="TERPENUHI",
                    bukti_di_skrip="Muncul 2x di dialog Miki.",
                    saran_perbaikan="-",
                ),
                QCCheckItem(
                    poin_brief="Sebut rasa melati asli tanpa pemanis buatan",
                    status="TERPENUHI",
                    bukti_di_skrip="'melati asli tanpa pemanis buatan'",
                    saran_perbaikan="-",
                ),
                QCCheckItem(
                    poin_brief="Wajib sebut kode promo DENNMIKI10",
                    status="TIDAK_TERPENUHI",
                    bukti_di_skrip="Kode promo belum disebut di skrip.",
                    saran_perbaikan="Tambahkan celetukan Miki: 'Pake kode DENNMIKI10 biar dompet aman!'",
                ),
            ],
            peringatan_larangan=["Kalimat 'jauh lebih enak dari teh sebelah' berisiko menyinggung kompetitor."],
            rekomendasi_revisi_cepat="Hapus perbandingan dengan 'teh sebelah' dan sisipkan kode promo DENNMIKI10 di ending.",
        )


class TestCSQCAgent(unittest.TestCase):
    def test_load_rate_card_default_and_custom_file(self) -> None:
        default_text = load_rate_card_and_faq()
        self.assertIn("ENDORSE", default_text.upper())
        self.assertIn("WEBSITE UMKM", default_text.upper())

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "rate_card.md"
            custom_path.write_text("# Rate Card Khusus\nPaket Web: Rp1.500.000", encoding="utf-8")
            loaded = load_rate_card_and_faq(custom_path)
            self.assertIn("Rp1.500.000", loaded)

            with self.assertRaises(ValueError):
                load_rate_card_and_faq(Path(tmpdir) / "tidak_ada.md")

    def test_draft_cs_reply_and_format(self) -> None:
        fake_client = FakeCSQCGeminiClient()
        agent = CSQCAgent(gemini_client=fake_client)  # type: ignore[arg-type]

        report = agent.draft_cs_reply(
            pesan_klien="Halo kak, rate card endorse 3 platform berapa ya?",
            layanan="endorse",
            nama_klien="Tim Brand A",
            nama_pengirim="Denn",
            rate_card_override="Paket B 3 Platform: Rp2.500.000",
        )
        self.assertEqual(report.kategori_klien, "endorse")
        self.assertIn("Rp2.500.000", fake_client.calls[0]["system_instruction"])
        self.assertIn("Tim Brand A", fake_client.calls[0]["prompt"])

        formatted = agent.format_cs_reply(report)
        self.assertIn("Draf Balasan Siap Kirim", formatted)
        self.assertIn("Perlu Dicek / Diisi Owner", formatted)

        with self.assertRaises(ValueError):
            agent.draft_cs_reply(pesan_klien="   ")

    def test_qc_brief_safeguard_forces_perlu_revisi_and_computes_score(self) -> None:
        fake_client = FakeCSQCGeminiClient()
        agent = CSQCAgent(gemini_client=fake_client)  # type: ignore[arg-type]

        report = agent.check_endorse_script(
            brief_klien="1. Sebut Es Teh Segar 2x. 2. Melati asli. 3. Kode DENNMIKI10.",
            skrip="Miki kasih Es Teh Segar: 'Es Teh Segar melati asli, lebih enak dari teh sebelah!'",
            nama_brand="Es Teh Segar",
        )
        # Safeguard harus memaksa PERLU_REVISI walaupun mock LLM mengembalikan LOLOS
        self.assertEqual(report.status_keseluruhan, "PERLU_REVISI")
        self.assertEqual(report.poin_terpenuhi, 2)
        self.assertEqual(report.total_poin, 3)
        self.assertEqual(report.skor_persen, 67)
        self.assertEqual(len(report.peringatan_larangan), 1)

        formatted = agent.format_qc_report(report)
        self.assertIn("PERLU_REVISI", formatted)
        self.assertIn("[KURANG]", formatted)
        self.assertIn("[PERINGATAN]", formatted)

    def test_qc_brief_passes_when_all_items_met_and_no_warnings(self) -> None:
        all_ok = BriefQCOutput(
            status_keseluruhan="LOLOS",
            daftar_cek=[
                QCCheckItem(
                    poin_brief="Sebut brand",
                    status="TERPENUHI",
                    bukti_di_skrip="Ada di dialog 1.",
                    saran_perbaikan="-",
                )
            ],
            peringatan_larangan=[],
            rekomendasi_revisi_cepat="Skrip siap masuk tahap animasi.",
        )
        fake_client = FakeCSQCGeminiClient(qc_output=all_ok)
        agent = CSQCAgent(gemini_client=fake_client)  # type: ignore[arg-type]

        report = agent.check_endorse_script(brief_klien="Sebut brand.", skrip="Halo brand!")
        self.assertEqual(report.status_keseluruhan, "LOLOS")
        self.assertEqual(report.skor_persen, 100)

    def test_qc_brief_rejects_empty_inputs(self) -> None:
        fake_client = FakeCSQCGeminiClient()
        agent = CSQCAgent(gemini_client=fake_client)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            agent.check_endorse_script(brief_klien=" ", skrip="Halo")
        with self.assertRaises(ValueError):
            agent.check_endorse_script(brief_klien="Brief", skrip=" ")
        self.assertEqual(len(fake_client.calls), 0)


if __name__ == "__main__":
    unittest.main()
