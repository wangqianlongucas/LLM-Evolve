"""模拟退火框架（支持自定义组件）"""
import random
import math
import time
from tsp_problem import generate_initial_solution, calculate_total_cost, check_solution_validity
from config import SA_MAX_TOTAL_ITERATIONS

def simulated_annealing(instance, operator_func, process_info_func, accept_criterion_func, 
                       T_init, T_end, cooling_rate, max_iter, timeout=30):
    """
    SA框架（支持自定义组件，带超时保护）
    Args:
        instance: TSP算例
        operator_func: 邻域算子函数 operator(solution, dist_matrix, info)
        process_info_func: 信息加工函数 process_info(iteration, total_iter, T, T_init, current_cost, best_cost, dist_matrix)
        accept_criterion_func: 接受准则函数 accept_criterion(delta, T, info)
        T_init: 初始温度
        T_end: 终止温度
        cooling_rate: 冷却率
        max_iter: 每个温度最大迭代次数
        timeout: 最大运行时间（秒）
    Returns:
        (best_solution, best_cost, time_used)
    """
    start_time = time.time()
    
    # 初始化
    current = generate_initial_solution(instance.n_cities)
    current_cost = calculate_total_cost(current, instance.dist_matrix)
    best = current[:]
    best_cost = current_cost
    
    T = T_init
    total_iterations = 0
    failed_attempts = 0
    max_failed_attempts = 100  # 连续失败上限
    
    # 维护近期目标值历史（最多100个）
    cost_history = [current_cost]
    
    while T > T_end:
        # 超时检查
        if time.time() - start_time > timeout:
            print(f"    ⚠️ SA超时（{timeout}秒），提前终止")
            break
        
        for _ in range(max_iter):
            total_iterations += 1
            
            # 总迭代次数保护
            if total_iterations > 100000:
                print(f"    ⚠️ 达到最大迭代次数限制")
                break
            
            # 每1000次迭代检查一次时间
            if total_iterations % 1000 == 0:
                if time.time() - start_time > timeout:
                    break
            
            # 加工信息
            try:
                info = process_info_func(
                    total_iterations,
                    SA_MAX_TOTAL_ITERATIONS,  # 理论最大迭代次数
                    T,
                    T_init,
                    current_cost,
                    best_cost,
                    instance.dist_matrix,
                    cost_history[-100:]  # 近100次的目标值历史
                )
            except Exception:
                info = {}
            
            # 生成邻域解
            try:
                # 单次operator调用超时保护
                op_start = time.time()
                neighbor = operator_func(current, instance.dist_matrix, info)
                op_time = time.time() - op_start
                
                # operator执行时间过长（可能有问题）
                if op_time > 1.0:
                    failed_attempts += 1
                    if failed_attempts > max_failed_attempts:
                        raise Exception("算子执行时间过长，可能存在性能问题")
                    continue
                
                # 检查解的有效性
                valid, msg = check_solution_validity(neighbor, instance.n_cities)
                if not valid:
                    failed_attempts += 1
                    if failed_attempts > max_failed_attempts:
                        raise Exception(f"算子生成无效解次数过多: {msg}")
                    continue
                
                # 重置失败计数
                failed_attempts = 0
                
                neighbor_cost = calculate_total_cost(neighbor, instance.dist_matrix)
                delta = neighbor_cost - current_cost
                
                # 自定义接受准则
                try:
                    accept = accept_criterion_func(delta, T, info)
                except Exception:
                    # fallback到经典准则
                    accept = delta < 0 or (random.random() < math.exp(-delta / T) if T > 0 else False)
                
                if accept:
                    current = neighbor[:]
                    current_cost = neighbor_cost
                    
                    # 记录到历史
                    cost_history.append(current_cost)
                    
                    if current_cost < best_cost:
                        best = current[:]
                        best_cost = current_cost
            except Exception as e:
                failed_attempts += 1
                if failed_attempts > max_failed_attempts:
                    raise Exception(f"算子执行失败: {str(e)}")
                continue
        
        T *= cooling_rate
    
    time_used = time.time() - start_time
    return best, best_cost, time_used

