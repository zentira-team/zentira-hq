"""Penyimpanan ringan berbasis JSON & import CSV untuk daftar prospek UMKM."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pydantic import BaseModel

from core.config import PROJECT_ROOT
from core.formatter import timestamp_wib

DEFAULT_LEADS_FILE = PROJECT_ROOT / "data" / "leads.json"

ALLOWED_STATUSES: tuple[str, ...] = (
    "baru",
    "dihubungi",
    "follow_up",
    "tertarik",
    "deal",
    "ditolak",
)

ALLOWED_CHANNELS: tuple[str, ...] = (
    "whatsapp",
    "instagram",
    "email",
)


class LeadNotFoundError(ValueError):
    """Dilempar ketika ID prospek tidak ditemukan di daftar."""


class Lead(BaseModel):
    """Satu data prospek UMKM lokal."""

    id: int
    nama_usaha: str
    kategori: str
    kota: str = ""
    kontak: str = ""
    saluran: str = "whatsapp"
    punya_website: bool = False
    catatan: str = ""
    status: str = "baru"
    dibuat_pada: str
    diperbarui_pada: str


def _validate_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized not in ALLOWED_STATUSES:
        valid = ", ".join(ALLOWED_STATUSES)
        raise ValueError(f"Status '{status}' tidak valid. Pilihan: {valid}.")
    return normalized


def _validate_channel(channel: str) -> str:
    normalized = channel.strip().lower() or "whatsapp"
    if normalized not in ALLOWED_CHANNELS:
        valid = ", ".join(ALLOWED_CHANNELS)
        raise ValueError(f"Saluran '{channel}' tidak valid. Pilihan: {valid}.")
    return normalized


def _parse_bool(raw: str | bool) -> bool:
    if isinstance(raw, bool):
        return raw
    return raw.strip().lower() in ("true", "1", "ya", "yes", "sudah")


class LeadStore:
    """Pengelola CRUD daftar prospek UMKM dalam file JSON lokal."""

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or DEFAULT_LEADS_FILE

    def _load_all(self) -> list[Lead]:
        if not self.file_path.exists():
            return []
        raw_text = self.file_path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"File data prospek rusak/tidak valid ({self.file_path}): {exc}"
            ) from exc
        return [Lead.model_validate(item) for item in data]

    def _save_all(self, leads: list[Lead]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [lead.model_dump() for lead in leads]
        self.file_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _duplicate_key(self, nama_usaha: str, kota: str) -> tuple[str, str]:
        return (nama_usaha.strip().casefold(), kota.strip().casefold())

    def add_lead(
        self,
        nama_usaha: str,
        kategori: str,
        kota: str = "",
        kontak: str = "",
        saluran: str = "whatsapp",
        punya_website: bool = False,
        catatan: str = "",
        status: str = "baru",
    ) -> Lead:
        """Menambahkan 1 prospek UMKM baru ke penyimpanan lokal."""
        cleaned_name = nama_usaha.strip()
        cleaned_category = kategori.strip()
        if not cleaned_name:
            raise ValueError("Nama usaha tidak boleh kosong.")
        if not cleaned_category:
            raise ValueError("Kategori usaha tidak boleh kosong.")

        valid_status = _validate_status(status)
        valid_channel = _validate_channel(saluran)

        leads = self._load_all()
        target_key = self._duplicate_key(cleaned_name, kota)
        if any(self._duplicate_key(item.nama_usaha, item.kota) == target_key for item in leads):
            loc = f" ({kota.strip()})" if kota.strip() else ""
            raise ValueError(f"Prospek '{cleaned_name}'{loc} sudah ada di daftar.")

        next_id = max((item.id for item in leads), default=0) + 1
        now = timestamp_wib()
        new_lead = Lead(
            id=next_id,
            nama_usaha=cleaned_name,
            kategori=cleaned_category,
            kota=kota.strip(),
            kontak=kontak.strip(),
            saluran=valid_channel,
            punya_website=punya_website,
            catatan=catatan.strip(),
            status=valid_status,
            dibuat_pada=now,
            diperbarui_pada=now,
        )
        leads.append(new_lead)
        self._save_all(leads)
        return new_lead

    def list_leads(
        self,
        status: str | None = None,
        only_without_website: bool = False,
    ) -> list[Lead]:
        """Mengambil daftar prospek dengan filter status dan kepemilikan website opsional."""
        leads = self._load_all()
        if status:
            valid_status = _validate_status(status)
            leads = [item for item in leads if item.status == valid_status]
        if only_without_website:
            leads = [item for item in leads if not item.punya_website]
        return leads

    def get_lead(self, lead_id: int) -> Lead:
        """Mengambil 1 prospek berdasarkan ID."""
        for item in self._load_all():
            if item.id == lead_id:
                return item
        raise LeadNotFoundError(f"Prospek dengan ID #{lead_id} tidak ditemukan.")

    def update_status(
        self,
        lead_id: int,
        new_status: str,
        catatan_tambahan: str = "",
    ) -> Lead:
        """Memperbarui status prospek (dan opsional menambah catatan perkembangan)."""
        valid_status = _validate_status(new_status)
        leads = self._load_all()

        for idx, item in enumerate(leads):
            if item.id == lead_id:
                updated_note = item.catatan
                extra = catatan_tambahan.strip()
                if extra:
                    updated_note = f"{updated_note} | {extra}" if updated_note else extra
                updated = item.model_copy(
                    update={
                        "status": valid_status,
                        "catatan": updated_note,
                        "diperbarui_pada": timestamp_wib(),
                    }
                )
                leads[idx] = updated
                self._save_all(leads)
                return updated

        raise LeadNotFoundError(f"Prospek dengan ID #{lead_id} tidak ditemukan.")

    def delete_lead(self, lead_id: int) -> Lead:
        """Menghapus prospek berdasarkan ID."""
        leads = self._load_all()
        for idx, item in enumerate(leads):
            if item.id == lead_id:
                removed = leads.pop(idx)
                self._save_all(leads)
                return removed
        raise LeadNotFoundError(f"Prospek dengan ID #{lead_id} tidak ditemukan.")

    def import_csv(self, csv_path: Path) -> tuple[int, int]:
        """Mengimpor banyak prospek dari file CSV. Mengembalikan (jumlah_ditambah, jumlah_dilewati)."""
        if not csv_path.is_file():
            raise ValueError(f"File CSV tidak ditemukan: {csv_path}")

        added = 0
        skipped = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                nama = (row.get("nama_usaha") or "").strip()
                kategori = (row.get("kategori") or "").strip()
                if not nama or not kategori:
                    skipped += 1
                    continue
                try:
                    self.add_lead(
                        nama_usaha=nama,
                        kategori=kategori,
                        kota=(row.get("kota") or "").strip(),
                        kontak=(row.get("kontak") or "").strip(),
                        saluran=(row.get("saluran") or "whatsapp").strip() or "whatsapp",
                        punya_website=_parse_bool(row.get("punya_website") or "false"),
                        catatan=(row.get("catatan") or "").strip(),
                        status=(row.get("status") or "baru").strip() or "baru",
                    )
                    added += 1
                except ValueError:
                    skipped += 1

        return added, skipped
