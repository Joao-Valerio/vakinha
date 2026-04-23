import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


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
        remote_jid = key_data.get("remoteJid", "")
        message_id = key_data.get("id", "")
        message_type = body.get("data", {}).get("messageType", "conversation")
        conversation = body.get("data", {}).get("message", {}).get("conversation", "")

        if not remote_jid:
            return JsonResponse({"status": "no_jid"}, status=200)

        logger.info("Webhook received from %s (type=%s)", remote_jid, message_type)

        from .tasks import process_whatsapp_message, process_audio_message

        if message_type == "audioMessage":
            process_audio_message.delay(remote_jid, instance_key, message_id)
        else:
            if conversation.strip():
                process_whatsapp_message.delay(remote_jid, conversation)

        return JsonResponse({"status": "queued"})

    except Exception as exc:
        logger.error("Webhook processing error: %s", exc)
        return JsonResponse({"error": "Internal error"}, status=500)
