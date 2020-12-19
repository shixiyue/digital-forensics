from django.db.models.signals import post_save
from django.dispatch import receiver

import os

from .models import Image, Crop
from myproject.settings import PROJECT_ROOT
from myproject.celery import celery_app


@receiver(post_save, sender=Image)
def run_cropping_script(sender, instance, created, **kwargs):
    if created:
        task = celery_app.tasks["cropping"]
        img = f"{PROJECT_ROOT}/temp/{instance.submission.id}/{instance.id}.jpg"
        task.delay(instance.id, img)
