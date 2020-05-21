from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.contrib import messages

from rest_framework.parsers import FileUploadParser
from rest_framework import permissions, renderers, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response


from .forms import SignUpForm, LoginForm
from .tokens import account_activation_token
from .models import WebsiteUser, Image, Submission
from .serializers import ImageSerializer
from .serializers import SubmissionSerializer

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    parser_classes = (FormParser, MultiPartParser)

    @action(detail=True, methods=['post'])
    def submit(self, request):
        image = request.data['image']
        x = float(request.data['x'])
        y = float(request.data['y'])
        width = float(request.data['width'])
        height = float(request.data['height'])

        try:
            image = Image.objects.get(image=image, x=x, y=y, width=width, height=height)
        except Image.DoesNotExist:
            image = Image.objects.create(image=image, x=x, y=y, width=width, height=height)
            image.save()
        serializer = SubmissionSerializer(data={})
        if serializer.is_valid():
            serializer.save(images=[image], user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def index_view(request):
    return render(request, 'index.html')

def about_view(request):
    return render(request, 'about.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.username = user.email
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Digital Forensics: Please Activate Your Account'
            # load a template like get_template() 
            # and calls its render() method immediately.
            message = render_to_string('activation_request.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                # method will generate a hash value with user related data
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message, from_email='digitalforensics.report@gmail.com')
            return redirect('activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def activation_sent_view(request):
    return render(request, 'activation_sent.html')

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = WebsiteUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, WebsiteUser.DoesNotExist):
        user = None
    # checking if the user exists, if the token is valid.
    if user is not None and account_activation_token.check_token(user, token):
        # if valid set active true 
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'activation_invalid.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                if user.is_active:
                    form = login(request, user)
                    return redirect('index')
            else:
                messages.error(request, "Invalid username or password, or you haven't activate your account yet.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return render(request, 'index.html')

def dashboard_view(request):
    if request.user.is_authenticated:
        return render(request, 'dashboard.html')
    return redirect('index')