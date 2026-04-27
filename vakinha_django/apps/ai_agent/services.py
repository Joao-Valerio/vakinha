from __future__ import annotations

import base64
import logging
import os
import time
from typing import Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from agno.exceptions import ModelProviderError, ModelRateLimitError
except ImportError:  # pragma: no cover
    ModelProviderError = Exception  # type: ignore
    ModelRateLimitError = type("ModelRateLimitError", (Exception,), {})  # type: ignore

# Modelo Gemini (agno 2.x + google-genai). Ajuste no .env: GEMINI_MODEL=gemini-2.0-flash
_default_gemini_id = "gemini-2.0-flash"


def _agno_postgres_url() -> str:
    u = (os.environ.get("DATABASE_URL") or "").strip()
    if u.startswith("postgres"):
        return u
    return ""


def get_agno_db():
    """
    Sessão/histórico do agente (agno 2.x). Usa a mesma URL do Django (Neon) ou SQLite local.
    """
    pg = _agno_postgres_url()
    if pg:
        from agno.db.postgres import PostgresDb
        return PostgresDb(db_url=pg, create_schema=True)

    db = settings.DATABASES.get("default", {})
    if "sqlite" in (db.get("ENGINE") or ""):
        from pathlib import Path
        from agno.db.sqlite import SqliteDb
        name = db.get("NAME", "")
        path = Path(name) if not isinstance(name, Path) else name
        return SqliteDb(db_url=f"sqlite:///{path.as_posix()}")

    logger.warning("Nenhum banco adequado para Agno: use DATABASE_URL (Neon) ou SQLite.")
    return None


def create_agent(session_id: str):
    from agno.agent import Agent
    from agno.models.google import Gemini
    from .tools import SYSTEM_PROMPT, build_tools_for_session

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada no .env")

    model_id = os.environ.get("GEMINI_MODEL", _default_gemini_id).strip() or _default_gemini_id
    tools = build_tools_for_session(session_id)
    db = get_agno_db()
    # Menos histórico = menos tokens e menos chamadas ao Gemini (ajuda no limite do plano free)
    num_hist = int(os.environ.get("GEMINI_NUM_HISTORY_RUNS", "2"))

    return Agent(
        name="VakinhaAssistant",
        model=Gemini(
            id=model_id,
            api_key=settings.GEMINI_API_KEY,
        ),
        db=db,
        instructions=SYSTEM_PROMPT,
        tools=tools,
        num_history_runs=num_hist,
    )


def _is_gemini_rate_limit(exc: BaseException) -> bool:
    if isinstance(exc, ModelRateLimitError):
        return True
    if isinstance(exc, ModelProviderError) and getattr(exc, "status_code", None) == 429:
        return True
    s = str(exc).lower()
    if "429" in s or "resource exhausted" in s or "too many requests" in s:
        return True
    if "rate" in s and "limit" in s:
        return True
    return False


def run_agent_text(agent, text: str, session_id: str) -> str:
    """Executa o agente e devolve a resposta em texto (API agno 2.x), com retry em 429."""
    max_retries = getattr(settings, "GEMINI_MAX_RETRIES", 6)
    base = getattr(settings, "GEMINI_RETRY_BASE_SECONDS", 2.0)
    last_exc: Optional[BaseException] = None

    for attempt in range(max_retries):
        try:
            out = agent.run(text, session_id=session_id)
            if out is None:
                return ""
            if hasattr(out, "get_content_as_string"):
                return (out.get_content_as_string() or "").strip()
            c = getattr(out, "content", None)
            return (str(c) if c is not None else "").strip()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_gemini_rate_limit(exc):
                logger.exception("Erro no agente Gemini: %s", exc)
                raise
            if attempt >= max_retries - 1:
                logger.error("Gemini 429 após %s tentativas: %s", max_retries, exc)
                raise
            wait = base * (2**attempt)  # backoff exponencial: 2s, 4s, 8s...
            logger.warning(
                "Gemini rate limit (429), tentativa %s/%s — aguardando %.1fs",
                attempt + 1,
                max_retries,
                wait,
            )
            time.sleep(wait)

    if last_exc:
        raise last_exc
    return ""


def transcribe_audio(instance: str, message_id: str) -> str:
    if not settings.GROQ_API_KEY:
        return "❌ GROQ_API_KEY não configurada"

    url = f"{settings.EVOLUTION_API_URL}/{instance}/chat/{message_id}"
    headers = {"apikey": settings.EVOLUTION_TOKEN}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        audio_b64 = response.json().get("audioMessage", {}).get("data")
    except requests.RequestException as exc:
        logger.error("Failed to download audio from Evolution API: %s", exc)
        return "❌ Erro ao baixar áudio"

    if not audio_b64:
        return "❌ Áudio não encontrado"

    audio_bytes = base64.b64decode(audio_b64)
    groq_url = "https://api.groq.com/openai/v1/audio/transcriptions"
    groq_headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    files = {"file": ("audio.ogg", audio_bytes, "audio/ogg")}
    data = {
        "model": "whisper-large-v3",
        "response_format": "json",
        "language": "pt",
        "temperature": "0",
    }

    try:
        result = requests.post(groq_url, headers=groq_headers, files=files, data=data, timeout=60)
        result.raise_for_status()
        return result.json().get("text", "❌ Erro na transcrição")
    except requests.RequestException as exc:
        logger.error("Groq transcription failed: %s", exc)
        return "❌ Erro na transcrição de áudio"
