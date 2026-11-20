"""Prompt engineering untuk draf pesan pengingat DP/pelunasan klien (Agent 4)."""

from __future__ import annotations

from agents.finance_admin.storage import ClientInvoice


def build_reminder_system_instruction() -> str:
    """Instruksi AI untuk menyusun pesan pengingat pembayaran yang sopan dan profesional."""
    return (
        "Kamu adalah Admin Keuangan yang ramah, sopan, dan profesional untuk kreator konten "
        "animasi & penyedia jasa pembuatan website UMKM di Indonesia.\n\n"
        "ATURAN MENULIS PESAN PENGINGAT PEMBAYARAN (WAJIB):\n"
        "1. Tetap sopan, hangat, tidak menuduh, dan tidak terkesan menagih dengan kasar.\n"
        "2. Cantumkan detail angka yang PERSIS sama dengan data yang diberikan (JANGAN mengubah atau menghitung ulang nominal!).\n"
        "3. Ringkas dan mudah dibaca di WhatsApp (2-4 paragraf pendek).\n"
        "4. Tutup dengan kalimat apresiasi dan ajakan konfirmasi bukti transfer jika sudah melakukan pembayaran."
    )


def build_reminder_user_prompt(
    invoice: ClientInvoice,
    total_str: str,
    dibayar_str: str,
    sisa_str: str,
    status_waktu: str,
    nama_pengirim: str = "",
    info_rekening: str = "",
) -> str:
    """Menyusun konteks tagihan klien untuk dibuatkan draf pesan pengingat WhatsApp."""
    lines = [
        "Tolong buatkan draf pesan pengingat pembayaran WhatsApp yang sopan untuk data berikut:\n",
        f"- Nama Klien: {invoice.klien}",
        f"- Proyek: {invoice.proyek}",
        f"- Status Saat Ini: {invoice.status}",
        f"- Total Nilai Proyek: {total_str}",
        f"- Sudah Dibayarkan: {dibayar_str}",
        f"- Sisa yang Perlu Dibayar: {sisa_str}",
        f"- Jatuh Tempo: {invoice.jatuh_tempo or 'Belum ditentukan'} ({status_waktu})",
    ]
    if invoice.catatan:
        lines.append(f"- Catatan Proyek: {invoice.catatan}")
    if nama_pengirim.strip():
        lines.append(f"- Nama Pengirim: {nama_pengirim.strip()}")
    else:
        lines.append("- Nama Pengirim: [Nama Anda]")
    if info_rekening.strip():
        lines.append(f"- Informasi Rekening / Pembayaran: {info_rekening.strip()}")
    else:
        lines.append("- Informasi Rekening: [Isi No. Rekening / E-Wallet Anda]")
    return "\n".join(lines)
