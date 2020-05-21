from django.db.models.signals import post_save
from django.dispatch import receiver

import os

from .algo import check_images
from .models import Image
from myproject.settings import PROJECT_ROOT

@receiver(post_save, sender=Image)
def run_detection_script(sender, instance, created, **kwargs):
    if created:
        image_dir = PROJECT_ROOT + instance.image.url
        print(PROJECT_ROOT)
        check_images.delay(image_dir)
