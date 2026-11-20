"""Orkestrasi Agent 5: Asisten CS (balasan calon klien) & QC Brief Endorse."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from agents.cs_qc.knowledge import load_rate_card_and_faq
from agents.cs_qc.prompts import (
    build_cs_system_instruction,
    build_cs_user_prompt,
    build_qc_system_instruction,
    build_qc_user_prompt,
)
from core.formatter import timestamp_wib
from core.gemini_client import GeminiClient

ALLOWED_CS_SERVICES: tuple[str, ...] = ("auto", "endorse", "web_umkm")
_VALID_QC_ITEM_STATUSES = {"TERPENUHI", "SEBAGIAN", "TIDAK_TERPENUHI"}


class CSReplyOutput(BaseModel):
    """Skema JSON terstruktur dari Gemini untuk draf balasan calon klien."""

    kategori_klien: str = Field(
        description="Kategori pertanyaan: endorse, web_umkm, atau umum"
    )
    ringkasan_kebutuhan: str = Field(
        description="Ringkasan singkat 1-2 kalimat tentang apa yang dicari calon klien"
    )
    draf_balasan: str = Field(
        description="Draf balasan ramah & profesional siap salin ke WhatsApp/DM/Email"
    )
    perlu_konfirmasi_owner: list[str] = Field(
        default_factory=list,
        description="Daftar poin yang perlu dicek/diisi dulu oleh owner sebelum mengirim balasan",
    )
    langkah_lanjut: str = Field(
        description="Saran langkah follow-up berikutnya agar mengarah ke deal"
    )


class CSReplyReport(BaseModel):
    """Laporan akhir mode Asisten CS."""

    waktu_dibuat: str
    kategori_klien: str
    ringkasan_kebutuhan: str
    draf_balasan: str
    perlu_konfirmasi_owner: list[str] = Field(default_factory=list)
    langkah_lanjut: str


class QCCheckItem(BaseModel):
    """Status kepatuhan satu poin dari brief klien."""

    poin_brief: str = Field(description="Syarat atau poin spesifik dari brief klien")
    status: str = Field(
        description="Harus salah satu dari: TERPENUHI, SEBAGIAN, atau TIDAK_TERPENUHI"
    )
    bukti_di_skrip: str = Field(
        description="Kutipan singkat dari skrip yang membuktikan, atau keterangan jika tidak ada/melanggar"
    )
    saran_perbaikan: str = Field(
        description="Saran dialog/visual ala Denn & Miki jika belum terpenuhi, atau '-' jika sudah lolos"
    )


class BriefQCOutput(BaseModel):
    """Skema JSON terstruktur dari Gemini untuk hasil pemeriksaan QC Brief."""

    status_keseluruhan: str = Field(
        description="LOLOS jika semua poin terpenuhi dan tanpa pelanggaran, selain itu PERLU_REVISI"
    )
    daftar_cek: list[QCCheckItem] = Field(
        default_factory=list,
        description="Daftar pemeriksaan poin demi poin dari seluruh syarat brief klien",
    )
    peringatan_larangan: list[str] = Field(
        default_factory=list,
        description="Daftar pelanggaran larangan/don'ts atau risiko brand-safety jika ada",
    )
    rekomendasi_revisi_cepat: str = Field(
        description="Ringkasan perbaikan cepat siap diterapkan ke skrip tanpa merusak gaya komedi Denn & Miki"
    )


class BriefQCReport(BaseModel):
    """Laporan akhir QC Brief dengan kalkulasi status & skor deterministik."""

    waktu_dibuat: str
    nama_brand: str
    status_keseluruhan: str
    poin_terpenuhi: int
    total_poin: int
    skor_persen: int
    daftar_cek: list[QCCheckItem] = Field(default_factory=list)
    peringatan_larangan: list[str] = Field(default_factory=list)
    rekomendasi_revisi_cepat: str


def _normalize_qc_status(raw: str) -> str:
    cleaned = raw.strip().upper().replace(" ", "_")
    if cleaned in _VALID_QC_ITEM_STATUSES:
        return cleaned
    if "SEBAGIAN" in cleaned or "PARTIAL" in cleaned:
        return "SEBAGIAN"
    if "TIDAK" in cleaned or "BELUM" in cleaned or "GAGAL" in cleaned or "MISS" in cleaned:
        return "TIDAK_TERPENUHI"
    return "TERPENUHI"


class CSQCAgent:
    """Agent 5 untuk menyusun balasan calon klien (CS) dan melakukan QC skrip endorse."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        rate_card_file: Path | None = None,
    ) -> None:
        self.gemini_client = gemini_client
        self.rate_card_file = rate_card_file

    def draft_cs_reply(
        self,
        pesan_klien: str,
        layanan: str = "auto",
        nama_klien: str = "",
        nama_pengirim: str = "",
        rate_card_override: str | None = None,
    ) -> CSReplyReport:
        """Menyusun draf balasan calon klien berdasarkan Rate Card & FAQ."""
        cleaned_msg = pesan_klien.strip()
        if not cleaned_msg:
            raise ValueError("Pesan calon klien tidak boleh kosong.")

        normalized_service = layanan.strip().lower() or "auto"
        if normalized_service not in ALLOWED_CS_SERVICES:
            valid = ", ".join(ALLOWED_CS_SERVICES)
            raise ValueError(f"Layanan '{layanan}' tidak valid. Pilihan: {valid}.")

        knowledge = (
            rate_card_override.strip()
            if rate_card_override is not None and rate_card_override.strip()
            else load_rate_card_and_faq(self.rate_card_file)
        )
        result = self.gemini_client.generate_structured(
            prompt=build_cs_user_prompt(
                pesan_klien=cleaned_msg,
                layanan=normalized_service,
                nama_klien=nama_klien,
                nama_pengirim=nama_pengirim,
            ),
            response_schema=CSReplyOutput,
            system_instruction=build_cs_system_instruction(knowledge),
            temperature=0.5,
        )

        return CSReplyReport(
            waktu_dibuat=timestamp_wib(),
            kategori_klien=result.kategori_klien.strip() or normalized_service,
            ringkasan_kebutuhan=result.ringkasan_kebutuhan.strip(),
            draf_balasan=result.draf_balasan.strip(),
            perlu_konfirmasi_owner=[
                item.strip() for item in result.perlu_konfirmasi_owner if item.strip()
            ],
            langkah_lanjut=result.langkah_lanjut.strip(),
        )

    def check_endorse_script(
        self,
        brief_klien: str,
        skrip: str,
        nama_brand: str = "",
    ) -> BriefQCReport:
        """Memeriksa apakah skrip endorse sudah mencakup seluruh poin brief klien."""
        cleaned_brief = brief_klien.strip()
        cleaned_script = skrip.strip()
        if not cleaned_brief:
            raise ValueError("Isi brief klien tidak boleh kosong.")
        if not cleaned_script:
            raise ValueError("Isi skrip endorse tidak boleh kosong.")

        raw = self.gemini_client.generate_structured(
            prompt=build_qc_user_prompt(
                brief_klien=cleaned_brief,
                skrip=cleaned_script,
                nama_brand=nama_brand,
            ),
            response_schema=BriefQCOutput,
            system_instruction=build_qc_system_instruction(),
            temperature=0.3,
        )

        normalized_items = [
            QCCheckItem(
                poin_brief=item.poin_brief.strip(),
                status=_normalize_qc_status(item.status),
                bukti_di_skrip=item.bukti_di_skrip.strip(),
                saran_perbaikan=item.saran_perbaikan.strip() or "-",
            )
            for item in raw.daftar_cek
            if item.poin_brief.strip()
        ]
        warnings = [w.strip() for w in raw.peringatan_larangan if w.strip()]

        total_poin = len(normalized_items)
        poin_terpenuhi = sum(
            1 for item in normalized_items if item.status == "TERPENUHI"
        )
        skor_persen = (
            int(round((poin_terpenuhi / total_poin) * 100)) if total_poin > 0 else 0
        )

        # Safeguard deterministik: hanya LOLOS jika semua poin TERPENUHI dan tanpa peringatan larangan.
        all_passed = total_poin > 0 and poin_terpenuhi == total_poin and not warnings
        final_status = "LOLOS" if all_passed else "PERLU_REVISI"

        return BriefQCReport(
            waktu_dibuat=timestamp_wib(),
            nama_brand=nama_brand.strip() or "-",
            status_keseluruhan=final_status,
            poin_terpenuhi=poin_terpenuhi,
            total_poin=total_poin,
            skor_persen=skor_persen,
            daftar_cek=normalized_items,
            peringatan_larangan=warnings,
            rekomendasi_revisi_cepat=raw.rekomendasi_revisi_cepat.strip(),
        )

    def format_cs_reply(self, report: CSReplyReport) -> str:
        """Memformat hasil draf balasan CS ke Markdown siap salin."""
        lines = [
            "# Draf Balasan Calon Klien (Asisten CS)",
            f"Waktu: {report.waktu_dibuat}",
            f"Kategori: `{report.kategori_klien}`",
            f"Kebutuhan klien: {report.ringkasan_kebutuhan}",
            "",
            "## Draf Balasan Siap Kirim",
            report.draf_balasan,
            "",
        ]
        if report.perlu_konfirmasi_owner:
            lines.append("## Perlu Dicek / Diisi Owner Sebelum Kirim")
            for note in report.perlu_konfirmasi_owner:
                lines.append(f"- {note}")
            lines.append("")
        lines.extend(
            [
                "## Saran Langkah Lanjut",
                report.langkah_lanjut,
            ]
        )
        return "\n".join(lines)

    def format_qc_report(self, report: BriefQCReport) -> str:
        """Memformat hasil audit QC Brief Endorse ke Markdown yang mudah dipindai."""
        lines = [
            f"# Hasil QC Brief Endorse — {report.nama_brand}",
            f"Waktu: {report.waktu_dibuat}",
            f"Status Keseluruhan: **{report.status_keseluruhan}** "
            f"({report.poin_terpenuhi}/{report.total_poin} poin terpenuhi — {report.skor_persen}%)",
            "",
            "## Checklist Poin Brief",
        ]

        badges = {
            "TERPENUHI": "[OK]",
            "SEBAGIAN": "[SEBAGIAN]",
            "TIDAK_TERPENUHI": "[KURANG]",
        }
        for idx, item in enumerate(report.daftar_cek, start=1):
            badge = badges.get(item.status, f"[{item.status}]")
            lines.append(f"{idx}. {badge} **{item.poin_brief}**")
            lines.append(f"   - Bukti di skrip: {item.bukti_di_skrip}")
            if item.status != "TERPENUHI" and item.saran_perbaikan != "-":
                lines.append(f"   - Saran perbaikan: {item.saran_perbaikan}")

        if report.peringatan_larangan:
            lines.extend(["", "## Peringatan Larangan / Brand Safety"])
            for warn in report.peringatan_larangan:
                lines.append(f"- [PERINGATAN] {warn}")

        lines.extend(
            [
                "",
                "## Rekomendasi Revisi Cepat",
                report.rekomendasi_revisi_cepat,
            ]
        )
        return "\n".join(lines)
