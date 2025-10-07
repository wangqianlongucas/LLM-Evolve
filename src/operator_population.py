"""算子种群管理"""
import random
from llm_client import llm_client
from evaluator import evaluate_operator

# 手写种子算法组件（算子 + 信息加工 + 接受准则）
SEED_COMPONENTS = {
    "2-swap_classic": """
def operator(solution, dist_matrix, info):
    import random
    new_sol = solution[:]
    i, j = random.sample(range(len(solution)), 2)
    new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    # 计算搜索进度
    progress = iteration / total_iterations if total_iterations > 0 else 0
    temperature_ratio = T / T_init if T_init > 0 else 0
    improvement = (current_cost - best_cost) / best_cost if best_cost > 0 else 0
    
    # 分析历史趋势
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
    # 经典Metropolis准则
    if delta < 0:
        return True
    return random.random() < math.exp(-delta / T) if T > 0 else False
""",
    
    "2-opt_adaptive": """
def operator(solution, dist_matrix, info):
    import random
    new_sol = solution[:]
    # 根据搜索进度调整邻域大小
    progress = info.get('progress', 0)
    if progress < 0.3:
        # 早期：大邻域
        i, j = sorted(random.sample(range(len(solution)), 2))
        new_sol[i:j+1] = list(reversed(new_sol[i:j+1]))
    else:
        # 后期：小邻域
        i = random.randint(0, len(solution)-1)
        j = (i + random.randint(1, 3)) % len(solution)
        if i > j:
            i, j = j, i
        new_sol[i:j+1] = list(reversed(new_sol[i:j+1]))
    return new_sol

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    progress = iteration / total_iterations if total_iterations > 0 else 0
    # 计算改进速度
    improvement_rate = 0
    if len(cost_history) >= 2:
        improvement_rate = (cost_history[-1] - cost_history[0]) / cost_history[0] if cost_history[0] > 0 else 0
    return {'progress': progress, 'improvement_rate': improvement_rate}

def accept_criterion(delta, T, info):
    import random
    import math
    # 自适应接受准则
    progress = info.get('progress', 0)
    if delta < 0:
        return True
    # 后期更严格
    adjusted_T = T * (1 - progress * 0.5)
    return random.random() < math.exp(-delta / adjusted_T) if adjusted_T > 0 else False
"""
}

class OperatorPopulation:
    def __init__(self, pop_size, instances):
        self.pop_size = pop_size
        self.instances = instances
        self.population = []
        self.next_id = 0
        
    def initialize(self):
        """初始化种群：种子算子 + LLM生成"""
        print("🔧 初始化算子种群...")
        
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
        
        # LLM生成剩余个体（带diversity约束）
        attempts = 0
        max_attempts = self.pop_size * 3  # 最多尝试3倍
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
        # 构建已有算子摘要
        if existing_operators:
            existing_summary = "\n".join([
                f"算子{i+1}: {op['code'][:120]}..."
                for i, op in enumerate(existing_operators[-3:])  # 只显示最近的3个
            ])
            diversity_hint = f"""
【已有算子（避免重复）】
{existing_summary}

请生成与上述算子不同的新算子，可以尝试：
- 不同的邻域结构（如3-opt, insert, reverse等）
- 组合多种操作
- 自适应策略
"""
        else:
            diversity_hint = ""
        
        system_prompt = "你是TSP算法专家，只输出代码，不要任何解释"
        user_prompt = f"""生成一套完整的TSP模拟退火算法组件（三个函数）。

要求：
{diversity_hint}

【必须生成3个函数】

1. operator函数 - 邻域算子
   - 参数：solution (list), dist_matrix (list[list]), info (dict)
   - 返回：new_solution (list)
   - 可以利用info中的进度信息设计自适应策略

2. process_info函数 - 信息加工
   - 参数：iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history
   - cost_history (list): 近100次的目标值历史，可用于分析趋势
   - 返回：info (dict) - 包含各种有用信息
   - 可以计算进度、温度比率、改进幅度、历史趋势等

3. accept_criterion函数 - 接受准则
   - 参数：delta (float), T (float), info (dict)
   - 返回：bool - 是否接受
   - 可以设计自适应的接受策略

示例：
def operator(solution, dist_matrix, info):
    import random
    new_sol = solution[:]
    progress = info.get('progress', 0)
    # 根据progress调整策略
    i, j = random.sample(range(len(solution)), 2)
    new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    progress = iteration / total_iterations if total_iterations > 0 else 0
    temperature_ratio = T / T_init if T_init > 0 else 0
    # 分析历史趋势
    trend = 0
    if len(cost_history) >= 10:
        trend = (cost_history[-1] - cost_history[-10]) / cost_history[-10] if cost_history[-10] > 0 else 0
    return {{'progress': progress, 'temperature_ratio': temperature_ratio, 'trend': trend}}

def accept_criterion(delta, T, info):
    import random
    import math
    if delta < 0:
        return True
    return random.random() < math.exp(-delta / T) if T > 0 else False
"""
        return llm_client.generate(system_prompt, user_prompt)
    
    def select_parent(self):
        """选择父本（轮盘赌，fitness越小越好）"""
        # 转换为最大化问题
        max_fitness = max(ind["fitness"] for ind in self.population)
        weights = [max_fitness - ind["fitness"] + 1 for ind in self.population]
        return random.choices(self.population, weights=weights, k=1)[0]
    
    def add_offspring(self, code, parent_id, prompt_text):
        """添加新个体"""
        result = evaluate_operator(code, self.instances)
        
        if result["success"]:
            offspring = {
                "id": f"op_{self.next_id}",
                "code": code,
                "fitness": result["avg_objective"],
                "time": result["avg_time"],
                "parent_id": parent_id,
                "prompt_used": prompt_text
            }
            self.next_id += 1
            
            # 环境选择：替换最差个体
            worst_idx = max(range(len(self.population)), 
                          key=lambda i: self.population[i]["fitness"])
            
            if offspring["fitness"] < self.population[worst_idx]["fitness"]:
                self.population[worst_idx] = offspring
                return True, offspring
        
        return False, None
    
    def get_best(self):
        """获取最优个体"""
        return min(self.population, key=lambda x: x["fitness"])
    
    def get_top_k(self, k):
        """获取top K个体"""
        sorted_pop = sorted(self.population, key=lambda x: x["fitness"])
        return sorted_pop[:min(k, len(sorted_pop))]
    
    def update_population(self, offspring_list):
        """批量更新种群（父代+子代选择）"""
        # 合并父代和子代
        combined = self.population + offspring_list
        # 按fitness排序，选择前pop_size个
        combined.sort(key=lambda x: x["fitness"])
        self.population = combined[:self.pop_size]

