"""Celery task for making ML Model predictions."""
import importlib
from celery import Task

from forensics.cropping import CroppingModel
from django.conf import settings

class CroppingModelPredictionTask(Task):
    """Celery Task for making ML Model predictions."""

    def __init__(self):
        """Class constructor."""
        super().__init__()
        self._model = None
        self.name = "cropping"

    def initialize(self):
        """Class initialization."""
        model_object = CroppingModel(settings.CROPPING_MODEL)
        self._model = model_object

    def run(self, img_id, img):
        """Execute predictions with the MLModel class."""
        if self._model is None:
            self.initialize()
        return self._model.medical_bounding_boxes(img_id, img)