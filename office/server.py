"""Backend FastAPI untuk Kantor Virtual 3D Voxel yang menghubungkan seluruh 5 Agent AI."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agents.cs_qc import CSQCAgent, DEFAULT_RATE_CARD_FILE, load_rate_card_and_faq
from agents.finance_admin import (
    FinanceAdminAgent,
    FinanceNotFoundError,
    FinanceStore,
    format_rupiah,
    parse_shares_spec,
)
from agents.lead_hunter import (
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
from core.config import ConfigError, load_settings
from core.formatter import save_markdown_output
from core.gemini_client import GeminiClient, GeminiClientError
from office.state import OfficeStateManager

STATIC_DIR = Path(__file__).resolve().parent / "static"


def get_local_lan_ip() -> str:
    """Mendeteksi alamat IP Wi-Fi/LAN lokal PC agar bisa dibuka dari browser HP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip:
                return ip
    except OSError:
        pass
    return "127.0.0.1"


# --- Request Schemas ---

class TrendRunRequest(BaseModel):
    geo: str = "ID"
    max_items: int = Field(default=20, ge=1, le=50)
    max_ideas: int = Field(default=3, ge=1, le=3)
    fetch_only: bool = False


class RepurposeRunRequest(BaseModel):
    ringkasan: str
    judul_kerja: str = ""
    cta_tambahan: str = ""
    catatan_gaya: str = ""


class LeadAddRequest(BaseModel):
    nama_usaha: str
    kategori: str
    kota: str = ""
    kontak: str = ""
    saluran: str = "whatsapp"
    punya_website: bool = False
    catatan: str = ""


class LeadStatusRequest(BaseModel):
    status: str
    catatan_tambahan: str = ""


class LeadDiscoverRequest(BaseModel):
    keyword: str
    city: str
    radius_km: float = Field(default=5.0, ge=1.0, le=25.0)
    limit: int = Field(default=10, ge=1, le=30)
    save_leads: bool = True
    include_with_web: bool = False
    include_chains: bool = False


class LeadPitchRequest(BaseModel):
    offer: str = ""
    sender: str = ""
    mark_contacted: bool = False


class FinanceTxRequest(BaseModel):
    jenis: str
    nominal: int
    kategori: str
    sumber: str = "umum"
    keterangan: str = ""
    tanggal: str = ""


class FinanceInvoiceRequest(BaseModel):
    klien: str
    proyek: str
    total_harga: int
    dp: int = 0
    sumber: str = "web_umkm"
    jatuh_tempo: str = ""
    catatan: str = ""


class FinancePayRequest(BaseModel):
    nominal: int
    catatan: str = ""


class FinanceSplitRequest(BaseModel):
    total_pendapatan: int
    biaya_operasional: int = 0
    shares: str


class FinanceRemindDraftRequest(BaseModel):
    sender: str = ""
    bank: str = ""


class CSReplyRequest(BaseModel):
    pesan_klien: str
    layanan: str = "auto"
    nama_klien: str = ""
    nama_pengirim: str = ""


class CSQCRequest(BaseModel):
    brief_klien: str
    skrip: str
    nama_brand: str = ""


class RateCardUpdateRequest(BaseModel):
    content: str


class SaveOutputRequest(BaseModel):
    prefix: str = "laporan"
    content: str


class InboxReadRequest(BaseModel):
    agent_id: str | None = None


class AgentNamesUpdateRequest(BaseModel):
    names: dict[str, str]


class ManagerRunRequest(BaseModel):
    perintah: str


class OfficeModeRequest(BaseModel):
    mode: str


class LoginRequest(BaseModel):
    password: str


class BackupImportRequest(BaseModel):
    leads: dict[str, Any] | None = None
    finance: dict[str, Any] | None = None
    names: dict[str, str] | None = None
    rate_card: str | None = None


_AUTH_COOKIE_NAME = "zentira_auth"
_PUBLIC_API_PATHS = frozenset(
    {"/api/health", "/api/auth/status", "/api/auth/login", "/api/auth/logout"}
)


def _compute_auth_token(password: str) -> str:
    return hmac.new(
        password.encode("utf-8"),
        b"zentira-hq-session-v1",
        hashlib.sha256,
    ).hexdigest()


