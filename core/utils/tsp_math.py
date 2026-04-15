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
    logs = []

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
            
        logs.append({
            'Algorithm': '2-opt',
            'Run': run_idx + 1,
            'Distance': best_dist,
            'Path': "->".join(str(loc.name) for loc in best_route)
        })
            
    return overall_best_dist, overall_best_route, logs

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
    logs = []

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
            
        logs.append({
            'Algorithm': 'GA',
            'Run': run_idx + 1,
            'Distance': best_dist,
            'Path': "->".join(str(loc.name) for loc in best_route)
        })
            
    return overall_best_dist, overall_best_route, logs

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
    logs = []

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
            
        logs.append({
            'Algorithm': 'ACO',
            'Run': run_idx + 1,
            'Distance': best_dist,
            'Path': "->".join(str(loc.name) for loc in best_route) if best_route else ""
        })
            
    return overall_best_dist, overall_best_route, logs


# ============================================================
# PIPELINE THỐNG KÊ: Kiểm định t-test từng cặp thuật toán
# ============================================================

def run_tsp_statistics(all_logs, excel_path):
    """
    Pipeline thống kê t-test pairwise cho kết quả TSP.
    
    So sánh tất cả các cặp thuật toán bằng kiểm định t-test (two-sided → one-sided).
    Đếm số lần thắng (wins) để xác định thuật toán tốt nhất.
    Xuất kết quả ra file Excel gồm 4 sheet.
    
    Params:
        all_logs: list of dict {Algorithm, Run, Distance, Path}
        excel_path: đường dẫn file Excel xuất ra
    Returns:
        dict {best_algorithm, conclusion} hoặc None nếu lỗi
    """
    import numpy as np
    import pandas as pd
    from scipy.stats import ttest_ind
    from itertools import combinations
    
    try:
        df = pd.DataFrame(all_logs)
        
        # ── 1. Tách dữ liệu theo thuật toán ──
        algorithms = df['Algorithm'].unique().tolist()
        algo_distances = {}
        for algo in algorithms:
            algo_distances[algo] = df[df['Algorithm'] == algo]['Distance'].values
        
        # ── 2. Thống kê mô tả ──
        # μ = (1/n) * Σxᵢ
        # s² = (1/(n-1)) * Σ(xᵢ - μ)²
        # s = sqrt(s²)
        stats_rows = []
        for algo in algorithms:
            distances = algo_distances[algo]
            n = len(distances)
            mean_val = np.mean(distances)                    # μ
            variance_val = np.var(distances, ddof=1)         # s² (unbiased, ddof=1)
            std_val = np.std(distances, ddof=1)              # s  (unbiased)
            stats_rows.append({
                'Algorithm': algo,
                'Mean': round(mean_val, 6),
                'Std': round(std_val, 6),
                'Variance': round(variance_val, 6)
            })
        stats_df = pd.DataFrame(stats_rows)
        
        # ── 3. Kiểm định t-test từng cặp (6 cặp) ──
        # Giả thuyết:
        #   H0: μ_A = μ_B (không có khác biệt)
        #   H1: μ_A < μ_B (A tốt hơn B vì distance nhỏ hơn)
        pairwise_rows = []
        wins = {algo: 0 for algo in algorithms}
        
        for algo_a, algo_b in combinations(algorithms, 2):
            dist_a = algo_distances[algo_a]
            dist_b = algo_distances[algo_b]
            mean_a = np.mean(dist_a)
            mean_b = np.mean(dist_b)
            
            # t-test hai phía (two-sided)
            t_stat, p_two = ttest_ind(dist_a, dist_b)
            
            # Chuyển sang một phía (one-sided):
            # Luôn test theo hướng: thuật toán có mean nhỏ hơn tốt hơn
            if mean_a < mean_b:
                # H1: μ_A < μ_B → t_stat âm khi A thực sự nhỏ hơn
                p_one = p_two / 2 if t_stat < 0 else 1 - (p_two / 2)
            elif mean_a > mean_b:
                # H1: μ_B < μ_A → t_stat dương khi A thực sự lớn hơn
                p_one = p_two / 2 if t_stat > 0 else 1 - (p_two / 2)
            else:
                p_one = 1.0  # mean bằng nhau → không có winner
            
            # Quy tắc quyết định
            winner = ''
            if p_one < 0.05:
                # Bác bỏ H0 → thuật toán có mean nhỏ hơn thắng
                winner = algo_a if mean_a < mean_b else algo_b
                wins[winner] += 1
            # Nếu p >= 0.05 → không đủ bằng chứng, không có winner
            
            pairwise_rows.append({
                'Algo_A': algo_a,
                'Algo_B': algo_b,
                'Mean_A': round(mean_a, 4),
                'Mean_B': round(mean_b, 4),
                't_stat': round(t_stat, 4),
                'p_value': round(p_one, 6),
                'Winner': winner if winner else 'Không đủ bằng chứng'
            })
        
        pairwise_df = pd.DataFrame(pairwise_rows)
        
        # ── 4. Xác định thuật toán tốt nhất ──
        # Thuật toán có wins cao nhất → best
        # Trường hợp hòa (wins bằng nhau) → chọn thuật toán có mean nhỏ hơn
        max_wins = max(wins.values())
        candidates = [algo for algo, w in wins.items() if w == max_wins]
        
        if len(candidates) == 1:
            best_algorithm = candidates[0]
        else:
            # Tie-break: chọn thuật toán có mean nhỏ hơn
            algo_means = {algo: np.mean(algo_distances[algo]) for algo in candidates}
            best_algorithm = min(algo_means, key=algo_means.get)
        
        # Tạo summary dataframe
        summary_rows = [{'Algorithm': algo, 'Wins': wins[algo]} for algo in algorithms]
        summary_df = pd.DataFrame(summary_rows)
        summary_df = summary_df.sort_values('Wins', ascending=False).reset_index(drop=True)
        
        # ── 5. Xuất file Excel (4 sheets) ──
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Raw_Data', index=False)
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            pairwise_df.to_excel(writer, sheet_name='Pairwise_Test', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # ── 6. Câu kết luận ──
        conclusion = (
            f"Thuật toán {best_algorithm} thắng nhiều nhất trong các kiểm định "
            f"t-test (p < 0.05), và có giá trị trung bình nhỏ hơn nên được "
            f"đánh giá là tối ưu nhất."
        )
        
        return {
            'best_algorithm': best_algorithm,
            'conclusion': conclusion
        }
        
    except Exception as e:
        print("Lỗi trong pipeline thống kê t-test:", e)
        import traceback
        traceback.print_exc()
        return None
