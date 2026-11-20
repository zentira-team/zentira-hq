"""Orkestrasi Agent 4: Admin Keuangan & Pengingat (kas, DP/pelunasan, pengingat, bagi hasil)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from agents.finance_admin.prompts import (
    build_reminder_system_instruction,
    build_reminder_user_prompt,
)
from agents.finance_admin.storage import (
    ALLOWED_STREAMS,
    ClientInvoice,
    FinanceStore,
    Transaction,
)
from core.formatter import WIB, timestamp_wib
from core.gemini_client import GeminiClient


def format_rupiah(amount: int) -> str:
    """Memformat angka bulat menjadi string Rupiah Indonesia (mis. Rp1.500.000)."""
    sign = "-" if amount < 0 else ""
    formatted = f"{abs(int(amount)):,}".replace(",", ".")
    return f"{sign}Rp{formatted}"


def parse_shares_spec(spec: str) -> dict[str, float]:
    """Mem-parsing format bagi hasil seperti 'Saya:60,Partner:40' menjadi dict persentase."""
    cleaned = spec.strip()
    if not cleaned:
        raise ValueError(
            "Format bagi hasil kosong. Contoh yang benar: 'Saya:60,Partner:40'."
        )

    shares: dict[str, float] = {}
    for part in cleaned.split(","):
        piece = part.strip()
        if not piece:
            continue
        if ":" not in piece:
            raise ValueError(
                f"Bagian '{piece}' tidak valid. Gunakan format Nama:Persen (contoh: 'Saya:60,Partner:40')."
            )
        name, raw_pct = piece.split(":", 1)
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Nama penerima bagi hasil tidak boleh kosong.")
        try:
            pct = float(raw_pct.strip().rstrip("%"))
        except ValueError as exc:
            raise ValueError(
                f"Persentase '{raw_pct.strip()}' untuk '{cleaned_name}' harus berupa angka."
            ) from exc
        if cleaned_name in shares:
            raise ValueError(f"Nama penerima '{cleaned_name}' muncul lebih dari sekali.")
        shares[cleaned_name] = pct

    if not shares:
        raise ValueError("Minimal harus ada 1 penerima bagi hasil.")
    return shares


class CashflowSummary(BaseModel):
    """Ringkasan arus kas pemasukan, pengeluaran, saldo, dan piutang klien."""

    periode: str
    total_masuk: int
    total_keluar: int
    saldo_bersih: int
    total_piutang_klien: int
    jumlah_transaksi: int
    rincian_per_sumber: dict[str, dict[str, int]] = Field(default_factory=dict)


class ReminderItem(BaseModel):
    """Satu item pengingat DP/pelunasan klien berdasarkan jatuh tempo."""

    invoice: ClientInvoice
    hari_tersisa: int | None
    kategori_urgensi: str


class SplitShare(BaseModel):
    """Bagian satu pihak dalam perhitungan bagi hasil."""

    penerima: str
    persen: float
    nominal: int


class ProfitSplitResult(BaseModel):
    """Hasil perhitungan bagi hasil bersih yang deterministik."""

    total_pendapatan: int
    biaya_operasional: int
    laba_bersih: int
    pembagian: list[SplitShare]
    sisa_pembulatan: int


class ReminderDraftOutput(BaseModel):
    """Draf pesan pengingat pembayaran dari Gemini."""

    pesan_pengingat: str = Field(
        description="Draf pesan WhatsApp sopan dan ramah untuk mengingatkan pembayaran klien"
    )
    catatan_nada: str = Field(
        description="Catatan singkat 1 kalimat soal pendekatan nada pesan"
    )


_URGENCY_ORDER = {
    "terlambat": 0,
    "hari_ini": 1,
    "segera": 2,
    "menunggu": 3,
    "tanpa_tenggat": 4,
}


class FinanceAdminAgent:
    """Agent 4 untuk pencatatan kas, pelacakan DP/pelunasan, pengingat, dan bagi hasil."""

    def __init__(
        self,
        store: FinanceStore,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.store = store
        self.gemini_client = gemini_client

    def get_summary(
        self,
        month: str | None = None,
        sumber: str | None = None,
    ) -> CashflowSummary:
        """Menghitung ringkasan kas dan total piutang klien secara deterministik."""
        transactions = self.store.list_transactions(sumber=sumber, month=month)
        unpaid_invoices = self.store.list_invoices(unpaid_only=True)
        if sumber:
            unpaid_invoices = [
                inv for inv in unpaid_invoices if inv.sumber == sumber.strip().lower()
            ]

        total_masuk = sum(tx.nominal for tx in transactions if tx.jenis == "masuk")
        total_keluar = sum(tx.nominal for tx in transactions if tx.jenis == "keluar")
        total_piutang = sum(inv.sisa_tagihan for inv in unpaid_invoices)

        rincian: dict[str, dict[str, int]] = {}
        for stream in ALLOWED_STREAMS:
            stream_txs = [tx for tx in transactions if tx.sumber == stream]
            if not stream_txs and sumber and sumber.strip().lower() != stream:
                continue
            s_in = sum(tx.nominal for tx in stream_txs if tx.jenis == "masuk")
            s_out = sum(tx.nominal for tx in stream_txs if tx.jenis == "keluar")
            if s_in or s_out:
                rincian[stream] = {
                    "masuk": s_in,
                    "keluar": s_out,
                    "bersih": s_in - s_out,
                }

        periode = month.strip() if (month and month.strip()) else "Semua waktu"
        if sumber:
            periode = f"{periode} (lini: {sumber.strip().lower()})"

        return CashflowSummary(
            periode=periode,
            total_masuk=total_masuk,
            total_keluar=total_keluar,
            saldo_bersih=total_masuk - total_keluar,
            total_piutang_klien=total_piutang,
            jumlah_transaksi=len(transactions),
            rincian_per_sumber=rincian,
        )

    def get_reminders(
        self,
        within_days: int = 7,
        reference_date: date | None = None,
    ) -> list[ReminderItem]:
        """Menyaring dan mengurutkan tagihan belum lunas berdasarkan urgensi jatuh tempo."""
        today = reference_date or datetime.now(WIB).date()
        unpaid = self.store.list_invoices(unpaid_only=True)
        items: list[ReminderItem] = []

        for inv in unpaid:
            if not inv.jatuh_tempo:
                items.append(
                    ReminderItem(
                        invoice=inv,
                        hari_tersisa=None,
                        kategori_urgensi="tanpa_tenggat",
                    )
                )
                continue

            due_date = date.fromisoformat(inv.jatuh_tempo)
            delta = (due_date - today).days
            if delta < 0:
                urgency = "terlambat"
            elif delta == 0:
                urgency = "hari_ini"
            elif delta <= within_days:
                urgency = "segera"
            else:
                urgency = "menunggu"

            items.append(
                ReminderItem(
                    invoice=inv,
                    hari_tersisa=delta,
                    kategori_urgensi=urgency,
                )
            )

        items.sort(
            key=lambda item: (
                _URGENCY_ORDER.get(item.kategori_urgensi, 99),
                item.hari_tersisa if item.hari_tersisa is not None else 999999,
                item.invoice.id,
            )
        )
        return items

    def calculate_profit_split(
        self,
        total_pendapatan: int,
        splits: dict[str, float],
        biaya_operasional: int = 0,
    ) -> ProfitSplitResult:
        """Menghitung pembagian hasil sederhana secara eksak dalam Rupiah bulat."""
        if total_pendapatan <= 0:
            raise ValueError("Total pendapatan harus lebih dari 0.")
        if biaya_operasional < 0:
            raise ValueError("Biaya operasional tidak boleh negatif.")
        if biaya_operasional > total_pendapatan:
            raise ValueError("Biaya operasional tidak boleh melebihi total pendapatan.")
        if not splits:
            raise ValueError("Daftar pembagian persentase tidak boleh kosong.")

        for name, pct in splits.items():
            if pct <= 0:
                raise ValueError(
                    f"Persentase bagi hasil untuk '{name}' harus lebih dari 0%."
                )

        total_pct = sum(splits.values())
        if abs(total_pct - 100.0) > 1e-6:
            raise ValueError(
                f"Total persentase bagi hasil harus tepat 100% (saat ini: {total_pct:g}%)."
            )

        laba_bersih = int(total_pendapatan) - int(biaya_operasional)
        pembagian: list[SplitShare] = []
        allocated = 0
        for name, pct in splits.items():
            amount = int(round(laba_bersih * (pct / 100.0)))
            allocated += amount
            pembagian.append(SplitShare(penerima=name, persen=pct, nominal=amount))

        return ProfitSplitResult(
            total_pendapatan=int(total_pendapatan),
            biaya_operasional=int(biaya_operasional),
            laba_bersih=laba_bersih,
            pembagian=pembagian,
            sisa_pembulatan=laba_bersih - allocated,
        )

    def draft_payment_reminder(
        self,
        invoice_id: int,
        nama_pengirim: str = "",
        info_rekening: str = "",
        reference_date: date | None = None,
    ) -> tuple[ClientInvoice, ReminderDraftOutput]:
        """Membuat draf pesan pengingat pembayaran sopan pakai Gemini untuk 1 tagihan."""
        invoice = self.store.get_invoice(invoice_id)
        if invoice.status == "lunas" or invoice.sisa_tagihan <= 0:
            raise ValueError(
                f"Tagihan #{invoice.id} ({invoice.klien}) sudah lunas, tidak perlu pengingat pembayaran."
            )
        if self.gemini_client is None:
            raise ValueError(
                "GeminiClient diperlukan untuk menyusun draf pesan pengingat."
            )

        today = reference_date or datetime.now(WIB).date()
        if invoice.jatuh_tempo:
            delta = (date.fromisoformat(invoice.jatuh_tempo) - today).days
            if delta < 0:
                status_waktu = f"lewat {abs(delta)} hari dari jatuh tempo"
            elif delta == 0:
                status_waktu = "jatuh tempo hari ini"
            else:
                status_waktu = f"H-{delta} sebelum jatuh tempo"
        else:
            status_waktu = "tanpa tanggal jatuh tempo khusus"

        prompt = build_reminder_user_prompt(
            invoice=invoice,
            total_str=format_rupiah(invoice.total_harga),
            dibayar_str=format_rupiah(invoice.dibayar),
            sisa_str=format_rupiah(invoice.sisa_tagihan),
            status_waktu=status_waktu,
            nama_pengirim=nama_pengirim,
            info_rekening=info_rekening,
        )
        draft = self.gemini_client.generate_structured(
            prompt=prompt,
            response_schema=ReminderDraftOutput,
            system_instruction=build_reminder_system_instruction(),
            temperature=0.6,
        )
        return invoice, draft

    def draft_ad_hoc_billing(
        self,
        klien: str,
        proyek: str,
        nominal_sisa: str = "",
        nama_pengirim: str = "",
        info_rekening: str = "",
        catatan: str = "",
    ) -> ReminderDraftOutput:
        """Menyusun format pesan tagihan pelunasan WA meski klien belum tercatat di database."""
        if self.gemini_client is None:
            raise ValueError(
                "GeminiClient diperlukan untuk menyusun format pesan tagihan."
            )
        lines = [
            "Tolong buatkan draf pesan WhatsApp format tagihan pelunasan yang sopan dan profesional untuk data berikut:\n",
            f"- Nama Klien / Brand: {klien.strip() or '[Nama Klien]'}",
            f"- Proyek / Konten: {proyek.strip() or 'Konten Endorse / Website'}",
            f"- Nominal Pelunasan: {nominal_sisa.strip() or '[Isi Nominal Pelunasan]'}",
            f"- Nama Pengirim: {nama_pengirim.strip() or '[Nama Anda]'}",
            f"- Rekening Tujuan: {info_rekening.strip() or '[Isi No. Rekening / E-Wallet Anda]'}",
        ]
        if catatan.strip():
            lines.append(f"- Catatan Tambahan: {catatan.strip()}")
        return self.gemini_client.generate_structured(
            prompt="\n".join(lines),
            response_schema=ReminderDraftOutput,
            system_instruction=build_reminder_system_instruction(),
            temperature=0.6,
        )

    def format_summary(self, summary: CashflowSummary) -> str:
        """Memformat ringkasan kas menjadi laporan Markdown."""
        lines = [
            f"# Ringkasan Keuangan — {summary.periode}",
            f"Waktu: {timestamp_wib()}",
            "",
            f"- **Total Pemasukan:** {format_rupiah(summary.total_masuk)}",
            f"- **Total Pengeluaran:** {format_rupiah(summary.total_keluar)}",
            f"- **Saldo Bersih:** {format_rupiah(summary.saldo_bersih)}",
            f"- **Piutang Klien (Belum Lunas):** {format_rupiah(summary.total_piutang_klien)}",
            f"- **Jumlah Transaksi:** {summary.jumlah_transaksi}",
        ]
        if summary.rincian_per_sumber:
            lines.extend(["", "## Rincian per Lini Usaha"])
            for stream, data in summary.rincian_per_sumber.items():
                lines.append(
                    f"- **{stream}**: Masuk {format_rupiah(data['masuk'])} | "
                    f"Keluar {format_rupiah(data['keluar'])} | Bersih {format_rupiah(data['bersih'])}"
                )
        return "\n".join(lines)

    def format_transactions(self, transactions: list[Transaction]) -> str:
        """Memformat daftar transaksi kas."""
        lines = [
            "# Riwayat Transaksi Keuangan",
            f"Total ditampilkan: {len(transactions)}",
            "",
        ]
        if not transactions:
            lines.append("Belum ada transaksi yang tercatat.")
            return "\n".join(lines)

        for tx in transactions:
            sign = "+" if tx.jenis == "masuk" else "-"
            note = f" — {tx.keterangan}" if tx.keterangan else ""
            lines.append(
                f"- **#{tx.id}** [{tx.tanggal}] `{tx.jenis.upper()}` "
                f"{sign}{format_rupiah(tx.nominal)} | {tx.sumber}/{tx.kategori}{note}"
            )
        return "\n".join(lines)

    def format_invoices(self, invoices: list[ClientInvoice]) -> str:
        """Memformat daftar tagihan DP/pelunasan klien."""
        lines = [
            "# Daftar Tagihan & Status DP/Pelunasan Klien",
            f"Total ditampilkan: {len(invoices)}",
            "",
        ]
        if not invoices:
            lines.append("Belum ada data tagihan klien.")
            return "\n".join(lines)

        for inv in invoices:
            due = f" | Jatuh tempo: {inv.jatuh_tempo}" if inv.jatuh_tempo else ""
            lines.append(
                f"- **#{inv.id} {inv.klien}** — {inv.proyek} ({inv.sumber}) | Status: `{inv.status}`"
            )
            lines.append(
                f"  Total: {format_rupiah(inv.total_harga)} | Dibayar: {format_rupiah(inv.dibayar)} "
                f"| Sisa: {format_rupiah(inv.sisa_tagihan)}{due}"
            )
            if inv.catatan:
                lines.append(f"  Catatan: {inv.catatan}")
        return "\n".join(lines)

    def format_reminders(self, reminders: list[ReminderItem]) -> str:
        """Memformat daftar pengingat jatuh tempo DP/pelunasan klien."""
        lines = [
            "# Pengingat Tagihan & Pelunasan Klien",
            f"Waktu: {timestamp_wib()}",
            f"Tagihan belum lunas: {len(reminders)}",
            "",
        ]
        if not reminders:
            lines.append("Semua tagihan klien sudah lunas! Tidak ada pengingat aktif.")
            return "\n".join(lines)

        labels = {
            "terlambat": "[TERLAMBAT]",
            "hari_ini": "[JATUH TEMPO HARI INI]",
            "segera": "[SEGERA JATUH TEMPO]",
            "menunggu": "[TERJADWAL]",
            "tanpa_tenggat": "[TANPA TENGGAT]",
        }
        for item in reminders:
            inv = item.invoice
            tag = labels.get(item.kategori_urgensi, "[INFO]")
            if item.hari_tersisa is None:
                due_info = "Belum ada tanggal jatuh tempo"
            elif item.hari_tersisa < 0:
                due_info = f"Lewat {abs(item.hari_tersisa)} hari ({inv.jatuh_tempo})"
            elif item.hari_tersisa == 0:
                due_info = f"Hari ini ({inv.jatuh_tempo})"
            else:
                due_info = f"H-{item.hari_tersisa} ({inv.jatuh_tempo})"

            lines.append(
                f"- {tag} **#{inv.id} {inv.klien}** ({inv.proyek}) | "
                f"Sisa: **{format_rupiah(inv.sisa_tagihan)}** | {due_info}"
            )
        return "\n".join(lines)

    def format_profit_split(self, result: ProfitSplitResult) -> str:
        """Memformat hasil kalkulator bagi hasil."""
        lines = [
            "# Perhitungan Bagi Hasil Sederhana",
            f"- **Total Pendapatan:** {format_rupiah(result.total_pendapatan)}",
            f"- **Biaya Operasional:** {format_rupiah(result.biaya_operasional)}",
            f"- **Laba Bersih Dibagi:** {format_rupiah(result.laba_bersih)}",
            "",
            "## Rincian Pembagian",
        ]
        for share in result.pembagian:
            lines.append(
                f"- **{share.penerima}** ({share.persen:g}%): **{format_rupiah(share.nominal)}**"
            )
        if result.sisa_pembulatan != 0:
            lines.append(
                f"\nCatatan: Selisih pembulatan {format_rupiah(result.sisa_pembulatan)}."
            )
        return "\n".join(lines)

    def format_reminder_draft(
        self, invoice: ClientInvoice, draft: ReminderDraftOutput
    ) -> str:
        """Memformat draf pesan pengingat pembayaran siap salin."""
        lines = [
            f"# Draf Pesan Pengingat Pembayaran — {invoice.klien}",
            f"Waktu: {timestamp_wib()}",
            f"Tagihan #{invoice.id}: {invoice.proyek} | Sisa: {format_rupiah(invoice.sisa_tagihan)}",
            f"Catatan nada: {draft.catatan_nada.strip()}",
            "",
            "## Pesan WhatsApp Siap Kirim",
            draft.pesan_pengingat.strip(),
        ]
        return "\n".join(lines)
