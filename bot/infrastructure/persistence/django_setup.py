import os

import django
import django.apps


def setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if not django.apps.apps.ready:
        django.setup()
