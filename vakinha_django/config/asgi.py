import os

from django.core.asgi import get_asgi_application

# Produção por padrão (Vercel e outros handlers ASGI chamam antes do manage.py)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
