"""Penyimpanan JSON lokal untuk pencatatan kas dan tagihan DP/pelunasan klien."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel

from core.config import PROJECT_ROOT
from core.formatter import WIB, timestamp_wib

DEFAULT_FINANCE_FILE = PROJECT_ROOT / "data" / "finance.json"

ALLOWED_TX_TYPES: tuple[str, ...] = ("masuk", "keluar")
ALLOWED_STREAMS: tuple[str, ...] = ("konten", "web_umkm", "umum")
ALLOWED_INVOICE_STATUSES: tuple[str, ...] = ("belum_bayar", "dp", "lunas")


class FinanceNotFoundError(ValueError):
    """Dilempar ketika ID transaksi atau tagihan klien tidak ditemukan."""


class Transaction(BaseModel):
    """Satu catatan pemasukan atau pengeluaran dalam Rupiah bulat."""

    id: int
    tanggal: str
    jenis: str
    nominal: int
    sumber: str = "umum"
    kategori: str
    keterangan: str = ""
    dibuat_pada: str


class ClientInvoice(BaseModel):
    """Catatan proyek klien beserta status DP, pelunasan, dan jatuh tempo."""

    id: int
    klien: str
    proyek: str
    sumber: str = "web_umkm"
    total_harga: int
    dibayar: int = 0
    status: str = "belum_bayar"
    jatuh_tempo: str = ""
    catatan: str = ""
    dibuat_pada: str
    diperbarui_pada: str

    @property
    def sisa_tagihan(self) -> int:
        return max(0, self.total_harga - self.dibayar)


def today_wib_str() -> str:
    return datetime.now(WIB).strftime("%Y-%m-%d")


def _validate_date_str(value: str, field_name: str, allow_empty: bool = False) -> str:
    cleaned = value.strip()
    if not cleaned:
        if allow_empty:
            return ""
        return today_wib_str()
    try:
        date.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(
            f"Format {field_name} '{cleaned}' tidak valid. Gunakan format YYYY-MM-DD (contoh: 2026-11-30)."
        ) from exc
    return cleaned


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> str:
    normalized = value.strip().lower()
    if normalized not in allowed:
        valid = ", ".join(allowed)
        raise ValueError(f"Nilai {field_name} '{value}' tidak valid. Pilihan: {valid}.")
    return normalized


def _compute_invoice_status(total_harga: int, dibayar: int) -> str:
    if dibayar <= 0:
        return "belum_bayar"
    if dibayar >= total_harga:
        return "lunas"
    return "dp"


class FinanceStore:
    """Pengelola catatan transaksi dan tagihan klien berbasis JSON lokal."""

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or DEFAULT_FINANCE_FILE

    def _load_db(self) -> tuple[list[Transaction], list[ClientInvoice]]:
        if not self.file_path.exists():
            return [], []
        raw_text = self.file_path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return [], []
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"File data keuangan rusak/tidak valid ({self.file_path}): {exc}"
            ) from exc

        transactions = [
            Transaction.model_validate(item) for item in data.get("transactions", [])
        ]
        invoices = [
            ClientInvoice.model_validate(item) for item in data.get("invoices", [])
        ]
        return transactions, invoices

    def _save_db(
        self,
        transactions: list[Transaction],
        invoices: list[ClientInvoice],
    ) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "transactions": [tx.model_dump() for tx in transactions],
            "invoices": [inv.model_dump() for inv in invoices],
        }
        self.file_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_transaction(
        self,
        jenis: str,
        nominal: int,
        kategori: str,
        sumber: str = "umum",
        keterangan: str = "",
        tanggal: str = "",
    ) -> Transaction:
        """Mencatat satu transaksi pemasukan atau pengeluaran."""
        valid_jenis = _validate_choice(jenis, ALLOWED_TX_TYPES, "jenis transaksi")
        valid_sumber = _validate_choice(sumber, ALLOWED_STREAMS, "sumber/lini usaha")
        valid_tanggal = _validate_date_str(tanggal, "tanggal", allow_empty=False)
        cleaned_cat = kategori.strip()
        if not cleaned_cat:
            raise ValueError("Kategori transaksi tidak boleh kosong.")
        if nominal <= 0:
            raise ValueError("Nominal transaksi harus lebih dari 0.")

        transactions, invoices = self._load_db()
        next_id = max((tx.id for tx in transactions), default=0) + 1
        tx = Transaction(
            id=next_id,
            tanggal=valid_tanggal,
            jenis=valid_jenis,
            nominal=int(nominal),
            sumber=valid_sumber,
            kategori=cleaned_cat,
            keterangan=keterangan.strip(),
            dibuat_pada=timestamp_wib(),
        )
        transactions.append(tx)
        self._save_db(transactions, invoices)
        return tx

    def list_transactions(
        self,
        jenis: str | None = None,
        sumber: str | None = None,
        month: str | None = None,
    ) -> list[Transaction]:
        """Mengambil daftar transaksi dengan filter opsional jenis, sumber, dan bulan (YYYY-MM)."""
        transactions, _ = self._load_db()
        if jenis:
            valid_jenis = _validate_choice(jenis, ALLOWED_TX_TYPES, "jenis transaksi")
            transactions = [tx for tx in transactions if tx.jenis == valid_jenis]
        if sumber:
            valid_sumber = _validate_choice(sumber, ALLOWED_STREAMS, "sumber/lini usaha")
            transactions = [tx for tx in transactions if tx.sumber == valid_sumber]
        if month:
            cleaned_month = month.strip()
            transactions = [
                tx for tx in transactions if tx.tanggal.startswith(cleaned_month)
            ]
        return transactions

    def delete_transaction(self, tx_id: int) -> Transaction:
        """Menghapus 1 transaksi berdasarkan ID."""
        transactions, invoices = self._load_db()
        for idx, tx in enumerate(transactions):
            if tx.id == tx_id:
                removed = transactions.pop(idx)
                self._save_db(transactions, invoices)
                return removed
        raise FinanceNotFoundError(f"Transaksi dengan ID #{tx_id} tidak ditemukan.")

    def add_invoice(
        self,
        klien: str,
        proyek: str,
        total_harga: int,
        dp: int = 0,
        sumber: str = "web_umkm",
        jatuh_tempo: str = "",
        catatan: str = "",
        catat_transaksi_dp: bool = True,
    ) -> tuple[ClientInvoice, Transaction | None]:
        """Mencatat tagihan proyek klien (endorse/website) beserta DP awal bila ada."""
        cleaned_client = klien.strip()
        cleaned_project = proyek.strip()
        if not cleaned_client:
            raise ValueError("Nama klien tidak boleh kosong.")
        if not cleaned_project:
            raise ValueError("Nama proyek tidak boleh kosong.")
        if total_harga <= 0:
            raise ValueError("Total harga proyek harus lebih dari 0.")
        if dp < 0 or dp > total_harga:
            raise ValueError("Nominal DP harus antara 0 hingga total harga proyek.")

        valid_sumber = _validate_choice(sumber, ALLOWED_STREAMS, "sumber/lini usaha")
        valid_due = _validate_date_str(jatuh_tempo, "jatuh_tempo", allow_empty=True)

        transactions, invoices = self._load_db()
        next_inv_id = max((inv.id for inv in invoices), default=0) + 1
        now = timestamp_wib()
        status = _compute_invoice_status(total_harga, dp)

        invoice = ClientInvoice(
            id=next_inv_id,
            klien=cleaned_client,
            proyek=cleaned_project,
            sumber=valid_sumber,
            total_harga=int(total_harga),
            dibayar=int(dp),
            status=status,
            jatuh_tempo=valid_due,
            catatan=catatan.strip(),
            dibuat_pada=now,
            diperbarui_pada=now,
        )
        invoices.append(invoice)

        created_tx: Transaction | None = None
        if dp > 0 and catat_transaksi_dp:
            next_tx_id = max((tx.id for tx in transactions), default=0) + 1
            tx_category = "pelunasan_klien" if status == "lunas" else "dp_klien"
            created_tx = Transaction(
                id=next_tx_id,
                tanggal=today_wib_str(),
                jenis="masuk",
                nominal=int(dp),
                sumber=valid_sumber,
                kategori=tx_category,
                keterangan=f"Invoice #{next_inv_id} — {cleaned_client} ({cleaned_project})",
                dibuat_pada=now,
            )
            transactions.append(created_tx)

        self._save_db(transactions, invoices)
        return invoice, created_tx

    def record_payment(
        self,
        invoice_id: int,
        nominal: int,
        catatan: str = "",
        catat_transaksi: bool = True,
    ) -> tuple[ClientInvoice, Transaction | None]:
        """Mencatat pembayaran DP tambahan atau pelunasan untuk tagihan klien."""
        if nominal <= 0:
            raise ValueError("Nominal pembayaran harus lebih dari 0.")

        transactions, invoices = self._load_db()
        for idx, inv in enumerate(invoices):
            if inv.id != invoice_id:
                continue

            if inv.sisa_tagihan <= 0:
                raise ValueError(
                    f"Tagihan #{inv.id} ({inv.klien}) sudah berstatus lunas."
                )
            if nominal > inv.sisa_tagihan:
                raise ValueError(
                    f"Nominal pembayaran ({nominal}) melebihi sisa tagihan ({inv.sisa_tagihan})."
                )

            new_paid = inv.dibayar + int(nominal)
            new_status = _compute_invoice_status(inv.total_harga, new_paid)
            now = timestamp_wib()
            extra = catatan.strip()
            updated_note = (
                f"{inv.catatan} | {extra}" if (inv.catatan and extra) else (extra or inv.catatan)
            )
            updated_inv = inv.model_copy(
                update={
                    "dibayar": new_paid,
                    "status": new_status,
                    "catatan": updated_note,
                    "diperbarui_pada": now,
                }
            )
            invoices[idx] = updated_inv

            created_tx: Transaction | None = None
            if catat_transaksi:
                next_tx_id = max((tx.id for tx in transactions), default=0) + 1
                tx_cat = "pelunasan_klien" if new_status == "lunas" else "cicilan_dp_klien"
                tx_note = f"Invoice #{inv.id} — {inv.klien} ({inv.proyek})"
                if extra:
                    tx_note = f"{tx_note} | {extra}"
                created_tx = Transaction(
                    id=next_tx_id,
                    tanggal=today_wib_str(),
                    jenis="masuk",
                    nominal=int(nominal),
                    sumber=inv.sumber,
                    kategori=tx_cat,
                    keterangan=tx_note,
                    dibuat_pada=now,
                )
                transactions.append(created_tx)

            self._save_db(transactions, invoices)
            return updated_inv, created_tx

        raise FinanceNotFoundError(f"Tagihan dengan ID #{invoice_id} tidak ditemukan.")

    def list_invoices(
        self,
        status: str | None = None,
        unpaid_only: bool = False,
    ) -> list[ClientInvoice]:
        """Mengambil daftar tagihan klien dengan filter opsional."""
        _, invoices = self._load_db()
        if status:
            valid_status = _validate_choice(
                status, ALLOWED_INVOICE_STATUSES, "status tagihan"
            )
            invoices = [inv for inv in invoices if inv.status == valid_status]
        if unpaid_only:
            invoices = [inv for inv in invoices if inv.status != "lunas"]
        return invoices

    def get_invoice(self, invoice_id: int) -> ClientInvoice:
        """Mengambil 1 tagihan klien berdasarkan ID."""
        _, invoices = self._load_db()
        for inv in invoices:
            if inv.id == invoice_id:
                return inv
        raise FinanceNotFoundError(f"Tagihan dengan ID #{invoice_id} tidak ditemukan.")

    def delete_invoice(self, invoice_id: int) -> ClientInvoice:
        """Menghapus 1 tagihan klien berdasarkan ID."""
        transactions, invoices = self._load_db()
        for idx, inv in enumerate(invoices):
            if inv.id == invoice_id:
                removed = invoices.pop(idx)
                self._save_db(transactions, invoices)
                return removed
        raise FinanceNotFoundError(f"Tagihan dengan ID #{invoice_id} tidak ditemukan.")

    def reset_all(self) -> None:
        """Menghapus seluruh riwayat transaksi dan tagihan klien (kembali ke Rp0)."""
        self._save_db([], [])
