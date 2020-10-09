from django.db.models.signals import post_save
from django.dispatch import receiver

import os

from .algo import check_image
from .models import Image
from myproject.settings import PROJECT_ROOT


@receiver(post_save, sender=Image)
def run_detection_script(sender, instance, created, **kwargs):
    pass
    '''
    if created:
        image_dir = PROJECT_ROOT + "/temp/" + instance.sig + "/upload.jpg"
        check_image.delay(image_dir, instance.sig)
    '''