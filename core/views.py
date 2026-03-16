from django.shortcuts import render, redirect
from django.contrib import messages
from .utils.dss_csv import dss_engine_analyze
import os
from django.conf import settings

def home(request):
    """Trang chủ hiển thị thông tin giới thiệu Đồ án DSS"""
    return render(request, 'core/home.html')

def dss_dashboard(request):
    """
    Trang phân tích và trả kết quả Khuyến nghị.
    Nó gọi trực tiếp Backend Engine và gửi cho template HTMl hiển thị.
    """
    report = dss_engine_analyze()
    
    # Render ra HTML. Dữ liệu báo cáo sẽ nằm dưới biến context 'report'
    return render(request, 'core/dashboard.html', {'report': report})

def upload_data(request):
    """View nhận file từ Form, lưu đè lên file CSV có sẵn"""
    if request.method == 'POST':
        locations_file = request.FILES.get('locations_file')
        routes_file = request.FILES.get('routes_file')
        
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        
        if locations_file:
            path_loc = os.path.join(data_dir, 'locations.csv')
            with open(path_loc, 'wb+') as dest:
                for chunk in locations_file.chunks():
                    dest.write(chunk)
                    
        if routes_file:
            path_route = os.path.join(data_dir, 'routes.csv')
            with open(path_route, 'wb+') as dest:
                for chunk in routes_file.chunks():
                    dest.write(chunk)
                    
        if locations_file or routes_file:
            messages.success(request, 'Đã cập nhật dữ liệu CSV thành công!')
            return redirect('upload_data')
            
    return render(request, 'core/upload_data.html')


