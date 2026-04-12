"""
core/utils/tsp_db.py
[DSS] - Model Management + DSS Engine

Đọc Location từ SQLite, chạy các thuật toán Nearest Neighbor, 2-opt, GA, ACO
dựa trên khoảng cách đường bộ thực tế từ OSRM (Table API).
"""

import math
import json
import urllib.request
import urllib.error
import random
import os
import pandas as pd
import scipy.stats as stats
from django.conf import settings
from ..models import Location
from .tsp_math import solve_tsp_2opt, solve_tsp_ga, solve_tsp_aco

DEFAULT_LOCATIONS = [
    {"name": "Kho Tân Bình (Mẫu)",      "latitude": 10.8017, "longitude": 106.6500, "is_depot": True},
    {"name": "Khách hàng Quận 1",      "latitude": 10.7769, "longitude": 106.7009, "is_depot": False},
    {"name": "Khách hàng Bình Thạnh",  "latitude": 10.8037, "longitude": 106.7124, "is_depot": False},
]

def _seed_sample_data():
    if Location.objects.exists():
        return
    for data in DEFAULT_LOCATIONS:
        Location.objects.create(**data)

def haversine(loc1, loc2):
    R = 6371
    lat1, lon1 = math.radians(loc1.latitude),  math.radians(loc1.longitude)
    lat2, lon2 = math.radians(loc2.latitude),  math.radians(loc2.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_osrm_distance_matrix(locations):
    """
    Gọi OSRM Table API để lấy ma trận khoảng cách đường bộ.
    Trả về dict hai chiều: matrix[loc1.id][loc2.id] = khoảng cách (km).
    Nếu lỗi, fallback về Haversine.
    """
    matrix = {}
    
    # Chuẩn bị chuỗi toạ độ cho OSRM (lon,lat)
    coords_str = ";".join([f"{loc.longitude},{loc.latitude}" for loc in locations])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DSS-Logistics/1.0 (Student Project)'})
        response = urllib.request.urlopen(req, timeout=5)
        res = json.loads(response.read().decode())
        
        if res.get("code") == "Ok" and "distances" in res:
            distances = res["distances"]
            for i, loc_from in enumerate(locations):
                matrix[loc_from.id] = {}
                for j, loc_to in enumerate(locations):
                    matrix[loc_from.id][loc_to.id] = float(distances[i][j]) / 1000.0
            return matrix, True
    except Exception as e:
        print("Lỗi gọi OSRM Table API, dùng Haversine:", e)
        
    for loc_from in locations:
        matrix[loc_from.id] = {}
        for loc_to in locations:
            matrix[loc_from.id][loc_to.id] = haversine(loc_from, loc_to)
            
    return matrix, False

def build_segments(route, dist_matrix):
    segments = []
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i+1]
        segments.append({
            'from_name': a.name,
            'to_name':   b.name,
            'from_lat':  a.latitude,
            'from_lng':  a.longitude,
            'to_lat':    b.latitude,
            'to_lng':    b.longitude,
            'km': round(dist_matrix[a.id][b.id], 3),
        })
    return segments

