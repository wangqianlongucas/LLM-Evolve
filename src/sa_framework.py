"""模拟退火框架（使用距离矩阵优化）"""
import random
import math
import time
from tsp_problem import generate_initial_solution, calculate_total_cost, check_solution_validity

def simulated_annealing(instance, operator_func, T_init, T_end, cooling_rate, max_iter, timeout=30):
    """
    SA框架（带超时保护）
    Args:
        instance: TSP算例
        operator_func: 邻域算子函数
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
            
            # 生成邻域解
            try:
                # 单次operator调用超时保护
                op_start = time.time()
                neighbor = operator_func(current)
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
                
                # SA接受准则
                if delta < 0 or random.random() < math.exp(-delta / T):
                    current = neighbor[:]
                    current_cost = neighbor_cost
                    
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

