"""Orkestrasi Agent 3: Lead Hunter UMKM (kelola prospek & buat draf outreach personal)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.lead_hunter.finder import DiscoveredLead
from agents.lead_hunter.prompts import build_system_instruction, build_user_prompt
from agents.lead_hunter.storage import Lead, LeadStore
from core.formatter import timestamp_wib
from core.gemini_client import GeminiClient


class OutreachOutput(BaseModel):
    """Skema JSON terstruktur dari Gemini untuk draf penawaran personal UMKM."""

    sudut_pendekatan: str = Field(
        description="Analisis singkat 1-2 kalimat mengenai nilai tambah paling relevan bagi UMKM ini"
    )
    pesan_utama: str = Field(
        description="Draf pesan penawaran pertama siap kirim sesuai saluran (WhatsApp/IG DM/Email)"
    )
    pesan_followup: str = Field(
        description="Draf pesan follow-up singkat dan sopan jika belum dibalas setelah 3 hari"
    )
    tips_kirim: str = Field(
        description="1-2 tips praktis waktu kirim atau bahan pendukung sebelum menghubungi prospek"
    )


class OutreachReport(BaseModel):
    """Laporan lengkap hasil draf penawaran Agent 3."""

    waktu_dibuat: str
    lead: Lead
    sudut_pendekatan: str
    pesan_utama: str
    pesan_followup: str
    tips_kirim: str


class LeadHunterAgent:
    """Agent 3 untuk mengelola prospek UMKM dan menyusun pesan penawaran personal."""

    def __init__(
        self,
        store: LeadStore,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.store = store
        self.gemini_client = gemini_client

    def draft_outreach(
        self,
        lead_id: int,
        penawaran_khusus: str = "",
        nama_pengirim: str = "",
    ) -> OutreachReport:
        """Membuat draf pesan penawaran personal berbasis AI untuk 1 prospek berdasarkan ID."""
        lead = self.store.get_lead(lead_id)
        if self.gemini_client is None:
            raise ValueError(
                "GeminiClient diperlukan untuk membuat draf pesan penawaran."
            )

        system_instruction = build_system_instruction()
        user_prompt = build_user_prompt(
            lead=lead,
            penawaran_khusus=penawaran_khusus,
            nama_pengirim=nama_pengirim,
        )
        result = self.gemini_client.generate_structured(
            prompt=user_prompt,
            response_schema=OutreachOutput,
            system_instruction=system_instruction,
            temperature=0.7,
        )

        return OutreachReport(
            waktu_dibuat=timestamp_wib(),
            lead=lead,
            sudut_pendekatan=result.sudut_pendekatan.strip(),
            pesan_utama=result.pesan_utama.strip(),
            pesan_followup=result.pesan_followup.strip(),
            tips_kirim=result.tips_kirim.strip(),
        )

    def format_leads_list(self, leads: list[Lead]) -> str:
        """Memformat daftar prospek UMKM menjadi ringkasan Markdown rapi."""
        lines = [
            "# Daftar Prospek UMKM",
            f"Total ditampilkan: {len(leads)}",
            "",
        ]
        if not leads:
            lines.append("Belum ada prospek yang sesuai filter. Tambahkan lewat perintah `leads add`.")
            return "\n".join(lines)

        for item in leads:
            web_label = "Sudah ada web" if item.punya_website else "Belum punya web"
            kota_str = f" — {item.kota}" if item.kota else ""
            kontak_str = f"{item.saluran}: {item.kontak}" if item.kontak else item.saluran
            lines.append(
                f"- **#{item.id} {item.nama_usaha}** ({item.kategori}{kota_str}) "
                f"| Status: `{item.status}` | {web_label} | Kontak: {kontak_str}"
            )
            if item.catatan:
                lines.append(f"  Catatan: {item.catatan}")
        return "\n".join(lines)

    def save_discovered_leads(
        self, discovered: list[DiscoveredLead]
    ) -> tuple[list[Lead], int]:
        """Menyimpan daftar kandidat hasil pencarian otomatis ke LeadStore (lewati duplikat)."""
        added: list[Lead] = []
        skipped = 0
        for candidate in discovered:
            try:
                saved = self.store.add_lead(
                    nama_usaha=candidate.nama_usaha,
                    kategori=candidate.kategori,
                    kota=candidate.kota,
                    kontak=candidate.kontak,
                    saluran=candidate.saluran,
                    punya_website=candidate.punya_website,
                    catatan=candidate.catatan,
                )
                added.append(saved)
            except ValueError:
                skipped += 1
        return added, skipped

    def format_discovered_leads(
        self,
        keyword: str,
        city: str,
        leads: list[DiscoveredLead],
    ) -> str:
        """Memformat hasil pencarian prospek UMKM otomatis dari OpenStreetMap."""
        lines = [
            f"# Hasil Pencarian Prospek UMKM Otomatis — '{keyword}' ({city})",
            f"Waktu: {timestamp_wib()}",
            f"Total kandidat ditemukan: {len(leads)}",
            "",
        ]
        if not leads:
            lines.append(
                "Tidak ditemukan kandidat yang sesuai. Coba perbesar --radius-km atau gunakan kata kunci lebih umum (mis. 'kopi', 'bengkel', 'salon', 'laundry', 'bakso')."
            )
            return "\n".join(lines)

        for idx, item in enumerate(leads, start=1):
            web_label = (
                f"Ada web ({item.website_url})"
                if item.punya_website
                else "Belum tercantum website"
            )
            kontak_label = (
                f"{item.saluran}: {item.kontak}"
                if item.kontak
                else "Kontak belum ada di OSM"
            )
            lines.append(
                f"{idx}. **{item.nama_usaha}** ({item.kategori} — {item.kota}) | {web_label} | {kontak_label}"
            )
            if item.alamat:
                lines.append(f"   Alamat: {item.alamat}")
            if item.sumber_url:
                lines.append(f"   Peta: {item.sumber_url}")
        return "\n".join(lines)

    def format_outreach_report(self, report: OutreachReport) -> str:
        """Memformat draf penawaran menjadi Markdown siap salin."""
        lead = report.lead
        kota_str = f" ({lead.kota})" if lead.kota else ""
        web_label = "Sudah ada website" if lead.punya_website else "Belum punya website"
        lines = [
            f"# Draf Penawaran UMKM — {lead.nama_usaha}{kota_str}",
            f"Waktu: {report.waktu_dibuat}",
            f"Prospek: #{lead.id} | Kategori: {lead.kategori} | {web_label} | Saluran: {lead.saluran}",
            f"Kontak: {lead.kontak or '-'}",
            "",
            "## Sudut Pendekatan",
            report.sudut_pendekatan,
            "",
            f"## Pesan Penawaran Utama ({lead.saluran.upper()})",
            report.pesan_utama,
            "",
            "## Pesan Follow-Up (H+3)",
            report.pesan_followup,
            "",
            "## Tips Pengiriman",
            report.tips_kirim,
        ]
        return "\n".join(lines)
