"""CVRP算子评估器"""
from cvrp_sa_framework import simulated_annealing
from config import SA_T_INIT, SA_T_END, SA_COOLING_RATE, SA_MAX_ITER, SA_TIMEOUT

def evaluate_operator(operator_code, instances, timeout=None):
    """
    评估CVRP算子（带超时保护）
    Args:
        operator_code: 算子代码字符串
        instances: CVRP算例列表
        timeout: 超时时间（秒），None则使用配置值
    Returns:
        {
            "success": bool,
            "avg_objective": float,
            "avg_time": float,
            "details": [...],
            "error": str (if failed)
        }
    """
    if timeout is None:
        timeout = SA_TIMEOUT
    
    try:
        # 执行代码，加载三个函数
        namespace = {"__builtins__": __builtins__}
        exec(operator_code, namespace)
        
        # 检查三个必需函数
        if "operator" not in namespace:
            return {"success": False, "error": "未找到operator函数"}
        if "process_info" not in namespace:
            return {"success": False, "error": "未找到process_info函数"}
        if "accept_criterion" not in namespace:
            return {"success": False, "error": "未找到accept_criterion函数"}
        
        operator_func = namespace["operator"]
        process_info_func = namespace["process_info"]
        accept_criterion_func = namespace["accept_criterion"]
        
        # 简单检查：确保都是函数
        if not callable(operator_func):
            return {"success": False, "error": "operator不是可调用函数"}
        if not callable(process_info_func):
            return {"success": False, "error": "process_info不是可调用函数"}
        if not callable(accept_criterion_func):
            return {"success": False, "error": "accept_criterion不是可调用函数"}
        
        # 在多个算例上测试
        results = []
        for instance in instances:
            try:
                best_sol, best_cost, time_used = simulated_annealing(
                    instance, operator_func, process_info_func, accept_criterion_func,
                    SA_T_INIT, SA_T_END, SA_COOLING_RATE, SA_MAX_ITER,
                    timeout=timeout
                )
                
                results.append({
                    "instance": instance.name,
                    "cost": best_cost,
                    "time": time_used,
                    "routes": len(best_sol),
                    "gap": (best_cost - instance.optimal) / instance.optimal * 100 if instance.optimal else None
                })
            except Exception as e:
                return {"success": False, "error": f"算例{instance.name}运行失败: {e}"}
        
        # 计算平均值
        avg_cost = sum(r["cost"] for r in results) / len(results)
        avg_time = sum(r["time"] for r in results) / len(results)
        
        return {
            "success": True,
            "avg_objective": avg_cost,
            "avg_time": avg_time,
            "details": results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
