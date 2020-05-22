from django.urls import path
from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

#router = DefaultRouter()
#router.register(r'dashboard', views.SubmissionViewSet)

urlpatterns = [
    path('', views.index_view, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('sent/', views.activation_sent_view, name="activation_sent"),
    path('activate/<slug:uidb64>/<slug:token>/', views.activate, name='activate'),
    path('about/', views.about_view, name='about'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/api/post/', views.SubmissionViewSet.as_view({'post': 'submit'})),
    path('dashboard/api/view/', views.SubmissionViewSet.as_view({'get': 'list'})),
]
