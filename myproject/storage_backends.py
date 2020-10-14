from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class StaticStorage(S3Boto3Storage):
    default_acl = 'public-read'
    location = settings.AWS_STATIC_LOCATION

class MediaStorage(S3Boto3Storage):
    location = settings.AWS_MEDIA_LOCATION
    default_acl = 'public-read'
    file_overwrite = False

    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise (Exception("name's length is greater than max_length"))
        return name
