import os
from celery import Celery
from celery.app.registry import TaskRegistry

from .ml_model_task import CroppingModelPredictionTask

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

registry = TaskRegistry()
registry.register(CroppingModelPredictionTask())

celery_app = Celery("myproject", tasks=registry)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
