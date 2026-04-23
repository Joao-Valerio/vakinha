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


def send_whatsapp_message(jid: str, message: str) -> bool:
    """
    Sends a WhatsApp message via Evolution API.
    Returns True on success, False on failure.
    """
    if not all([settings.EVOLUTION_API_URL, settings.EVOLUTION_INSTANCE, settings.EVOLUTION_TOKEN]):
        logger.warning("Evolution API not configured — skipping WhatsApp notification")
        return False

    url = f"{settings.EVOLUTION_API_URL}/{settings.EVOLUTION_INSTANCE}/message/sendText/{jid}"
    headers = {"apikey": settings.EVOLUTION_TOKEN, "Content-Type": "application/json"}
    payload = {
        "delay": 1000,
        "presence": "composing",
        "linkPreview": True,
        "message": message,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        logger.info("WhatsApp message sent to %s", jid)
        return True
    except requests.RequestException as exc:
        logger.error("Failed to send WhatsApp message to %s: %s", jid, exc)
        return False
