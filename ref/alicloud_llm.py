"""
阿里云LLM接口 - OpenAI兼容模式
"""

from openai import OpenAI
from config import get_config, validate_config

class AliCloudLLM:
    """阿里云LLM"""
    
    def __init__(self):
        if not validate_config():
            raise ValueError("配置验证失败")
        
        config = get_config()
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        self.model_name = config["model_name"]
        self.params = {
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"],
            "top_p": config["top_p"]
        }
        
        print(f"✅ LLM初始化成功，模型: {self.model_name}")
    
    def __call__(self, params):
        """调用LLM"""
        prompt = params.get("prompt", "")
        
        try:
            print(f"🚀 调用API...")
            
            messages = [
                {"role": "system", "content": "你是进化算法专家，生成高质量的operator代码。"},
                {"role": "user", "content": prompt}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.params
            )
            
            response = completion.choices[0].message.content
            print(f"✅ 生成成功，长度: {len(response)}")
            
            return self._clean_code(response)
            
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            raise
    
    def _clean_code(self, text):
        """清理代码"""
        # 去掉markdown标记
        text = text.replace("```python", "").replace("```", "")
        # 去掉空行
        lines = [line for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

def test_llm():
    """测试LLM"""
    try:
        llm = AliCloudLLM()
        result = llm({"prompt": "写个Python函数计算1+1"})
        print("测试结果:", result)
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_llm()