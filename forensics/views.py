from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
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
from django.core.files.storage import FileSystemStorage

from rest_framework.parsers import FileUploadParser
from rest_framework import permissions, renderers, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

import django_tables2 as tables

import io
import os
import uuid
import subprocess
import shlex
import PIL

from .forms import SignUpForm, LoginForm
from .tokens import account_activation_token
from .models import (
    WebsiteUser,
    Image,
    Submission,
    Crop,
    ImageStatus,
    AnalysisCrop,
    AnalysisType,
)
from .tables import SubmissionTable, SubmissionAdminTable
from .serializers import (
    ImageSerializer,
    SubmissionSerializer,
    CropSerializer,
    AnalysisCropSerializer,
)
from .mixin import StaffRequiredMixin
from myproject.settings import PROJECT_ROOT


def index_view(request):
    return render(request, "index.html")


def about_view(request):
    return render(request, "about.html")


def certificate_demo(request):
    return render(request, "certificate.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.username = user.email
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = "Digital Forensics: Please Activate Your Account"
            # load a template like get_template()
            # and calls its render() method immediately.
            message = render_to_string(
                "activation_request.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    # method will generate a hash value with user related data
                    "token": account_activation_token.make_token(user),
                },
            )
            user.email_user(
                subject, message, from_email="digitalforensics.report@gmail.com"
            )
            return redirect("activation_sent")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def activation_sent_view(request):
    return render(request, "activation_sent.html")


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
        return redirect("index")
    else:
        return render(request, "activation_invalid.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(email=email, password=password)
            if user is not None:
                if user.is_active:
                    form = login(request, user)
                    return redirect("index")
            else:
                messages.error(
                    request,
                    "Invalid username or password, or you haven't activate your account yet.",
                )
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required(login_url="/login/")
def logout_view(request):
    logout(request)
    return render(request, "index.html")


@login_required(login_url="/login/")
def dashboard_view(request):
    return render(request, "dashboard.html")


@login_required(login_url="/login/")
def data_view(request):
    return render(request, "more_data.html")


@login_required(login_url="/login/")
def adjust_view(request):
    disabled = True
    if request.method == "POST":
        disabled = False
        if request.POST.get("remove"):
            id = int(request.POST.get("id"))
            Crop.objects.filter(id=id).delete()
        elif request.POST.get("adjust"):
            x = int(float(request.POST.get("x")))
            y = int(float(request.POST.get("y")))
            width = int(float(request.POST.get("width")))
            height = int(float(request.POST.get("height")))

            id = int(request.POST.get("id"))
            if id < 0:
                original_image = Image.objects.get(id=int(request.POST.get("image_id")))
                crop = Crop.objects.create(original_image=original_image)
            else:
                crop = Crop.objects.get(id=id)
            dirname = f"{PROJECT_ROOT}/temp/{crop.original_image.submission.id}"
            filename = os.path.join(dirname, f"{crop.original_image.id}")
            image = PIL.Image.open(filename + ".jpg")
            image = image.crop((x, y, x + width, y + height))
            image = image.convert("RGB")
            filename = filename + "/updated.jpg"
            image.save(filename)
            f = open(filename, "rb")
            crop.x, crop.y, crop.width, crop.height = x, y, width, height
            crop.image.delete(save=False)
            crop.image = File(f)
            crop.save()
        elif request.POST.get("next"):
            image = Image.objects.filter(
                certified=ImageStatus.NOT_CONFIRMED, submission__user=request.user
            ).order_by("id")[0]
            image.certified = ImageStatus.DEFAULT
            image.save()

    images = Image.objects.filter(
        certified=ImageStatus.NOT_CONFIRMED, submission__user=request.user
    ).order_by("id")
    if len(images) == 0:
        return render(request, "all_set.html")
    image = images[0]
    crops = list(Crop.objects.filter(original_image=image.id).order_by("id"))
    return render(
        request,
        "adjust_crop.html",
        {
            "submission_id": image.submission.id,
            "image": image,
            "crops": crops,
            "disabled": disabled,
        },
    )


@login_required(login_url="/login/")
def submission_details_view(request, id):
    submission = Submission.objects.get(id=id)
    images = list(Image.objects.filter(submission=submission.id).order_by("id"))
    crops = []
    for image in images:
        crops.append(list(Crop.objects.filter(original_image=image.id).order_by("id")))
    return render(
        request,
        "submission_details.html",
        {"id": id, "submission": submission, "crops": crops},
    )


@staff_member_required
def submission_admin_view(request, id):
    submission = Submission.objects.get(id=id)
    images = list(Image.objects.filter(submission=submission.id).order_by("id"))
    crops = []
    for image in images:
        crops.append(list(Crop.objects.filter(original_image=image.id).order_by("id")))
    num_cert = 0
    in_progress = False
    if submission.status != 0:
        for image in images:
            if image.certified == ImageStatus.CERTIFIED:
                num_cert += 1
            elif (
                image.certified == ImageStatus.DEFAULT
                or image.certified == ImageStatus.PROCESSED
            ):
                in_progress = True
    if request.method == "POST":
        if in_progress:
            submission.status = 2
        elif num_cert == len(images):
            submission.status = 3
        else:
            submission.status = 4
        submission.admin = request.user
        submission.save()
    return render(
        request,
        "submission_admin.html",
        {
            "id": id,
            "submission": submission,
            "crops": crops,
            "num_cert": num_cert,
            "total": len(images),
        },
    )


@login_required(login_url="/login/")
def analysis_view(request, sub_id, crop_id):
    crop = Crop.objects.get(id=crop_id)
    upload = crop.image.url
    status = crop.certified != 0
    manipulation = AnalysisCrop.objects.filter(
        crop=crop_id, analysis_type=AnalysisType.MANIPULATION
    ).first()
    if manipulation:
        manipulation = manipulation.analysis_image.url
    ela = AnalysisCrop.objects.filter(
        crop=crop_id, analysis_type=AnalysisType.ELA
    ).first()
    if ela:
        ela = ela.analysis_image.url

    return render(
        request,
        "analysis.html",
        {"sub_id": sub_id, "upload": upload, "manipulation": manipulation, "ela": ela, "status": status},
    )


@staff_member_required
def analysis_admin_view(request, sub_id, crop_id):
    crop = Crop.objects.get(id=crop_id)
    status = None
    if request.method == "POST":
        status = request.POST.get("status")
        if status:
            if status == "default":
                crop.certified = ImageStatus.DEFAULT
            elif status == "pass":
                crop.certified = ImageStatus.CERTIFIED
            else:
                crop.certified = ImageStatus.MANIPULATED
            crop.save()
            # TODO: cascade to image certified status

    upload = crop.image.url
    status = crop.certified != 0
    manipulation = AnalysisCrop.objects.filter(
        crop=crop_id, analysis_type=AnalysisType.MANIPULATION
    ).first()    
    if manipulation:
        manipulation = manipulation.analysis_image.url
    ela = AnalysisCrop.objects.filter(
        crop=crop_id, analysis_type=AnalysisType.ELA
    ).first()
    if ela:
        ela = ela.analysis_image.url
    return render(
        request,
        "analysis_admin.html",
        {"sub_id": sub_id, "upload": upload, "manipulation": manipulation, "ela": ela, "status": status},
    )


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    parser_classes = (FormParser, MultiPartParser)

    @action(detail=True, methods=["post"])
    def submit(self, request):
        request.data.pop("csrfmiddlewaretoken", None)
        try:
            request.data.pop("apply")
            require_certificate = 1
        except:
            require_certificate = 0
        submission = Submission.objects.create(
            user=request.user, status=require_certificate
        )
        dirname = f"{PROJECT_ROOT}/temp/{submission.id}"
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if "pdf" in request.data:
            upload = request.data["pdf"]
            with open(dirname + "/upload.pdf", "wb+") as f:
                for chunk in upload.chunks():
                    f.write(chunk)
            subprocess.call(
                shlex.split("/home/ubuntu/myprojectdir/extract.sh {}".format(dirname))
            )
            for output in sorted(os.listdir(dirname)):
                file_name = os.path.join(dirname, output)
                f = open(file_name, "rb")
                new_id = Image.objects.latest("id").id + 1
                image = Image.objects.create(
                    id=new_id, submission=submission, image=File(f)
                )
                new_name = os.path.join(dirname, f"{image.id}.jpg")
                os.rename(file_name, new_name)
        else:
            for upload in request.data.values():
                new_id = Image.objects.latest("id").id + 1
                with open(os.path.join(dirname, str(new_id) + ".jpg"), "wb+") as f:
                    for chunk in upload.chunks():
                        f.write(chunk)
                upload.seek(0)
                image = Image.objects.create(
                    id=new_id, submission=submission, image=upload
                )
        return HttpResponse(status=201)


class MoreDataViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    parser_classes = (FormParser, MultiPartParser)

    @action(detail=True, methods=["post"])
    def submit(self, request):
        request.data.pop("csrfmiddlewaretoken", None)
        return HttpResponse(status=201)


class HistoryView(LoginRequiredMixin, tables.SingleTableView):
    login_url = "/login/"
    table_class = SubmissionTable
    template_name = "history.html"

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user).order_by("-id")


class HistoryAdminView(StaffRequiredMixin, tables.SingleTableView):
    login_url = "/login/"
    table_class = SubmissionAdminTable
    template_name = "admin.html"

    def get_queryset(self):
        return Submission.objects.order_by("-id")


class UnprocessedCropsView(APIView):
    """
    List all unprocessed crops.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        crops = Crop.objects.filter(certified=ImageStatus.DEFAULT).order_by("id")
        serializer = CropSerializer(crops, many=True)
        return Response(serializer.data)


class AnalysisCropView(APIView):
    """
    List all unprocessed crops.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        crops = Crop.objects.filter(certified=ImageStatus.DEFAULT).order_by("id")
        serializer = CropSerializer(crops, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = AnalysisCropSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            crop = Crop.objects.get(id=data["crop"])
            manipulation = AnalysisCrop.objects.create(
                crop=crop, analysis_type=data["analysis_type"]
            )
            manipulation.analysis_image = File(request.FILES["analysis_image"])
            manipulation.save()
            crop.certified = ImageStatus.PROCESSED
            crop.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
