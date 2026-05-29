import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email(subject: str, to_email: str, template_html: str, context: dict):
    """Sends an HTML email with plain text fallback."""
    html_content = render_to_string(template_html, context)
    text_content = render_to_string(template_html.replace(".html", ".txt"), context) if False else ""

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content or "Veja a versão HTML deste e-mail.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        logger.info("Email sent to %s | subject: %s", to_email, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        raise


def _format_evolution_send_number(jid: str) -> str:
    """
    Evolution API v2 expects `number` in sendText body (not JID in URL).
    Supports @s.whatsapp.net and @lid identifiers.
    """
    jid = (jid or "").strip()
    if not jid:
        return ""
    if jid.endswith("@lid"):
        return jid
    if "@" in jid:
        return jid.split("@", 1)[0].lstrip("+").replace(" ", "")
    return jid.lstrip("+").replace(" ", "")


def send_whatsapp_message(jid: str, message: str) -> bool:
    """
    Sends a WhatsApp message via Evolution API v2.
    Returns True on success, False on failure.
    """
    if not all([settings.EVOLUTION_API_URL, settings.EVOLUTION_INSTANCE, settings.EVOLUTION_TOKEN]):
        logger.warning("Evolution API not configured — skipping WhatsApp notification")
        return False

    number = _format_evolution_send_number(jid)
    if not number:
        logger.error("Invalid WhatsApp target jid: %r", jid)
        return False

    base = settings.EVOLUTION_API_URL.rstrip("/")
    instance = settings.EVOLUTION_INSTANCE
    url = f"{base}/message/sendText/{instance}"
    headers = {"apikey": settings.EVOLUTION_TOKEN, "Content-Type": "application/json"}
    payload = {
        "number": number,
        "text": message,
        "delay": 1000,
        "linkPreview": True,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        logger.info("WhatsApp message sent to %s (number=%s)", jid, number)
        return True
    except requests.RequestException as exc:
        body = ""
        if exc.response is not None:
            body = (exc.response.text or "")[:500]
        logger.error(
            "Failed to send WhatsApp message to %s (number=%s): %s %s",
            jid,
            number,
            exc,
            body,
        )
        return False
