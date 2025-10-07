"""多进程worker函数（避免不必要的导入）"""

def evaluate_one_process(code, instances):
    """
    在独立进程中评估单个算子
    注意：这个模块不导入llm_client，避免子进程触发LLM测试代码
    """
    from evaluator import evaluate_operator
    try:
        result = evaluate_operator(code, instances)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

