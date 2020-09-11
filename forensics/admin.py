from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import WebsiteUser, Submission, Image


class WebsiteAdmin(UserAdmin):
    model = WebsiteUser


admin.site.register(WebsiteUser, WebsiteAdmin)
admin.site.register(Submission)
admin.site.register(Image)