def _default_gemini_factory() -> GeminiClient:
    settings = load_settings(require_gemini_key=True)
    return GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        fallback_models=settings.gemini_fallback_models,
        groq_api_key=settings.groq_api_key,
        groq_model=settings.groq_model,
        groq_fallback_models=settings.groq_fallback_models,
        primary_provider=settings.ai_primary_provider,
    )


_ALLOWED_MEDIA_EXTENSIONS = frozenset(
    {".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mpeg", ".mpga"}
)


def _client_model_label(client: Any) -> str:
    return str(getattr(client, "last_used_model", "") or "").strip()


def _http_error_from_exc(exc: Exception) -> HTTPException:
    if isinstance(exc, (LeadNotFoundError, FinanceNotFoundError)):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (ConfigError, ValueError)):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, (TrendFetchError, LeadDiscoveryError, GeminiClientError)):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=500, detail=f"Kesalahan internal: {exc}")


def create_app(
    lead_store: LeadStore | None = None,
    finance_store: FinanceStore | None = None,
    gemini_factory: Callable[[], GeminiClient] | None = None,
    trend_fetcher: Callable[[str, int], list[Any]] = fetch_google_trends,
    lead_discoverer: Callable[..., list[Any]] = discover_umkm_leads,
    rate_card_file: Path | None = None,
    output_dir: Path | None = None,
    profile_path: Path | None = None,
    state_manager: OfficeStateManager | None = None,
    office_password: str | None = None,
    port: int = 8000,
) -> FastAPI:
    """Membuat instance FastAPI Kantor Virtual 3D yang terhubung ke seluruh Agent."""
    app = FastAPI(title="Zentira — Kantor Virtual 3D Multi-Agent AI")

    leads_db = lead_store or LeadStore()
    finance_db = finance_store or FinanceStore()
    make_gemini = gemini_factory or _default_gemini_factory
    rc_path = rate_card_file or DEFAULT_RATE_CARD_FILE
    state = state_manager or OfficeStateManager(profile_path=profile_path)
    lan_ip = get_local_lan_ip()

    def _active_password() -> str:
        if office_password is not None:
            return office_password.strip()
        return os.environ.get("OFFICE_PASSWORD", "").strip()

    def _is_request_authenticated(request: Request) -> bool:
        pw = _active_password()
        if not pw:
            return True
        cookie_val = request.cookies.get(_AUTH_COOKIE_NAME, "")
        if not cookie_val:
            return False
        return hmac.compare_digest(cookie_val, _compute_auth_token(pw))

    @app.middleware("http")
    async def auth_gate_middleware(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and path not in _PUBLIC_API_PATHS:
            if not _is_request_authenticated(request):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Akses terkunci. Silakan login terlebih dahulu."},
                )
        return await call_next(request)

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    async def api_health() -> dict[str, Any]:
        return {"ok": True, "service": "zentira-hq"}

    @app.get("/api/auth/status")
    async def api_auth_status(request: Request) -> dict[str, Any]:
        pw = _active_password()
        return {
            "protected": bool(pw),
            "authenticated": _is_request_authenticated(request),
        }

    @app.post("/api/auth/login")
    async def api_auth_login(req: LoginRequest) -> JSONResponse:
        pw = _active_password()
        if not pw:
            return JSONResponse({"ok": True, "protected": False})
        if not hmac.compare_digest(req.password.strip(), pw):
            raise HTTPException(status_code=401, detail="Password salah. Silakan coba lagi.")
        resp = JSONResponse({"ok": True, "protected": True})
        resp.set_cookie(
            key=_AUTH_COOKIE_NAME,
            value=_compute_auth_token(pw),
            httponly=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
        )
        return resp

    @app.post("/api/auth/logout")
    async def api_auth_logout() -> JSONResponse:
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(_AUTH_COOKIE_NAME)
        return resp

    @app.get("/api/backup/export")
    async def api_backup_export() -> dict[str, Any]:
        leads_data = (
            json.loads(leads_db.file_path.read_text(encoding="utf-8"))
            if leads_db.file_path.is_file()
            else {"next_id": 1, "leads": []}
        )
        finance_data = (
            json.loads(finance_db.file_path.read_text(encoding="utf-8"))
            if finance_db.file_path.is_file()
            else {"next_tx_id": 1, "next_invoice_id": 1, "transactions": [], "invoices": []}
        )
        snap = state.snapshot()
        names_map = {a["id"]: a["name"] for a in snap["agents"]}
        rate_card_text = rc_path.read_text(encoding="utf-8") if rc_path.is_file() else ""
        return {
            "version": 1,
            "exported_at": snap["server_time"],
            "names": names_map,
            "leads": leads_data,
            "finance": finance_data,
            "rate_card": rate_card_text,
        }

    @app.post("/api/backup/import")
    async def api_backup_import(req: BackupImportRequest) -> dict[str, Any]:
        try:
            if isinstance(req.leads, dict):
                leads_db.file_path.parent.mkdir(parents=True, exist_ok=True)
                leads_db.file_path.write_text(
                    json.dumps(req.leads, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            if isinstance(req.finance, dict):
                finance_db.file_path.parent.mkdir(parents=True, exist_ok=True)
                finance_db.file_path.write_text(
                    json.dumps(req.finance, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            if isinstance(req.rate_card, str) and req.rate_card.strip():
                rc_path.parent.mkdir(parents=True, exist_ok=True)
                rc_path.write_text(req.rate_card.strip() + "\n", encoding="utf-8")
            if isinstance(req.names, dict) and req.names:
                state.update_agent_names(req.names)
            snap = state.snapshot()
            snap["urls"] = {
                "pc": f"http://127.0.0.1:{port}",
                "phone": f"http://{lan_ip}:{port}",
            }
            return {"ok": True, "state": snap}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.get("/api/state")
    async def api_state() -> dict[str, Any]:
        snap = state.snapshot()
        snap["urls"] = {
            "pc": f"http://127.0.0.1:{port}",
            "phone": f"http://{lan_ip}:{port}",
        }
        return snap

    @app.get("/api/events")
    async def api_events() -> StreamingResponse:
        async def event_stream():
            sub = state.subscribe()
            _, queue = sub
            try:
                initial = state.snapshot()
                yield f"data: {json.dumps(initial, ensure_ascii=False)}\n\n"
                while True:
                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
            finally:
                state.unsubscribe(sub)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/api/inbox/read")
    async def api_mark_read(req: InboxReadRequest) -> dict[str, Any]:
        state.mark_read(req.agent_id)
        return {"ok": True}

    @app.delete("/api/inbox/{item_id}")
    async def api_delete_inbox_item(item_id: int) -> dict[str, Any]:
        try:
            snap = state.delete_inbox_item(item_id)
            snap["urls"] = {
                "pc": f"http://127.0.0.1:{port}",
                "phone": f"http://{lan_ip}:{port}",
            }
            return snap
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete("/api/inbox")
    async def api_clear_inbox() -> dict[str, Any]:
        snap = state.clear_inbox()
        snap["urls"] = {
            "pc": f"http://127.0.0.1:{port}",
            "phone": f"http://{lan_ip}:{port}",
        }
        return snap

    @app.post("/api/agents/idle-all")
    async def api_agents_idle_all() -> dict[str, Any]:
        snap = state.set_all_idle()
        snap["urls"] = {
            "pc": f"http://127.0.0.1:{port}",
            "phone": f"http://{lan_ip}:{port}",
        }
        return snap

    @app.post("/api/agents/{agent_id}/idle")
    async def api_agent_idle(agent_id: str) -> dict[str, Any]:
        try:
            snap = state.set_idle(agent_id)
            snap["urls"] = {
                "pc": f"http://127.0.0.1:{port}",
                "phone": f"http://{lan_ip}:{port}",
            }
            return snap
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/office/mode")
    async def api_office_mode(req: OfficeModeRequest) -> dict[str, Any]:
        try:
            snap = state.set_office_mode(req.mode)
            snap["urls"] = {
                "pc": f"http://127.0.0.1:{port}",
                "phone": f"http://{lan_ip}:{port}",
            }
            return snap
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.put("/api/agents/names")
    async def api_update_agent_names(req: AgentNamesUpdateRequest) -> dict[str, Any]:
        try:
            snap = state.update_agent_names(req.names)
            snap["urls"] = {
                "pc": f"http://127.0.0.1:{port}",
                "phone": f"http://{lan_ip}:{port}",
            }
            return snap
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/save-output")
    async def api_save_output(req: SaveOutputRequest) -> dict[str, Any]:
        if not req.content.strip():
            raise HTTPException(status_code=400, detail="Konten laporan kosong.")
        safe_prefix = "".join(c for c in req.prefix if c.isalnum() or c in ("_", "-")) or "laporan"
        saved = save_markdown_output(safe_prefix, req.content, output_dir=output_dir)
        return {"ok": True, "path": str(saved), "filename": saved.name}

    # --- AGENT 1: RISET TREN ---
    @app.post("/api/agents/trend/run")
    async def api_trend_run(req: TrendRunRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            geo = req.geo.strip().upper() or "ID"
            if req.fetch_only:
                state.set_working("trend", f"Membuka Google Trends RSS ({geo})...", "Ambil tren mentah")
                trends = trend_fetcher(geo, req.max_items)
                lines = [f"# Tren Mentah Google Trends ({geo})", f"Total: {len(trends)}", ""]
                for i, t in enumerate(trends, start=1):
                    traffic = f" ({t.approx_traffic})" if t.approx_traffic else ""
                    lines.append(f"{i}. {t.title}{traffic}")
                md = "\n".join(lines)
                state.set_done(
                    "trend",
                    f"{len(trends)} tren mentah ({geo}) siap dilihat!",
                    f"Tren Mentah {geo} ({len(trends)} topik)",
                    md,
                )
                return {
                    "mode": "fetch_only",
                    "trends": [t.model_dump() for t in trends],
                    "markdown": md,
                }

            state.set_working("trend", f"Membaca Google Trends ({geo})...", "Riset tren harian")

            def _step_fetcher(g: str, limit: int):
                items = trend_fetcher(g, limit)
                state.set_working(
                    "trend",
                    f"Menyaring {len(items)} tren jadi maks. {req.max_ideas} ide Denn & Miki...",
                )
                return items

            client = make_gemini()
            agent = TrendResearcherAgent(
                gemini_client=client,
                geo=geo,
                max_items=req.max_items,
                max_ideas=req.max_ideas,
                fetcher=_step_fetcher,
            )
            report = agent.run()
            md = agent.format_report(report)
            used_model = _client_model_label(client)
            state.set_done(
                "trend",
                f"{len(report.ide_cerita)} ide cerita Denn & Miki siap!",
                f"Riset Tren {geo} ({len(report.ide_cerita)} ide)",
                md,
                model_used=used_model,
            )
            return {
                "mode": "full",
                "report": report.model_dump(),
                "markdown": md,
                "model_used": used_model,
            }

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("trend", str(exc))
            raise _http_error_from_exc(exc) from exc

    # --- AGENT 2: REPURPOSER 3 PLATFORM ---
    @app.post("/api/agents/repurpose/run")
    async def api_repurpose_run(req: RepurposeRunRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            state.set_working(
                "repurpose",
                "Meracik copy TikTok, IG Reels & YT Shorts...",
                req.judul_kerja or "Repurpose 3 platform",
            )
            client = make_gemini()
            agent = RepurposerAgent(gemini_client=client)
            brief = VideoBrief(
                ringkasan=req.ringkasan,
                judul_kerja=req.judul_kerja,
                cta_tambahan=req.cta_tambahan,
                catatan_gaya=req.catatan_gaya,
            )
            report = agent.run(brief)
            md = agent.format_report(report)
            used_model = _client_model_label(client)
            title = req.judul_kerja.strip() or "Paket 3 Platform"
            state.set_done(
                "repurpose",
                "Paket TikTok, IG Reels & Shorts siap disalin!",
                f"Repurpose: {title}",
                md,
                model_used=used_model,
            )
            return {"report": report.model_dump(), "markdown": md, "model_used": used_model}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("repurpose", str(exc))
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/repurpose/media")
    async def api_repurpose_media(
        request: Request,
        judul_kerja: str = Query(default=""),
        cta_tambahan: str = Query(default=""),
        transcribe_only: bool = Query(default=False),
    ) -> dict[str, Any]:
        raw_name = unquote(request.headers.get("x-file-name", "video.mp4")).strip()
        safe_name = Path(raw_name.replace("\\", "/")).name or "video.mp4"
        ext = Path(safe_name).suffix.lower()
        if ext and ext not in _ALLOWED_MEDIA_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Format file '{ext}' tidak didukung. Gunakan file video/audio: "
                    ".mp4, .mov, .webm, .mp3, .wav, .m4a, atau .ogg."
                ),
            )
        file_bytes = await request.body()
        content_type = request.headers.get("content-type", "application/octet-stream")

        def _worker() -> dict[str, Any]:
            state.set_working(
                "repurpose",
                f"Mendengarkan & transkrip '{safe_name}' (Groq Whisper)...",
                f"Transkrip: {safe_name}",
            )
            client = make_gemini()
            transcript, whisper_model = client.transcribe_audio(
                file_bytes=file_bytes,
                filename=safe_name,
                content_type=content_type,
                language="id",
            )
            if transcribe_only:
                state.set_done(
                    "repurpose",
                    f"Transkrip '{safe_name}' siap diedit!",
                    f"Transkrip: {safe_name}",
                    transcript,
                    add_to_inbox=False,
                    model_used=whisper_model,
                )
                return {
                    "mode": "transcribe_only",
                    "filename": safe_name,
                    "transcript": transcript,
                    "model_used": whisper_model,
                }

            state.set_working(
                "repurpose",
                "Transkrip selesai! Meracik copy TikTok, IG Reels & YT Shorts...",
                judul_kerja.strip() or Path(safe_name).stem,
            )
            agent = RepurposerAgent(gemini_client=client)
            brief = VideoBrief(
                ringkasan=transcript,
                judul_kerja=judul_kerja.strip() or Path(safe_name).stem,
                cta_tambahan=cta_tambahan.strip(),
            )
            report = agent.run(brief)
            body_md = agent.format_report(report)
            full_md = (
                f"> **Transkrip Audio/Video (`{safe_name}`):**\n"
                f"> {transcript}\n\n"
                f"{body_md}"
            )
            llm_model = _client_model_label(client)
            used_model = f"{whisper_model} + {llm_model}" if llm_model else whisper_model
            title = judul_kerja.strip() or Path(safe_name).stem
            state.set_done(
                "repurpose",
                "Transkrip & paket 3 platform siap disalin!",
                f"Video → 3 Platform: {title}",
                full_md,
                model_used=used_model,
            )
            return {
                "mode": "full",
                "filename": safe_name,
                "transcript": transcript,
                "report": report.model_dump(),
                "markdown": full_md,
                "model_used": used_model,
            }

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("repurpose", str(exc))
            raise _http_error_from_exc(exc) from exc

    # --- AGENT 3: LEAD HUNTER UMKM ---
    @app.get("/api/agents/leads/list")
    async def api_leads_list(
        status: str | None = Query(default=None),
        no_web: bool = Query(default=False),
    ) -> dict[str, Any]:
        try:
            leads = leads_db.list_leads(status=status, only_without_website=no_web)
            return {"leads": [item.model_dump() for item in leads]}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/leads/add")
    async def api_leads_add(req: LeadAddRequest) -> dict[str, Any]:
        try:
            lead = leads_db.add_lead(
                nama_usaha=req.nama_usaha,
                kategori=req.kategori,
                kota=req.kota,
                kontak=req.kontak,
                saluran=req.saluran,
                punya_website=req.punya_website,
                catatan=req.catatan,
            )
            state.set_done(
                "leads",
                f"Prospek '{lead.nama_usaha}' dicatat!",
                f"Prospek baru: {lead.nama_usaha}",
                f"Prospek #{lead.id} **{lead.nama_usaha}** ({lead.kategori}) ditambahkan.",
                add_to_inbox=False,
            )
            return {"lead": lead.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.patch("/api/agents/leads/{lead_id}/status")
    async def api_leads_status(lead_id: int, req: LeadStatusRequest) -> dict[str, Any]:
        try:
            updated = leads_db.update_status(
                lead_id=lead_id,
                new_status=req.status,
                catatan_tambahan=req.catatan_tambahan,
            )
            return {"lead": updated.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.delete("/api/agents/leads/{lead_id}")
    async def api_leads_delete(lead_id: int) -> dict[str, Any]:
        try:
            removed = leads_db.delete_lead(lead_id)
            return {"removed": removed.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/leads/discover")
    async def api_leads_discover(req: LeadDiscoverRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            state.set_working(
                "leads",
                f"Memindai peta UMKM '{req.keyword}' di {req.city}...",
                f"Cari UMKM: {req.keyword} ({req.city})",
            )
            found = lead_discoverer(
                keyword=req.keyword,
                city=req.city,
                radius_km=req.radius_km,
                limit=req.limit,
                only_without_website=not req.include_with_web,
                exclude_chains=not req.include_chains,
            )
            agent = LeadHunterAgent(store=leads_db)
            md = agent.format_discovered_leads(req.keyword, req.city, found)
            saved_leads = []
            skipped = 0
            if req.save_leads and found:
                saved_leads, skipped = agent.save_discovered_leads(found)

            bubble = (
                f"Ketemu {len(found)} UMKM! ({len(saved_leads)} disimpan)"
                if req.save_leads
                else f"Ketemu {len(found)} kandidat UMKM di {req.city}!"
            )
            state.set_done(
                "leads",
                bubble,
                f"Prospek OSM: {req.keyword} ({req.city})",
                md,
            )
            return {
                "discovered": [item.model_dump() for item in found],
                "saved_count": len(saved_leads),
                "skipped_count": skipped,
                "markdown": md,
            }

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("leads", str(exc))
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/leads/{lead_id}/pitch")
    async def api_leads_pitch(lead_id: int, req: LeadPitchRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            lead = leads_db.get_lead(lead_id)
            state.set_working(
                "leads",
                f"Menulis pesan personal untuk {lead.nama_usaha}...",
                f"Pitch UMKM: {lead.nama_usaha}",
            )
            client = make_gemini()
            agent = LeadHunterAgent(store=leads_db, gemini_client=client)
            report = agent.draft_outreach(
                lead_id=lead_id,
                penawaran_khusus=req.offer,
                nama_pengirim=req.sender,
            )
            md = agent.format_outreach_report(report)
            used_model = _client_model_label(client)
            if req.mark_contacted:
                leads_db.update_status(lead_id, "dihubungi")
            state.set_done(
                "leads",
                f"Pesan penawaran {lead.nama_usaha} siap dikirim!",
                f"Pitch WA/DM: {lead.nama_usaha}",
                md,
                model_used=used_model,
            )
            return {"report": report.model_dump(), "markdown": md, "model_used": used_model}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("leads", str(exc))
            raise _http_error_from_exc(exc) from exc

    # --- AGENT 4: ADMIN KEUANGAN & PENGINGAT ---
    @app.get("/api/agents/finance/overview")
    async def api_finance_overview(
        month: str | None = Query(default=None),
        stream: str | None = Query(default=None),
        days: int = Query(default=7, ge=1, le=90),
    ) -> dict[str, Any]:
        try:
            agent = FinanceAdminAgent(store=finance_db)
            summary = agent.get_summary(month=month, sumber=stream)
            txs = finance_db.list_transactions(sumber=stream, month=month)
            invs = finance_db.list_invoices()
            reminders = agent.get_reminders(within_days=days)
            return {
                "summary": summary.model_dump(),
                "summary_markdown": agent.format_summary(summary),
                "transactions": [tx.model_dump() for tx in reversed(txs)],
                "invoices": [
                    {**inv.model_dump(), "sisa_tagihan": inv.sisa_tagihan}
                    for inv in reversed(invs)
                ],
                "reminders": [
                    {
                        **r.model_dump(),
                        "invoice": {
                            **r.invoice.model_dump(),
                            "sisa_tagihan": r.invoice.sisa_tagihan,
                        },
                    }
                    for r in reminders
                ],
                "reminders_markdown": agent.format_reminders(reminders),
            }
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/tx")
    async def api_finance_tx(req: FinanceTxRequest) -> dict[str, Any]:
        try:
            tx = finance_db.add_transaction(
                jenis=req.jenis,
                nominal=req.nominal,
                kategori=req.kategori,
                sumber=req.sumber,
                keterangan=req.keterangan,
                tanggal=req.tanggal,
            )
            state.set_done(
                "finance",
                f"Catat {tx.jenis} {format_rupiah(tx.nominal)} selesai!",
                f"Kas {tx.jenis}: {format_rupiah(tx.nominal)}",
                f"Transaksi #{tx.id}: `{tx.jenis.upper()}` {format_rupiah(tx.nominal)} ({tx.sumber}/{tx.kategori})",
                add_to_inbox=False,
            )
            return {"transaction": tx.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/invoice")
    async def api_finance_invoice(req: FinanceInvoiceRequest) -> dict[str, Any]:
        try:
            inv, tx = finance_db.add_invoice(
                klien=req.klien,
                proyek=req.proyek,
                total_harga=req.total_harga,
                dp=req.dp,
                sumber=req.sumber,
                jatuh_tempo=req.jatuh_tempo,
                catatan=req.catatan,
            )
            state.set_done(
                "finance",
                f"Tagihan {inv.klien} ({inv.status}) dicatat!",
                f"Tagihan: {inv.klien}",
                f"Tagihan #{inv.id} {inv.klien} — Sisa {format_rupiah(inv.sisa_tagihan)}",
                add_to_inbox=False,
            )
            return {
                "invoice": {**inv.model_dump(), "sisa_tagihan": inv.sisa_tagihan},
                "transaction": tx.model_dump() if tx else None,
            }
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/invoice/{invoice_id}/pay")
    async def api_finance_pay(invoice_id: int, req: FinancePayRequest) -> dict[str, Any]:
        try:
            inv, tx = finance_db.record_payment(
                invoice_id=invoice_id,
                nominal=req.nominal,
                catatan=req.catatan,
            )
            state.set_done(
                "finance",
                f"Pembayaran {inv.klien} dicatat ({inv.status})!",
                f"Bayar Tagihan #{inv.id}: {inv.klien}",
                f"Pembayaran {format_rupiah(req.nominal)} diterima. Status: **{inv.status}**.",
            )
            return {
                "invoice": {**inv.model_dump(), "sisa_tagihan": inv.sisa_tagihan},
                "transaction": tx.model_dump() if tx else None,
            }
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/split")
    async def api_finance_split(req: FinanceSplitRequest) -> dict[str, Any]:
        try:
            agent = FinanceAdminAgent(store=finance_db)
            shares = parse_shares_spec(req.shares)
            result = agent.calculate_profit_split(
                total_pendapatan=req.total_pendapatan,
                splits=shares,
                biaya_operasional=req.biaya_operasional,
            )
            md = agent.format_profit_split(result)
            state.set_done(
                "finance",
                f"Bagi hasil {format_rupiah(result.laba_bersih)} selesai dihitung!",
                f"Bagi Hasil: {format_rupiah(result.laba_bersih)}",
                md,
            )
            return {"result": result.model_dump(), "markdown": md}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/invoice/{invoice_id}/remind-draft")
    async def api_finance_remind_draft(
        invoice_id: int, req: FinanceRemindDraftRequest
    ) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            inv = finance_db.get_invoice(invoice_id)
            state.set_working(
                "finance",
                f"Menyusun pesan pengingat sopan untuk {inv.klien}...",
                f"Pengingat WA: {inv.klien}",
            )
            client = make_gemini()
            agent = FinanceAdminAgent(store=finance_db, gemini_client=client)
            invoice, draft = agent.draft_payment_reminder(
                invoice_id=invoice_id,
                nama_pengirim=req.sender,
                info_rekening=req.bank,
            )
            md = agent.format_reminder_draft(invoice, draft)
            used_model = _client_model_label(client)
            state.set_done(
                "finance",
                f"Pesan pengingat untuk {invoice.klien} siap kirim!",
                f"Pengingat WA: {invoice.klien}",
                md,
                model_used=used_model,
            )
            return {
                "invoice": {**invoice.model_dump(), "sisa_tagihan": invoice.sisa_tagihan},
                "draft": draft.model_dump(),
                "markdown": md,
                "model_used": used_model,
            }

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("finance", str(exc))
            raise _http_error_from_exc(exc) from exc

    # --- AGENT 5: ASISTEN CS & QC BRIEF ---
    @app.get("/api/agents/cs/rate-card")
    async def api_cs_get_rate_card() -> dict[str, Any]:
        is_custom = rc_path.is_file()
        content = load_rate_card_and_faq(rc_path if is_custom else None)
        return {
            "content": content,
            "is_custom": is_custom,
            "path": str(rc_path),
        }

    @app.put("/api/agents/cs/rate-card")
    async def api_cs_save_rate_card(req: RateCardUpdateRequest) -> dict[str, Any]:
        cleaned = req.content.strip()
        if not cleaned:
            raise HTTPException(status_code=400, detail="Isi Rate Card & FAQ tidak boleh kosong.")
        rc_path.parent.mkdir(parents=True, exist_ok=True)
        rc_path.write_text(cleaned + "\n", encoding="utf-8")
        return {"ok": True, "path": str(rc_path)}

    @app.post("/api/agents/cs/reply")
    async def api_cs_reply(req: CSReplyRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            state.set_working(
                "cs",
                "Membaca Rate Card & menyusun balasan ramah...",
                "Balas calon klien",
            )
            client = make_gemini()
            agent = CSQCAgent(
                gemini_client=client,
                rate_card_file=rc_path if rc_path.is_file() else None,
            )
            report = agent.draft_cs_reply(
                pesan_klien=req.pesan_klien,
                layanan=req.layanan,
                nama_klien=req.nama_klien,
                nama_pengirim=req.nama_pengirim,
            )
            md = agent.format_cs_reply(report)
            used_model = _client_model_label(client)
            state.set_done(
                "cs",
                f"Balasan CS ({report.kategori_klien}) siap kirim!",
                f"Balasan CS ({report.kategori_klien})",
                md,
                model_used=used_model,
            )
            return {"report": report.model_dump(), "markdown": md, "model_used": used_model}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("cs", str(exc))
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/cs/qc")
    async def api_cs_qc(req: CSQCRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            brand_label = req.nama_brand.strip() or "Endorse"
            state.set_working(
                "cs",
                f"Mengecek poin brief {brand_label} di skrip...",
                f"QC Brief: {brand_label}",
            )
            client = make_gemini()
            agent = CSQCAgent(gemini_client=client)
            report = agent.check_endorse_script(
                brief_klien=req.brief_klien,
                skrip=req.skrip,
                nama_brand=req.nama_brand,
            )
            md = agent.format_qc_report(report)
            used_model = _client_model_label(client)
            state.set_done(
                "cs",
                f"QC {brand_label}: {report.status_keseluruhan} ({report.skor_persen}%)",
                f"QC Brief: {brand_label} ({report.status_keseluruhan})",
                md,
                model_used=used_model,
            )
            return {"report": report.model_dump(), "markdown": md, "model_used": used_model}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("cs", str(exc))
            raise _http_error_from_exc(exc) from exc

    # --- FINANCE DELETE & RESET ---
    @app.delete("/api/agents/finance/tx/{tx_id}")
    async def api_finance_delete_tx(tx_id: int) -> dict[str, Any]:
        try:
            removed = finance_db.delete_transaction(tx_id)
            return {"removed": removed.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.delete("/api/agents/finance/invoice/{invoice_id}")
    async def api_finance_delete_invoice(invoice_id: int) -> dict[str, Any]:
        try:
            removed = finance_db.delete_invoice(invoice_id)
            return {"removed": removed.model_dump()}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    @app.post("/api/agents/finance/reset")
    async def api_finance_reset() -> dict[str, Any]:
        try:
            finance_db.reset_all()
            state.set_done(
                "finance",
                "Buku kas & tagihan berhasil di-reset ke Rp0!",
                "Reset Buku Kas",
                "Seluruh transaksi dan tagihan keuangan telah dikosongkan ke Rp0.",
                add_to_inbox=False,
            )
            return {"ok": True}
        except Exception as exc:
            raise _http_error_from_exc(exc) from exc

    # --- AGENT 6: MANAJER (ORCHESTRATOR) ---
    @app.post("/api/agents/manager/run")
    async def api_manager_run(req: ManagerRunRequest) -> dict[str, Any]:
        def _worker() -> dict[str, Any]:
            def _on_event(agent_id: str, ev_type: str, msg: str) -> None:
                if ev_type == "working":
                    state.set_working(agent_id, msg, msg)
                elif ev_type == "done":
                    state.set_done(
                        agent_id,
                        msg,
                        msg,
                        msg,
                        add_to_inbox=False,
                    )
                elif ev_type == "error":
                    state.set_error(agent_id, msg)

            client = make_gemini()
            agent = ManagerOrchestratorAgent(
                gemini_client=client,
                lead_store=leads_db,
                finance_store=finance_db,
                trend_fetcher=trend_fetcher,
                lead_discoverer=lead_discoverer,
                rate_card_file=rc_path if rc_path.is_file() else None,
                on_agent_event=_on_event,
            )
            report = agent.run(req.perintah)
            md = agent.format_report(report)
            used_model = _client_model_label(client)
            ok_count = sum(1 for r in report.hasil_delegasi if r.berhasil)
            total_count = len(report.hasil_delegasi)
            state.set_done(
                "manager",
                f"{ok_count}/{total_count} delegasi selesai — laporan siap di Inbox!",
                f"Manajer: {req.perintah.strip()[:48]}",
                md,
                model_used=used_model,
            )
            return {"report": report.model_dump(), "markdown": md, "model_used": used_model}

        try:
            return await asyncio.to_thread(_worker)
        except Exception as exc:
            state.set_error("manager", str(exc))
            raise _http_error_from_exc(exc) from exc

    return app
