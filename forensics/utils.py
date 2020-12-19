import os
import boto3
from random import randrange
from myproject.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME

def _get_upload(instance):
    return os.path.join("uploads", str(instance.id))

def _get_crop(instance):
    return os.path.join(_get_upload(instance.original_image), str(instance.id))

def _get_analysis(instance):
    return os.path.join(_get_crop(instance.crop), str(instance.id))

def upload_file_name(instance, filename):
    _, ext = os.path.splitext(filename)
    return os.path.join(_get_upload(instance), "upload" + ext.lower())

def crop_file_name(instance, filename):
    return os.path.join(_get_upload(instance.original_image), f"{instance.id}-{randrange(10)}.jpg")

def analysis_file_name(instance, filename):
    return os.path.join(_get_crop(instance.crop), f"{instance.id}.jpg")