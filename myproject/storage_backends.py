from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class StaticStorage(S3Boto3Storage):
    default_acl = 'public-read'
    location = settings.AWS_STATIC_LOCATION

class MediaStorage(S3Boto3Storage):
    location = settings.AWS_MEDIA_LOCATION
    file_overwrite = False