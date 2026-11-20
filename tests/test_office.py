"""Unit test offline untuk backend FastAPI Kantor Virtual 3D (Agent 1–5)."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from agents.cs_qc import BriefQCOutput, CSReplyOutput, QCCheckItem
from agents.finance_admin import FinanceStore, ReminderDraftOutput
from agents.lead_hunter import DiscoveredLead, LeadStore, OutreachOutput
from agents.orchestrator import DelegatedTask, OrchestratorPlan
from agents.repurposer.agent import RepurposeOutput, _LLMPlatformCopy
from agents.trend_researcher import StoryIdea, TrendAnalysisOutput, TrendItem
from office import OfficeStateManager, create_app


class MockAllAgentsGeminiClient:
    """Mock serba bisa untuk seluruh skema terstruktur Agent 1–5 + Whisper tanpa API call."""

    def __init__(self) -> None:
        self.last_used_model = "gemini-3.5-flash"

    def transcribe_audio(
        self,
        file_bytes: bytes,
        filename: str = "media.mp4",
        content_type: str = "application/octet-stream",
        language: str = "id",
    ) -> tuple[str, str]:
        if not file_bytes:
            raise ValueError("File kosong")
        return "Denn kaget lihat harga es kopi kekinian, Miki cuma ketawa.", "groq:whisper-large-v3-turbo"

    def generate_structured(
        self,
        prompt: str,
        response_schema: type,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ):
        if response_schema is TrendAnalysisOutput:
            return TrendAnalysisOutput(
                ringkasan_filter="1 tren relatable dipilih.",
                ide_cerita=[
                    StoryIdea(
                        judul_ide="Jas Hujan 3 Lapis",
                        tren_sumber="bmkg hari ini",
                        alasan_dipilih="Relatable cuaca labil.",
                        sudut_pandang_cerita="Denn overthinking, Miki nyindir logis.",
                        hook_3_detik="Denn pakai 3 jas hujan di kafe!",
                        estimasi_durasi="40 detik",
                    )
                ],
            )
        if response_schema is RepurposeOutput:
            return RepurposeOutput(
                catatan_strategi="Disesuaikan 3 platform.",
                tiktok=_LLMPlatformCopy(
                    judul="Panik BMKG",
                    caption="Siapa yang kaya Denn?",
                    hashtags="#DennMiki #Animasi",
                    pinned_comment="Tim bawa jas hujan?",
                ),
                instagram_reels=_LLMPlatformCopy(
                    judul="Ekspektasi Badai",
                    caption="Share ke temen lu!",
                    hashtags="#DennMiki #ReelsLucu",
                    pinned_comment="Miki geleng kepala.",
                ),
                youtube_shorts=_LLMPlatformCopy(
                    judul="Denn Panik Notif Cuaca",
                    caption="Subscribe Denn & Miki!",
                    hashtags="#DennMiki #Komedi",
                    pinned_comment="Pernah kena prank cuaca?",
                ),
            )
        if response_schema is OutreachOutput:
            return OutreachOutput(
                sudut_pendekatan="Katalog menu online ke WA.",
                pesan_utama="Halo Kak Kedai Kopi Lokal!",
                pesan_followup="Izin follow-up singkat ya Kak.",
                tips_kirim="Kirim jam 10 pagi.",
            )
        if response_schema is ReminderDraftOutput:
            return ReminderDraftOutput(
                pesan_pengingat="Halo Kak, izin mengingatkan sisa Rp1.000.000.",
                catatan_nada="Ramah dan sopan.",
            )
        if response_schema is CSReplyOutput:
            return CSReplyOutput(
                kategori_klien="endorse",
                ringkasan_kebutuhan="Tanya rate card endorse.",
                draf_balasan="Halo Kak! Terima kasih sudah menghubungi Denn & Miki.",
                perlu_konfirmasi_owner=["Cek slot jadwal"],
                langkah_lanjut="Minta brief produk.",
            )
        if response_schema is BriefQCOutput:
            return BriefQCOutput(
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
                rekomendasi_revisi_cepat="Siap produksi.",
            )
        if response_schema is OrchestratorPlan:
            return OrchestratorPlan(
                ringkasan_rencana="Delegasi Floatee ke Repurposer dan Keuangan.",
                tugas=[
                    DelegatedTask(
                        target_agent="repurpose",
                        action="repurpose_video",
                        ringkasan_tugas="Siapkan paket tayang Floatee.",
                        alasan_delegasi="Baru ACC.",
                        klien="Floatee",
                        ringkasan="Video endorse Floatee siap tayang.",
                    ),
                    DelegatedTask(
                        target_agent="finance",
                        action="finance_bill",
                        ringkasan_tugas="Buat tagihan pelunasan Floatee.",
                        alasan_delegasi="Diminta bos.",
                        klien="Floatee",
                    ),
                ],
            )
        raise AssertionError(f"Skema tidak dikenal: {response_schema}")


class TestOfficeServer(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.app = create_app(
            lead_store=LeadStore(file_path=tmp / "leads.json"),
            finance_store=FinanceStore(file_path=tmp / "finance.json"),
            gemini_factory=lambda: MockAllAgentsGeminiClient(),  # type: ignore[arg-type,return-value]
            trend_fetcher=lambda geo, max_items: [
                TrendItem(title="bmkg hari ini", approx_traffic="1000+")
            ],
            lead_discoverer=lambda **kwargs: [
                DiscoveredLead(
                    nama_usaha="Kedai Kopi Lokal",
                    kategori="Kopi",
                    kota="Bandung",
                    alamat="Jl. Braga",
                )
            ],
            rate_card_file=tmp / "rate_card.md",
            output_dir=tmp / "outputs",
            profile_path=tmp / "office_profile.json",
        )
        self.profile_path = tmp / "office_profile.json"
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_index_and_initial_state(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Kantor Virtual 3D", resp.text)

        state = self.client.get("/api/state").json()
        self.assertEqual(len(state["agents"]), 6)
        self.assertEqual(state["agents"][0]["id"], "manager")
        self.assertIn("phone", state["urls"])

    def test_all_five_agent_endpoints_and_inbox(self) -> None:
        # Agent 1
        r1 = self.client.post("/api/agents/trend/run", json={"geo": "ID", "max_ideas": 3})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(len(r1.json()["report"]["ide_cerita"]), 1)

        # Agent 2
        r2 = self.client.post(
            "/api/agents/repurpose/run",
            json={"ringkasan": "Denn pakai jas hujan 3 lapis."},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertIn("#Shorts", r2.json()["report"]["youtube_shorts"]["hashtags"])

        # Agent 3: discover -> list -> pitch
        r3_disc = self.client.post(
            "/api/agents/leads/discover",
            json={"keyword": "kopi", "city": "Bandung", "save_leads": True},
        )
        self.assertEqual(r3_disc.status_code, 200)
        self.assertEqual(r3_disc.json()["saved_count"], 1)

        r3_pitch = self.client.post("/api/agents/leads/1/pitch", json={"sender": "Denn"})
        self.assertEqual(r3_pitch.status_code, 200)
        self.assertIn("Kedai Kopi Lokal", r3_pitch.json()["report"]["pesan_utama"])

        # Agent 4: invoice -> overview -> split -> remind-draft -> pay
        r4_inv = self.client.post(
            "/api/agents/finance/invoice",
            json={
                "klien": "Kedai Kopi Lokal",
                "proyek": "Web Katalog",
                "total_harga": 2_000_000,
                "dp": 1_000_000,
                "jatuh_tempo": "2026-11-28",
            },
        )
        self.assertEqual(r4_inv.status_code, 200)

        r4_ov = self.client.get("/api/agents/finance/overview")
        self.assertEqual(r4_ov.status_code, 200)
        self.assertEqual(r4_ov.json()["summary"]["total_piutang_klien"], 1_000_000)

        r4_split = self.client.post(
            "/api/agents/finance/split",
            json={"total_pendapatan": 2_000_000, "biaya_operasional": 200_000, "shares": "Saya:60,Partner:40"},
        )
        self.assertEqual(r4_split.status_code, 200)
        self.assertEqual(r4_split.json()["result"]["laba_bersih"], 1_800_000)

        r4_draft = self.client.post(
            "/api/agents/finance/invoice/1/remind-draft", json={"bank": "BCA 123"}
        )
        self.assertEqual(r4_draft.status_code, 200)

        # Agent 5: rate-card update -> reply -> qc
        r5_rc = self.client.put(
            "/api/agents/cs/rate-card", json={"content": "# Rate Card\nPaket A: Rp1.000.000"}
        )
        self.assertEqual(r5_rc.status_code, 200)

        r5_rep = self.client.post(
            "/api/agents/cs/reply", json={"pesan_klien": "Tanya rate card endorse kak"}
        )
        self.assertEqual(r5_rep.status_code, 200)

        r5_qc = self.client.post(
            "/api/agents/cs/qc",
            json={"brief_klien": "Sebut brand.", "skrip": "Halo brand!", "nama_brand": "Brand X"},
        )
        self.assertEqual(r5_qc.status_code, 200)
        self.assertEqual(r5_qc.json()["report"]["status_keseluruhan"], "LOLOS")

        # Inbox Bos terisi laporan & save-output berfungsi
        state = self.client.get("/api/state").json()
        self.assertGreaterEqual(len(state["inbox"]), 5)

        saved = self.client.post(
            "/api/save-output", json={"prefix": "test_office", "content": "# Halo"}
        )
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(Path(saved.json()["path"]).is_file())

    def test_custom_agent_names_persist(self) -> None:
        resp = self.client.put(
            "/api/agents/names",
            json={"names": {"trend": "Denn", "repurpose": "Miki"}},
        )
        self.assertEqual(resp.status_code, 200)
        names_map = {a["id"]: a["name"] for a in resp.json()["agents"]}
        self.assertEqual(names_map["trend"], "Denn")
        self.assertEqual(names_map["repurpose"], "Miki")
        self.assertTrue(self.profile_path.is_file())

        # Pastikan nama kosong ditolak
        bad = self.client.put("/api/agents/names", json={"names": {"trend": "   "}})
        self.assertEqual(bad.status_code, 400)

    def test_manager_orchestrator_and_finance_reset_delete(self) -> None:
        # Tambah transaksi lalu hapus 1 dan reset sisanya
        t1 = self.client.post(
            "/api/agents/finance/tx",
            json={"jenis": "masuk", "nominal": 500_000, "kategori": "endorse", "sumber": "konten"},
        )
        self.assertEqual(t1.status_code, 200)
        tx_id = t1.json()["transaction"]["id"]
        self.assertEqual(self.client.delete(f"/api/agents/finance/tx/{tx_id}").status_code, 200)

        self.client.post(
            "/api/agents/finance/tx",
            json={"jenis": "masuk", "nominal": 750_000, "kategori": "web", "sumber": "web_umkm"},
        )
        self.assertEqual(self.client.post("/api/agents/finance/reset").status_code, 200)
        ov = self.client.get("/api/agents/finance/overview").json()
        self.assertEqual(ov["summary"]["saldo_bersih"], 0)
        self.assertEqual(len(ov["transactions"]), 0)

        # Jalankan Agent Manajer (Orchestrator)
        mgr = self.client.post(
            "/api/agents/manager/run",
            json={"perintah": "Floatee baru ACC, siapin buat tayang dan tagih pelunasan"},
        )
        self.assertEqual(mgr.status_code, 200)
        results = mgr.json()["report"]["hasil_delegasi"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["berhasil"] for r in results))

    def test_inbox_delete_and_agent_idle_lifecycle(self) -> None:
        # Buat 2 laporan di inbox
        self.assertEqual(
            self.client.post("/api/agents/trend/run", json={"geo": "ID", "max_ideas": 1}).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/agents/repurpose/run",
                json={"ringkasan": "Denn pakai jas hujan."},
            ).status_code,
            200,
        )

        snap = self.client.get("/api/state").json()
        self.assertEqual(len(snap["inbox"]), 2)
        first_id = snap["inbox"][0]["id"]

        # Hapus 1 item inbox
        del_one = self.client.delete(f"/api/inbox/{first_id}")
        self.assertEqual(del_one.status_code, 200)
        self.assertEqual(len(del_one.json()["inbox"]), 1)
        self.assertEqual(self.client.delete(f"/api/inbox/{first_id}").status_code, 404)

        # Kembalikan 1 agent ke idle secara manual
        idle_resp = self.client.post("/api/agents/trend/idle")
        self.assertEqual(idle_resp.status_code, 200)
        trend_state = next(a for a in idle_resp.json()["agents"] if a["id"] == "trend")
        self.assertEqual(trend_state["status"], "idle")

        # Kosongkan semua inbox
        del_all = self.client.delete("/api/inbox")
        self.assertEqual(del_all.status_code, 200)
        self.assertEqual(len(del_all.json()["inbox"]), 0)

        # Verifikasi auto-idle timer otomatis mengembalikan status done -> idle tanpa menghapus inbox
        fast_state = OfficeStateManager(
            profile_path=self.profile_path,
            auto_idle_seconds=0.06,
        )
        fast_state.set_done("trend", "Selesai!", "Tes Auto Idle", "# Konten")
        self.assertEqual(fast_state.snapshot()["agents"][1]["status"], "done")
        time.sleep(0.18)
        after = fast_state.snapshot()
        trend_after = next(a for a in after["agents"] if a["id"] == "trend")
        self.assertEqual(trend_after["status"], "idle")
        self.assertEqual(len(after["inbox"]), 1)

    def test_office_modes_work_meeting_holiday_and_auto_wake(self) -> None:
        # Awalnya mode work
        init = self.client.get("/api/state").json()
        self.assertEqual(init["office_mode"], "work")

        # Pindah ke meeting
        r_meet = self.client.post("/api/office/mode", json={"mode": "meeting"})
        self.assertEqual(r_meet.status_code, 200)
        self.assertEqual(r_meet.json()["office_mode"], "meeting")

        # Pindah ke holiday (Libur)
        r_hol = self.client.post("/api/office/mode", json={"mode": "holiday"})
        self.assertEqual(r_hol.status_code, 200)
        self.assertEqual(r_hol.json()["office_mode"], "holiday")

        # Mode tidak valid ditolak 400
        r_bad = self.client.post("/api/office/mode", json={"mode": "tidur"})
        self.assertEqual(r_bad.status_code, 400)

        # Jika bos jalankan agent saat kantor Libur, otomatis bangun ke mode work
        r_run = self.client.post("/api/agents/trend/run", json={"geo": "ID", "max_ideas": 1})
        self.assertEqual(r_run.status_code, 200)
        after = self.client.get("/api/state").json()
        self.assertEqual(after["office_mode"], "work")

    def test_repurpose_media_whisper_and_model_badge(self) -> None:
        # Format tidak didukung ditolak 400
        bad = self.client.post(
            "/api/agents/repurpose/media",
            headers={"X-File-Name": "skrip.txt"},
            content=b"halo",
        )
        self.assertEqual(bad.status_code, 400)

        # Mode transkrip saja
        tr = self.client.post(
            "/api/agents/repurpose/media?transcribe_only=true",
            headers={"X-File-Name": "denn_kopi.mp4", "Content-Type": "video/mp4"},
            content=b"fake-mp4-audio-bytes",
        )
        self.assertEqual(tr.status_code, 200)
        self.assertIn("es kopi", tr.json()["transcript"])
        self.assertEqual(tr.json()["model_used"], "groq:whisper-large-v3-turbo")

        # Mode full: transkrip -> 3 platform + model_used badge tersimpan di Inbox Bos
        full = self.client.post(
            "/api/agents/repurpose/media?judul_kerja=Kopi%20Mahal",
            headers={"X-File-Name": "denn_kopi.mp4", "Content-Type": "video/mp4"},
            content=b"fake-mp4-audio-bytes",
        )
        self.assertEqual(full.status_code, 200)
        data = full.json()
        self.assertEqual(data["model_used"], "groq:whisper-large-v3-turbo + gemini-3.5-flash")
        self.assertIn("#Shorts", data["report"]["youtube_shorts"]["hashtags"])

        snap = self.client.get("/api/state").json()
        self.assertEqual(
            snap["inbox"][0]["model_used"],
            "groq:whisper-large-v3-turbo + gemini-3.5-flash",
        )

    def test_auth_password_protection_and_backup_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            t = Path(tmpdir)
            protected_app = create_app(
                lead_store=LeadStore(file_path=t / "leads.json"),
                finance_store=FinanceStore(file_path=t / "finance.json"),
                gemini_factory=lambda: MockAllAgentsGeminiClient(),  # type: ignore[arg-type,return-value]
                rate_card_file=t / "rate_card.md",
                output_dir=t / "outputs",
                profile_path=t / "office_profile.json",
                office_password="rahasia-zentira",
            )
            c = TestClient(protected_app)

            # Sebelum login: /api/health & /api/auth/status terbuka, /api/state terkunci 401
            self.assertEqual(c.get("/api/health").status_code, 200)
            st = c.get("/api/auth/status").json()
            self.assertTrue(st["protected"])
            self.assertFalse(st["authenticated"])
            self.assertEqual(c.get("/api/state").status_code, 401)

            # Password salah ditolak 401
            self.assertEqual(
                c.post("/api/auth/login", json={"password": "salah"}).status_code, 401
            )

            # Password benar membuka sesi cookie
            ok = c.post("/api/auth/login", json={"password": "rahasia-zentira"})
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(c.get("/api/state").status_code, 200)

            # Tambah data, export backup, reset, lalu import restore
            c.post(
                "/api/agents/finance/tx",
                json={"jenis": "masuk", "nominal": 1_500_000, "kategori": "endorse", "sumber": "konten"},
            )
            c.put("/api/agents/names", json={"names": {"manager": "Denn"}})
            exported = c.get("/api/backup/export").json()
            self.assertEqual(exported["names"]["manager"], "Denn")

            c.post("/api/agents/finance/reset")
            self.assertEqual(
                c.get("/api/agents/finance/overview").json()["summary"]["saldo_bersih"], 0
            )

            imp = c.post("/api/backup/import", json=exported)
            self.assertEqual(imp.status_code, 200)
            self.assertEqual(
                c.get("/api/agents/finance/overview").json()["summary"]["saldo_bersih"],
                1_500_000,
            )

            # Logout mengunci sesi lagi
            self.assertEqual(c.post("/api/auth/logout").status_code, 200)
            self.assertEqual(c.get("/api/state").status_code, 401)


if __name__ == "__main__":
    unittest.main()
