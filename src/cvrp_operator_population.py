"""CVRP算子种群管理"""
import random
from cvrp_evaluator import evaluate_operator

# 手写种子算法组件（算子 + 信息加工 + 接受准则）
SEED_COMPONENTS = {
    "swap_inter_route": """
def operator(solution, dist_matrix, info):
    import random
    import copy
    routes = [r[:] for r in solution]
    # 至少需要2条路线才能做路线间交换
    if len(routes) < 2:
        # 只有1条路线，做路线内swap
        r = routes[0]
        if len(r) >= 2:
            i, j = random.sample(range(len(r)), 2)
            r[i], r[j] = r[j], r[i]
        return routes
    
    demands = info.get('demands', [])
    capacity = info.get('capacity', 1e9)
    
    # 选两条非空路线
    non_empty = [i for i, r in enumerate(routes) if len(r) > 0]
    if len(non_empty) < 2:
        return routes
    r1_idx, r2_idx = random.sample(non_empty, 2)
    
    # 各选一个客户尝试交换
    i = random.randint(0, len(routes[r1_idx]) - 1)
    j = random.randint(0, len(routes[r2_idx]) - 1)
    
    c1 = routes[r1_idx][i]
    c2 = routes[r2_idx][j]
    
    # 检查交换后容量是否可行
    load1 = sum(demands[c] for c in routes[r1_idx]) - demands[c1] + demands[c2]
    load2 = sum(demands[c] for c in routes[r2_idx]) - demands[c2] + demands[c1]
    
    if load1 <= capacity and load2 <= capacity:
        routes[r1_idx][i] = c2
        routes[r2_idx][j] = c1
    
    return routes

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    progress = iteration / total_iterations if total_iterations > 0 else 0
    temperature_ratio = T / T_init if T_init > 0 else 0
    improvement = (current_cost - best_cost) / best_cost if best_cost > 0 else 0
    
    recent_trend = 0
    if len(cost_history) >= 10:
        recent_avg = sum(cost_history[-10:]) / 10
        earlier_avg = sum(cost_history[-20:-10]) / 10 if len(cost_history) >= 20 else recent_avg
        recent_trend = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
    
    return {
        'progress': progress,
        'temperature_ratio': temperature_ratio,
        'improvement': improvement,
        'recent_trend': recent_trend
    }

def accept_criterion(delta, T, info):
    import random
    import math
    if delta < 0:
        return True
    return random.random() < math.exp(-delta / T) if T > 0 else False
""",
    
    "relocate_adaptive": """
def operator(solution, dist_matrix, info):
    import random
    routes = [r[:] for r in solution]
    demands = info.get('demands', [])
    capacity = info.get('capacity', 1e9)
    progress = info.get('progress', 0)
    
    non_empty = [i for i, r in enumerate(routes) if len(r) > 0]
    if len(non_empty) < 2:
        # 路线内2-opt
        if non_empty and len(routes[non_empty[0]]) >= 2:
            r = routes[non_empty[0]]
            i, j = sorted(random.sample(range(len(r)), 2))
            r[i:j+1] = reversed(r[i:j+1])
        return routes
    
    # 选择源路线和目标路线
    src_idx = random.choice(non_empty)
    dst_candidates = [i for i in non_empty if i != src_idx]
    if not dst_candidates:
        return routes
    dst_idx = random.choice(dst_candidates)
    
    # 从源路线随机选一个客户
    if len(routes[src_idx]) == 0:
        return routes
    pos = random.randint(0, len(routes[src_idx]) - 1)
    customer = routes[src_idx][pos]
    
    # 检查目标路线容量
    dst_load = sum(demands[c] for c in routes[dst_idx])
    if dst_load + demands[customer] <= capacity:
        routes[src_idx].pop(pos)
        # 根据进度决策插入位置
        if progress < 0.5:
            # 早期：随机插入
            insert_pos = random.randint(0, len(routes[dst_idx]))
        else:
            # 后期：贪心插入（找最佳位置）
            best_pos = 0
            best_increase = float('inf')
            for p in range(len(routes[dst_idx]) + 1):
                # 计算插入代价
                if p == 0:
                    prev_node = 0  # depot
                else:
                    prev_node = routes[dst_idx][p - 1]
                if p == len(routes[dst_idx]):
                    next_node = 0  # depot
                else:
                    next_node = routes[dst_idx][p]
                increase = (dist_matrix[prev_node][customer] + 
                           dist_matrix[customer][next_node] - 
                           dist_matrix[prev_node][next_node])
                if increase < best_increase:
                    best_increase = increase
                    best_pos = p
            insert_pos = best_pos
        routes[dst_idx].insert(insert_pos, customer)
        
        # 清理空路线
        routes = [r for r in routes if len(r) > 0]
    
    return routes

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    progress = iteration / total_iterations if total_iterations > 0 else 0
    improvement_rate = 0
    if len(cost_history) >= 2:
        improvement_rate = (cost_history[-1] - cost_history[0]) / cost_history[0] if cost_history[0] > 0 else 0
    return {'progress': progress, 'improvement_rate': improvement_rate}

def accept_criterion(delta, T, info):
    import random
    import math
    progress = info.get('progress', 0)
    if delta < 0:
        return True
    adjusted_T = T * (1 - progress * 0.5)
    return random.random() < math.exp(-delta / adjusted_T) if adjusted_T > 0 else False
"""
}

