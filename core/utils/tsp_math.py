import math
import random

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

def solve_tsp_2opt(route, dist_matrix, runs=10):
    """
    Thuật toán 2-opt (Local Search - tối ưu cục bộ).
    Chạy 'runs' lần (1 lần route gốc, 9 lần route ngẫu nhiên), trả về kết quả tốt nhất.
    """
    overall_best_route = None
    overall_best_dist = float('inf')

    def calculate_route_distance(r):
        dist = 0.0
        for i in range(len(r) - 1):
            dist += dist_matrix[r[i].id][r[i+1].id]
        return dist

    for run_idx in range(runs):
        if run_idx == 0:
            current_initial_route = list(route)
        else:
            # Randomize inner path for different local optima exploration
            customers = route[1:-1]
            random.shuffle(customers)
            current_initial_route = [route[0]] + customers + [route[-1]]

        best_route = list(current_initial_route)
        best_dist = calculate_route_distance(best_route)
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(best_route) - 2):
                for j in range(i + 1, len(best_route) - 1):
                    # Đảo đoạn từ i đến j
                    new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                    new_dist = calculate_route_distance(new_route)
                    
                    if new_dist < best_dist:
                        best_route = new_route
                        best_dist = new_dist
                        improved = True
                        break # Cải thiện xong thì break khỏi vòng for j để xét từ đầu
                if improved:
                    break
                    
        if best_dist < overall_best_dist:
            overall_best_dist = best_dist
            overall_best_route = best_route
            
    return overall_best_dist, overall_best_route

def solve_tsp_ga(depot, customers, dist_matrix, pop_size=50, generations=100, mutation_rate=0.1, runs=10):
    """
    Thuật toán Genetic Algorithm (GA - Di truyền).
    Chạy 'runs' lần, lấy kết quả cá thể xuất sắc nhất.
    """
    if not customers:
        return 0.0, [depot, depot]

    def calculate_route_distance(r):
        dist = 0.0
        for i in range(len(r) - 1):
            dist += dist_matrix[r[i].id][r[i+1].id]
        return dist
        
    def fitness(individual):
        route = [depot] + individual + [depot]
        dist = calculate_route_distance(route)
        return 1.0 / (dist + 1e-6)

    overall_best_route = None
    overall_best_dist = float('inf')

    for run_idx in range(runs):
        # Khởi tạo quần thể ngẫu nhiên
        population = []
        for _ in range(pop_size):
            individual = list(customers)
            random.shuffle(individual)
            population.append(individual)

        for gen in range(generations):
            # Đánh giá fitness và sắp xếp giảm dần
            population.sort(key=lambda ind: fitness(ind), reverse=True)
            
            # Chọn lọc và Lai ghép (Crossover - OX: Order Crossover)
            new_population = population[:2] # Elitism: Giữ lại 2 cá thể tốt nhất
            
            while len(new_population) < pop_size:
                # Chọn ngẫu nhiên 2 cá thể (ưu tiên nhóm tốt)
                parent1 = random.choice(population[:pop_size//2])
                parent2 = random.choice(population[:pop_size//2])
                
                # Lấy ngẫu nhiên đoạn lai ghép
                start, end = sorted(random.sample(range(len(customers)), 2))
                child = [None] * len(customers)
                child[start:end+1] = parent1[start:end+1]
                p2_filtered = [c for c in parent2 if c not in child]
                
                idx = 0
                for i in range(len(customers)):
                    if child[i] is None:
                        child[i] = p2_filtered[idx]
                        idx += 1
                        
                # Đột biến (Mutation - Swap)
                if random.random() < mutation_rate:
                    idx1, idx2 = random.sample(range(len(customers)), 2)
                    child[idx1], child[idx2] = child[idx2], child[idx1]
                    
                new_population.append(child)
                
            population = new_population
            
        best_individual = max(population, key=lambda ind: fitness(ind))
        best_route = [depot] + best_individual + [depot]
        best_dist = calculate_route_distance(best_route)
        
        if best_dist < overall_best_dist:
            overall_best_dist = best_dist
            overall_best_route = best_route
            
    return overall_best_dist, overall_best_route

def solve_tsp_aco(depot, customers, dist_matrix, num_ants=10, iterations=50, alpha=1.0, beta=2.0, evaporation_rate=0.5, Q=100.0, runs=10):
    """
    Thuật toán Ant Colony Optimization (ACO - Bầy kiến).
    Chạy 'runs' lần, lấy kết quả bầy kiến xuất sắc nhất.
    """
    all_locations = [depot] + customers
    if not customers:
        return 0.0, [depot, depot]
    
    def calculate_route_distance(r):
        dist = 0.0
        for i in range(len(r) - 1):
            dist += dist_matrix[r[i].id][r[i+1].id]
        return dist

    overall_best_route = None
    overall_best_dist = float('inf')

    for run_idx in range(runs):
        # Khởi tạo lại ma trận pheromone cho mỗi lần chạy
        pheromone_matrix = {loc1.id: {loc2.id: 1.0 for loc2 in all_locations if loc2.id != loc1.id} for loc1 in all_locations}
        
        best_route = None
        best_dist = float('inf')
        
        for _ in range(iterations):
            all_routes = []
            all_dists = []
            
            for ant in range(num_ants):
                current_node = depot
                unvisited = list(customers)
                route = [current_node]
                route_dist = 0.0
                
                while unvisited:
                    # Tính xác suất chọn node tiếp theo
                    probabilities = []
                    total_prob = 0.0
                    for node in unvisited:
                        dist = dist_matrix[current_node.id][node.id]
                        if dist <= 0:
                            dist = 1e-6
                        tau = pheromone_matrix[current_node.id][node.id]
                        eta = 1.0 / dist
                        prob = (tau ** alpha) * (eta ** beta)
                        probabilities.append((node, prob))
                        total_prob += prob
                        
                    # Roullete wheel selection
                    rand_val = random.uniform(0, total_prob)
                    cumulative_prob = 0.0
                    selected_node = unvisited[-1] # fallback
                    for node, prob in probabilities:
                        cumulative_prob += prob
                        if cumulative_prob >= rand_val:
                            selected_node = node
                            break
                            
                    route_dist += dist_matrix[current_node.id][selected_node.id]
                    current_node = selected_node
                    route.append(current_node)
                    unvisited.remove(current_node)
                    
                # Trở về kho
                route_dist += dist_matrix[current_node.id][depot.id]
                route.append(depot)
                
                all_routes.append(route)
                all_dists.append(route_dist)
                
                if route_dist < best_dist:
                    best_dist = route_dist
                    best_route = list(route)
                    
            # Cập nhật Pheromone
            # 1. Bốc hơi
            for loc1 in all_locations:
                for loc2 in all_locations:
                    if loc1.id != loc2.id:
                        pheromone_matrix[loc1.id][loc2.id] *= (1.0 - evaporation_rate)
                        
            # 2. Kiến để lại vết
            for i in range(num_ants):
                route = all_routes[i]
                dist = all_dists[i]
                pheromone_to_add = Q / dist
                
                for j in range(len(route) - 1):
                    node_a = route[j].id
                    node_b = route[j+1].id
                    pheromone_matrix[node_a][node_b] += pheromone_to_add
                    pheromone_matrix[node_b][node_a] += pheromone_to_add # Đồ thị đối xứng vô hướng
                    
        if best_dist < overall_best_dist:
            overall_best_dist = best_dist
            overall_best_route = best_route
            
    return overall_best_dist, overall_best_route
