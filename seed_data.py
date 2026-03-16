import os
import django

# Khởi tạo môi trường Django cho Script chạy bên ngoài manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dss_project.settings')
django.setup()

from core.models import Location, RoutePlan, RouteStop

def create_sample_data():
    print("Đang tạo Depot và Khách hàng...")

    # 1. Tạo Depot
    depot, created = Location.objects.get_or_create(
        name="Depot (Kho Chính)",
        defaults={'x': 0.0, 'y': 0.0, 'is_depot': True}
    )

    # 2. Tạo KH A, B, C
    a, _ = Location.objects.get_or_create(name="Khách hàng A", defaults={'x': 10.0, 'y': 10.0, 'is_depot': False})
    b, _ = Location.objects.get_or_create(name="Khách hàng B", defaults={'x': 20.0, 'y': 5.0, 'is_depot': False})
    c, _ = Location.objects.get_or_create(name="Khách hàng C", defaults={'x': 5.0, 'y': 20.0, 'is_depot': False})
    
    print("Đang tạo tuyến đường ban đầu...")

    # 3. Tạo 1 RoutePlan chưa tối ưu
    plan, created = RoutePlan.objects.get_or_create(
        name="Tuyến hiện tại (Chưa tối ưu)",
        defaults={'is_optimized': False, 'total_distance': 0.0}
    )

    # 4. Gán các điểm dừng vào Tuyến này
    # Nếu đã tạo rồi thì bỏ qua để tránh rác
    if created:
        RouteStop.objects.create(route=plan, location=depot, stop_order=1)
        RouteStop.objects.create(route=plan, location=a, stop_order=2)
        RouteStop.objects.create(route=plan, location=b, stop_order=3)
        RouteStop.objects.create(route=plan, location=c, stop_order=4)
        
        # Thường xe tải giao xong sẽ quay về kho
        RouteStop.objects.create(route=plan, location=depot, stop_order=5)

    print("Hoàn tất thêm dữ liệu mẫu!")

if __name__ == '__main__':
    create_sample_data()