class CVRPOperatorPopulation:
    def __init__(self, pop_size, instances):
        self.pop_size = pop_size
        self.instances = instances
        self.population = []
        self.next_id = 0
        
    def initialize(self):
        """初始化种群：种子算子 + LLM生成"""
        print("🔧 初始化CVRP算子种群...")
        
        # 添加种子算法组件
        for name, code in SEED_COMPONENTS.items():
            result = evaluate_operator(code, self.instances)
            if result["success"]:
                self.population.append({
                    "id": f"op_{self.next_id}",
                    "code": code,
                    "fitness": result["avg_objective"],
                    "time": result["avg_time"],
                    "source": f"seed_{name}"
                })
                self.next_id += 1
                print(f"  ✅ {name}: {result['avg_objective']:.2f}")
        
        # LLM生成剩余个体
        attempts = 0
        max_attempts = self.pop_size * 3
        while len(self.population) < self.pop_size and attempts < max_attempts:
            attempts += 1
            code = self._generate_random_operator(self.population)
            if code:
                result = evaluate_operator(code, self.instances)
                if result["success"]:
                    self.population.append({
                        "id": f"op_{self.next_id}",
                        "code": code,
                        "fitness": result["avg_objective"],
                        "time": result["avg_time"],
                        "source": "llm_init"
                    })
                    self.next_id += 1
                    print(f"  ✅ LLM生成: {result['avg_objective']:.2f}")
        
        if len(self.population) < self.pop_size:
            print(f"  ⚠️ 只生成了 {len(self.population)} 个算子（目标: {self.pop_size}）")
        
        print(f"✅ 初始种群完成，大小: {len(self.population)}\n")
    
    def _generate_random_operator(self, existing_operators):
        """生成随机算子（带diversity约束）"""
        if existing_operators:
            existing_summary = "\n".join([
                f"算子{i+1}: {op['code'][:120]}..."
                for i, op in enumerate(existing_operators[-3:])
            ])
            diversity_hint = f"""
【已有算子（避免重复）】
{existing_summary}

请生成与上述算子不同的新算子，可以尝试：
- 不同的路线间/路线内操作（如cross-exchange, or-opt, 2-opt*等）
- 组合多种操作
- 自适应策略
"""
        else:
            diversity_hint = ""
        
        system_prompt = "你是CVRP（带容量约束的车辆路径问题）算法专家，只输出代码，不要任何解释"
        user_prompt = f"""生成一套完整的CVRP模拟退火算法组件（三个函数）。

CVRP问题：给定depot（节点0）和若干客户，每个客户有需求量，车辆有固定容量，
找到最短的路线集合，使得每个客户恰好被访问一次，每条路线从depot出发返回depot，且不超载。

解的表示：list of lists，每个子列表是一条路线上的客户编号列表（不含depot）。
例如 [[1,3,5],[2,4,6]] 表示两条路线：depot->1->3->5->depot 和 depot->2->4->6->depot。

要求：
{diversity_hint}

【必须生成3个函数】

1. operator函数 - 邻域算子
   - 参数：solution (list of lists), dist_matrix (list[list]), info (dict)
   - info中包含：demands (list), capacity (int), n_customers (int), progress (float) 等
   - 返回：new_solution (list of lists)
   - 必须保证可行性：每个客户恰好出现一次，每条路线不超载

2. process_info函数 - 信息加工
   - 参数：iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history
   - 返回：info (dict)

3. accept_criterion函数 - 接受准则
   - 参数：delta (float), T (float), info (dict)
   - 返回：bool

示例：
def operator(solution, dist_matrix, info):
    import random
    routes = [r[:] for r in solution]
    demands = info.get('demands', [])
    capacity = info.get('capacity', 1e9)
    # 路线间交换客户
    ...
    return routes

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    progress = iteration / total_iterations if total_iterations > 0 else 0
    return {{'progress': progress}}

def accept_criterion(delta, T, info):
    import random
    import math
    if delta < 0:
        return True
    return random.random() < math.exp(-delta / T) if T > 0 else False
"""
        from llm_client import llm_client
        return llm_client.generate(system_prompt, user_prompt)
    
    def select_parent(self):
        """选择父本（轮盘赌，fitness越小越好）"""
        max_fitness = max(ind["fitness"] for ind in self.population)
        weights = [max_fitness - ind["fitness"] + 1 for ind in self.population]
        return random.choices(self.population, weights=weights, k=1)[0]
    
    def get_best(self):
        """获取最优个体"""
        return min(self.population, key=lambda x: x["fitness"])
    
    def get_top_k(self, k):
        """获取top K个体"""
        sorted_pop = sorted(self.population, key=lambda x: x["fitness"])
        return sorted_pop[:min(k, len(sorted_pop))]
    
    def update_population(self, offspring_list):
        """批量更新种群（父代+子代选择）"""
        combined = self.population + offspring_list
        combined.sort(key=lambda x: x["fitness"])
        self.population = combined[:self.pop_size]
