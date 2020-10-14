from django.apps import AppConfig

from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

class ForensicsConfig(AppConfig):
    name = "forensics"

    def ready(self):
        from .signals import run_cropping_script
        from .models import Image

        post_save.connect(run_cropping_script, sender=Image)
