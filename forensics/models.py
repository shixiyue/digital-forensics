from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractUser
)
from django.core.files.storage import FileSystemStorage

import django_tables2 as tables
from django_tables2.utils import A

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
    REQUIRED_FIELDS = []


class MediaFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise(Exception("name's length is greater than max_length"))
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(MediaFileSystemStorage, self)._save(name, content)


def upload_file_name(instance, filename):
    _, ext = os.path.splitext(filename)
    return os.path.join('uploads', instance.sig, 'upload' + ext.lower())


class Image(models.Model):
    # use the custom storage class fo the FileField
    sig = models.CharField(max_length=64, primary_key=True)
    image = models.ImageField(
        upload_to=upload_file_name, storage=MediaFileSystemStorage())

    class Status(models.IntegerChoices):
        DEFAULT = 0
        CERTIFIED = 1
        MANIPULATED = 2
        REDO = 3
    certified = models.IntegerField(choices=Status.choices, default=0)
    certificate_link = models.URLField(blank=True)

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
        related_name='admin',
        verbose_name="reviewer"
    )
    images = models.ManyToManyField(Image, blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)

    class Status(models.IntegerChoices):
        NOT_REQUESTED = 0
        WAITING = 1
        UNDER_REVIEW = 2
        CERTIFIED = 3
        FAILED = 4
        APPEAL = 5
        FLAGGED = 6
    status = models.IntegerField(choices=Status.choices, default=0, verbose_name="Certificate Status")

    class Meta:
        ordering = ['submission_time']

    def __str__(self):
        return self.user.email + '_' + str(self.submission_time)

    def num_of_images(self):
        return self.images.count()

class SubmissionTable(tables.Table):
    id = tables.Column(verbose_name="Submission ID")
    submission_time = tables.DateTimeColumn(
        format='Y-m-d', verbose_name="Date")
    num_of_images = tables.Column(
        accessor=A('num_of_images'),
        verbose_name='Number of Images'
    )
    links = tables.LinkColumn(
        'submission_details',
        verbose_name='Analysis and Certificates',
        text='Details',
        args=[A('pk')],
        attrs={"a": {"style": "color: #0275d8;"}}
    )
    template = """
        <div class="dropleft">
            <button class="btn btn-sm btn-primary dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"></button>
            <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                {% if record.status == 4 %}
                <a class="dropdown-item" href="#">Appeal</a>
                {% elif record.status == 0 %}
                <a class="dropdown-item" href="#">Request Certificates</a>
                {% endif %}
                <a class="dropdown-item" href="#">Contact Support</a>
            </div>
        </div>
    """
    actions = tables.TemplateColumn(template)

    class Meta:
        model = Submission
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "submission_time", "status")
        sequence = ("id", "submission_time", "status",
                    "num_of_images", "links", "actions")
        attrs = {"style": "background-color: #ffffff;"}
