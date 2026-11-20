"""Utilitas pemformatan output untuk terminal, file lokal, dan Telegram."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.config import PROJECT_ROOT

WIB = timezone(timedelta(hours=7))


def configure_utf8_stdout() -> None:
    """Memastikan stdout/stderr mendukung UTF-8 di Windows PowerShell."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def timestamp_wib() -> str:
    """Mengembalikan stempel waktu saat ini dalam zona waktu WIB."""
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M WIB")


def save_markdown_output(
    prefix: str, content: str, output_dir: Path | None = None
) -> Path:
    """Menyimpan laporan teks/Markdown ke folder outputs/ dengan nama berstempel waktu."""
    target_dir = output_dir or (PROJECT_ROOT / "outputs")
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(WIB).strftime("%Y%m%d_%H%M%S")
    file_path = target_dir / f"{prefix}_{stamp}.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def truncate_for_telegram(text: str, limit: int = 4096) -> str:
    """Memotong pesan agar aman dikirim dalam batas karakter Telegram Bot."""
    if len(text) <= limit:
        return text
    suffix = "\n\n... (terpotong)"
    return text[: max(0, limit - len(suffix))] + suffix
