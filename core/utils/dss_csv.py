import csv
import os
from django.conf import settings
from .tsp_math import solve_tsp_nearest_neighbor, calculate_euclidean_distance

class CSVLocation:
    """Class giả lập cấu trúc của Database để Thuật toán có thể dùng chung"""
    def __init__(self, id, name, x, y, is_depot):
        self.id = int(id)
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.is_depot = bool(int(is_depot))

    def __str__(self):
        return f"{self.name} ({self.x}, {self.y})"

def get_csv_path(filename):
    """Lấy đường dẫn tuyệt đối của file CSV thư mục data"""
    return os.path.join(settings.BASE_DIR, 'data', filename)

def load_locations_from_csv():
    """Đọc file locations.csv và trả về tuple (depot, list_customers)"""
    file_path = get_csv_path('locations.csv')
    depot = None
    customers = []
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc = CSVLocation(
                id=row['id'], 
                name=row['name'], 
                x=row['x'], 
                y=row['y'], 
                is_depot=row['is_depot']
            )
            if loc.is_depot:
                depot = loc
            else:
                customers.append(loc)
    return depot, customers

def load_current_route_from_csv(locations_dict):
    """
    Đọc file routes.csv để biết lộ trình hiện tại do User nhập sẵn.
    Trả về: danh sách các đối tượng CSVLocation theo thứ tự.
    """
    file_path = get_csv_path('routes.csv')
    current_route = []
    
    # Sort theo stop_order
    rows = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    rows.sort(key=lambda x: int(x['stop_order']))
    
    for row in rows:
        loc_id = int(row['location_id'])
        if loc_id in locations_dict:
            current_route.append(locations_dict[loc_id])
            
    return current_route

def calculate_route_distance(route_list):
    """Tính tổng đường đi của 1 list các CSVLocation"""
    if not route_list or len(route_list) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(route_list) - 1):
        total += calculate_euclidean_distance(route_list[i], route_list[i+1])
    return total

def dss_engine_analyze():
    """
    Hàm lõi (Core) của hệ thống DSS.
    Sẽ tổng hợp dữ liệu, chạy AI/Thuật toán, tính toán và xuất ra Report.
    """
    # 1. Đọc Data Manager (CSV)
    depot, customers = load_locations_from_csv()
    
    if not depot or not customers:
        return {"error": "Không tìm thấy Depot hoặc Khách hàng trong CSV."}
        
    # Tạo dictionary tìm kiếm nhanh O(1)
    all_locs = {depot.id: depot}
    for c in customers:
        all_locs[c.id] = c
        
    # 2. Phân tích Tuyến đường Cũ
    current_route = load_current_route_from_csv(all_locs)
    current_distance = calculate_route_distance(current_route)
    
    # 3. Model Manager: Gọi thuật toán Nearest Neighbor
    optimized_distance, optimized_route = solve_tsp_nearest_neighbor(depot, customers)
    
    # 4. Tri thức (Knowledge / Rule) - Đưa ra Recommendation
    savings = current_distance - optimized_distance
    savings_percent = (savings / current_distance * 100) if current_distance > 0 else 0
    
    recommendation = ""
    if savings > 0:
        recommendation = f"Hệ thống phát hiện tuyến đường mới tiết kiệm {savings:.2f} đơn vị khoảng cách ({savings_percent:.1f}%). KHUYẾN NGHỊ: NÊN CHUYỂN ĐỔI SANG TUYẾN MỚI."
    else:
        recommendation = "Tuyến đường hiện tại đã là tối ưu nhất với thuật toán Nearest Neighbor. KHUYẾN NGHỊ: GIỮ NGUYÊN TUYẾN CŨ."

    # 5. Gói Report đưa lên View (Giao diện)
    report = {
        "current_distance": round(current_distance, 2),
        "current_route_names": [loc.name for loc in current_route],
        
        "optimized_distance": round(optimized_distance, 2),
        "optimized_route_names": [loc.name for loc in optimized_route],
        
        "savings": round(savings, 2),
        "savings_percent": round(savings_percent, 1),
        "recommendation": recommendation
    }
    
    return report
