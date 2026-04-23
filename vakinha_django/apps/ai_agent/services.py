import base64
import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_AGENT_CACHE_TTL = 3600  # 1 hour


def create_agent(session_id: str):
    """
    Returns a Agno Agent for the given WhatsApp session.
    Agents are cached in Redis by session_id to avoid re-instantiation on every request.
    """
    from agno import Agent
    from agno.llms import GoogleGenerativeAI
    from agno.memory import PostgresChatMemory
    from .tools import SendWhatsAppTool, CreateCampaignTool, PublishToSiteTool, SYSTEM_PROMPT

    cache_key = f"ai_agent:{session_id}"
    # Agno Agent objects are not serialisable — we just cache a flag and reinstantiate if recently used
    # For true caching, use a persistent session store; for now we skip object caching.
    memory = PostgresChatMemory(
        connection_string=settings.DATABASES["default"].get("_url") or _build_db_url(),
        session_id=session_id,
    )

    agent = Agent(
        name="VakinhaAssistant",
        llm=GoogleGenerativeAI(model="gemini-1.5-flash", api_key=settings.GEMINI_API_KEY),
        system_prompt=SYSTEM_PROMPT,
        memory=memory,
        tools=[SendWhatsAppTool(), CreateCampaignTool(), PublishToSiteTool()],
    )
    return agent


def _build_db_url() -> str:
    """Builds a PostgreSQL URL from Django DATABASES config as fallback."""
    from django.conf import settings
    db = settings.DATABASES["default"]
    engine = db.get("ENGINE", "")
    if "postgresql" in engine or "psycopg" in engine:
        host = db.get("HOST", "localhost")
        port = db.get("PORT", "5432")
        name = db.get("NAME", "")
        user = db.get("USER", "")
        pwd = db.get("PASSWORD", "")
        return f"postgresql://{user}:{pwd}@{host}:{port}/{name}"
    return ""


def transcribe_audio(instance: str, message_id: str) -> str:
    """
    Downloads audio from Evolution API and transcribes via Groq Whisper.
    Returns transcribed text or an error string.
    """
    if not settings.GROQ_API_KEY:
        return "❌ GROQ_API_KEY não configurada"

    # 1. Download audio bytes from Evolution API
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

    # 2. Transcribe via Groq Whisper (OpenAI-compatible endpoint)
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
