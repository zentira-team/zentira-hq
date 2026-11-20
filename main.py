"""CLI entry point terpadu untuk sistem Multi-Agent AI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from agents.cs_qc import (
    CSQCAgent,
    DEFAULT_RATE_CARD_FILE,
    load_rate_card_and_faq,
)
from agents.cs_qc.agent import ALLOWED_CS_SERVICES
from agents.finance_admin import (
    ALLOWED_INVOICE_STATUSES,
    ALLOWED_STREAMS,
    ALLOWED_TX_TYPES,
    FinanceAdminAgent,
    FinanceNotFoundError,
    FinanceStore,
    format_rupiah,
    parse_shares_spec,
)
from agents.lead_hunter import (
    ALLOWED_CHANNELS,
    ALLOWED_STATUSES,
    LeadDiscoveryError,
    LeadHunterAgent,
    LeadNotFoundError,
    LeadStore,
    discover_umkm_leads,
)
from agents.orchestrator import ManagerOrchestratorAgent
from agents.repurposer import RepurposerAgent, VideoBrief
from agents.trend_researcher import (
    TrendFetchError,
    TrendResearcherAgent,
    fetch_google_trends,
)
from core.config import ConfigError, Settings, load_settings
from core.formatter import configure_utf8_stdout, save_markdown_output, timestamp_wib
from core.gemini_client import GeminiClient, GeminiClientError


def _build_gemini_client(settings: Settings) -> GeminiClient:
    return GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        fallback_models=settings.gemini_fallback_models,
        groq_api_key=settings.groq_api_key,
        groq_model=settings.groq_model,
        groq_fallback_models=settings.groq_fallback_models,
        primary_provider=settings.ai_primary_provider,
    )


def _format_raw_trends(geo: str, trends: list) -> str:
    lines = [
        f"# Daftar Tren Mentah Google Trends ({geo})",
        f"Waktu: {timestamp_wib()}",
        f"Jumlah tren ditemukan: {len(trends)}",
        "",
    ]
    for idx, item in enumerate(trends, start=1):
        traffic = f" ({item.approx_traffic})" if item.approx_traffic else ""
        lines.append(f"{idx}. {item.title}{traffic}")
        for news in item.news_items[:2]:
            source = f"[{news.source}] " if news.source else ""
            lines.append(f"   - {source}{news.title}")
    return "\n".join(lines)


def _run_trend_command(args: argparse.Namespace) -> int:
    settings = load_settings(require_gemini_key=not args.fetch_only)
    geo = (args.geo or settings.trends_geo).upper()
    max_items = args.max_items or settings.trends_max_items
    max_ideas = args.max_ideas or settings.trends_max_ideas

    if args.fetch_only:
        trends = fetch_google_trends(geo=geo, max_items=max_items)
        output = _format_raw_trends(geo, trends)
        print(output)
        if args.save:
            saved_path = save_markdown_output("trend_raw", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    gemini_client = _build_gemini_client(settings)
    agent = TrendResearcherAgent(
        gemini_client=gemini_client,
        geo=geo,
        max_items=max_items,
        max_ideas=max_ideas,
    )
    report = agent.run()
    output = agent.format_report(report)
    print(output)

    if args.save:
        saved_path = save_markdown_output("trend", output)
        print(f"\nHasil disimpan ke: {saved_path}")
    return 0


def _resolve_video_summary(args: argparse.Namespace) -> str:
    if args.summary and args.summary.strip():
        return args.summary.strip()

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            raise ValueError(f"File ringkasan tidak ditemukan: {path}")
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Isi file ringkasan kosong: {path}")
        return content

    print("Masukkan ringkasan 1 video (tekan Enter jika selesai):")
    summary = input("> ").strip()
    if not summary:
        raise ValueError("Ringkasan video belum diisi.")
    return summary


def _run_repurpose_command(args: argparse.Namespace) -> int:
    summary = _resolve_video_summary(args)
    settings = load_settings(require_gemini_key=True)
    gemini_client = _build_gemini_client(settings)

    agent = RepurposerAgent(gemini_client=gemini_client)
    brief = VideoBrief(
        ringkasan=summary,
        judul_kerja=args.title or "",
        cta_tambahan=args.cta or "",
        catatan_gaya=args.tone or "",
    )
    report = agent.run(brief)
    output = agent.format_report(report)
    print(output)

    if args.save:
        saved_path = save_markdown_output("repurpose", output)
        print(f"\nHasil disimpan ke: {saved_path}")
    return 0


def _run_leads_command(args: argparse.Namespace) -> int:
    data_path = Path(args.data_file) if args.data_file else None
    store = LeadStore(file_path=data_path)

    if args.leads_action == "add":
        lead = store.add_lead(
            nama_usaha=args.name,
            kategori=args.category,
            kota=args.city or "",
            kontak=args.contact or "",
            saluran=args.channel,
            punya_website=args.has_website,
            catatan=args.notes or "",
        )
        print(
            f"[OK] Prospek #{lead.id} '{lead.nama_usaha}' ({lead.kategori}) berhasil ditambahkan."
        )
        return 0

    if args.leads_action == "list":
        leads = store.list_leads(
            status=args.status,
            only_without_website=args.no_web,
        )
        agent = LeadHunterAgent(store=store)
        print(agent.format_leads_list(leads))
        return 0

    if args.leads_action == "status":
        updated = store.update_status(
            lead_id=args.id,
            new_status=args.status,
            catatan_tambahan=args.notes or "",
        )
        print(
            f"[OK] Status prospek #{updated.id} '{updated.nama_usaha}' diperbarui menjadi '{updated.status}'."
        )
        return 0

    if args.leads_action == "delete":
        removed = store.delete_lead(args.id)
        print(f"[OK] Prospek #{removed.id} '{removed.nama_usaha}' dihapus dari daftar.")
        return 0

    if args.leads_action == "import":
        added, skipped = store.import_csv(Path(args.csv))
        print(f"[OK] Import CSV selesai: {added} prospek ditambahkan, {skipped} dilewati.")
        return 0

    if args.leads_action == "discover":
        discovered = discover_umkm_leads(
            keyword=args.keyword,
            city=args.city,
            radius_km=args.radius_km,
            limit=args.limit,
            only_without_website=not args.include_with_web,
            exclude_chains=not args.include_chains,
        )
        agent = LeadHunterAgent(store=store)
        output = agent.format_discovered_leads(
            keyword=args.keyword, city=args.city, leads=discovered
        )
        print(output)

        if args.save_leads and discovered:
            saved_leads, skipped = agent.save_discovered_leads(discovered)
            id_list = ", ".join(f"#{lead.id}" for lead in saved_leads) or "-"
            print(
                f"\n[OK] Tersimpan ke daftar prospek: {len(saved_leads)} baru ({id_list}), {skipped} duplikat dilewati."
            )

        if args.save:
            saved_path = save_markdown_output("lead_discover", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.leads_action == "pitch":
        settings = load_settings(require_gemini_key=True)
        gemini_client = _build_gemini_client(settings)
        agent = LeadHunterAgent(store=store, gemini_client=gemini_client)
        report = agent.draft_outreach(
            lead_id=args.id,
            penawaran_khusus=args.offer or "",
            nama_pengirim=args.sender or "",
        )
        output = agent.format_outreach_report(report)
        print(output)

        if args.mark_contacted:
            store.update_status(args.id, "dihubungi")
            print(f"\n[OK] Status prospek #{args.id} otomatis diperbarui menjadi 'dihubungi'.")

        if args.save:
            saved_path = save_markdown_output(f"lead_pitch_{args.id}", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    raise ValueError("Sub-perintah leads tidak dikenali.")


def _run_finance_command(args: argparse.Namespace) -> int:
    data_path = Path(args.data_file) if args.data_file else None
    store = FinanceStore(file_path=data_path)
    agent = FinanceAdminAgent(store=store)

    if args.finance_action == "tx-add":
        tx = store.add_transaction(
            jenis=args.type,
            nominal=args.amount,
            kategori=args.category,
            sumber=args.stream,
            keterangan=args.notes or "",
            tanggal=args.date or "",
        )
        print(
            f"[OK] Transaksi #{tx.id} ({tx.jenis.upper()} {format_rupiah(tx.nominal)} "
            f"- {tx.sumber}/{tx.kategori}) berhasil dicatat."
        )
        return 0

    if args.finance_action == "tx-list":
        txs = store.list_transactions(
            jenis=args.type,
            sumber=args.stream,
            month=args.month,
        )
        print(agent.format_transactions(txs))
        return 0

    if args.finance_action == "invoice-add":
        inv, tx = store.add_invoice(
            klien=args.client,
            proyek=args.project,
            total_harga=args.total,
            dp=args.dp,
            sumber=args.stream,
            jatuh_tempo=args.due or "",
            catatan=args.notes or "",
            catat_transaksi_dp=not args.no_sync_tx,
        )
        print(
            f"[OK] Tagihan #{inv.id} '{inv.klien}' ({inv.proyek}) dicatat | "
            f"Status: {inv.status} | Sisa: {format_rupiah(inv.sisa_tagihan)}."
        )
        if tx is not None:
            print(
                f"[OK] DP/pembayaran awal otomatis dicatat sebagai Transaksi #{tx.id} "
                f"({format_rupiah(tx.nominal)})."
            )
        return 0

    if args.finance_action == "invoice-pay":
        inv, tx = store.record_payment(
            invoice_id=args.id,
            nominal=args.amount,
            catatan=args.notes or "",
            catat_transaksi=not args.no_sync_tx,
        )
        print(
            f"[OK] Pembayaran {format_rupiah(args.amount)} untuk Tagihan #{inv.id} ({inv.klien}) dicatat | "
            f"Status kini: {inv.status} | Sisa: {format_rupiah(inv.sisa_tagihan)}."
        )
        if tx is not None:
            print(f"[OK] Otomatis tercatat sebagai Transaksi #{tx.id}.")
        return 0

    if args.finance_action == "invoice-list":
        invs = store.list_invoices(status=args.status, unpaid_only=args.unpaid)
        print(agent.format_invoices(invs))
        return 0

    if args.finance_action == "summary":
        summary = agent.get_summary(month=args.month, sumber=args.stream)
        output = agent.format_summary(summary)
        print(output)
        if args.save:
            saved_path = save_markdown_output("finance_summary", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.finance_action == "remind":
        reminders = agent.get_reminders(within_days=args.days)
        output = agent.format_reminders(reminders)
        print(output)
        if args.save:
            saved_path = save_markdown_output("finance_reminders", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.finance_action == "remind-draft":
        settings = load_settings(require_gemini_key=True)
        ai_agent = FinanceAdminAgent(
            store=store, gemini_client=_build_gemini_client(settings)
        )
        invoice, draft = ai_agent.draft_payment_reminder(
            invoice_id=args.id,
            nama_pengirim=args.sender or "",
            info_rekening=args.bank or "",
        )
        output = ai_agent.format_reminder_draft(invoice, draft)
        print(output)
        if args.save:
            saved_path = save_markdown_output(f"finance_remind_{args.id}", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.finance_action == "split":
        shares = parse_shares_spec(args.shares)
        result = agent.calculate_profit_split(
            total_pendapatan=args.amount,
            splits=shares,
            biaya_operasional=args.cost,
        )
        output = agent.format_profit_split(result)
        print(output)
        if args.save:
            saved_path = save_markdown_output("finance_split", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.finance_action == "tx-delete":
        removed = store.delete_transaction(args.id)
        print(f"[OK] Transaksi #{removed.id} ({format_rupiah(removed.nominal)}) dihapus.")
        return 0

    if args.finance_action == "invoice-delete":
        removed = store.delete_invoice(args.id)
        print(f"[OK] Tagihan #{removed.id} ({removed.klien}) dihapus.")
        return 0

    if args.finance_action == "reset":
        if not args.yes:
            raise ValueError(
                "Tambahkan flag --yes untuk mengonfirmasi reset seluruh data keuangan ke Rp0."
            )
        store.reset_all()
        print("[OK] Seluruh transaksi & tagihan keuangan berhasil di-reset ke Rp0.")
        return 0

    raise ValueError("Sub-perintah finance tidak dikenali.")


def _read_text_or_file(
    direct_text: str | None,
    file_path: str | None,
    label: str,
    prompt_if_empty: bool = False,
) -> str:
    if direct_text and direct_text.strip():
        return direct_text.strip()
    if file_path:
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f"File {label} tidak ditemukan: {path}")
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Isi file {label} kosong: {path}")
        return content
    if prompt_if_empty:
        print(f"Masukkan {label} (tekan Enter jika selesai):")
        typed = input("> ").strip()
        if typed:
            return typed
    raise ValueError(f"{label.capitalize()} belum diisi.")


def _run_cs_command(args: argparse.Namespace) -> int:
    rate_card_path = Path(args.rate_card) if getattr(args, "rate_card", None) else None

    if args.cs_action == "rate-card":
        content = load_rate_card_and_faq(rate_card_path)
        source_info = (
            str(rate_card_path)
            if rate_card_path
            else (
                str(DEFAULT_RATE_CARD_FILE)
                if DEFAULT_RATE_CARD_FILE.is_file()
                else "Template bawaan (buat data/rate_card.md untuk kustomisasi)"
            )
        )
        print(f"# Rate Card & FAQ Aktif\nSumber: {source_info}\n\n{content}")
        return 0

    settings = load_settings(require_gemini_key=True)
    agent = CSQCAgent(
        gemini_client=_build_gemini_client(settings),
        rate_card_file=rate_card_path,
    )

    if args.cs_action == "reply":
        pesan = _read_text_or_file(
            args.message, args.file, label="pesan calon klien", prompt_if_empty=True
        )
        report = agent.draft_cs_reply(
            pesan_klien=pesan,
            layanan=args.service,
            nama_klien=args.client or "",
            nama_pengirim=args.sender or "",
        )
        output = agent.format_cs_reply(report)
        print(output)
        if args.save:
            saved_path = save_markdown_output("cs_reply", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    if args.cs_action == "qc":
        brief = _read_text_or_file(
            args.brief, args.brief_file, label="brief klien", prompt_if_empty=False
        )
        skrip = _read_text_or_file(
            args.script, args.script_file, label="skrip endorse", prompt_if_empty=False
        )
        report = agent.check_endorse_script(
            brief_klien=brief,
            skrip=skrip,
            nama_brand=args.brand or "",
        )
        output = agent.format_qc_report(report)
        print(output)
        if args.save:
            saved_path = save_markdown_output("cs_qc", output)
            print(f"\nHasil disimpan ke: {saved_path}")
        return 0

    raise ValueError("Sub-perintah cs tidak dikenali.")


def _run_office_command(args: argparse.Namespace) -> int:
    import threading
    import time
    import webbrowser

    import uvicorn

    from office import create_app, get_local_lan_ip

    lan_ip = get_local_lan_ip()
    pc_url = f"http://127.0.0.1:{args.port}"
    phone_url = f"http://{lan_ip}:{args.port}"

    print("=" * 60)
    print("  ZENTIRA HQ — KANTOR VIRTUAL 3D MULTI-AGENT AI")
    print("=" * 60)
    print(f"  Buka di PC           : {pc_url}")
    print(f"  Buka di HP (1 Wi-Fi) : {phone_url}")
    print("  Tekan Ctrl+C di jendela ini untuk menutup kantor.")
    print("=" * 60)

    if not args.no_browser:
        def _open_later() -> None:
            time.sleep(1.2)
            try:
                webbrowser.open(pc_url)
            except OSError:
                pass

        threading.Thread(target=_open_later, daemon=True).start()

    app = create_app(port=args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


def _run_manager_command(args: argparse.Namespace) -> int:
    command_text = _read_text_or_file(
        args.command_text, None, label="perintah untuk Manajer", prompt_if_empty=True
    )
    settings = load_settings(require_gemini_key=True)
    agent = ManagerOrchestratorAgent(gemini_client=_build_gemini_client(settings))
    report = agent.run(command_text)
    output = agent.format_report(report)
    print(output)
    if args.save:
        saved_path = save_markdown_output("manager", output)
        print(f"\nHasil disimpan ke: {saved_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Membangun parser argumen CLI."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Sistem Multi-Agent AI ringan untuk kreator Denn & Miki & jasa web UMKM.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    trend_parser = subparsers.add_parser(
        "trend",
        help="Jalankan Agent 1: Riset Tren Indonesia -> maks. 3 ide cerita Denn & Miki.",
    )
    trend_parser.add_argument(
        "--geo",
        type=str,
        default=None,
        help="Kode wilayah Google Trends (default dari .env, mis. ID).",
    )
    trend_parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Jumlah maksimal item tren RSS yang dipindai (default dari .env).",
    )
    trend_parser.add_argument(
        "--max-ideas",
        type=int,
        default=None,
        help="Jumlah maksimal ide cerita yang dihasilkan, dibatasi 1..3 (default dari .env).",
    )
    trend_parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Hanya ambil dan tampilkan tren mentah dari RSS tanpa memanggil Gemini API.",
    )
    trend_parser.add_argument(
        "--save",
        action="store_true",
        help="Simpan laporan ke folder outputs/ dalam format Markdown.",
    )

    repurpose_parser = subparsers.add_parser(
        "repurpose",
        help="Jalankan Agent 2: Ubah 1 ringkasan video -> paket TikTok, IG Reels, & YT Shorts.",
    )
    repurpose_parser.add_argument(
        "--summary",
        type=str,
        default=None,
        help="Ringkasan cerita/isi 1 video yang ingin di-repurpose.",
    )
    repurpose_parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path file teks/Markdown yang berisi ringkasan video.",
    )
    repurpose_parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Judul kerja video (opsional).",
    )
    repurpose_parser.add_argument(
        "--cta",
        type=str,
        default=None,
        help="CTA khusus atau info endorse yang ingin diselipkan (opsional).",
    )
    repurpose_parser.add_argument(
        "--tone",
        type=str,
        default=None,
        help="Catatan gaya/vibe tambahan (opsional).",
    )
    repurpose_parser.add_argument(
        "--save",
        action="store_true",
        help="Simpan hasil paket 3 platform ke folder outputs/ dalam format Markdown.",
    )

    leads_parser = subparsers.add_parser(
        "leads",
        help="Jalankan Agent 3: Kelola prospek UMKM tanpa website & buat draf penawaran personal.",
    )
    leads_parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Path file JSON penyimpanan prospek opsional (default: data/leads.json).",
    )
    leads_sub = leads_parser.add_subparsers(dest="leads_action", required=True)

    leads_add = leads_sub.add_parser("add", help="Tambah prospek UMKM baru.")
    leads_add.add_argument("--name", required=True, help="Nama usaha UMKM.")
    leads_add.add_argument("--category", required=True, help="Kategori bisnis (mis. Kafe, Bengkel, Laundry).")
    leads_add.add_argument("--city", default="", help="Kota/daerah usaha (opsional).")
    leads_add.add_argument("--contact", default="", help="Nomor WA / akun IG / email (opsional).")
    leads_add.add_argument(
        "--channel",
        default="whatsapp",
        choices=ALLOWED_CHANNELS,
        help="Saluran kontak utama (default: whatsapp).",
    )
    leads_add.add_argument(
        "--has-website",
        action="store_true",
        help="Tandai jika UMKM sudah punya website (default: belum punya website).",
    )
    leads_add.add_argument("--notes", default="", help="Catatan observasi spesifik usaha (opsional).")

    leads_list = leads_sub.add_parser("list", help="Tampilkan daftar prospek UMKM.")
    leads_list.add_argument(
        "--status",
        default=None,
        choices=ALLOWED_STATUSES,
        help="Filter berdasarkan status prospek.",
    )
    leads_list.add_argument(
        "--no-web",
        action="store_true",
        help="Hanya tampilkan UMKM yang belum punya website.",
    )

    leads_status = leads_sub.add_parser("status", help="Perbarui status prospek UMKM.")
    leads_status.add_argument("--id", type=int, required=True, help="ID prospek.")
    leads_status.add_argument(
        "--status",
        required=True,
        choices=ALLOWED_STATUSES,
        help="Status baru prospek.",
    )
    leads_status.add_argument("--notes", default="", help="Catatan tambahan perkembangan (opsional).")

    leads_delete = leads_sub.add_parser("delete", help="Hapus prospek berdasarkan ID.")
    leads_delete.add_argument("--id", type=int, required=True, help="ID prospek yang akan dihapus.")

    leads_import = leads_sub.add_parser("import", help="Impor daftar prospek dari file CSV.")
    leads_import.add_argument("--csv", required=True, help="Path file CSV prospek.")

    leads_discover = leads_sub.add_parser(
        "discover",
        help="Cari prospek UMKM lokal otomatis via OpenStreetMap gratis (filter belum punya website).",
    )
    leads_discover.add_argument(
        "--keyword",
        required=True,
        help="Kata kunci jenis usaha (mis. kopi, bengkel, laundry, barbershop, bakso, salon).",
    )
    leads_discover.add_argument(
        "--city",
        required=True,
        help="Nama kota atau kecamatan target (mis. Bandung, 'Dago, Bandung', Bekasi).",
    )
    leads_discover.add_argument(
        "--radius-km",
        type=float,
        default=5.0,
        help="Radius pencarian dalam kilometer dari pusat lokasi (default: 5.0).",
    )
    leads_discover.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Jumlah maksimal kandidat yang ditampilkan (default: 10).",
    )
    leads_discover.add_argument(
        "--include-with-web",
        action="store_true",
        help="Sertakan juga usaha yang sudah mencantumkan website di OpenStreetMap.",
    )
    leads_discover.add_argument(
        "--include-chains",
        action="store_true",
        help="Sertakan juga jaringan/franchise besar (default: difilter agar fokus UMKM lokal).",
    )
    leads_discover.add_argument(
        "--save-leads",
        action="store_true",
        help="Langsung simpan hasil kandidat ke data/leads.json (otomatis melewati duplikat).",
    )
    leads_discover.add_argument(
        "--save",
        action="store_true",
        help="Simpan laporan pencarian ke folder outputs/ dalam format Markdown.",
    )

    leads_pitch = leads_sub.add_parser(
        "pitch",
        help="Buat draf pesan penawaran personal pakai Gemini untuk 1 prospek.",
    )
    leads_pitch.add_argument("--id", type=int, required=True, help="ID prospek.")
    leads_pitch.add_argument(
        "--offer",
        default="",
        help="Promo/penawaran khusus opsional (mis. 'Gratis contoh konsep halaman depan').",
    )
    leads_pitch.add_argument(
        "--sender",
        default="",
        help="Nama pengirim yang dicantumkan di pesan (opsional).",
    )
    leads_pitch.add_argument(
        "--mark-contacted",
        action="store_true",
        help="Otomatis ubah status prospek menjadi 'dihubungi' setelah draf dibuat.",
    )
    leads_pitch.add_argument(
        "--save",
        action="store_true",
        help="Simpan draf penawaran ke folder outputs/ dalam format Markdown.",
    )

    finance_parser = subparsers.add_parser(
        "finance",
        help="Jalankan Agent 4: Admin Keuangan & Pengingat (kas, DP/pelunasan, bagi hasil).",
    )
    finance_parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Path file JSON penyimpanan keuangan opsional (default: data/finance.json).",
    )
    fin_sub = finance_parser.add_subparsers(dest="finance_action", required=True)

    tx_add = fin_sub.add_parser("tx-add", help="Catat pemasukan atau pengeluaran baru.")
    tx_add.add_argument("--type", required=True, choices=ALLOWED_TX_TYPES, help="Jenis: masuk atau keluar.")
    tx_add.add_argument("--amount", type=int, required=True, help="Nominal dalam Rupiah bulat (mis. 500000).")
    tx_add.add_argument("--category", required=True, help="Kategori (mis. endorse, dp_web, hosting, tools).")
    tx_add.add_argument("--stream", default="umum", choices=ALLOWED_STREAMS, help="Lini usaha (konten/web_umkm/umum).")
    tx_add.add_argument("--date", default="", help="Tanggal YYYY-MM-DD (default: hari ini WIB).")
    tx_add.add_argument("--notes", default="", help="Keterangan tambahan (opsional).")

    tx_list = fin_sub.add_parser("tx-list", help="Lihat daftar transaksi keuangan.")
    tx_list.add_argument("--type", default=None, choices=ALLOWED_TX_TYPES, help="Filter masuk/keluar.")
    tx_list.add_argument("--stream", default=None, choices=ALLOWED_STREAMS, help="Filter lini usaha.")
    tx_list.add_argument("--month", default=None, help="Filter bulan YYYY-MM (mis. 2026-11).")

    inv_add = fin_sub.add_parser("invoice-add", help="Catat proyek & tagihan DP/pelunasan klien.")
    inv_add.add_argument("--client", required=True, help="Nama klien / UMKM / brand endorse.")
    inv_add.add_argument("--project", required=True, help="Nama proyek (mis. Website Katalog / Endorse TikTok).")
    inv_add.add_argument("--total", type=int, required=True, help="Total nilai proyek dalam Rupiah.")
    inv_add.add_argument("--dp", type=int, default=0, help="Nominal DP awal yang sudah diterima (default: 0).")
    inv_add.add_argument("--stream", default="web_umkm", choices=ALLOWED_STREAMS, help="Lini usaha (default: web_umkm).")
    inv_add.add_argument("--due", default="", help="Tanggal jatuh tempo pelunasan YYYY-MM-DD (opsional).")
    inv_add.add_argument("--notes", default="", help="Catatan proyek (opsional).")
    inv_add.add_argument("--no-sync-tx", action="store_true", help="Jangan otomatis catat DP ke riwayat kas.")

    inv_pay = fin_sub.add_parser("invoice-pay", help="Catat pembayaran DP tambahan atau pelunasan klien.")
    inv_pay.add_argument("--id", type=int, required=True, help="ID tagihan klien.")
    inv_pay.add_argument("--amount", type=int, required=True, help="Nominal pembayaran yang diterima.")
    inv_pay.add_argument("--notes", default="", help="Catatan pembayaran (mis. Transfer BCA).")
    inv_pay.add_argument("--no-sync-tx", action="store_true", help="Jangan otomatis catat ke riwayat kas.")

    inv_list = fin_sub.add_parser("invoice-list", help="Lihat daftar tagihan DP/pelunasan klien.")
    inv_list.add_argument("--status", default=None, choices=ALLOWED_INVOICE_STATUSES, help="Filter status.")
    inv_list.add_argument("--unpaid", action="store_true", help="Hanya tampilkan tagihan yang belum lunas.")

    fin_summary = fin_sub.add_parser("summary", help="Tampilkan ringkasan kas & piutang klien.")
    fin_summary.add_argument("--month", default=None, help="Filter bulan YYYY-MM (opsional).")
    fin_summary.add_argument("--stream", default=None, choices=ALLOWED_STREAMS, help="Filter lini usaha (opsional).")
    fin_summary.add_argument("--save", action="store_true", help="Simpan ringkasan ke outputs/.")

    fin_remind = fin_sub.add_parser("remind", help="Cek pengingat tagihan klien mendekati/lewat jatuh tempo.")
    fin_remind.add_argument("--days", type=int, default=7, help="Ambang hari 'segera jatuh tempo' (default: 7).")
    fin_remind.add_argument("--save", action="store_true", help="Simpan daftar pengingat ke outputs/.")

    fin_remind_draft = fin_sub.add_parser(
        "remind-draft",
        help="Buat draf pesan WA pengingat pembayaran sopan pakai Gemini untuk 1 tagihan.",
    )
    fin_remind_draft.add_argument("--id", type=int, required=True, help="ID tagihan klien.")
    fin_remind_draft.add_argument("--sender", default="", help="Nama pengirim (opsional).")
    fin_remind_draft.add_argument("--bank", default="", help="Info rekening/e-wallet tujuan (opsional).")
    fin_remind_draft.add_argument("--save", action="store_true", help="Simpan draf pesan ke outputs/.")

    fin_split = fin_sub.add_parser("split", help="Hitung bagi hasil sederhana setelah biaya operasional.")
    fin_split.add_argument("--amount", type=int, required=True, help="Total pendapatan proyek (Rupiah).")
    fin_split.add_argument("--cost", type=int, default=0, help="Biaya operasional/modal yang dipotong dulu (default: 0).")
    fin_split.add_argument(
        "--shares",
        required=True,
        help="Komposisi bagi hasil (total 100%%), contoh: 'Saya:60,Partner:40'.",
    )
    fin_split.add_argument("--save", action="store_true", help="Simpan perhitungan ke outputs/.")

    fin_tx_del = fin_sub.add_parser("tx-delete", help="Hapus 1 transaksi berdasarkan ID.")
    fin_tx_del.add_argument("--id", type=int, required=True, help="ID transaksi.")

    fin_inv_del = fin_sub.add_parser("invoice-delete", help="Hapus 1 tagihan klien berdasarkan ID.")
    fin_inv_del.add_argument("--id", type=int, required=True, help="ID tagihan.")

    fin_reset = fin_sub.add_parser("reset", help="Reset seluruh data keuangan kembali ke Rp0.")
    fin_reset.add_argument("--yes", action="store_true", help="Konfirmasi reset seluruh kas & tagihan.")

    cs_parser = subparsers.add_parser(
        "cs",
        help="Jalankan Agent 5: Asisten CS (balasan calon klien) & QC Brief Endorse.",
    )
    cs_sub = cs_parser.add_subparsers(dest="cs_action", required=True)

    cs_reply = cs_sub.add_parser(
        "reply",
        help="Buat draf balasan calon klien berdasarkan Rate Card & FAQ.",
    )
    cs_reply.add_argument("--message", default=None, help="Isi pesan dari calon klien.")
    cs_reply.add_argument("--file", default=None, help="Path file teks berisi pesan calon klien.")
    cs_reply.add_argument(
        "--service",
        default="auto",
        choices=ALLOWED_CS_SERVICES,
        help="Fokus layanan: auto, endorse, atau web_umkm (default: auto).",
    )
    cs_reply.add_argument("--client", default="", help="Nama calon klien/brand (opsional).")
    cs_reply.add_argument("--sender", default="", help="Nama pengirim/admin (opsional).")
    cs_reply.add_argument(
        "--rate-card",
        default=None,
        help="Path file Markdown rate card/FAQ kustom (opsional, default: data/rate_card.md).",
    )
    cs_reply.add_argument("--save", action="store_true", help="Simpan draf balasan ke outputs/.")

    cs_qc = cs_sub.add_parser(
        "qc",
        help="Cek apakah skrip endorse sudah mencakup semua poin brief klien.",
    )
    cs_qc.add_argument("--brief", default=None, help="Teks poin-poin brief dari klien.")
    cs_qc.add_argument("--brief-file", default=None, help="Path file teks berisi brief klien.")
    cs_qc.add_argument("--script", default=None, help="Teks skrip animasi Denn & Miki.")
    cs_qc.add_argument("--script-file", default=None, help="Path file teks berisi skrip endorse.")
    cs_qc.add_argument("--brand", default="", help="Nama brand/klien endorse (opsional).")
    cs_qc.add_argument("--save", action="store_true", help="Simpan hasil audit QC ke outputs/.")

    cs_rc = cs_sub.add_parser(
        "rate-card",
        help="Tampilkan isi Rate Card & FAQ aktif yang dipakai Asisten CS.",
    )
    cs_rc.add_argument("--rate-card", default=None, help="Path file rate card kustom (opsional).")

    office_parser = subparsers.add_parser(
        "office",
        help="Buka Kantor Virtual 3D Voxel di browser PC & HP (semua 5 Agent dalam 1 ruangan 3D).",
    )
    office_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Alamat bind server (default: 0.0.0.0 agar bisa diakses dari HP satu Wi-Fi).",
    )
    office_parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port server (otomatis membaca env PORT bila di cloud, default lokal: 8000).",
    )
    office_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Jangan otomatis membuka browser PC saat server menyala.",
    )

    mgr_parser = subparsers.add_parser(
        "manager",
        help="Jalankan Agent Manajer (Orchestrator): 1 perintah bos → delegasi otomatis ke Agent 1–5.",
    )
    mgr_parser.add_argument(
        "--command",
        dest="command_text",
        default=None,
        help="Perintah bebas untuk Manajer (mis. 'Floatee baru ACC, siapin buat tayang dan tagih pelunasan').",
    )
    mgr_parser.add_argument("--save", action="store_true", help="Simpan laporan gabungan ke outputs/.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Fungsi utama CLI."""
    configure_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "trend":
            return _run_trend_command(args)
        if args.command == "repurpose":
            return _run_repurpose_command(args)
        if args.command == "leads":
            return _run_leads_command(args)
        if args.command == "finance":
            return _run_finance_command(args)
        if args.command == "cs":
            return _run_cs_command(args)
        if args.command == "office":
            return _run_office_command(args)
        if args.command == "manager":
            return _run_manager_command(args)
        parser.print_help()
        return 1
    except (
        ConfigError,
        TrendFetchError,
        GeminiClientError,
        LeadDiscoveryError,
        LeadNotFoundError,
        FinanceNotFoundError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
