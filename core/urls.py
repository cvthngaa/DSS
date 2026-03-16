from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dss_dashboard, name='dashboard'),
    path('upload/', views.upload_data, name='upload_data'),
]

