import math

def calculate_euclidean_distance(loc1, loc2):
    """
    Tính khoảng cách giữa 2 điểm (Object có x, y) dựa trên công thức Euclid.
    d = sqrt((x2 - x1)^2 + (y2 - y1)^2)
    """
    return math.sqrt((loc2.x - loc1.x)**2 + (loc2.y - loc1.y)**2)

def build_distance_matrix(locations):
    """
    Tạo ma trận khoảng cách từ một list các objects có 'id', 'x', 'y'.
    Kết quả trả về là một dictionary 2 chiều:
    matrix[id1][id2] = distance
    """
    matrix = {}
    for lot_from in locations:
        matrix[lot_from.id] = {}
        for lot_to in locations:
            if lot_from.id == lot_to.id:
                matrix[lot_from.id][lot_to.id] = 0.0
            else:
                matrix[lot_from.id][lot_to.id] = calculate_euclidean_distance(lot_from, lot_to)
    return matrix

def solve_tsp_nearest_neighbor(depot, customers):
    """
    Thuật toán Nearest Neighbor (Láng giềng gần nhất - Tham lam).
    Mục tiêu: Tìm 1 chu trình TSP tương đối bắt đầu từ Depot, đi qua tất cả Customers và quay về Depot.
    """
    # 1. Khởi tạo mảng và biến
    all_locations = [depot] + customers
    dist_matrix = build_distance_matrix(all_locations)
    
    unvisited = [c for c in customers] # Copy list để dễ xóa
    current_node = depot
    
    optimized_route = [depot] # Tuyến đường bắt đầu bằng Depot
    total_distance = 0.0
    
    # 2. Vòng lặp tìm điểm gần nhất
    while unvisited:
        nearest_node = None
        min_dist = float('inf') # Khởi tạo vô cực
        
        # Duyệt nốt những điểm chưa đi
        for node in unvisited:
            dist = dist_matrix[current_node.id][node.id]
            if dist < min_dist:
                min_dist = dist
                nearest_node = node
                
        # Ghi nhận chặng
        optimized_route.append(nearest_node)
        total_distance += min_dist
        
        # Di chuyển xe sang điểm đó và loại nó khỏi danh sách
        current_node = nearest_node
        unvisited.remove(nearest_node)
        
    # 3. Kết thúc: Xe chạy về kho
    return_dist = dist_matrix[current_node.id][depot.id]
    total_distance += return_dist
    optimized_route.append(depot)
    
    return total_distance, optimized_route
