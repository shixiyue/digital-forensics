import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from celery import Celery
from celery.app.registry import TaskRegistry

from .ml_model_task import CroppingModelPredictionTask

celery_app = Celery("myproject")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
celery_app.register_task(CroppingModelPredictionTask())
