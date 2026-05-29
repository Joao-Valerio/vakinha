import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .utils import resolve_reply_jid

logger = logging.getLogger(__name__)


def _extract_message_text(body: dict) -> str:
    """
    Extracts user text from common Evolution/WhatsApp message payload variants.
    """
    message = body.get("data", {}).get("message", {}) or {}
    conversation = (message.get("conversation") or "").strip()
    if conversation:
        return conversation

    extended = message.get("extendedTextMessage", {}) or {}
    extended_text = (extended.get("text") or "").strip()
    if extended_text:
        return extended_text

    image_caption = ((message.get("imageMessage", {}) or {}).get("caption") or "").strip()
    if image_caption:
        return image_caption

    video_caption = ((message.get("videoMessage", {}) or {}).get("caption") or "").strip()
    if video_caption:
        return video_caption

    return ""


@csrf_exempt
@require_POST
def whatsapp_webhook(request, token: str):
    """
    Webhook endpoint for Evolution API WhatsApp messages.
    Secured by a secret token in the URL path (configure AI_WEBHOOK_TOKEN in .env).
    """
    if token != settings.AI_WEBHOOK_TOKEN:
        logger.warning("Invalid AI webhook token received")
        return JsonResponse({"error": "Unauthorized"}, status=401)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        body = data.get("body", data)
        instance_key = body.get("instance", settings.EVOLUTION_INSTANCE)
        key_data = body.get("data", {}).get("key", {})
        remote_jid = resolve_reply_jid(key_data)
        message_id = key_data.get("id", "")
        message_type = body.get("data", {}).get("messageType", "conversation")
        message_text = _extract_message_text(body)
        from_me = key_data.get("fromMe", False)

        if not remote_jid:
            return JsonResponse({"status": "no_jid"}, status=200)

        if from_me:
            logger.info("Ignoring outgoing message (fromMe=true) for %s", remote_jid)
            return JsonResponse({"status": "ignored_outgoing"})

        logger.info(
            "Webhook received from %s (type=%s, text=%.40s)",
            remote_jid,
            message_type,
            message_text,
        )

        from .tasks import process_whatsapp_message, process_audio_message

        if message_type == "audioMessage":
            process_audio_message.delay(remote_jid, instance_key, message_id)
        else:
            if message_text:
                process_whatsapp_message.delay(remote_jid, message_text)
            else:
                logger.warning(
                    "Empty message text from %s (type=%s)",
                    remote_jid,
                    message_type,
                )
                return JsonResponse({"status": "empty_message"})

        return JsonResponse({"status": "queued"})

    except Exception as exc:
        logger.error("Webhook processing error: %s", exc)
        return JsonResponse({"error": "Internal error"}, status=500)
