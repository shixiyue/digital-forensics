from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import WebsiteUser
from .models import Image

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=150)

    class Meta:
        model = WebsiteUser
        fields = (
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        # Call to ModelForm constructor
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"

class LoginForm(AuthenticationForm):
    email = forms.EmailField(max_length=150)

    class Meta:
        model = WebsiteUser
        fields = ("email", "password")

    def __init__(self, *args, **kwargs):
        # Call to ModelForm constructor
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields.pop("username")
        self.fields["email"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["class"] = "form-control"
