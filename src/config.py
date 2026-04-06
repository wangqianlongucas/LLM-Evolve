"""配置文件"""
import os
import math


# LLM配置
API_KEY = os.getenv("ALICLOUD_API_KEY", "sk-XXX")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# MODEL_NAME = "qwen-plus"
MODEL_NAME = "qwen3-max"
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# EA配置
MAX_GENERATIONS = 30  
OPERATOR_POP_SIZE = 10  
PROMPT_POP_SIZE = 10 
PROMPT_UPDATE_FREQ = 3  # 每5代更新一次Prompt
TOP_K_FOR_DIVERSITY = 5  # 生成时参考的top K个体数

# 并发配置
MAX_WORKERS_LLM = 10  # LLM API并发数（多线程，IO密集型）
MAX_WORKERS_EVAL = 10   # 评估并发数（多进程，CPU密集型，建议≤CPU核心数）

# Prompt fitness权重
PROMPT_ALPHA = 0.8  # 平均性能权重
PROMPT_BETA = 0.2   # 平均提升权重

# SA配置
SA_T_INIT = 100
SA_T_END = 0.1
SA_COOLING_RATE = 0.98
SA_MAX_ITER = 100
SA_TIMEOUT = 30  # SA内部超时（秒）

# 进程级超时控制（防止死循环）
PROCESS_TIMEOUT = 40  # 进程级强制超时（秒），应该 > SA_TIMEOUT

# 计算SA最大迭代次数
def _calculate_max_iterations():
    """计算SA框架的理论最大迭代次数"""
    if SA_COOLING_RATE >= 1 or SA_COOLING_RATE <= 0:
        return 100000  # 默认值
    # 温度阶段数 = log(T_end/T_init) / log(cooling_rate)
    num_stages = math.log(SA_T_END / SA_T_INIT) / math.log(SA_COOLING_RATE)
    # 总迭代次数 = 温度阶段数 × 每温度迭代次数
    total_iterations = int(abs(num_stages) * SA_MAX_ITER)
    return total_iterations

SA_MAX_TOTAL_ITERATIONS = _calculate_max_iterations()

# 打印计算结果（便于调试）
if __name__ == "__main__":
    print(f"SA参数配置：")
    print(f"  初始温度: {SA_T_INIT}")
    print(f"  终止温度: {SA_T_END}")
    print(f"  冷却率: {SA_COOLING_RATE}")
    print(f"  每温度迭代: {SA_MAX_ITER}")
    print(f"  理论最大迭代次数: {SA_MAX_TOTAL_ITERATIONS}")
    print(f"  温度阶段数: {SA_MAX_TOTAL_ITERATIONS // SA_MAX_ITER}")

