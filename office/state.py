"""Manajemen status real-time 5 karyawan AI & Inbox Bos untuk Kantor Virtual 3D."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Any

from core.config import PROJECT_ROOT
from core.formatter import timestamp_wib

DEFAULT_OFFICE_PROFILE_FILE = PROJECT_ROOT / "data" / "office_profile.json"

AGENTS_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "manager",
        "number": 0,
        "name": "Zeno",
        "role": "Manajer (Orchestrator)",
        "subtitle": "1 perintah bos → otomatis delegasi ke karyawan AI",
        "color": "#f43f5e",
        "idle_bubble": "Siap terima 1 perintah & delegasikan ke seluruh tim!",
    },
    {
        "id": "trend",
        "number": 1,
        "name": "Risa",
        "role": "Riset Tren",
        "subtitle": "Google Trends ID → maks. 3 ide Denn & Miki",
        "color": "#38bdf8",
        "idle_bubble": "Ngopi dulu sambil mantau tren Indonesia...",
    },
    {
        "id": "repurpose",
        "number": 2,
        "name": "Repo",
        "role": "Repurposer 3 Platform",
        "subtitle": "1 ringkasan video → TikTok, IG Reels, YT Shorts",
        "color": "#f472b6",
        "idle_bubble": "Siap ubah ringkasan video jadi paket 3 platform!",
    },
    {
        "id": "leads",
        "number": 3,
        "name": "Lido",
        "role": "Lead Hunter UMKM",
        "subtitle": "Cari prospek UMKM tanpa web & buat draf WA",
        "color": "#34d399",
        "idle_bubble": "Siap berburu prospek UMKM lokal hari ini!",
    },
    {
        "id": "finance",
        "number": 4,
        "name": "Fina",
        "role": "Admin Keuangan",
        "subtitle": "Catat kas, DP/pelunasan, pengingat, bagi hasil",
        "color": "#fbbf24",
        "idle_bubble": "Buku kas rapi, siap cek DP & bagi hasil.",
    },
    {
        "id": "cs",
        "number": 5,
        "name": "Caca",
        "role": "Asisten CS & QC",
        "subtitle": "Balasan calon klien & audit QC brief endorse",
        "color": "#a78bfa",
        "idle_bubble": "Rate card & checklist QC brief sudah siap!",
    },
)


class OfficeStateManager:
    """Menyimpan status live karyawan AI, profil nama custom, Inbox Bos, dan broadcast SSE."""

    def __init__(
        self,
        max_inbox: int = 25,
        profile_path: Path | None = None,
        auto_idle_seconds: float = 10.0,
    ) -> None:
        self._lock = threading.Lock()
        self._max_inbox = max_inbox
        self._profile_path = profile_path or DEFAULT_OFFICE_PROFILE_FILE
        self._auto_idle_seconds = max(0.0, float(auto_idle_seconds))
        self._inbox_seq = 0
        self._subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]] = []
        self._agents: dict[str, dict[str, Any]] = {}
        self._inbox: list[dict[str, Any]] = []
        self._idle_timers: dict[str, threading.Timer] = {}
        self._agent_tokens: dict[str, int] = {}
        self._office_mode: str = "work"
        self._mode_seq: int = 0
        self._mode_updated: str = timestamp_wib()

        saved_names = self._load_custom_names()
        for meta in AGENTS_CATALOG:
            custom_name = saved_names.get(meta["id"], "").strip()
            self._agent_tokens[meta["id"]] = 0
            self._agents[meta["id"]] = {
                **meta,
                "name": custom_name or meta["name"],
                "status": "idle",
                "bubble": meta["idle_bubble"],
                "last_task": "",
                "last_updated": "",
                "unread": False,
            }

    def _load_custom_names(self) -> dict[str, str]:
        result: dict[str, str] = {}
        # Fallback dari env var CUSTOM_AGENT_NAMES (misal: manager=Denn,trend=ucok,repurpose=ali)
        raw_env = os.environ.get("CUSTOM_AGENT_NAMES", "").strip()
        if raw_env:
            for pair in raw_env.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k_clean, v_clean = k.strip(), v.strip()
                    if k_clean and v_clean:
                        result[k_clean] = v_clean[:24]

        if not self._profile_path.is_file():
            return result
        try:
            data = json.loads(self._profile_path.read_text(encoding="utf-8"))
            raw_names = data.get("names", {})
            if isinstance(raw_names, dict):
                for k, v in raw_names.items():
                    if isinstance(v, str) and v.strip():
                        result[str(k)] = v.strip()[:24]
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        return result

    def _save_custom_names_locked(self) -> None:
        self._profile_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "names": {
                meta["id"]: self._agents[meta["id"]]["name"]
                for meta in AGENTS_CATALOG
            }
        }
        self._profile_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update_agent_names(self, names: dict[str, str]) -> dict[str, Any]:
        """Memperbarui nama custom satu atau beberapa agent dan menyimpannya permanen."""
        if not isinstance(names, dict) or not names:
            raise ValueError("Daftar nama agent tidak boleh kosong.")

        with self._lock:
            for agent_id, raw_name in names.items():
                if agent_id not in self._agents:
                    continue
                cleaned = str(raw_name).strip()
                if not cleaned:
                    raise ValueError(
                        f"Nama untuk agent '{agent_id}' tidak boleh kosong."
                    )
                if len(cleaned) > 24:
                    raise ValueError(
                        f"Nama '{cleaned}' terlalu panjang (maksimal 24 karakter)."
                    )
                self._agents[agent_id]["name"] = cleaned
            self._save_custom_names_locked()

        self._broadcast()
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        """Mengembalikan salinan state lengkap seluruh kantor."""
        with self._lock:
            agents_list = [dict(self._agents[m["id"]]) for m in AGENTS_CATALOG]
            inbox_copy = [dict(item) for item in self._inbox]
            unread_count = sum(1 for item in inbox_copy if item.get("unread"))
        return {
            "agents": agents_list,
            "inbox": inbox_copy,
            "unread_count": unread_count,
            "office_mode": self._office_mode,
            "mode_seq": self._mode_seq,
            "mode_updated": self._mode_updated,
            "server_time": timestamp_wib(),
        }

    def _notify_locked(self, payload: dict[str, Any]) -> None:
        stale: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]] = []
        for loop, queue in self._subscribers:
            if loop.is_closed():
                stale.append((loop, queue))
                continue
            try:
                loop.call_soon_threadsafe(self._put_nowait_safe, queue, payload)
            except RuntimeError:
                stale.append((loop, queue))
        for item in stale:
            if item in self._subscribers:
                self._subscribers.remove(item)

    @staticmethod
    def _put_nowait_safe(queue: asyncio.Queue[dict[str, Any]], payload: dict[str, Any]) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass

    def _broadcast(self) -> None:
        snap = self.snapshot()
        with self._lock:
            self._notify_locked(snap)

    def _cancel_idle_timer_locked(self, agent_id: str) -> None:
        timer = self._idle_timers.pop(agent_id, None)
        if timer is not None:
            timer.cancel()

    def _schedule_auto_idle_locked(self, agent_id: str, expected_token: int) -> None:
        self._cancel_idle_timer_locked(agent_id)
        if self._auto_idle_seconds <= 0:
            return
        timer = threading.Timer(
            self._auto_idle_seconds,
            self._auto_reset_idle,
            args=(agent_id, expected_token),
        )
        timer.daemon = True
        self._idle_timers[agent_id] = timer
        timer.start()

    def _auto_reset_idle(self, agent_id: str, expected_token: int) -> None:
        changed = False
        with self._lock:
            if self._agent_tokens.get(agent_id) != expected_token:
                return
            agent = self._agents.get(agent_id)
            if not agent or agent["status"] not in ("done", "error"):
                return
            self._idle_timers.pop(agent_id, None)
            agent["status"] = "idle"
            agent["bubble"] = agent["idle_bubble"]
            agent["unread"] = False
            agent["last_updated"] = timestamp_wib()
            changed = True
        if changed:
            self._broadcast()

    def set_office_mode(self, mode: str) -> dict[str, Any]:
        """Mengubah mode kantor 3D: 'work' (Masuk), 'meeting' (Meeting), atau 'holiday' (Libur)."""
        normalized = str(mode).strip().lower()
        if normalized not in ("work", "meeting", "holiday"):
            raise ValueError("Mode kantor harus salah satu dari: work, meeting, holiday.")
        with self._lock:
            self._office_mode = normalized
            self._mode_seq += 1
            self._mode_updated = timestamp_wib()
            if normalized in ("meeting", "holiday"):
                for aid, agent in self._agents.items():
                    if agent["status"] in ("done", "error"):
                        self._agent_tokens[aid] = self._agent_tokens.get(aid, 0) + 1
                        self._cancel_idle_timer_locked(aid)
                        agent["status"] = "idle"
                        agent["bubble"] = agent["idle_bubble"]
                        agent["unread"] = False
        self._broadcast()
        return self.snapshot()

    def set_working(self, agent_id: str, bubble: str, task: str = "") -> None:
        with self._lock:
            if self._office_mode == "holiday":
                self._office_mode = "work"
                self._mode_seq += 1
                self._mode_updated = timestamp_wib()
            self._agent_tokens[agent_id] = self._agent_tokens.get(agent_id, 0) + 1
            self._cancel_idle_timer_locked(agent_id)
            agent = self._agents[agent_id]
            agent["status"] = "working"
            agent["bubble"] = bubble
            if task:
                agent["last_task"] = task
            agent["last_updated"] = timestamp_wib()
        self._broadcast()

    def set_done(
        self,
        agent_id: str,
        bubble: str,
        title: str,
        markdown: str,
        add_to_inbox: bool = True,
        model_used: str = "",
    ) -> dict[str, Any] | None:
        now = timestamp_wib()
        inbox_item: dict[str, Any] | None = None
        with self._lock:
            token = self._agent_tokens.get(agent_id, 0) + 1
            self._agent_tokens[agent_id] = token
            agent = self._agents[agent_id]
            agent["status"] = "done"
            agent["bubble"] = bubble
            agent["last_task"] = title
            agent["last_updated"] = now
            agent["unread"] = add_to_inbox

            if add_to_inbox:
                self._inbox_seq += 1
                inbox_item = {
                    "id": self._inbox_seq,
                    "agent_id": agent_id,
                    "agent_name": agent["name"],
                    "agent_role": agent["role"],
                    "color": agent["color"],
                    "title": title,
                    "markdown": markdown,
                    "model_used": model_used,
                    "timestamp": now,
                    "unread": True,
                }
                self._inbox.insert(0, inbox_item)
                self._inbox = self._inbox[: self._max_inbox]
            self._schedule_auto_idle_locked(agent_id, token)
        self._broadcast()
        return inbox_item

    def set_error(self, agent_id: str, message: str) -> None:
        upper = message.upper()
        if "503" in upper or "UNAVAILABLE" in upper:
            friendly = "Server Gemini sedang padat sebentar (503). Coba klik ulang!"
        elif "429" in upper or "RESOURCE_EXHAUSTED" in upper:
            friendly = "Limit kecepatan Gemini tercapai (429). Tunggu 1 menit lalu coba lagi."
        else:
            friendly = f"Ups, ada kendala: {message.splitlines()[0][:85]}"
        with self._lock:
            token = self._agent_tokens.get(agent_id, 0) + 1
            self._agent_tokens[agent_id] = token
            agent = self._agents[agent_id]
            agent["status"] = "error"
            agent["bubble"] = friendly
            agent["last_updated"] = timestamp_wib()
            self._schedule_auto_idle_locked(agent_id, token)
        self._broadcast()

    def set_idle(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            if agent_id not in self._agents:
                raise KeyError(f"Agent '{agent_id}' tidak ditemukan.")
            self._agent_tokens[agent_id] = self._agent_tokens.get(agent_id, 0) + 1
            self._cancel_idle_timer_locked(agent_id)
            agent = self._agents[agent_id]
            agent["status"] = "idle"
            agent["bubble"] = agent["idle_bubble"]
            agent["unread"] = False
            agent["last_updated"] = timestamp_wib()
        self._broadcast()
        return self.snapshot()

    def set_all_idle(self) -> dict[str, Any]:
        with self._lock:
            for agent_id, agent in self._agents.items():
                if agent["status"] in ("done", "error"):
                    self._agent_tokens[agent_id] = self._agent_tokens.get(agent_id, 0) + 1
                    self._cancel_idle_timer_locked(agent_id)
                    agent["status"] = "idle"
                    agent["bubble"] = agent["idle_bubble"]
                    agent["unread"] = False
                    agent["last_updated"] = timestamp_wib()
        self._broadcast()
        return self.snapshot()

    def delete_inbox_item(self, item_id: int) -> dict[str, Any]:
        """Menghapus satu laporan dari Inbox Bos berdasarkan ID."""
        with self._lock:
            idx = next(
                (i for i, item in enumerate(self._inbox) if item.get("id") == item_id),
                None,
            )
            if idx is None:
                raise KeyError(f"Laporan inbox #{item_id} tidak ditemukan.")
            self._inbox.pop(idx)
        self._broadcast()
        return self.snapshot()

    def clear_inbox(self) -> dict[str, Any]:
        """Mengosongkan seluruh riwayat laporan di Inbox Bos."""
        with self._lock:
            self._inbox.clear()
            for agent in self._agents.values():
                agent["unread"] = False
        self._broadcast()
        return self.snapshot()

    def mark_read(self, agent_id: str | None = None) -> None:
        with self._lock:
            if agent_id and agent_id in self._agents:
                self._agents[agent_id]["unread"] = False
                if self._agents[agent_id]["status"] in ("done", "error"):
                    self._agent_tokens[agent_id] = self._agent_tokens.get(agent_id, 0) + 1
                    self._cancel_idle_timer_locked(agent_id)
                    self._agents[agent_id]["status"] = "idle"
                    self._agents[agent_id]["bubble"] = self._agents[agent_id]["idle_bubble"]
                for item in self._inbox:
                    if item["agent_id"] == agent_id:
                        item["unread"] = False
            else:
                for aid, agent in self._agents.items():
                    agent["unread"] = False
                    if agent["status"] in ("done", "error"):
                        self._agent_tokens[aid] = self._agent_tokens.get(aid, 0) + 1
                        self._cancel_idle_timer_locked(aid)
                        agent["status"] = "idle"
                        agent["bubble"] = agent["idle_bubble"]
                for item in self._inbox:
                    item["unread"] = False
        self._broadcast()

    def subscribe(self) -> tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=20)
        with self._lock:
            self._subscribers.append((loop, queue))
        return loop, queue

    def unsubscribe(
        self, sub: tuple[asyncio.AbstractEventLoop, asyncio.Queue[dict[str, Any]]]
    ) -> None:
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)
