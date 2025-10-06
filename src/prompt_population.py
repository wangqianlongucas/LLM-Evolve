"""Prompt种群管理"""
import random
from llm_client import llm_client
from config import PROMPT_ALPHA, PROMPT_BETA

# 预定义Prompt模板
SEED_PROMPTS = [
    "改进搜索效率，减少不必要的移动",
    "增加邻域多样性，避免局部最优",
    "结合贪心思想，优先改进差的边",
    "引入自适应机制，根据搜索阶段调整策略",
    "设计更大的邻域结构，提高搜索能力",
]

class PromptPopulation:
    def __init__(self, pop_size):
        self.pop_size = pop_size
        self.population = []
        self.next_id = 0
        
    def initialize(self):
        """初始化Prompt种群"""
        print("📝 初始化Prompt种群...")
        for text in SEED_PROMPTS[:self.pop_size]:
            self.population.append({
                "id": f"prompt_{self.next_id}",
                "text": text,
                "fitness": 0.0,
                "usage_count": 0,
                "offspring_fitness": [],  # 记录生成的子代fitness
                "offspring_improvements": []  # 记录相对父本的提升
            })
            self.next_id += 1
        print(f"✅ 初始Prompt种群: {len(self.population)}个\n")
    
    def select_prompt(self):
        """选择Prompt（轮盘赌 + ε-greedy）"""
        # 如果所有prompt都没用过，或10%概率探索
        if all(p["usage_count"] == 0 for p in self.population) or random.random() < 0.1:
            return random.choice(self.population)
        
        # 基于fitness选择
        # 将fitness转换为正权重（处理负数和0的情况）
        min_fitness = min(p["fitness"] for p in self.population)
        weights = [p["fitness"] - min_fitness + 1 for p in self.population]
        
        # 再次检查，确保有正权重
        if sum(weights) <= 0:
            return random.choice(self.population)
        
        return random.choices(self.population, weights=weights, k=1)[0]
    
    def record_usage(self, prompt_id, offspring_fitness, parent_fitness):
        """记录Prompt使用结果"""
        for prompt in self.population:
            if prompt["id"] == prompt_id:
                prompt["usage_count"] += 1
                prompt["offspring_fitness"].append(offspring_fitness)
                
                improvement = (parent_fitness - offspring_fitness) / parent_fitness
                prompt["offspring_improvements"].append(improvement)
                break
    
    def update_fitness(self):
        """更新Prompt的fitness"""
        for prompt in self.population:
            if len(prompt["offspring_fitness"]) > 0:
                # 计算平均性能（越小越好，所以取负）
                avg_objective = sum(prompt["offspring_fitness"]) / len(prompt["offspring_fitness"])
                # 计算平均提升率
                avg_improvement = sum(prompt["offspring_improvements"]) / len(prompt["offspring_improvements"])
                
                # fitness = 提升率权重 - 性能惩罚（归一化到合理范围）
                # 注意：这里简化处理，主要看提升率
                prompt["fitness"] = PROMPT_BETA * avg_improvement - PROMPT_ALPHA * avg_objective / 10000
        
        print("📊 Prompt fitness更新:")
        for p in sorted(self.population, key=lambda x: x["fitness"], reverse=True)[:3]:
            print(f"  {p['text'][:40]}... -> {p['fitness']:.3f} (用{p['usage_count']}次)")
    
    def generate_new_prompt(self):
        """使用LLM生成新Prompt（元Prompt）"""
        top_prompts = sorted(self.population, key=lambda x: x["fitness"], reverse=True)[:3]
        
        system_prompt = "你是进化计算专家，只输出一句话的改进方向，不要任何解释"
        user_prompt = f"""当前效果最好的算子改进方向：
{chr(10).join([f"{i+1}. {p['text']} (效果评分: {p['fitness']:.3f})" for i, p in enumerate(top_prompts)])}

【任务】
生成一个新的、更有潜力的TSP邻域算子改进方向。

【要求】
1. 一句话描述，15-30字
2. 要具体、可操作
3. 不要重复已有方向
4. 只输出改进方向文本，不要编号、不要解释

【输出格式】
改进搜索效率，减少不必要的移动"""
        
        new_text = llm_client.generate(system_prompt, user_prompt)
        
        if new_text:
            # 清理可能的编号、标点
            new_text = new_text.strip().lstrip('1234567890.、- ').strip()
            
            # 替换最差的prompt
            worst_idx = min(range(len(self.population)), 
                          key=lambda i: self.population[i]["fitness"])
            
            self.population[worst_idx] = {
                "id": f"prompt_{self.next_id}",
                "text": new_text,
                "fitness": 0.0,
                "usage_count": 0,
                "offspring_fitness": [],
                "offspring_improvements": []
            }
            self.next_id += 1
            print(f"  🆕 新Prompt: {new_text}")
    
    def get_top_k(self, k):
        """获取top K个体（按fitness降序）"""
        sorted_pop = sorted(self.population, key=lambda x: x["fitness"], reverse=True)
        return sorted_pop[:min(k, len(sorted_pop))]

