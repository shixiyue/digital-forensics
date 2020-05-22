from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.files.base import File

from rest_framework.parsers import FileUploadParser
from rest_framework import permissions, renderers, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

import django_tables2 as tables

import io
import hashlib

from .forms import SignUpForm, LoginForm
from .tokens import account_activation_token
from .models import WebsiteUser, Image, Submission, SubmissionTable
from .serializers import ImageSerializer
from .serializers import SubmissionSerializer

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

def details_view(request, id):
    return render(request, 'index.html')

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    parser_classes = (FormParser, MultiPartParser)

    @action(detail=True, methods=['post'])
    def submit(self, request):
        images = []
        request.data.pop('csrfmiddlewaretoken', None)
        try:
            request.data.pop('apply')
            require_certificate = 1
        except:
            require_certificate = 0
        for upload in request.data.values():
            sha = hashlib.sha256()
            for chunk in upload.chunks():
                sha.update(chunk)
            sig = sha.hexdigest()
            try:
                image = Image.objects.get(sig=sig)
            except Image.DoesNotExist:
                image = Image.objects.create(image=upload, sig=sig)
                image.save()
            images.append(image)
        serializer = SubmissionSerializer(data={'status':require_certificate})
        if serializer.is_valid():
            serializer.save(images=images, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HistoryView(tables.SingleTableView):
    table_class = SubmissionTable
    template_name = "history.html"

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)