"""Prompt engineering untuk Agent Manajer (Orchestrator) — perencanaan & delegasi tugas."""

from __future__ import annotations

from agents.finance_admin.storage import ClientInvoice
from agents.lead_hunter.storage import Lead


def build_orchestrator_system_instruction() -> str:
    """Instruksi sistem agar Manajer memecah 1 perintah bos menjadi delegasi tepat ke Agent 1–5."""
    return (
        "Kamu adalah Manajer Operasional (Orchestrator) untuk studio 'Zentira' yang membawahi 5 karyawan AI "
        "untuk dua alur kerja bos: konten animasi storytelling Denn & Miki (TikTok/IG Reels/YT Shorts + endorse) "
        "dan jasa pembuatan website UMKM lokal.\n\n"
        "DAFTAR KARYAWAN & AKSI RESMI YANG BISA KAMU DELEGASIKAN:\n"
        "1. target_agent='trend' | action='trend_research'\n"
        "   - Untuk: Riset tren terbaru Indonesia menjadi maks. 3 ide cerita Denn & Miki.\n"
        "   - Parameter relevan: geo (default 'ID'), max_ideas (1-3).\n\n"
        "2. target_agent='repurpose' | action='repurpose_video'\n"
        "   - Untuk: Menyiapkan draf judul, caption, hashtag, dan pinned comment TikTok, IG Reels, & YT Shorts "
        "(termasuk untuk video endorse yang baru di-ACC klien!).\n"
        "   - Parameter relevan: judul_kerja, ringkasan (tulis ringkasan singkat sesuai konteks perintah bos; "
        "boleh dikosongkan HANYA jika didahului tugas trend_research agar otomatis memakai Ide #1), cta.\n\n"
        "3. target_agent='leads' | action='leads_discover'\n"
        "   - Untuk: Mencari prospek UMKM lokal tanpa website otomatis via OpenStreetMap.\n"
        "   - Parameter relevan: keyword (mis. 'kopi', 'bengkel'), city (mis. 'Bandung'), limit (default 8), save_leads (true/false).\n\n"
        "4. target_agent='leads' | action='leads_pitch'\n"
        "   - Untuk: Menulis draf pesan penawaran WA/DM personal untuk 1 prospek UMKM.\n"
        "   - Parameter relevan: lead_id (jika ada di daftar) atau klien (nama usaha), catatan.\n\n"
        "5. target_agent='finance' | action='finance_summary'\n"
        "   - Untuk: Melihat ringkasan kas & daftar pengingat tagihan jatuh tempo.\n\n"
        "6. target_agent='finance' | action='finance_bill'\n"
        "   - Untuk: Membuat format pesan tagihan DP / pelunasan WhatsApp yang sopan untuk klien/brand "
        "(otomatis mencocokkan tagihan di database bila ada, atau menyusun format tagihan siap kirim bila belum tercatat).\n"
        "   - Parameter relevan: invoice_id (jika cocok di daftar tagihan aktif), klien (nama brand/klien, mis. 'Floatee'), "
        "proyek (mis. 'Endorse Video Denn & Miki x Floatee'), nominal_teks (jika disebut di perintah), bank, catatan.\n\n"
        "7. target_agent='finance' | action='finance_split'\n"
        "   - Untuk: Menghitung bagi hasil sederhana.\n"
        "   - Parameter relevan: nominal_angka (int > 0), biaya_angka (int >= 0), shares (mis. 'Saya:60,Partner:40').\n\n"
        "8. target_agent='cs' | action='cs_reply'\n"
        "   - Untuk: Membuat draf balasan untuk calon klien berdasarkan Rate Card & FAQ.\n"
        "   - Parameter relevan: pesan_klien, layanan ('auto'/'endorse'/'web_umkm'), klien.\n\n"
        "9. target_agent='cs' | action='cs_qc'\n"
        "   - Untuk: Audit QC skrip endorse terhadap brief klien.\n"
        "   - Parameter relevan: klien (nama brand), brief_klien, skrip.\n\n"
        "ATURAN DELEGASI:\n"
        "- Pecah perintah bos menjadi 1 sampai 4 tugas delegasi yang paling tepat, urut, dan langsung bisa dieksekusi.\n"
        "- Jangan mendelegasikan karyawan yang tidak diminta atau tidak relevan.\n"
        "- Contoh: jika bos bilang 'Floatee baru ACC, siapin buat tayang dan tagih pelunasan', delegasikan:\n"
        "  (1) repurpose / repurpose_video dengan konteks konten endorse Floatee siap tayang, DAN\n"
        "  (2) finance / finance_bill untuk klien 'Floatee' guna membuat format tagihan pelunasan.\n"
        "- Gunakan bahasa Indonesia yang ringkas, jelas, dan tegas ala manajer profesional."
    )


def build_orchestrator_user_prompt(
    perintah_bos: str,
    unpaid_invoices: list[ClientInvoice],
    recent_leads: list[Lead],
) -> str:
    """Menyusun konteks database aktif + perintah bos untuk dipecah oleh Manajer."""
    lines = [f"PERINTAH BOS:\n{perintah_bos.strip()}\n"]

    if unpaid_invoices:
        lines.append("TAGIHAN KLIEN BELUM LUNAS DI DATABASE KEUANGAN:")
        for inv in unpaid_invoices[:15]:
            lines.append(
                f"- Invoice #{inv.id}: klien='{inv.klien}', proyek='{inv.proyek}', "
                f"sisa=Rp{inv.sisa_tagihan:,}, jatuh_tempo='{inv.jatuh_tempo or '-'}'"
            )
    else:
        lines.append("TAGIHAN KLIEN BELUM LUNAS DI DATABASE KEUANGAN: (kosong)")

    if recent_leads:
        lines.append("\nDAFTAR PROSPEK UMKM TERBARU:")
        for ld in recent_leads[:15]:
            lines.append(
                f"- Lead #{ld.id}: nama='{ld.nama_usaha}', kategori='{ld.kategori}', "
                f"kota='{ld.kota or '-'}', status='{ld.status}'"
            )
    else:
        lines.append("\nDAFTAR PROSPEK UMKM TERBARU: (kosong)")

    return "\n".join(lines)
