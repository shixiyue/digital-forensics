from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path(
        "2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea/",
        views.certificate_demo,
        name="certificate",
    ),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("sent/", views.activation_sent_view, name="activation_sent"),
    path("activate/<slug:uidb64>/<slug:token>/", views.activate, name="activate"),
    path("about/", views.about_view, name="about"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("more_data/", views.data_view, name="more_data"),
    path("more_data/api/post/", views.MoreDataViewSet.as_view({"post": "submit"})),
    path("adjust_crops/", views.adjust_view, name="adjust_crops"),
    path("dashboard/api/post/", views.SubmissionViewSet.as_view({"post": "submit"})),
    path("dashboard/api/view/", views.SubmissionViewSet.as_view({"get": "list"})),
    path("history/", views.HistoryView.as_view(), name="history"),
    path(
        "history/submission/<int:id>/",
        views.submission_details_view,
        name="submission_details",
    ),
    path(
        "history/submission/<int:sub_id>/analysis/<int:crop_id>/",
        views.analysis_view,
        name="analysis",
    ),
    path("history_admin/", views.HistoryAdminView.as_view(), name="history_admin"),
    path(
        "history_admin/submission/<int:id>/",
        views.submission_admin_view,
        name="submission_admin",
    ),
    path(
        "history_admin/submission/<int:sub_id>/analysis/<int:crop_id>/",
        views.analysis_admin_view,
        name="analysis_admin",
    ),
    path(
        "api/crops/unprocessed/",
        views.UnprocessedCropsView.as_view(),
        name="unprocessed_crops",
    ),
    path(
        "api/analysis_crop/",
        csrf_exempt(views.AnalysisCropView.as_view()),
        name="analysis_crop",
    ),
    # Forget Password
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html',
            subject_template_name='password_reset_subject.txt',
            email_template_name='password_reset_email.html',
        ),
        name='password_reset'),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html'
        ),
        name='password_reset_confirm'),
    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete'),
]
