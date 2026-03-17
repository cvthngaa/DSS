"""
core/utils/tsp_db.py
[DSS] - Model Management + DSS Engine

Đọc Location từ SQLite, chạy thuật toán Nearest Neighbor (Haversine),
trả về thứ tự tối ưu để frontend vẽ lên bản đồ + gọi OSRM.
"""

import math
import itertools
from ..models import Location



# ─────────────────────────────────────────────
# AUTO-SEED: tự động tạo dữ liệu khi DB trống
# ─────────────────────────────────────────────
DEFAULT_LOCATIONS = [
    {"name": "Kho Tân Bình (Mẫu)",      "latitude": 10.8017, "longitude": 106.6500, "is_depot": True},
    {"name": "Khách hàng Quận 1",      "latitude": 10.7769, "longitude": 106.7009, "is_depot": False},
    {"name": "Khách hàng Bình Thạnh",  "latitude": 10.8037, "longitude": 106.7124, "is_depot": False},
]

def _seed_sample_data():
    """Tạo 3 điểm mẫu HCM nếu DB đang trống. Chỉ chạy 1 lần."""
    if Location.objects.exists():
        return  # Đã có dữ liệu, không làm gì
    for data in DEFAULT_LOCATIONS:
        Location.objects.create(**data)


# ─────────────────────────────────────────────
# 1. HAVERSINE: tính khoảng cách thực trên Trái Đất
# ─────────────────────────────────────────────
def haversine(loc1, loc2):
    """
    Tính khoảng cách (km) giữa 2 điểm dựa trên Latitude/Longitude thực tế.
    Công thức Haversine đúng trên mặt cầu ( khác với Euclid chỉ dùng x/y phẳng ).
    """
    R = 6371  # Bán kính Trái Đất tính bằng km

    lat1, lon1 = math.radians(loc1.latitude),  math.radians(loc1.longitude)
    lat2, lon2 = math.radians(loc2.latitude),  math.radians(loc2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


# ─────────────────────────────────────────────
# 2. NEAREST NEIGHBOR - đọc thẳng từ DB
# ─────────────────────────────────────────────
def solve_routes_from_db():
    """
    [DSS Engine] Đọc Location từ SQLite, chạy thuật toán Nearest Neighbor.

    Trả về dict chứa:
      - 'ordered_locations': list object Location theo thứ tự đi tối ưu
      - 'segments': list dict mô tả từng chặng (from, to, haversine_km)
      - 'total_haversine_km': tổng km (đường thẳng) để ước lượng sơ bộ
      - 'error': chuỗi lỗi nếu không đủ dữ liệu
    """
    # Tự động seed 3 điểm mẫu nếu DB trống (khởi chạy lần đầu)
    _seed_sample_data()

    depot = Location.objects.filter(is_depot=True).first()
    customers = list(Location.objects.filter(is_depot=False))

    # Kiểm tra dữ liệu đầu vào
    if not depot:
        return {'error': 'Chưa có Kho xuất phát (Depot). Vui lòng thêm 1 điểm và tick "Là Kho".'}
    if len(customers) < 1:
        return {'error': 'Cần ít nhất 1 điểm Khách hàng để tính tuyến đường.'}

    # ── Nearest Neighbor ─────────────────────
    unvisited = list(customers)      # Tập chưa ghé thăm
    current   = depot                # Điểm đang đứng
    ordered   = [depot]              # Kết quả thứ tự đi
    total_km  = 0.0

    while unvisited:
        nearest  = None
        min_dist = float('inf')
        for loc in unvisited:
            d = haversine(current, loc)
            if d < min_dist:
                min_dist = d
                nearest  = loc

        ordered.append(nearest)
        total_km += min_dist
        current   = nearest
        unvisited.remove(nearest)

    # Quay về Kho
    return_km = haversine(current, depot)
    total_km += return_km
    ordered.append(depot)

    # ── Xây dựng danh sách từng chặng ────────
    segments = []
    for i in range(len(ordered) - 1):
        a = ordered[i]
        b = ordered[i + 1]
        segments.append({
            'from_name': a.name,
            'to_name':   b.name,
            'from_lat':  a.latitude,
            'from_lng':  a.longitude,
            'to_lat':    b.latitude,
            'to_lng':    b.longitude,
            'haversine_km': round(haversine(a, b), 3),
        })

    # ── Khuyến nghị DSS ──────────────────────
    n_points = len(customers)
    if n_points <= 3:
        recommendation = (
            f"Tuyến {n_points} điểm ngắn, thuật toán Nearest Neighbor cho kết quả rất tốt. "
            "KHUYẾN NGHỊ: Áp dụng ngay tuyến đề xuất."
        )
    elif n_points <= 8:
        recommendation = (
            f"{n_points} điểm giao hàng — Nearest Neighbor đưa ra lời giải hợp lý. "
            "KHUYẾN NGHỊ: Xem xét tuyến đề xuất trước khi phê duyệt."
        )
    else:
        recommendation = (
            f"Có {n_points} điểm — với số lượng lớn, Nearest Neighbor có thể chưa tối ưu ~15%. "
            "KHUYẾN NGHỊ: Cân nhắc dùng thuật toán nâng cao hơn (VD: 2-opt) cho bài toán thực tế."
        )

    return {
        'error': None,
        'ordered_locations': ordered,
        'segments': segments,
        'total_haversine_km': round(total_km, 2),
        'n_customers': n_points,
        'recommendation': recommendation,
        'all_options': _get_all_route_options(depot, customers) if n_points <= 5 else None
    }


def _get_all_route_options(depot, customers):
    """
    [DSS Comparison] Liệt kê tất cả các hoán vị điểm giao (n!)
    và tính tổng chi phí để so sánh. Chỉ thực hiện khi n nhỏ (n <= 5).
    """
    n = len(customers)
    all_perms = list(itertools.permutations(customers))
    options = []

    for perm in all_perms:
        route = [depot] + list(perm) + [depot]
        dist = 0.0
        for i in range(len(route) - 1):
            dist += haversine(route[i], route[i+1])
        
        # Tạo chuỗi mô tả lộ trình: Kho -> A -> B -> Kho
        route_str = " → ".join([loc.name for loc in route])
        
        # Danh sách tọa độ cho OSRM request
        coords = [{"lat": loc.latitude, "lng": loc.longitude} for loc in route]

        options.append({
            'route_str': route_str,
            'total_km': round(dist, 2),
            'coords': coords
        })

    # Sắp xếp theo khoảng cách tăng dần để thấy phương án tốt nhất ở đầu
    options.sort(key=lambda x: x['total_km'])
    return options
