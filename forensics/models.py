from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractUser
from utils import upload_file_name, analysis_file_name, crop_file_name

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

    USERNAME_FIELD = "email"
    # changes email to unique and blank to false
    email = models.EmailField(("email address"), unique=True)

    class Status(models.IntegerChoices):
        BANNED = -2
        SUSPICIOUS = -1
        NORMAL = 0
        UNRESTRICTED = 1

    status = models.IntegerField(choices=Status.choices, default=0)
    REQUIRED_FIELDS = []

class Submission(models.Model):
    user = models.ForeignKey(
        WebsiteUser, models.SET_NULL, null=True, related_name="user"
    )
    admin = models.ForeignKey(
        WebsiteUser,
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="admin",
        verbose_name="reviewer",
    )
    submission_time = models.DateTimeField(auto_now_add=True)

    class Status(models.IntegerChoices):
        NOT_REQUESTED = 0
        WAITING = 1
        UNDER_REVIEW = 2
        CERTIFIED = 3
        FAILED = 4
        APPEAL = 5
        FLAGGED = 6

    status = models.IntegerField(
        choices=Status.choices, default=0, verbose_name="Certificate Status"
    )

    class Meta:
        ordering = ["submission_time"]

    def __str__(self):
        return self.user.email + "_" + str(self.submission_time)

    def num_of_images(self):
        return Image.objects.filter(submission=self.id)

    def email(self):
        return self.user.email
    
    def admin_email(self):
        if self.admin is not None:
            return self.admin.email
        else:
            return "None"

class ImageStatus(models.IntegerChoices):
    DEFAULT = 0
    CERTIFIED = 1
    MANIPULATED = 2
    REDO = 3

class Image(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    image = models.FileField(upload_to=upload_file_name)
    certified = models.IntegerField(choices=ImageStatus.choices, default=0)
    certificate_link = models.URLField(blank=True)

class Crop(models.Model):
    original_image = models.ForeignKey(Image, on_delete=models.CASCADE)
    image = models.FileField(upload_to=crop_file_name)
    certified = models.IntegerField(choices=ImageStatus.choices, default=0)

class AnalysisImage(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    image = models.FileField(upload_to=analysis_file_name)
