"""LLM客户端"""
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL_NAME, MAX_TOKENS, TEMPERATURE

class LLMClient:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.model = MODEL_NAME
        
    def generate(self, system_prompt, user_prompt):
        """调用LLM生成内容"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE
            )
            content = response.choices[0].message.content
            return self._clean_code(content)
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return None
    
    def _clean_code(self, text):
        """清理代码"""
        text = text.replace("```python", "").replace("```", "")
        lines = [line for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

# 全局实例
llm_client = LLMClient()


if __name__ == "__main__":
    # 测试LLM是否链接成功
    print(llm_client.generate('你是什么模型', ''))

