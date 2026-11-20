"""Unit test offline untuk Agent 3 (Lead Hunter UMKM)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agents.lead_hunter import (
    LeadHunterAgent,
    LeadNotFoundError,
    LeadStore,
    OutreachOutput,
    parse_nominatim_places,
)


class FakeLeadGeminiClient:
    """Mock GeminiClient untuk menguji pembuatan draf penawaran tanpa API call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[OutreachOutput],
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> OutreachOutput:
        self.calls.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction or "",
            }
        )
        return OutreachOutput(
            sudut_pendekatan="Rating Google Maps sudah tinggi, katalog menu online mempermudah order lewat WA.",
            pesan_utama="Halo Kak pemilik Kedai Kopi Sudut! Saya lihat ulasan di Google Maps bagus banget...",
            pesan_followup="Halo Kak, izin follow-up singkat soal contoh tampilan katalog menu online-nya ya.",
            tips_kirim="Kirim di jam 10.00-11.00 WIB sebelum jam ramai makan siang.",
        )


class TestLeadStore(unittest.TestCase):
    def test_crud_and_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(file_path=Path(tmpdir) / "leads.json")

            lead1 = store.add_lead(
                nama_usaha="Kedai Kopi Sudut",
                kategori="Kafe",
                kota="Bandung",
                kontak="08123456789",
                saluran="whatsapp",
                punya_website=False,
                catatan="Rating Google Maps 4.9, menu cuma di highlight IG.",
            )
            lead2 = store.add_lead(
                nama_usaha="Bengkel Maju Jaya",
                kategori="Bengkel",
                kota="Bekasi",
                punya_website=True,
            )

            self.assertEqual(lead1.id, 1)
            self.assertEqual(lead2.id, 2)
            self.assertEqual(len(store.list_leads()), 2)
            self.assertEqual(len(store.list_leads(only_without_website=True)), 1)

            # Cegah duplikat nama+kota (case-insensitive)
            with self.assertRaises(ValueError):
                store.add_lead(
                    nama_usaha="kedai kopi sudut",
                    kategori="Kafe",
                    kota="bandung",
                )

            updated = store.update_status(1, "dihubungi", "Sudah kirim WA pagi")
            self.assertEqual(updated.status, "dihubungi")
            self.assertIn("Sudah kirim WA pagi", updated.catatan)
            self.assertEqual(len(store.list_leads(status="dihubungi")), 1)

            removed = store.delete_lead(2)
            self.assertEqual(removed.nama_usaha, "Bengkel Maju Jaya")
            self.assertEqual(len(store.list_leads()), 1)

    def test_invalid_status_and_missing_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(file_path=Path(tmpdir) / "leads.json")
            with self.assertRaises(LeadNotFoundError):
                store.get_lead(99)
            with self.assertRaises(ValueError):
                store.add_lead(
                    nama_usaha="Laundry Bersih",
                    kategori="Laundry",
                    status="status_ngawur",
                )

    def test_import_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "prospek.csv"
            csv_path.write_text(
                "nama_usaha,kategori,kota,kontak,saluran,punya_website,catatan\n"
                "Bakso Mantap,Kuliner,Depok,08111111,whatsapp,false,Ramai tapi belum ada web\n"
                "Bakso Mantap,Kuliner,Depok,08111111,whatsapp,false,Duplikat harus dilewati\n"
                "Barbershop Rapi,Jasa,Depok,@barberrapi,instagram,false,Foto rapi di IG\n"
                ",Kosong,Depok,,whatsapp,false,Baris tidak valid\n",
                encoding="utf-8",
            )
            store = LeadStore(file_path=tmp / "leads.json")
            added, skipped = store.import_csv(csv_path)
            self.assertEqual(added, 2)
            self.assertEqual(skipped, 2)
            self.assertEqual(len(store.list_leads(only_without_website=True)), 2)


