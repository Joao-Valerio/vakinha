#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    # Na Vercel a variável VERCEL=1; produção deve ser usada no deploy serverless.
    default = (
        "config.settings.production"
        if os.environ.get("VERCEL") == "1"
        else "config.settings.development"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
