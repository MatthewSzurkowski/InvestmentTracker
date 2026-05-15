import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investment_tracker.settings")

app = Celery("investment_tracker")

# reads CELERY_ settings from settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# auto-discover tasks in all apps
app.autodiscover_tasks()