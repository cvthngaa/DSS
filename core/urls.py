from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dss_dashboard, name='dashboard'),
    path('upload/', views.upload_data, name='upload_data'),
    # Địa điểm động
    path('locations/', views.manage_locations, name='manage_locations'),
    path('locations/add/', views.add_location, name='add_location'),
    path('locations/delete/<int:pk>/', views.delete_location, name='delete_location'),
    # Kết quả tối ưu hóa
    path('map-result/', views.map_result, name='map_result'),
    path('download-tsp/', views.download_tsp_results, name='download_tsp'),
]

