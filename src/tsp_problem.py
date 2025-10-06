"""TSP问题定义"""
import math
import random

def calculate_distance(coord1, coord2):
    """计算两点欧式距离"""
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def calculate_total_cost(solution, coords):
    """计算TSP路径总长度"""
    cost = 0
    for i in range(len(solution)):
        city1 = solution[i]
        city2 = solution[(i + 1) % len(solution)]
        cost += calculate_distance(coords[city1], coords[city2])
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