class TestLeadHunterAgent(unittest.TestCase):
    def test_draft_outreach_and_format_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(file_path=Path(tmpdir) / "leads.json")
            store.add_lead(
                nama_usaha="Kedai Kopi Sudut",
                kategori="Kafe",
                kota="Bandung",
                kontak="08123456789",
                saluran="whatsapp",
                catatan="Rating Google Maps 4.9, belum punya katalog menu online.",
            )
            fake_client = FakeLeadGeminiClient()
            agent = LeadHunterAgent(store=store, gemini_client=fake_client)  # type: ignore[arg-type]

            report = agent.draft_outreach(
                lead_id=1,
                penawaran_khusus="Gratis contoh tampilan halaman depan dulu",
                nama_pengirim="Andi",
            )
            self.assertEqual(len(fake_client.calls), 1)
            self.assertIn("Kedai Kopi Sudut", fake_client.calls[0]["prompt"])
            self.assertIn("Gratis contoh tampilan", fake_client.calls[0]["prompt"])
            self.assertIn("Andi", fake_client.calls[0]["prompt"])

            formatted = agent.format_outreach_report(report)
            self.assertIn("Kedai Kopi Sudut", formatted)
            self.assertIn("Pesan Penawaran Utama (WHATSAPP)", formatted)
            self.assertIn("Pesan Follow-Up (H+3)", formatted)

    def test_draft_outreach_without_gemini_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(file_path=Path(tmpdir) / "leads.json")
            store.add_lead(nama_usaha="Laundry Express", kategori="Laundry")
            agent = LeadHunterAgent(store=store, gemini_client=None)
            with self.assertRaises(ValueError):
                agent.draft_outreach(lead_id=1)

    def test_parse_nominatim_places_filters_chains_highways_and_websites(self) -> None:
        raw_places = [
            {
                "name": "Jalan Kopi",
                "category": "highway",
                "type": "residential",
            },
            {
                "name": "Kopi Kenangan Dago",
                "category": "amenity",
                "type": "cafe",
                "extratags": {},
            },
            {
                "name": "Kafe Sudah Punya Web",
                "category": "amenity",
                "type": "cafe",
                "extratags": {"website": "https://kafesudahada.id"},
            },
            {
                "name": "Kopi Lokal Sudut",
                "category": "amenity",
                "type": "cafe",
                "osm_type": "node",
                "osm_id": 12345,
                "extratags": {"contact:whatsapp": "+628123456789", "opening_hours": "08:00-22:00"},
                "address": {"road": "Jl. Braga", "suburb": "Sumur Bandung", "city": "Bandung"},
            },
            {
                "name": "kopi lokal sudut",
                "category": "amenity",
                "type": "cafe",
                "extratags": {},
            },
            {
                "name": "Kedai Senja IG",
                "category": "shop",
                "type": "coffee",
                "osm_type": "way",
                "osm_id": 999,
                "extratags": {"contact:instagram": "@kedaisenja"},
                "address": {"road": "Jl. Dago", "city": "Bandung"},
            },
        ]
        found = parse_nominatim_places(
            raw_places=raw_places,
            default_city="Bandung",
            default_category="kopi",
            only_without_website=True,
            exclude_chains=True,
            limit=10,
        )
        self.assertEqual([item.nama_usaha for item in found], ["Kopi Lokal Sudut", "Kedai Senja IG"])
        self.assertEqual(found[0].saluran, "whatsapp")
        self.assertEqual(found[0].kontak, "+628123456789")
        self.assertIn("Jl. Braga", found[0].alamat)
        self.assertEqual(found[1].saluran, "instagram")
        self.assertEqual(found[1].kontak, "@kedaisenja")

        with tempfile.TemporaryDirectory() as tmpdir:
            store = LeadStore(file_path=Path(tmpdir) / "leads.json")
            agent = LeadHunterAgent(store=store)
            added, skipped = agent.save_discovered_leads(found)
            self.assertEqual(len(added), 2)
            self.assertEqual(skipped, 0)
            added2, skipped2 = agent.save_discovered_leads(found)
            self.assertEqual(len(added2), 0)
            self.assertEqual(skipped2, 2)


if __name__ == "__main__":
    unittest.main()
