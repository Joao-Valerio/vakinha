import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=3,
    name="ai_agent.process_whatsapp_message",
)
def process_whatsapp_message(self, remote_jid: str, message: str):
    """
    Runs the Agno AI agent for a given WhatsApp message.
    The agent may call tools (SendWhatsApp, CreateCampaign) as needed.
    """
    from .services import create_agent, run_agent_text

    logger.info("Processing WhatsApp message from %s", remote_jid)

    try:
        agent = create_agent(remote_jid)
        response = run_agent_text(agent, message, session_id=remote_jid)
        logger.info("Agent responded to %s: %.80s...", remote_jid, response)
        return response
    except Exception as exc:
        logger.error("Agent failed for %s: %s", remote_jid, exc)
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=3,
    name="ai_agent.process_audio_message",
)
def process_audio_message(self, remote_jid: str, instance: str, message_id: str):
    """Transcribes audio then passes text to the AI agent."""
    from .services import transcribe_audio, create_agent, run_agent_text

    logger.info("Transcribing audio message %s from %s", message_id, remote_jid)

    text = transcribe_audio(instance, message_id)
    if text.startswith("❌"):
        logger.warning("Transcription failed for %s: %s", remote_jid, text)
        return

    logger.info("Transcription result: %.80s", text)
    agent = create_agent(remote_jid)
    response = run_agent_text(agent, text, session_id=remote_jid)
    logger.info("Agent responded to audio from %s", remote_jid)
    return response
