"""Wrapper klien AI terpadu: Google GenAI (Gemini) + Cadangan Otomatis Groq Cloud."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

import httpx
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_WHISPER_MODELS = ("whisper-large-v3-turbo", "whisper-large-v3")
MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024  # Batas ukuran file Groq Whisper (25 MB)

_AUTH_ERROR_MARKERS = ("401", "403", "UNAUTHENTICATED", "PERMISSION_DENIED", "INVALID_API_KEY")
_FALLBACK_ERROR_MARKERS = (
    "503",
    "429",
    "404",
    "500",
    "502",
    "504",
    "UNAVAILABLE",
    "RESOURCE_EXHAUSTED",
    "NOT_FOUND",
    "RATE_LIMIT",
    "TIMEOUT",
)


class GeminiClientError(RuntimeError):
    """Dilempar ketika seluruh pemanggilan atau parsing respons AI gagal."""


class _GroqAPIError(RuntimeError):
    """Error internal dari Groq Cloud API beserta kode HTTP."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Groq HTTP {status_code}: {message}")
        self.status_code = status_code
        self.code = status_code


def _is_fallback_eligible(exc: Exception) -> bool:
    """Menentukan apakah error layak dicoba ulang dengan model/provider cadangan."""
    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status_code in (401, 403):
        return False
    if status_code in (404, 429, 500, 502, 503, 504):
        return True

    message = str(exc).upper()
    if any(marker in message for marker in _AUTH_ERROR_MARKERS):
        return False
    return any(marker in message for marker in _FALLBACK_ERROR_MARKERS)


