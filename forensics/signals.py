from django.db.models.signals import post_save
from django.dispatch import receiver

import os

from .algo import check_image
from .models import Image, Crop
from myproject.settings import PROJECT_ROOT
from myproject.celery import celery_app
from .algo import check_image


@receiver(post_save, sender=Image)
def run_cropping_script(sender, instance, created, **kwargs):
    if created:
        task = celery_app.tasks["cropping"]
        img = f"{PROJECT_ROOT}/temp/{instance.submission.id}/{instance.id}.jpg"
        task.delay(instance.id, img)

def run_manipulation_script(img_id, img_name):
    task = celery_app.tasks["manipulation"]
    task.delay(img_id, img_name)
    check_image.delay(img_id, img_name)
