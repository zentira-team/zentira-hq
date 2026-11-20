"""Unit test offline untuk Agent 4 (Admin Keuangan & Pengingat)."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from agents.finance_admin import (
    FinanceAdminAgent,
    FinanceNotFoundError,
    FinanceStore,
    ReminderDraftOutput,
    format_rupiah,
    parse_shares_spec,
)


class FakeFinanceGeminiClient:
    """Mock GeminiClient untuk menguji draf pesan pengingat pembayaran tanpa API call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[ReminderDraftOutput],
        system_instruction: str | None = None,
        temperature: float = 0.6,
    ) -> ReminderDraftOutput:
        self.calls.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction or "",
            }
        )
        return ReminderDraftOutput(
            pesan_pengingat=(
                "Halo Kak, izin mengingatkan pelunasan proyek Website Katalog sebesar Rp1.000.000 "
                "ke BCA 123456 ya Kak. Terima kasih banyak!"
            ),
            catatan_nada="Ramah, sopan, dan langsung menyebutkan sisa tagihan secara jelas.",
        )


class TestFinanceAdmin(unittest.TestCase):
    def test_transactions_and_cashflow_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FinanceStore(file_path=Path(tmpdir) / "finance.json")
            store.add_transaction(
                jenis="masuk",
                nominal=1_500_000,
                kategori="endorse",
                sumber="konten",
                keterangan="Endorse Snack X",
                tanggal="2026-11-10",
            )
            store.add_transaction(
                jenis="keluar",
                nominal=250_000,
                kategori="hosting",
                sumber="web_umkm",
                keterangan="Domain + hosting klien",
                tanggal="2026-11-12",
            )
            store.add_transaction(
                jenis="masuk",
                nominal=500_000,
                kategori="adsense",
                sumber="konten",
                tanggal="2026-10-25",
            )

            agent = FinanceAdminAgent(store=store)
            nov_summary = agent.get_summary(month="2026-11")
            self.assertEqual(nov_summary.total_masuk, 1_500_000)
            self.assertEqual(nov_summary.total_keluar, 250_000)
            self.assertEqual(nov_summary.saldo_bersih, 1_250_000)
            self.assertEqual(nov_summary.rincian_per_sumber["konten"]["bersih"], 1_500_000)
            self.assertEqual(nov_summary.rincian_per_sumber["web_umkm"]["bersih"], -250_000)
            self.assertEqual(format_rupiah(1_250_000), "Rp1.250.000")

    def test_invoice_dp_to_lunas_syncs_transactions_and_guards_overpay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FinanceStore(file_path=Path(tmpdir) / "finance.json")
            inv, dp_tx = store.add_invoice(
                klien="Kedai Kopi Sudut",
                proyek="Website Katalog",
                total_harga=2_000_000,
                dp=800_000,
                sumber="web_umkm",
                jatuh_tempo="2026-11-25",
            )
            self.assertEqual(inv.status, "dp")
            self.assertEqual(inv.sisa_tagihan, 1_200_000)
            self.assertIsNotNone(dp_tx)
            self.assertEqual(len(store.list_transactions()), 1)

            # Pembayaran melebihi sisa harus ditolak
            with self.assertRaises(ValueError):
                store.record_payment(invoice_id=inv.id, nominal=1_500_000)

            updated, pay_tx = store.record_payment(
                invoice_id=inv.id, nominal=1_200_000, catatan="Transfer BCA"
            )
            self.assertEqual(updated.status, "lunas")
            self.assertEqual(updated.sisa_tagihan, 0)
            self.assertIsNotNone(pay_tx)
            self.assertEqual(len(store.list_transactions()), 2)

            # Tagihan lunas tidak bisa dibayar lagi
            with self.assertRaises(ValueError):
                store.record_payment(invoice_id=inv.id, nominal=100_000)

            with self.assertRaises(FinanceNotFoundError):
                store.get_invoice(999)

    def test_reminders_classification_and_sorting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FinanceStore(file_path=Path(tmpdir) / "finance.json")
            store.add_invoice("Klien Terjadwal", "Web A", 1_000_000, jatuh_tempo="2026-12-10")
            store.add_invoice("Klien Terlambat", "Web B", 1_500_000, dp=500_000, jatuh_tempo="2026-11-18")
            store.add_invoice("Klien Hari Ini", "Endorse C", 800_000, jatuh_tempo="2026-11-21")
            store.add_invoice("Klien Segera", "Web D", 2_000_000, dp=1_000_000, jatuh_tempo="2026-11-24")
            store.add_invoice("Klien Tanpa Tenggat", "Web E", 500_000, jatuh_tempo="")
            store.add_invoice("Klien Lunas", "Web F", 500_000, dp=500_000, jatuh_tempo="2026-11-15")

            agent = FinanceAdminAgent(store=store)
            reminders = agent.get_reminders(
                within_days=7, reference_date=date(2026, 11, 21)
            )
            self.assertEqual(
                [item.kategori_urgensi for item in reminders],
                ["terlambat", "hari_ini", "segera", "menunggu", "tanpa_tenggat"],
            )
            self.assertEqual(reminders[0].invoice.klien, "Klien Terlambat")
            self.assertEqual(reminders[0].hari_tersisa, -3)
            self.assertEqual(reminders[1].hari_tersisa, 0)
            self.assertEqual(reminders[2].hari_tersisa, 3)

    def test_profit_split_exact_and_validations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = FinanceAdminAgent(store=FinanceStore(file_path=Path(tmpdir) / "f.json"))
            shares = parse_shares_spec("Saya:60,Partner:40")
            result = agent.calculate_profit_split(
                total_pendapatan=2_000_000,
                splits=shares,
                biaya_operasional=200_000,
            )
            self.assertEqual(result.laba_bersih, 1_800_000)
            self.assertEqual(result.pembagian[0].nominal, 1_080_000)
            self.assertEqual(result.pembagian[1].nominal, 720_000)
            self.assertEqual(result.sisa_pembulatan, 0)

            with self.assertRaises(ValueError):
                agent.calculate_profit_split(1_000_000, {"A": 50, "B": 30})
            with self.assertRaises(ValueError):
                agent.calculate_profit_split(500_000, {"A": 100}, biaya_operasional=600_000)

    def test_draft_payment_reminder_uses_exact_amounts_and_blocks_paid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FinanceStore(file_path=Path(tmpdir) / "finance.json")
            inv, _ = store.add_invoice(
                klien="Kedai Kopi Sudut",
                proyek="Website Katalog",
                total_harga=2_000_000,
                dp=1_000_000,
                jatuh_tempo="2026-11-23",
            )
            fake_client = FakeFinanceGeminiClient()
            agent = FinanceAdminAgent(store=store, gemini_client=fake_client)  # type: ignore[arg-type]

            returned_inv, draft = agent.draft_payment_reminder(
                invoice_id=inv.id,
                nama_pengirim="Denn",
                info_rekening="BCA 123456",
                reference_date=date(2026, 11, 21),
            )
            self.assertEqual(returned_inv.id, inv.id)
            self.assertIn("Rp1.000.000", fake_client.calls[0]["prompt"])
            self.assertIn("BCA 123456", fake_client.calls[0]["prompt"])
            formatted = agent.format_reminder_draft(returned_inv, draft)
            self.assertIn("Pesan WhatsApp Siap Kirim", formatted)

            store.record_payment(inv.id, 1_000_000)
            with self.assertRaises(ValueError):
                agent.draft_payment_reminder(inv.id)


if __name__ == "__main__":
    unittest.main()