def _strip_json_fences(raw_text: str) -> str:
    """Membersihkan markdown fence ```json ... ``` agar valid untuk Pydantic."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text


class GeminiClient:
    """Klien bersama multi-provider (Gemini utama + Groq Cloud cadangan otomatis)."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-3.5-flash",
        fallback_models: Sequence[str] = (),
        client: Any | None = None,
        retry_delay: float = 1.5,
        sleep_fn: Callable[[float], None] = time.sleep,
        groq_api_key: str = "",
        groq_model: str = "openai/gpt-oss-120b",
        groq_fallback_models: Sequence[str] = ("qwen/qwen3.8-27b", "openai/gpt-oss-20b"),
        primary_provider: str = "gemini",
        groq_http_post: Callable[..., Any] | None = None,
    ) -> None:
        cleaned_gemini = (api_key or "").strip()
        cleaned_groq = (groq_api_key or "").strip()

        if not cleaned_gemini and client is None and not cleaned_groq:
            raise GeminiClientError("API key Gemini atau Groq tidak boleh kosong.")

        self.api_key = cleaned_gemini
        self.model = model.strip() or "gemini-3.5-flash"
        self.fallback_models = tuple(
            m.strip() for m in fallback_models if m and m.strip()
        )
        self.groq_api_key = cleaned_groq
        self.groq_model = groq_model.strip() or "openai/gpt-oss-120b"
        self.groq_fallback_models = tuple(
            m.strip() for m in groq_fallback_models if m and m.strip()
        )
        self.primary_provider = (
            "groq" if str(primary_provider).strip().lower() == "groq" else "gemini"
        )
        self.last_used_provider = self.primary_provider
        self.last_used_model = self.model if self.primary_provider == "gemini" else f"groq:{self.groq_model}"
        self._retry_delay = max(0.0, retry_delay)
        self._sleep = sleep_fn
        self._groq_post = groq_http_post or httpx.post

        if client is not None:
            self._client: Any | None = client
        elif cleaned_gemini:
            self._client = genai.Client(
                api_key=cleaned_gemini,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=2)
                ),
            )
        else:
            self._client = None

    def _candidate_models(self) -> list[str]:
        candidates: list[str] = []
        for candidate in (self.model, *self.fallback_models):
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        return candidates

    def _groq_candidate_models(self) -> list[str]:
        candidates: list[str] = []
        for candidate in (self.groq_model, *self.groq_fallback_models):
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        return candidates

    def _provider_order(self) -> list[str]:
        has_gemini = self._client is not None
        has_groq = bool(self.groq_api_key)
        order = ("groq", "gemini") if self.primary_provider == "groq" else ("gemini", "groq")
        return [
            p
            for p in order
            if (p == "gemini" and has_gemini) or (p == "groq" and has_groq)
        ]

    # --- GEMINI PROVIDER ---

    def _generate_gemini(
        self,
        prompt: str,
        config: types.GenerateContentConfig,
        max_rounds: int = 2,
    ) -> types.GenerateContentResponse:
        assert self._client is not None
        candidates = self._candidate_models()
        last_exc: Exception | None = None
        last_model = self.model

        for round_idx in range(max(1, max_rounds)):
            saw_transient = False
            for idx, model_name in enumerate(candidates):
                last_model = model_name
                try:
                    response = self._client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                    self.last_used_provider = "gemini"
                    self.last_used_model = model_name
                    return response
                except Exception as exc:
                    last_exc = exc
                    eligible = _is_fallback_eligible(exc)
                    if not eligible:
                        raise GeminiClientError(
                            f"Gagal memanggil Gemini API ({model_name}): "
                            f"{exc.__class__.__name__}: {exc}"
                        ) from exc
                    if any(
                        k in str(exc).upper()
                        for k in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
                    ):
                        saw_transient = True
                    if idx < len(candidates) - 1:
                        continue

            if round_idx < max_rounds - 1 and saw_transient and self._retry_delay > 0:
                self._sleep(self._retry_delay)
                continue
            break

        raise GeminiClientError(
            f"Gagal memanggil Gemini API ({last_model}): "
            f"{last_exc.__class__.__name__ if last_exc else 'Error'}: {last_exc}"
        ) from last_exc

    def _generate_text_gemini(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
        max_rounds: int,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )
        response = self._generate_gemini(prompt, config, max_rounds=max_rounds)
        text = (response.text or "").strip()
        if not text:
            raise GeminiClientError("Gemini mengembalikan respons teks kosong.")
        return text

    def _generate_structured_gemini(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None,
        temperature: float,
        max_rounds: int,
    ) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
        )
        response = self._generate_gemini(prompt, config, max_rounds=max_rounds)

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_schema):
            return parsed

        raw_text = (response.text or "").strip()
        if not raw_text:
            raise GeminiClientError(
                "Gemini mengembalikan respons terstruktur yang kosong."
            )

        try:
            return response_schema.model_validate_json(raw_text)
        except ValidationError as exc:
            raise GeminiClientError(
                f"Respons Gemini tidak sesuai skema {response_schema.__name__}: {exc}"
            ) from exc

    # --- GROQ CLOUD PROVIDER (OpenAI-compatible REST via httpx) ---

    def _call_groq_once(
        self,
        model_name: str,
        messages: list[dict[str, str]],
        temperature: float,
        json_mode: bool = False,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = self._groq_post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=45.0,
            )
        except Exception as exc:
            raise _GroqAPIError(503, f"Koneksi Groq bermasalah: {exc}") from exc

        if resp.status_code >= 400:
            err_msg = resp.text[:250]
            try:
                err_data = resp.json()
                if isinstance(err_data, dict) and isinstance(err_data.get("error"), dict):
                    err_msg = str(err_data["error"].get("message") or err_msg)
            except Exception:
                pass
            raise _GroqAPIError(resp.status_code, err_msg)

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise GeminiClientError(f"Groq ({model_name}) mengembalikan pilihan kosong.")
        content = str(choices[0].get("message", {}).get("content") or "").strip()
        if not content:
            raise GeminiClientError(f"Groq ({model_name}) mengembalikan respons kosong.")
        return content

    def _generate_text_groq(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        candidates = self._groq_candidate_models()
        last_exc: Exception | None = None
        last_model = self.groq_model

        for idx, model_name in enumerate(candidates):
            last_model = model_name
            try:
                text = self._call_groq_once(
                    model_name=model_name,
                    messages=messages,
                    temperature=temperature,
                    json_mode=False,
                )
                self.last_used_provider = "groq"
                self.last_used_model = f"groq:{model_name}"
                return text
            except Exception as exc:
                last_exc = exc
                if not _is_fallback_eligible(exc) or idx >= len(candidates) - 1:
                    break

        raise GeminiClientError(
            f"Gagal memanggil Groq API ({last_model}): "
            f"{last_exc.__class__.__name__ if last_exc else 'Error'}: {last_exc}"
        ) from last_exc

    def _generate_structured_groq(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None,
        temperature: float,
    ) -> T:
        schema_json = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        schema_rule = (
            "ATURAN FORMAT WAJIB: Kembalikan HANYA 1 objek JSON valid tanpa markdown fence, "
            "tanpa komentar, dan tanpa teks tambahan di luar JSON. "
            f"Struktur JSON harus 100% mengikuti JSON Schema berikut:\n{schema_json}"
        )
        full_system = (
            f"{system_instruction}\n\n{schema_rule}"
            if system_instruction
            else schema_rule
        )
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ]

        candidates = self._groq_candidate_models()
        last_exc: Exception | None = None
        last_model = self.groq_model

        for idx, model_name in enumerate(candidates):
            last_model = model_name
            try:
                raw_text = self._call_groq_once(
                    model_name=model_name,
                    messages=messages,
                    temperature=temperature,
                    json_mode=True,
                )
                cleaned = _strip_json_fences(raw_text)
                parsed = response_schema.model_validate_json(cleaned)
                self.last_used_provider = "groq"
                self.last_used_model = f"groq:{model_name}"
                return parsed
            except ValidationError as exc:
                last_exc = exc
                if idx < len(candidates) - 1:
                    continue
                raise GeminiClientError(
                    f"Respons Groq ({model_name}) tidak sesuai skema {response_schema.__name__}: {exc}"
                ) from exc
            except Exception as exc:
                last_exc = exc
                if not _is_fallback_eligible(exc) or idx >= len(candidates) - 1:
                    break

        raise GeminiClientError(
            f"Gagal memanggil Groq API ({last_model}): "
            f"{last_exc.__class__.__name__ if last_exc else 'Error'}: {last_exc}"
        ) from last_exc

    def transcribe_audio(
        self,
        file_bytes: bytes,
        filename: str = "media.mp4",
        content_type: str = "application/octet-stream",
        language: str = "id",
        whisper_models: Sequence[str] = DEFAULT_WHISPER_MODELS,
    ) -> tuple[str, str]:
        """Mentranskrip file audio/video mentah menjadi teks via Groq Whisper gratis."""
        if not self.groq_api_key:
            raise GeminiClientError(
                "GROQ_API_KEY belum diisi di .env. Fitur transkrip video/audio otomatis "
                "membutuhkan API key Groq Cloud gratis (https://console.groq.com/keys)."
            )
        if not file_bytes:
            raise ValueError("File audio/video yang diunggah kosong.")
        if len(file_bytes) > MAX_AUDIO_UPLOAD_BYTES:
            size_mb = len(file_bytes) / (1024 * 1024)
            raise ValueError(
                f"Ukuran file terlalu besar ({size_mb:.1f} MB). Maksimal 25 MB untuk transkrip otomatis."
            )

        safe_name = (filename or "media.mp4").strip().replace("\\", "/").split("/")[-1] or "media.mp4"
        models = [m.strip() for m in whisper_models if m and m.strip()] or list(DEFAULT_WHISPER_MODELS)
        headers = {"Authorization": f"Bearer {self.groq_api_key}"}

        last_exc: Exception | None = None
        last_model = models[0]
        for idx, model_name in enumerate(models):
            last_model = model_name
            try:
                resp = self._groq_post(
                    GROQ_AUDIO_URL,
                    headers=headers,
                    files={"file": (safe_name, file_bytes, content_type or "application/octet-stream")},
                    data={
                        "model": model_name,
                        "language": (language or "id").strip() or "id",
                        "response_format": "json",
                    },
                    timeout=90.0,
                )
            except Exception as exc:
                last_exc = _GroqAPIError(503, f"Koneksi Groq Whisper bermasalah: {exc}")
                if idx < len(models) - 1:
                    continue
                break

            if resp.status_code >= 400:
                err_msg = resp.text[:250]
                try:
                    err_data = resp.json()
                    if isinstance(err_data, dict) and isinstance(err_data.get("error"), dict):
                        err_msg = str(err_data["error"].get("message") or err_msg)
                except Exception:
                    pass
                err = _GroqAPIError(resp.status_code, err_msg)
                last_exc = err
                if not _is_fallback_eligible(err) or idx >= len(models) - 1:
                    break
                continue

            data = resp.json()
            transcript = str(data.get("text") or "").strip() if isinstance(data, dict) else ""
            if not transcript:
                last_exc = GeminiClientError(
                    "Audio/video tidak mengandung suara dialog yang bisa ditranskrip."
                )
                break
            return transcript, f"groq:{model_name}"

        raise GeminiClientError(
            f"Gagal mentranskrip media via Groq Whisper ({last_model}): "
            f"{last_exc.__class__.__name__ if last_exc else 'Error'}: {last_exc}"
        ) from last_exc

    # --- PUBLIC UNIFIED API ---

    def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Menghasilkan teks bebas (otomatis failover Gemini <-> Groq jika tersedia)."""
        providers = self._provider_order()
        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            has_backup = idx < len(providers) - 1
            try:
                if provider == "gemini":
                    return self._generate_text_gemini(
                        prompt,
                        system_instruction,
                        temperature,
                        max_rounds=1 if has_backup else 2,
                    )
                return self._generate_text_groq(prompt, system_instruction, temperature)
            except GeminiClientError as exc:
                last_exc = exc
                if has_backup:
                    continue
                raise
        raise last_exc or GeminiClientError("Tidak ada provider AI yang dikonfigurasi.")

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> T:
        """Menghasilkan output JSON Pydantic (otomatis failover Gemini <-> Groq jika tersedia)."""
        providers = self._provider_order()
        last_exc: Exception | None = None
        for idx, provider in enumerate(providers):
            has_backup = idx < len(providers) - 1
            try:
                if provider == "gemini":
                    return self._generate_structured_gemini(
                        prompt,
                        response_schema,
                        system_instruction,
                        temperature,
                        max_rounds=1 if has_backup else 2,
                    )
                return self._generate_structured_groq(
                    prompt, response_schema, system_instruction, temperature
                )
            except GeminiClientError as exc:
                last_exc = exc
                if has_backup:
                    continue
                raise
        raise last_exc or GeminiClientError("Tidak ada provider AI yang dikonfigurasi.")
