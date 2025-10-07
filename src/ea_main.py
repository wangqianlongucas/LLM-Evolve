"""EA主循环（支持混合并发：LLM多线程 + 评估多进程）"""
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from operator_population import OperatorPopulation
from prompt_population import PromptPopulation
from logger import ExperimentLogger
from worker import evaluate_one_process
from config import MAX_GENERATIONS, OPERATOR_POP_SIZE, PROMPT_POP_SIZE, PROMPT_UPDATE_FREQ, TOP_K_FOR_DIVERSITY
from config import MAX_WORKERS_LLM, MAX_WORKERS_EVAL, PROCESS_TIMEOUT
import time

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
            
            # ===== 并发生成子代 =====
            print(f"🔄 混合并发生成 {OPERATOR_POP_SIZE} 个子代...")
            gen_start_time = time.time()
            
            # 1. 批量选择父本和Prompt
            print(f"  1️⃣ 选择父本和Prompt...")
            parent_prompt_pairs = []
            for i in range(OPERATOR_POP_SIZE):
                parent = self.operator_pop.select_parent()
                selected_prompt = self.prompt_pop.select_prompt()
                parent_prompt_pairs.append({
                    "index": i,
                    "parent": parent,
                    "prompt": selected_prompt
                })
            
            # 2. 并发LLM生成算子（多线程 - IO密集）
            llm_start = time.time()
            print(f"  2️⃣ 并发LLM生成（{MAX_WORKERS_LLM}线程 - IO密集）...")
            generated_codes = self._concurrent_generate(
                parent_prompt_pairs, 
                top_k_operators, 
                top_k_prompts
            )
            llm_time = time.time() - llm_start
            print(f"     ⏱️  LLM生成耗时: {llm_time:.1f}秒")
            
            # 3. 并发评估算子（多进程 - CPU密集）
            eval_start = time.time()
            print(f"  3️⃣ 并发评估（{MAX_WORKERS_EVAL}进程 - CPU密集）...")
            offspring_list = self._concurrent_evaluate(
                generated_codes,
                parent_prompt_pairs
            )
            eval_time = time.time() - eval_start
            print(f"     ⏱️  评估耗时: {eval_time:.1f}秒")
            
            gen_total_time = time.time() - gen_start_time
            print(f"     ⏱️  本代总耗时: {gen_total_time:.1f}秒")
            
            # 4. 更新Prompt使用记录和最优解
            for offspring in offspring_list:
                # 记录Prompt使用结果
                self.prompt_pop.record_usage(
                    offspring["prompt_id"],
                    offspring["fitness"],
                    offspring["parent_fitness"]
                )
                
                # 更新最优
                if offspring["fitness"] < best_ever["fitness"]:
                    best_ever = offspring
                    self.logger.log_best(best_ever)
                    self.logger.save_best_operator(best_ever)
                    print(f"    🎉 发现新最优解: {best_ever['fitness']:.2f}")
            
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
        # 延迟导入llm_client（避免子进程导入）
        from llm_client import llm_client
        
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
1. 必须生成3个函数：operator, process_info, accept_criterion
2. operator函数：
   - 参数：solution (list), dist_matrix (list[list]), info (dict)
   - 返回：new_solution (list)
   - 可以利用info中的信息设计自适应策略
3. process_info函数：
   - 参数：iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history
   - cost_history (list): 近100次的目标值历史，可分析趋势
   - 返回：info (dict)
4. accept_criterion函数：
   - 参数：delta (float), T (float), info (dict)
   - 返回：bool
5. 只返回函数定义，不要任何解释、注释或markdown标记
6. 确保代码可直接执行，避免死循环和复杂逻辑
7. 与现有top算法组件保持差异性，创新设计

【输出格式】
def operator(solution, dist_matrix, info):
    ...
    return new_sol

def process_info(iteration, total_iterations, T, T_init, current_cost, best_cost, dist_matrix, cost_history):
    ...
    return info_dict

