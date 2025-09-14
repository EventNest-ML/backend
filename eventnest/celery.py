from __future__ import absolute_import
import os

# 1. Default to development but allow override via ENV
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "eventnest.settings.development")
)

from celery import Celery
from django.conf import settings

app = Celery("eventnest")

# 2. Load any CELERY_ prefixed settings from Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# 3. Auto-discover tasks from INSTALLED_APPS in whichever settings module is active
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)