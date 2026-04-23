import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AiAgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_agent"
    verbose_name = "Agente IA"

    def ready(self):
        from django.conf import settings

        missing = []
        for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "EVOLUTION_API_URL"):
            if not getattr(settings, key, ""):
                missing.append(key)

        if missing:
            logger.warning("AI Agent: variáveis não configuradas: %s", ", ".join(missing))
