"""配置文件"""
import os

# LLM配置
API_KEY = os.getenv("ALICLOUD_API_KEY", "sk-23986bd8245b41158f89ef0e37007bb5")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-plus"
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# EA配置
MAX_GENERATIONS = 10  # 50
OPERATOR_POP_SIZE = 5  # 10
PROMPT_POP_SIZE = 5 # 8
PROMPT_UPDATE_FREQ = 2  # 每5代更新一次Prompt
TOP_K_FOR_DIVERSITY = 3  # 生成时参考的top K个体数

# Prompt fitness权重
PROMPT_ALPHA = 0.7  # 平均性能权重
PROMPT_BETA = 0.3   # 平均提升权重

# SA配置
SA_T_INIT = 100
SA_T_END = 10
SA_COOLING_RATE = 0.95
SA_MAX_ITER = 100
SA_TIMEOUT = 200  # SA运行最大时间（秒）