def solve_routes_from_db():
    _seed_sample_data()

    depot = Location.objects.filter(is_depot=True).first()
    customers = list(Location.objects.filter(is_depot=False))

    if not depot:
        return {'error': 'Chưa có Kho xuất phát (Depot). Vui lòng thêm 1 điểm và tick "Là Kho".'}
    if len(customers) < 1:
        return {'error': 'Cần ít nhất 1 điểm Khách hàng để tính tuyến đường.'}

    all_locations = [depot] + customers
    dist_matrix, used_osrm = get_osrm_distance_matrix(all_locations)
    
    # ── 1. Nearest Neighbor ──
    unvisited = list(customers)
    current = depot
    route_nn = [depot]
    dist_nn = 0.0
    while unvisited:
        nearest = None
        min_dist = float('inf')
        for loc in unvisited:
            d = dist_matrix[current.id][loc.id]
            if d < min_dist:
                min_dist = d
                nearest = loc
        route_nn.append(nearest)
        dist_nn += min_dist
        current = nearest
        unvisited.remove(nearest)
    dist_nn += dist_matrix[current.id][depot.id]
    route_nn.append(depot)
    
    # ── 2. 2-opt ──
    dist_2opt, route_2opt, logs_2opt = solve_tsp_2opt(route_nn, dist_matrix)
    
    # ── 3. GA ──
    dist_ga, route_ga, logs_ga = solve_tsp_ga(depot, customers, dist_matrix, pop_size=50, generations=100)
    
    # ── 4. ACO ──
    dist_aco, route_aco, logs_aco = solve_tsp_aco(depot, customers, dist_matrix, num_ants=15, iterations=60)
    
    results = {
        'NN': {
            'route': route_nn,
            'segments': build_segments(route_nn, dist_matrix),
            'total_km': round(dist_nn, 2)
        },
        '2-opt': {
            'route': route_2opt,
            'segments': build_segments(route_2opt, dist_matrix),
            'total_km': round(dist_2opt, 2)
        },
        'GA': {
            'route': route_ga,
            'segments': build_segments(route_ga, dist_matrix),
            'total_km': round(dist_ga, 2)
        },
        'ACO': {
            'route': route_aco,
            'segments': build_segments(route_aco, dist_matrix),
            'total_km': round(dist_aco, 2)
        }
    }
    
    best_algo = min(results.keys(), key=lambda k: results[k]['total_km'])
    results[best_algo]['is_best'] = True

    stat_p_value = None
    stat_best_algo = None

    # --- Xuất báo cáo Excel ---
    try:
        logs_nn = []
        # Nearest Neighbor deterministic, copy 10 lần
        path_nn = "->".join(str(loc.name) for loc in route_nn)
        for i in range(10):
            logs_nn.append({
                'Algorithm': 'NN',
                'Run': i + 1,
                'Distance': dist_nn,
                'Path': path_nn
            })
            
        all_logs = logs_nn + logs_2opt + logs_ga + logs_aco
        df = pd.DataFrame(all_logs)
        
        # Thống kê
        stats_df = df.groupby('Algorithm')['Distance'].agg(['mean', 'std', 'var', 'min']).reset_index()
        stats_df.rename(columns={'mean': 'Mean', 'std': 'Std', 'var': 'Variance', 'min': 'Best'}, inplace=True)
        
        # Xác định thuật toán tốt nhất (Dựa trên Mean và Std)
        best_algo_stat = stats_df.sort_values(by=['Mean', 'Std']).iloc[0]['Algorithm']
        
        # Tính p-value (ANOVA)
        groups = [df[df['Algorithm'] == algo]['Distance'].values for algo in df['Algorithm'].unique()]
        if len(groups) > 1:
            f_stat, p_value = stats.f_oneway(*groups)
        else:
            p_value = None
            
        test_result = pd.DataFrame([{
            'Test': 'ANOVA (p-value)',
            'p-value': p_value,
            'Best Algorithm (Stat)': best_algo_stat,
            'Interpretation': 'Thống kê có sự khác biệt' if p_value and p_value < 0.05 else 'Không có sự khác biệt rõ rệt'
        }])
        
        stat_p_value = p_value
        stat_best_algo = best_algo_stat
        
        excel_path = os.path.join(settings.BASE_DIR, 'tsp_results.xlsx')
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Raw_Data', index=False)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            test_result.to_excel(writer, sheet_name='Statistical_Test', index=False)
            
    except Exception as e:
        print("Lỗi xuất file Excel:", e)

    return {
        'error': None,
        'algorithms': results,
        'n_customers': len(customers),
        'best_algo': best_algo,
        'used_osrm': used_osrm,
        'stat_p_value': stat_p_value,
        'stat_best_algo': stat_best_algo
    }
