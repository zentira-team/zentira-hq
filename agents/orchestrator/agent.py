"""Orkestrasi Agent 6: Agent Manajer (Orchestrator) untuk delegasi otomatis ke Agent 1–5."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agents.cs_qc import CSQCAgent
from agents.finance_admin import FinanceAdminAgent, FinanceStore, parse_shares_spec
from agents.lead_hunter import (
    LeadHunterAgent,
    LeadStore,
    discover_umkm_leads,
)
from agents.orchestrator.prompts import (
    build_orchestrator_system_instruction,
    build_orchestrator_user_prompt,
)
from agents.repurposer import RepurposerAgent, VideoBrief
from agents.trend_researcher import TrendResearcherAgent, fetch_google_trends
from core.formatter import timestamp_wib
from core.gemini_client import GeminiClient


class DelegatedTask(BaseModel):
    """Satu sub-tugas terstruktur yang didelegasikan Manajer ke karyawan AI spesialis."""

    target_agent: str = Field(
        description="Salah satu dari: trend, repurpose, leads, finance, cs"
    )
    action: str = Field(
        description=(
            "Salah satu dari: trend_research, repurpose_video, leads_discover, leads_pitch, "
            "finance_summary, finance_bill, finance_split, cs_reply, cs_qc"
        )
    )
    ringkasan_tugas: str = Field(
        description="Deskripsi singkat 1 kalimat tugas yang diberikan ke karyawan tersebut"
    )
    alasan_delegasi: str = Field(
        description="Alasan singkat kenapa karyawan ini dipilih"
    )
    # Parameter terstruktur opsional sesuai aksi (flat agar ramah structured JSON Gemini)
    geo: str = "ID"
    max_ideas: int = 3
    judul_kerja: str = ""
    ringkasan: str = ""
    cta: str = ""
    keyword: str = ""
    city: str = ""
    limit: int = 8
    save_leads: bool = True
    lead_id: int = 0
    invoice_id: int = 0
    klien: str = ""
    proyek: str = ""
    nominal_teks: str = ""
    nominal_angka: int = 0
    biaya_angka: int = 0
    shares: str = ""
    bank: str = ""
    pesan_klien: str = ""
    layanan: str = "auto"
    brief_klien: str = ""
    skrip: str = ""
    catatan: str = ""


class OrchestratorPlan(BaseModel):
    """Rencana delegasi yang dihasilkan Manajer dari 1 perintah bos."""

    ringkasan_rencana: str = Field(
        description="Ringkasan eksekutif 1-2 kalimat langkah delegasi yang akan dijalankan"
    )
    tugas: list[DelegatedTask] = Field(
        default_factory=list,
        description="Daftar 1 hingga 4 tugas delegasi berurutan",
    )


class DelegatedResult(BaseModel):
    """Hasil eksekusi satu sub-tugas oleh karyawan AI spesialis."""

    target_agent: str
    action: str
    ringkasan_tugas: str
    berhasil: bool
    output_markdown: str


class OrchestratorReport(BaseModel):
    """Laporan gabungan eksekutif dari Agent Manajer."""

    waktu_dibuat: str
    perintah_bos: str
    ringkasan_rencana: str
    hasil_delegasi: list[DelegatedResult] = Field(default_factory=list)


class ManagerOrchestratorAgent:
    """Agent 6 (Manajer) — menerima 1 perintah bos lalu mendelegasikan otomatis ke Agent 1–5."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        lead_store: LeadStore | None = None,
        finance_store: FinanceStore | None = None,
        trend_fetcher: Callable[[str, int], list[Any]] = fetch_google_trends,
        lead_discoverer: Callable[..., list[Any]] = discover_umkm_leads,
        rate_card_file: Path | None = None,
        on_agent_event: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self.gemini_client = gemini_client
        self.lead_store = lead_store or LeadStore()
        self.finance_store = finance_store or FinanceStore()
        self.trend_fetcher = trend_fetcher
        self.lead_discoverer = lead_discoverer
        self.rate_card_file = rate_card_file
        self.on_agent_event = on_agent_event

    def _emit(self, agent_id: str, event_type: str, message: str) -> None:
        if self.on_agent_event is not None:
            try:
                self.on_agent_event(agent_id, event_type, message)
            except Exception:
                pass

    def _match_unpaid_invoice_id(self, task: DelegatedTask) -> int | None:
        unpaid = self.finance_store.list_invoices(unpaid_only=True)
        if task.invoice_id > 0 and any(inv.id == task.invoice_id for inv in unpaid):
            return task.invoice_id
        if task.klien.strip():
            needle = task.klien.strip().casefold()
            for inv in unpaid:
                if needle in inv.klien.casefold() or needle in inv.proyek.casefold():
                    return inv.id
        return None

    def _match_lead_id(self, task: DelegatedTask) -> int | None:
        leads = self.lead_store.list_leads()
        if task.lead_id > 0 and any(ld.id == task.lead_id for ld in leads):
            return task.lead_id
        if task.klien.strip():
            needle = task.klien.strip().casefold()
            for ld in leads:
                if needle in ld.nama_usaha.casefold():
                    return ld.id
        return None

    def _execute_task(
        self,
        task: DelegatedTask,
        context_bag: dict[str, str],
    ) -> DelegatedResult:
        agent_id = task.target_agent.strip().lower()
        action = task.action.strip().lower()

        self._emit(agent_id, "working", f"Tugas dari Manajer: {task.ringkasan_tugas}")
        try:
            md = self._dispatch_action(action, task, context_bag)
            self._emit(agent_id, "done", f"Selesai: {task.ringkasan_tugas}")
            return DelegatedResult(
                target_agent=agent_id,
                action=action,
                ringkasan_tugas=task.ringkasan_tugas,
                berhasil=True,
                output_markdown=md,
            )
        except Exception as exc:
            err_msg = str(exc)
            self._emit(agent_id, "error", err_msg)
            return DelegatedResult(
                target_agent=agent_id,
                action=action,
                ringkasan_tugas=task.ringkasan_tugas,
                berhasil=False,
                output_markdown=f"[Kendala saat menjalankan {action}]: {err_msg}",
            )

    def _dispatch_action(
        self,
        action: str,
        task: DelegatedTask,
        context_bag: dict[str, str],
    ) -> str:
        if action == "trend_research":
            agent = TrendResearcherAgent(
                gemini_client=self.gemini_client,
                geo=task.geo or "ID",
                max_ideas=max(1, min(3, task.max_ideas or 3)),
                fetcher=self.trend_fetcher,
            )
            report = agent.run()
            if report.ide_cerita:
                first = report.ide_cerita[0]
                context_bag["latest_idea_title"] = first.judul_ide
                context_bag["latest_idea_summary"] = (
                    f"{first.hook_3_detik}\n\n{first.sudut_pandang_cerita}"
                )
            return agent.format_report(report)

        if action == "repurpose_video":
            summary = (
                task.ringkasan.strip()
                or context_bag.get("latest_idea_summary", "").strip()
                or f"Konten video animasi Denn & Miki untuk proyek {task.judul_kerja or task.klien or 'terbaru'} yang sudah ACC dan siap tayang."
            )
            title = (
                task.judul_kerja.strip()
                or context_bag.get("latest_idea_title", "").strip()
                or task.klien.strip()
            )
            agent = RepurposerAgent(gemini_client=self.gemini_client)
            report = agent.run(
                VideoBrief(
                    ringkasan=summary,
                    judul_kerja=title,
                    cta_tambahan=task.cta.strip(),
                    catatan_gaya=task.catatan.strip(),
                )
            )
            return agent.format_report(report)

        if action == "leads_discover":
            keyword = task.keyword.strip() or "kopi"
            city = task.city.strip() or "Bandung"
            found = self.lead_discoverer(
                keyword=keyword,
                city=city,
                limit=max(1, min(20, task.limit or 8)),
                only_without_website=True,
                exclude_chains=True,
            )
            agent = LeadHunterAgent(store=self.lead_store)
            md = agent.format_discovered_leads(keyword, city, found)
            if task.save_leads and found:
                added, skipped = agent.save_discovered_leads(found)
                md += f"\n\n*(Tersimpan otomatis ke daftar prospek: {len(added)} baru, {skipped} duplikat dilewati.)*"
            return md

        if action == "leads_pitch":
            lead_id = self._match_lead_id(task)
            if lead_id is None:
                raise ValueError(
                    f"Prospek '{task.klien or task.lead_id}' belum ada di daftar prospek UMKM. "
                    "Tambahkan atau cari dulu lewat Agent Lead Hunter."
                )
            agent = LeadHunterAgent(
                store=self.lead_store, gemini_client=self.gemini_client
            )
            report = agent.draft_outreach(
                lead_id=lead_id, penawaran_khusus=task.catatan.strip()
            )
            return agent.format_outreach_report(report)

        if action == "finance_summary":
            agent = FinanceAdminAgent(store=self.finance_store)
            summary = agent.get_summary()
            reminders = agent.get_reminders(within_days=7)
            return f"{agent.format_summary(summary)}\n\n{agent.format_reminders(reminders)}"

        if action == "finance_bill":
            agent = FinanceAdminAgent(
                store=self.finance_store, gemini_client=self.gemini_client
            )
            matched_id = self._match_unpaid_invoice_id(task)
            if matched_id is not None:
                inv, draft = agent.draft_payment_reminder(
                    invoice_id=matched_id, info_rekening=task.bank.strip()
                )
                return agent.format_reminder_draft(inv, draft)

            client_name = task.klien.strip() or "Klien"
            project_name = task.proyek.strip() or f"Proyek / Endorse {client_name}"
            draft = agent.draft_ad_hoc_billing(
                klien=client_name,
                proyek=project_name,
                nominal_sisa=task.nominal_teks.strip(),
                info_rekening=task.bank.strip(),
                catatan=task.catatan.strip(),
            )
            return (
                f"# Format Tagihan Pelunasan — {client_name}\n"
                f"Proyek: {project_name}\n"
                f"Catatan nada: {draft.catatan_nada.strip()}\n"
                f"*(Catatan: Tagihan '{client_name}' belum tercatat di database kas — "
                "Anda bisa mencatatnya di Agent Keuangan agar status pelunasan ikut terlacak.)*\n\n"
                f"## Pesan WhatsApp Siap Kirim\n{draft.pesan_pengingat.strip()}"
            )

        if action == "finance_split":
            agent = FinanceAdminAgent(store=self.finance_store)
            shares = parse_shares_spec(task.shares or "Saya:60,Partner:40")
            result = agent.calculate_profit_split(
                total_pendapatan=task.nominal_angka,
                splits=shares,
                biaya_operasional=task.biaya_angka,
            )
            return agent.format_profit_split(result)

        if action == "cs_reply":
            agent = CSQCAgent(
                gemini_client=self.gemini_client, rate_card_file=self.rate_card_file
            )
            report = agent.draft_cs_reply(
                pesan_klien=task.pesan_klien.strip() or task.ringkasan_tugas,
                layanan=task.layanan or "auto",
                nama_klien=task.klien.strip(),
            )
            return agent.format_cs_reply(report)

        if action == "cs_qc":
            agent = CSQCAgent(gemini_client=self.gemini_client)
            report = agent.check_endorse_script(
                brief_klien=task.brief_klien.strip(),
                skrip=task.skrip.strip(),
                nama_brand=task.klien.strip(),
            )
            return agent.format_qc_report(report)

        raise ValueError(f"Aksi delegasi '{action}' tidak dikenali.")

    def run(self, perintah_bos: str) -> OrchestratorReport:
        """Menerima 1 perintah natural dari bos, merencanakan, dan mengeksekusi delegasi."""
        cleaned = perintah_bos.strip()
        if not cleaned:
            raise ValueError(
                "Perintah untuk Manajer tidak boleh kosong. Contoh: "
                "'Floatee baru ACC, siapin buat tayang dan tagih pelunasan'."
            )

        self._emit("manager", "working", "Menganalisis perintah bos & menyusun delegasi...")
        unpaid = self.finance_store.list_invoices(unpaid_only=True)
        leads = self.lead_store.list_leads()

        plan = self.gemini_client.generate_structured(
            prompt=build_orchestrator_user_prompt(cleaned, unpaid, leads),
            response_schema=OrchestratorPlan,
            system_instruction=build_orchestrator_system_instruction(),
            temperature=0.4,
        )

        tasks = plan.tugas[:4]
        if tasks:
            team_list = ", ".join(dict.fromkeys(t.target_agent for t in tasks))
            self._emit("manager", "working", f"Mendelegasikan ke: {team_list}...")

        results: list[DelegatedResult] = []
        context_bag: dict[str, str] = {}
        for task in tasks:
            results.append(self._execute_task(task, context_bag))

        return OrchestratorReport(
            waktu_dibuat=timestamp_wib(),
            perintah_bos=cleaned,
            ringkasan_rencana=plan.ringkasan_rencana.strip(),
            hasil_delegasi=results,
        )

    def format_report(self, report: OrchestratorReport) -> str:
        """Memformat laporan gabungan Manajer dari seluruh hasil delegasi."""
        lines = [
            "# Laporan Eksekutif Manajer (Orchestrator)",
            f"Waktu: {report.waktu_dibuat}",
            f"Perintah Bos: {report.perintah_bos}",
            f"Rencana Delegasi: {report.ringkasan_rencana}",
            "",
        ]
        if not report.hasil_delegasi:
            lines.append("Tidak ada tugas yang didelegasikan untuk perintah ini.")
            return "\n".join(lines)

        for idx, res in enumerate(report.hasil_delegasi, start=1):
            badge = "BERHASIL" if res.berhasil else "KENDALA"
            lines.extend(
                [
                    f"---",
                    f"## Delegasi {idx}: [{res.target_agent.upper()}] — {res.ringkasan_tugas} ({badge})",
                    "",
                    res.output_markdown,
                    "",
                ]
            )
        return "\n".join(lines).rstrip()
