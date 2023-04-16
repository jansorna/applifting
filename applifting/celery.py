import os

# This is to prevent settings env var every time starting Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "applifting.settings")
from celery import Celery  # noqa pylint: disable=C0413
from . import celeryconfig  # noqa pylint: disable=C0413

celery_app = Celery()
celery_app.config_from_object(celeryconfig)

# period tasks
celery_app.conf.beat_schedule = {
    "update_product_offers": {
        "task": "applifting.tasks.update_offers_for_products_in_db",
        "schedule": 60.0,
    },
}
