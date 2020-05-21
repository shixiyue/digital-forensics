from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractUser
)

import hashlib
import os

class WebsiteUserManager(BaseUserManager):
    def create_superuser(self, email, password):
        user = self.model(
            email=self.normalize_email(email), username=self.normalize_email(email)
        )
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.status = 1
        user.save(using=self._db)
        return user


class WebsiteUser(AbstractUser):
    objects = WebsiteUserManager()

    USERNAME_FIELD = 'email'
    # changes email to unique and blank to false
    email = models.EmailField(('email address'), unique=True)

    class Status(models.IntegerChoices):
        BANNED = -2
        SUSPICIOUS = -1
        NORMAL = 0
        UNRESTRICTED = 1
    status = models.IntegerField(choices=Status.choices, default=0)
    REQUIRED_FIELDS = []  # removes email from REQUIRED_FIELDS

def upload_file_name(instance, filename):
    h = instance.sig.split("_")[0]
    _, ext = os.path.splitext(filename)
    return os.path.join('uploads', h, 'upload' + ext.lower())

class Image(models.Model):
    # use the custom storage class fo the FileField
    sig = models.CharField(max_length=300, blank=True, primary_key=True)
    image = models.ImageField(upload_to=upload_file_name)
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()

    class Status(models.IntegerChoices):
        NOT_AVAILABLE = 0
        PROCESSED = 1
        CERTIFIED = 2
        MANIPULATED = 3
        REDO = 4
    certified = models.IntegerField(choices=Status.choices, default=0)
    certificate_link = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:  # file is new
            sha = hashlib.sha256()
            for chunk in self.image.chunks():
                sha.update(chunk)
            self.sig = sha.hexdigest() + '_' + '_'.join(str(float(d)) for d in [self.x, self.y, self.width, self.height])
        super(Image, self).save(*args, **kwargs)
        print(1)            
    
    def __str__(self):
        return self.sig


class Submission(models.Model):
    user = models.ForeignKey(
        WebsiteUser, 
        models.SET_NULL,
        null=True,
        related_name='user'
    )
    admin = models.ForeignKey(
        WebsiteUser, 
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='admin'
    )
    images = models.ManyToManyField(Image, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)

    class Status(models.IntegerChoices):
        NO_NEED_TO_PROCESS = -1
        NOT_PROCESSED = 0
        PROCESSED = 1
        UNDER_REVIEW = 2
        PASSED = 3
        FAILED = 4
        APPEAL = 5
        FLAGGED = 6
    status = models.IntegerField(choices=Status.choices, default=0)
    
    class Meta:
        ordering = ['submission_time']
    
    def __str__(self):
        return self.user.email + '_' + str(self.submission_time)
    
