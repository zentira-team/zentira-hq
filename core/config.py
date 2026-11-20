"""Loader konfigurasi terpusat dari environment variables dan file .env."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_PLACEHOLDER_MARKERS = (
    "masukkan_api_key",
    "your_api_key",
    "changeme",
    "placeholder",
    "isi_api_key",
)


class ConfigError(ValueError):
    """Dilempar ketika konfigurasi wajib tidak tersedia atau tidak valid."""


@dataclass(frozen=True)
class Settings:
    """Konfigurasi aplikasi yang dipakai bersama oleh seluruh agent."""

    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_models: tuple[str, ...] = ("gemini-3.5-flash-lite", "gemini-3.8-flash")
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_models: tuple[str, ...] = ("qwen/qwen3.8-27b", "openai/gpt-oss-20b")
    ai_primary_provider: str = "gemini"
    trends_geo: str = "ID"
    trends_max_items: int = 20
    trends_max_ideas: int = 3
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    office_password: str = ""
    custom_agent_names: str = ""


def _is_placeholder_key(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS)


def _parse_int(
    env_map: Mapping[str, str],
    key: str,
    default: int,
    minimum: int,
    maximum: int | None = None,
) -> int:
    raw = env_map.get(key, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ConfigError(
            f"Nilai {key}='{raw}' di .env harus berupa angka bulat."
        ) from exc

    clamped = max(minimum, parsed)
    if maximum is not None:
        clamped = min(maximum, clamped)
    return clamped


def _parse_model_list(
    env_map: Mapping[str, str],
    key: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    if key not in env_map:
        return default
    raw = env_map[key].strip()
    if not raw or raw.lower() == "none":
        return ()
    models: list[str] = []
    for part in raw.split(","):
        cleaned = part.strip()
        if cleaned and cleaned not in models:
            models.append(cleaned)
    return tuple(models)


def load_settings(
    require_gemini_key: bool = True,
    load_dotenv_file: bool = True,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Memuat konfigurasi dari .env (bila diaktifkan) dan environment variables."""
    if environ is None:
        if load_dotenv_file:
            # override=True agar perubahan API key di .env (misal baru menempel GROQ_API_KEY)
            # langsung terbaca otomatis tanpa wajib restart server.
            load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
        env_map: Mapping[str, str] = os.environ
    else:
        env_map = environ

    raw_gemini_key = env_map.get("GEMINI_API_KEY", "").strip()
    gemini_api_key = "" if _is_placeholder_key(raw_gemini_key) else raw_gemini_key

    raw_groq_key = env_map.get("GROQ_API_KEY", "").strip()
    groq_api_key = "" if _is_placeholder_key(raw_groq_key) else raw_groq_key

    if require_gemini_key and not gemini_api_key and not groq_api_key:
        raise ConfigError(
            "GEMINI_API_KEY (atau GROQ_API_KEY) belum diisi dengan API key yang valid.\n"
            "Buka file .env di root proyek, lalu isi GEMINI_API_KEY "
            "(https://aistudio.google.com/apikey) dan/atau GROQ_API_KEY (https://console.groq.com/keys)."
        )

    gemini_model = env_map.get("GEMINI_MODEL", "").strip() or "gemini-3.5-flash"
    gemini_fallback_models = _parse_model_list(
        env_map,
        "GEMINI_FALLBACK_MODELS",
        ("gemini-3.5-flash-lite", "gemini-3.8-flash"),
    )
    groq_model = env_map.get("GROQ_MODEL", "").strip() or "openai/gpt-oss-120b"
    groq_fallback_models = _parse_model_list(
        env_map,
        "GROQ_FALLBACK_MODELS",
        ("qwen/qwen3.8-27b", "openai/gpt-oss-20b"),
    )
    raw_primary = env_map.get("AI_PRIMARY_PROVIDER", "gemini").strip().lower()
    ai_primary_provider = raw_primary if raw_primary in ("gemini", "groq") else "gemini"

    trends_geo = (env_map.get("TRENDS_GEO", "").strip() or "ID").upper()
    trends_max_items = _parse_int(env_map, "TRENDS_MAX_ITEMS", default=20, minimum=1)
    trends_max_ideas = _parse_int(
        env_map, "TRENDS_MAX_IDEAS", default=3, minimum=1, maximum=3
    )

    return Settings(
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        gemini_fallback_models=gemini_fallback_models,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        groq_fallback_models=groq_fallback_models,
        ai_primary_provider=ai_primary_provider,
        trends_geo=trends_geo,
        trends_max_items=trends_max_items,
        trends_max_ideas=trends_max_ideas,
        telegram_bot_token=env_map.get("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=env_map.get("TELEGRAM_CHAT_ID", "").strip(),
        office_password=env_map.get("OFFICE_PASSWORD", "").strip(),
        custom_agent_names=env_map.get("CUSTOM_AGENT_NAMES", "").strip(),
    )
