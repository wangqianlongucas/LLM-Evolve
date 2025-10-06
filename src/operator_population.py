"""算子种群管理"""
import random
from llm_client import llm_client
from evaluator import evaluate_operator

# 手写种子算子（带距离矩阵参数）
SEED_OPERATORS = {
    "2-swap": """def operator(solution, dist_matrix=None):
    import random
    new_sol = solution[:]
    i, j = random.sample(range(len(solution)), 2)
    new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol""",
    
    "2-opt": """def operator(solution, dist_matrix=None):
    import random
    new_sol = solution[:]
    i, j = sorted(random.sample(range(len(solution)), 2))
    new_sol[i:j+1] = list(reversed(new_sol[i:j+1]))
    return new_sol""",
    
    "3-swap": """def operator(solution, dist_matrix=None):
    import random
    new_sol = solution[:]
    i, j, k = random.sample(range(len(solution)), 3)
    new_sol[i], new_sol[j], new_sol[k] = new_sol[j], new_sol[k], new_sol[i]
    return new_sol""",
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
        
        # 添加种子算子
        for name, code in SEED_OPERATORS.items():
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
        user_prompt = f"""生成一个TSP邻域算子。

要求：
1. 函数名必须是 operator
2. 输入参数：
   - solution (list): 城市访问顺序，如 [0, 2, 1, 3]
   - dist_matrix (list[list]): 城市间距离矩阵，dist_matrix[i][j]表示城市i到j的距离
3. 输出：new_solution (list) - 新的城市访问顺序
4. 可以利用dist_matrix设计基于距离的智能策略（如优先交换距离大的边）
5. 只返回函数定义代码，不要任何解释文字
6. 确保代码简洁高效，避免死循环
{diversity_hint}

示例格式：
def operator(solution, dist_matrix=None):
    import random
    new_sol = solution[:]
    i, j = random.sample(range(len(solution)), 2)
    new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol

高级示例（使用距离矩阵）：
def operator(solution, dist_matrix=None):
    import random
    new_sol = solution[:]
    # 找到距离最大的边进行优化
    if dist_matrix:
        max_dist = 0
        max_i = 0
        for i in range(len(solution)):
            j = (i + 1) % len(solution)
            dist = dist_matrix[solution[i]][solution[j]]
            if dist > max_dist:
                max_dist = dist
                max_i = i
        # 对最差的边进行2-opt
        i, j = max_i, (max_i + 2) % len(solution)
        if i > j:
            i, j = j, i
        new_sol[i:j+1] = list(reversed(new_sol[i:j+1]))
    else:
        i, j = random.sample(range(len(solution)), 2)
        new_sol[i], new_sol[j] = new_sol[j], new_sol[i]
    return new_sol"""
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

