"""EA主循环"""
from llm_client import llm_client
from operator_population import OperatorPopulation
from prompt_population import PromptPopulation
from evaluator import evaluate_operator
from logger import ExperimentLogger
from config import MAX_GENERATIONS, OPERATOR_POP_SIZE, PROMPT_POP_SIZE, PROMPT_UPDATE_FREQ, TOP_K_FOR_DIVERSITY

class EAController:
    def __init__(self, instances, log_dir="logs"):
        self.instances = instances
        self.operator_pop = OperatorPopulation(OPERATOR_POP_SIZE, instances)
        self.prompt_pop = PromptPopulation(PROMPT_POP_SIZE)
        self.logger = ExperimentLogger(log_dir)
        
    def run(self):
        """EA主循环"""
        print("=" * 60)
        print("🚀 LLM驱动的双种群进化算法")
        print("=" * 60 + "\n")
        
        # 初始化
        self.operator_pop.initialize()
        self.prompt_pop.initialize()
        
        best_ever = self.operator_pop.get_best()
        self.logger.log_best(best_ever)
        
        # EA循环
        for gen in range(MAX_GENERATIONS):
            print(f"\n{'='*60}")
            print(f"📍 Generation {gen+1}/{MAX_GENERATIONS}")
            print(f"{'='*60}")
            
            # 获取当前top K（用于防止重复）
            top_k_operators = self.operator_pop.get_top_k(TOP_K_FOR_DIVERSITY)
            top_k_prompts = self.prompt_pop.get_top_k(TOP_K_FOR_DIVERSITY)
            
            # ===== 批量生成子代 =====
            offspring_list = []
            
            print(f"🔄 生成 {OPERATOR_POP_SIZE} 个子代...")
            
            for i in range(OPERATOR_POP_SIZE):
                print(f"\n  [{i+1}/{OPERATOR_POP_SIZE}]")
                
                # 1. 选择父本
                parent = self.operator_pop.select_parent()
                print(f"    1️⃣ 父本: {parent['id']}, fitness={parent['fitness']:.2f}")
                
                # 2. 选择Prompt
                selected_prompt = self.prompt_pop.select_prompt()
                print(f"    2️⃣ Prompt: {selected_prompt['text'][:50]}...")
                
                # 3. LLM生成新算子（带diversity约束）
                print(f"    3️⃣ LLM生成...")
                offspring_code = self._generate_offspring(
                    parent["code"], 
                    selected_prompt["text"],
                    top_k_operators,
                    top_k_prompts
                )
                
                if offspring_code:
                    # 4. 评估
                    print(f"    4️⃣ 评估...")
                    result = evaluate_operator(offspring_code, self.instances)
                    
                    if result["success"]:
                        offspring = {
                            "id": f"op_{self.operator_pop.next_id}",
                            "code": offspring_code,
                            "fitness": result["avg_objective"],
                            "time": result["avg_time"],
                            "parent_id": parent["id"],
                            "prompt_used": selected_prompt["text"]
                        }
                        self.operator_pop.next_id += 1
                        offspring_list.append(offspring)
                        
                        print(f"    ✅ fitness={offspring['fitness']:.2f}")
                        
                        # 记录Prompt使用结果
                        self.prompt_pop.record_usage(
                            selected_prompt["id"],
                            offspring["fitness"],
                            parent["fitness"]
                        )
                        
                        # 更新最优
                        if offspring["fitness"] < best_ever["fitness"]:
                            best_ever = offspring
                            self.logger.log_best(best_ever)
                            self.logger.save_best_operator(best_ever)
                            print(f"    🎉 发现新最优解: {best_ever['fitness']:.2f}")
                    else:
                        print(f"    ❌ 评估失败: {result.get('error', 'Unknown')[:50]}")
                else:
                    print(f"    ❌ LLM生成失败")
            
            # 5. 更新种群（父代+子代选择）
            if offspring_list:
                print(f"\n5️⃣ 更新种群: {len(offspring_list)}个有效子代")
                self.operator_pop.update_population(offspring_list)
                print(f"   新种群大小: {len(self.operator_pop.population)}")
            else:
                print(f"\n5️⃣ ⚠️ 本代未生成有效子代")
            
            # 记录本代日志
            current_best = self.operator_pop.get_best()
            self.logger.log_generation(gen + 1, {
                "offspring_count": len(offspring_list),
                "current_best_fitness": current_best["fitness"],
                "best_ever_fitness": best_ever["fitness"],
                "population_size": len(self.operator_pop.population)
            })
            
            # ===== Prompt进化 =====
            if (gen + 1) % PROMPT_UPDATE_FREQ == 0:
                print(f"\n🔄 Prompt种群进化...")
                self.prompt_pop.update_fitness()
                self.prompt_pop.generate_new_prompt()
            
            # 当前最优
            print(f"\n📊 当前最优: {current_best['fitness']:.2f}")
            print(f"📊 历史最优: {best_ever['fitness']:.2f}")
            
            # 定期保存种群快照
            if (gen + 1) % 5 == 0 or (gen + 1) == MAX_GENERATIONS:
                self.logger.save_population(gen + 1, self.operator_pop.population, self.prompt_pop.population)
        
        print(f"\n{'='*60}")
        print("🎉 进化完成!")
        print(f"{'='*60}")
        print(f"最优fitness: {best_ever['fitness']:.2f}")
        print(f"最优算子代码:\n{best_ever['code']}")
        
        # 保存最终结果
        self.logger.save_best_operator(best_ever)
        self.logger.save_population(MAX_GENERATIONS, self.operator_pop.population, self.prompt_pop.population)
        
        # 保存实验总结
        import config
        config_dict = {
            "MAX_GENERATIONS": MAX_GENERATIONS,
            "OPERATOR_POP_SIZE": OPERATOR_POP_SIZE,
            "PROMPT_POP_SIZE": PROMPT_POP_SIZE,
            "TOP_K_FOR_DIVERSITY": TOP_K_FOR_DIVERSITY,
            "SA_TIMEOUT": config.SA_TIMEOUT
        }
        self.logger.save_summary(best_ever, config_dict)
        
        return best_ever
    
    def _generate_offspring(self, parent_code, prompt_text, top_k_operators, top_k_prompts):
        """LLM生成子代算子（带diversity约束）"""
        # 构建top K代码摘要
        top_k_summary = "\n".join([
            f"算子{i+1} (fitness={op['fitness']:.2f}): {op['code'][:100]}..."
            for i, op in enumerate(top_k_operators)
        ])
        
        system_prompt = "你是TSP算法专家，只输出Python代码，不要任何解释"
        user_prompt = f"""基于以下父本算子进行改进：

【父本代码】
{parent_code}

【改进方向】
{prompt_text}

【当前种群Top {TOP_K_FOR_DIVERSITY}算子概览】
{top_k_summary}

【重要】请生成与上述算子有明显差异的新算子，避免简单重复。

【输出要求】
1. 函数名必须是 operator
2. 输入参数：
   - solution (list): 城市访问顺序
   - dist_matrix (list[list]): 距离矩阵，可用于智能决策
3. 输出：new_solution (list) - 新的城市访问顺序
4. 可以利用dist_matrix设计基于距离的策略
5. 只返回改进后的函数定义，不要任何解释、注释或markdown标记
6. 确保代码可直接执行，避免死循环和复杂逻辑
7. 与现有top算子保持差异性，创新邻域结构

【输出格式】
def operator(solution, dist_matrix=None):
    # 改进后的代码
    ...
    return new_sol"""
        
        return llm_client.generate(system_prompt, user_prompt)

