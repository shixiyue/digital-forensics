from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea/', views.certificate_demo, name='certificate'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('sent/', views.activation_sent_view, name="activation_sent"),
    path('activate/<slug:uidb64>/<slug:token>/',
         views.activate, name='activate'),
    path('about/', views.about_view, name='about'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/api/post/',
         views.SubmissionViewSet.as_view({'post': 'submit'})),
    path('dashboard/api/view/',
         views.SubmissionViewSet.as_view({'get': 'list'})),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('history/submission/<int:id>/',
         views.details_view, name='submission_details'),
    path('history/submission/<int:id>/analysis/<str:sig>/',
         views.analysis_view, name='analysis')
]