def accept_criterion(delta, T, info):
    ...
    return True/False"""
        
        return llm_client.generate(system_prompt, user_prompt)
    
    def _concurrent_generate(self, parent_prompt_pairs, top_k_operators, top_k_prompts):
        """并发LLM生成算子（多线程，IO密集）"""
        generated_codes = {}
        
        def generate_one(pair):
            """生成单个算子"""
            idx = pair["index"]
            parent = pair["parent"]
            prompt = pair["prompt"]
            
            try:
                code = self._generate_offspring(
                    parent["code"],
                    prompt["text"],
                    top_k_operators,
                    top_k_prompts
                )
                return idx, code, parent, prompt
            except Exception as e:
                print(f"    ❌ [{idx+1}] LLM生成失败: {e}")
                return idx, None, parent, prompt
        
        # 使用ThreadPoolExecutor并发生成
        with ThreadPoolExecutor(max_workers=MAX_WORKERS_LLM) as executor:
            futures = {executor.submit(generate_one, pair): pair for pair in parent_prompt_pairs}
            
            for future in as_completed(futures):
                idx, code, parent, prompt = future.result()
                if code:
                    generated_codes[idx] = {
                        "code": code,
                        "parent": parent,
                        "prompt": prompt
                    }
                    print(f"    ✅ [{idx+1}/{OPERATOR_POP_SIZE}] 生成完成")
                else:
                    print(f"    ❌ [{idx+1}/{OPERATOR_POP_SIZE}] 生成失败")
        
        return generated_codes
    
    def _concurrent_evaluate(self, generated_codes, parent_prompt_pairs):
        """并发评估算子（多进程，CPU密集）"""
        offspring_list = []
        
        # 使用ProcessPoolExecutor进行CPU密集型计算
        with ProcessPoolExecutor(max_workers=MAX_WORKERS_EVAL) as executor:
            # 提交所有评估任务
            futures = {}
            for idx, data in generated_codes.items():
                future = executor.submit(
                    evaluate_one_process,  # worker模块中的函数，可序列化
                    data["code"],
                    self.instances
                )
                futures[future] = (idx, data)
            
            # 收集结果（带进程级超时控制）
            for future in as_completed(futures):
                idx, data = futures[future]
                try:
                    # 进程级超时：如果超时会抛出TimeoutError，自动终止该进程
                    result = future.result(timeout=PROCESS_TIMEOUT)
                    
                    if result["success"]:
                        offspring = {
                            "success": True,
                            "id": f"op_{self.operator_pop.next_id + idx}",
                            "code": data["code"],
                            "fitness": result["avg_objective"],
                            "time": result["avg_time"],
                            "parent_id": data["parent"]["id"],
                            "parent_fitness": data["parent"]["fitness"],
                            "prompt_used": data["prompt"]["text"],
                            "prompt_id": data["prompt"]["id"]
                        }
                        offspring_list.append(offspring)
                        print(f"    ✅ [{idx+1}/{OPERATOR_POP_SIZE}] fitness={offspring['fitness']:.2f}")
                    else:
                        print(f"    ❌ [{idx+1}/{OPERATOR_POP_SIZE}] 评估失败: {result.get('error', 'Unknown')[:50]}")
                except TimeoutError:
                    # 进程超时，已被自动终止
                    print(f"    ⏰ [{idx+1}/{OPERATOR_POP_SIZE}] 进程超时({PROCESS_TIMEOUT}秒)，已强制终止（可能存在死循环）")
                    future.cancel()  # 取消future（进程已被终止）
                except Exception as e:
                    print(f"    ❌ [{idx+1}/{OPERATOR_POP_SIZE}] 进程异常: {str(e)[:50]}")
        
        # 更新next_id
        if offspring_list:
            self.operator_pop.next_id += len(offspring_list)
        
        return offspring_list
