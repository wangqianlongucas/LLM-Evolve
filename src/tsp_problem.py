"""TSP问题定义"""
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

def calculate_total_cost(solution, dist_matrix):
    """计算TSP路径总长度（使用距离矩阵）"""
    cost = 0
    for i in range(len(solution)):
        city1 = solution[i]
        city2 = solution[(i + 1) % len(solution)]
        cost += dist_matrix[city1][city2]
    return cost

def check_solution_validity(solution, n_cities):
    """检查解的有效性"""
    if len(solution) != n_cities:
        return False, "城市数量不匹配"
    if len(set(solution)) != n_cities:
        return False, "存在重复访问的城市"
    if set(solution) != set(range(n_cities)):
        return False, "城市索引不正确"
    return True, "有效"

def generate_initial_solution(n_cities):
    """生成初始解"""
    solution = list(range(n_cities))
    random.shuffle(solution)
    return solution

class TSPInstance:
    """TSP算例"""
    def __init__(self, name, coords, optimal=None):
        self.name = name
        self.coords = coords
        self.n_cities = len(coords)
        self.optimal = optimal
        # 预计算距离矩阵
        self.dist_matrix = calculate_distance_matrix(coords)
        print(f"  ✅ {name}: 预计算距离矩阵 ({self.n_cities}x{self.n_cities})")

