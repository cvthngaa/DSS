from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from .utils.dss_csv import dss_engine_analyze
from .utils.tsp_db import solve_routes_from_db
from .models import Location
import os
import csv
import io
from django.conf import settings
from .forms import CsvUploadForm

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
    """
    [DSS - Data Management] View xử lý upload file CSV danh sách địa điểm.
    - File CSV gồm 3 cột: name/ten, latitude/lat, longitude/lng
    - Dòng 1 (sau header) mặc định là Depot (Kho).
    - Dòng 2 trở đi là Khách hàng.
    """
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            import_mode = form.cleaned_data['import_mode']
            
            try:
                # Đọc nội dung file, dùng utf-8-sig để tự động loại bỏ ký tự BOM nếu file lưu từ Excel
                file_data = csv_file.read().decode('utf-8-sig')
                csv_reader = csv.DictReader(io.StringIO(file_data))
                
                # Chuyển header về lower case để dễ so sánh và linh hoạt
                headers = [h.lower().strip() for h in csv_reader.fieldnames] if csv_reader.fieldnames else []
                
                # Tìm các cột tương ứng
                name_col = next((h for h in headers if h in ['name', 'ten']), None)
                lat_col = next((h for h in headers if h in ['latitude', 'lat']), None)
                lng_col = next((h for h in headers if h in ['longitude', 'lng']), None)
                
                if not name_col or not lat_col or not lng_col:
                    messages.error(request, 'File CSV thiếu cột bắt buộc. Cần có 3 cột: (name/ten), (latitude/lat), (longitude/lng).')
                    return render(request, 'core/upload_data.html', {'form': form})
                
                locations_to_create = []
                row_idx = 0
                
                for row_dict in csv_reader:
                    # Tạo dictionary dễ truy cập theo header dạng lower
                    row_lower = {k.lower().strip() if k else '': v for k, v in row_dict.items() if k}
                    
                    name_val = row_lower.get(name_col, '').strip()
                    lat_str = row_lower.get(lat_col, '').strip()
                    lng_str = row_lower.get(lng_col, '').strip()
                    
                    if not name_val or not lat_str or not lng_str:
                        # Bỏ qua dòng thiếu dữ liệu
                        continue
                        
                    try:
                        lat_val = float(lat_str)
                        lng_val = float(lng_str)
                    except ValueError:
                        messages.error(request, f'Lỗi ở dòng {row_idx + 2}: Tọa độ không hợp lệ ({lat_str}, {lng_str}).')
                        return render(request, 'core/upload_data.html', {'form': form})
                        
                    # Áp dụng quy tắc: dòng đầu tiên (row_idx=0) là kho nếu overwrite.
                    if import_mode == 'overwrite':
                        is_depot = (row_idx == 0)
                    else:
                        # Chế độ append: mặc định không tạo điểm kho mới nếu đã từng có kho trong DB
                        has_depot_already = Location.objects.filter(is_depot=True).exists()
                        is_depot = (row_idx == 0) and not has_depot_already
                    
                    locations_to_create.append(Location(
                        name=name_val,
                        latitude=lat_val,
                        longitude=lng_val,
                        is_depot=is_depot
                    ))
                    row_idx += 1
                
                if not locations_to_create:
                    messages.error(request, 'File CSV không có dữ liệu hợp lệ (hoặc chỉ có tiêu đề).')
                    return render(request, 'core/upload_data.html', {'form': form})
                
                # Thực hiện lưu vào database
                if import_mode == 'overwrite':
                    Location.objects.all().delete()
                    
                Location.objects.bulk_create(locations_to_create)
                
                messages.success(request, f'Tải dữ liệu CSV thành công! Đã xử lý {len(locations_to_create)} địa điểm.')
                return redirect('manage_locations')
                
            except Exception as e:
                messages.error(request, f'Đã xảy ra lỗi khi đọc file: {str(e)}')
    else:
        form = CsvUploadForm()
        
    return render(request, 'core/upload_data.html', {'form': form})
def manage_locations(request):
    """
    [DSS - Data Management] Trang quản lý địa điểm.
    Hiển thị danh sách các điểm đã lưu, có Form để thêm mới.
    """
    locations = Location.objects.all()
    return render(request, 'core/manage_locations.html', {'locations': locations})


def add_location(request):
    """
    [DSS - Data Management] Nhận dữ liệu Form và lưu điểm mới vào SQLite.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        is_depot = request.POST.get('is_depot', '0') == '1'

        # Kiểm tra đầu vào cơ bản
        if not name or not latitude or not longitude:
            messages.error(request, 'Vui lòng nhập đủ Tên, Latitude và Longitude.')
            return redirect('manage_locations')

        try:
            lat_val = float(latitude)
            lng_val = float(longitude)
        except ValueError:
            messages.error(request, 'Latitude và Longitude phải là số thực.')
            return redirect('manage_locations')

        Location.objects.create(
            name=name,
            latitude=lat_val,
            longitude=lng_val,
            is_depot=is_depot
        )
        messages.success(request, f'Đã thêm địa điểm "{name}" thành công!')

    return redirect('manage_locations')


def delete_location(request, pk):
    """
    [DSS - Data Management] Xóa 1 địa điểm theo ID (Chấp nhận GET/POST).
    """
    print(f"[DEBUG] delete_location called! pk={pk}, method={request.method}")
    loc = get_object_or_404(Location, pk=pk)
    name = loc.name
    print(f"[DEBUG] Deleting: {name} (id={pk})")
    loc.delete()
    print(f"[DEBUG] Deleted successfully: {name}")

    messages.success(request, f'Đã xóa địa điểm "{name}".')
    return redirect('manage_locations')


def map_result(request):
    """
    [DSS Engine + UI] Trang kết quả tối ưu hóa tuyến đường.
    Gọi Engine tsp_db để chạy Nearest Neighbor → truyền kết quả cho Leaflet.
    """
    result = solve_routes_from_db()
    return render(request, 'core/map_result.html', {'result': result})

def download_tsp_results(request):
    """Tải xuống file kết quả thực nghiệm TSP."""
    excel_path = os.path.join(settings.BASE_DIR, 'tsp_results.xlsx')
    if os.path.exists(excel_path):
        return FileResponse(open(excel_path, 'rb'), as_attachment=True, filename='tsp_results.xlsx')
    else:
        messages.error(request, "File chưa được tạo. Vui lòng chạy tính toán lại.")
        return redirect('map_result')
