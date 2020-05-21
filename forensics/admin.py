from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import WebsiteUser

class WebsiteAdmin(UserAdmin):
    model = WebsiteUser
    
admin.site.register(WebsiteUser, WebsiteAdmin)
