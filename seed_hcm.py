"""
seed_hcm.py - Nhập dữ liệu mẫu TP. Hồ Chí Minh vào database

Chạy bằng lệnh:
    python seed_hcm.py
(Trong thư mục dss_logistics, với server KHÔNG đang chạy hoặc trong terminal khác)
"""

import os
import django

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dss_project.settings')
django.setup()

from core.models import Location

# Xóa dữ liệu cũ (tọa độ 0,0 không dùng được)
deleted_count = Location.objects.all().delete()[0]
print(f"Đã xóa {deleted_count} bản ghi cũ.")

# Dữ liệu thật tại TP. HCM
sample_locations = [
    {"name": "Kho Tân Bình (Depot)",    "latitude": 10.8017, "longitude": 106.6500, "is_depot": True},
    {"name": "Khách hàng Quận 1",       "latitude": 10.7769, "longitude": 106.7009, "is_depot": False},
    {"name": "Khách hàng Quận 3",       "latitude": 10.7880, "longitude": 106.6700, "is_depot": False},
    {"name": "Khách hàng Bình Thạnh",   "latitude": 10.8037, "longitude": 106.7124, "is_depot": False},
    {"name": "Khách hàng Quận 7",       "latitude": 10.7369, "longitude": 106.7218, "is_depot": False},
    {"name": "Khách hàng Gò Vấp",       "latitude": 10.8350, "longitude": 106.6800, "is_depot": False},
]

for data in sample_locations:
    loc = Location.objects.create(**data)
    icon = "🏭" if data["is_depot"] else "📦"
    print(f"  {icon} Tạo: {loc.name} ({loc.latitude}, {loc.longitude})")

print(f"\n✅ Tạo xong {len(sample_locations)} địa điểm!")
print("   Truy cập http://127.0.0.1:8000/map-result/ để xem kết quả.")
