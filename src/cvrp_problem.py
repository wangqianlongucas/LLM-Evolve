"""CVRP问题定义（Capacitated Vehicle Routing Problem）"""
import math
import random

def calculate_distance(coord1, coord2):
    """计算两点欧式距离"""
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def calculate_distance_matrix(coords):
    """预计算距离矩阵"""
    n = len(coords)
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = calculate_distance(coords[i], coords[j])
            dist_matrix[i][j] = dist
            dist_matrix[j][i] = dist
    return dist_matrix

def calculate_total_cost(solution, dist_matrix, depot=0):
    """
    计算CVRP总路径长度
    solution: list of lists，每个子列表为一条路线的客户编号
    每条路线从depot出发，最终返回depot
    """
    cost = 0.0
    for route in solution:
        if not route:
            continue
        # depot -> 第一个客户
        cost += dist_matrix[depot][route[0]]
        # 路线内部
        for i in range(len(route) - 1):
            cost += dist_matrix[route[i]][route[i + 1]]
        # 最后一个客户 -> depot
        cost += dist_matrix[route[-1]][depot]
    return cost

def check_solution_validity(solution, n_customers, demands, capacity):
    """
    检查CVRP解的有效性
    solution: list of lists, 每个子列表为一条路线
    n_customers: 客户数量（不含depot）
    demands: 需求列表（index 0 为 depot，需求为 0）
    capacity: 车辆容量
    """
    all_customers = []
    for route_idx, route in enumerate(solution):
        route_demand = 0
        for customer in route:
            if customer == 0:
                return False, f"路线{route_idx}中包含depot节点"
            if customer < 0 or customer >= len(demands):
                return False, f"客户编号{customer}超出范围"
            route_demand += demands[customer]
            all_customers.append(customer)
        if route_demand > capacity:
            return False, f"路线{route_idx}超载: {route_demand} > {capacity}"
    
    if len(all_customers) != n_customers:
        return False, f"客户数量不匹配: 期望{n_customers}, 实际{len(all_customers)}"
    if len(set(all_customers)) != n_customers:
        return False, "存在重复访问的客户"
    if set(all_customers) != set(range(1, n_customers + 1)):
        return False, "客户编号不正确"
    return True, "有效"

def generate_initial_solution(n_customers, demands, capacity):
    """
    生成初始可行解（贪心装箱）
    将客户随机打乱后，依次装入当前路线，超载则开新路线
    """
    customers = list(range(1, n_customers + 1))
    random.shuffle(customers)
    
    routes = []
    current_route = []
    current_load = 0
    
    for c in customers:
        if current_load + demands[c] <= capacity:
            current_route.append(c)
            current_load += demands[c]
        else:
            if current_route:
                routes.append(current_route)
            current_route = [c]
            current_load = demands[c]
    
    if current_route:
        routes.append(current_route)
    
    return routes

class CVRPInstance:
    """CVRP算例"""
    def __init__(self, name, coords, demands, capacity, num_vehicles=None, optimal=None):
        self.name = name
        self.coords = coords
        self.demands = demands
        self.capacity = capacity
        self.num_vehicles = num_vehicles
        self.n_nodes = len(coords)           # 包含depot
        self.n_customers = len(coords) - 1   # 不含depot
        self.optimal = optimal
        # 预计算距离矩阵
        self.dist_matrix = calculate_distance_matrix(coords)
        print(f"  ✅ {name}: 预计算距离矩阵 ({self.n_nodes}x{self.n_nodes}), "
              f"{self.n_customers}个客户, 容量={capacity}")
