from rest_framework import serializers
from .models import Image
from .models import Submission
from .models import WebsiteUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteUser
        fields = ("email",)


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"


class SubmissionSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, required=False)
    user = UserSerializer(read_only=True, required=False)
    admin = UserSerializer(read_only=True, required=False)

    class Meta:
        model = Submission
        fields = "__all__"
