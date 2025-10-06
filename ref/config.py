"""
配置文件 - 阿里云API配置
"""

import os

# 🔑 阿里云API配置 - 替换为你的API密钥
API_KEY = "sk-23986bd8245b41158f89ef0e37007bb5"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-plus"

# 从环境变量读取（可选）
API_KEY = os.getenv("ALICLOUD_API_KEY", API_KEY)

# 生成参数
MAX_TOKENS = 2000
TEMPERATURE = 0.7
TOP_P = 0.8

def get_config():
    """获取配置"""
    return {
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "model_name": MODEL_NAME,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P
    }

def validate_config():
    """验证配置"""
    if not API_KEY.startswith("sk-"):
        print("❌ API密钥格式错误，应该以 'sk-' 开头")
        return False
    print("✅ 配置OK")
    return True