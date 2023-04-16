from django.conf import settings


broker_url = settings.CELERY_BROKER_URL

# List of modules to import when the Celery worker starts.
imports = ("applifting.tasks",)
task_default_queue = "applifting"
