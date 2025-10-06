"""
进化算法Operator生成器
"""

import json
from alicloud_llm import AliCloudLLM
from promptmanager import PromptBuilder

class OperatorGenerator:
    """Operator生成器"""
    
    def __init__(self):
        self.llm = AliCloudLLM()
        self.prompt_builder = PromptBuilder()
        print("🚀 Operator生成器初始化完成")
    
    def generate_selection_operator(self, algorithm_info):
        """生成多目标父本选择operator"""
        # 使用增强版prompt构建器
        prompt = self.prompt_builder.build_enhanced_prompt(algorithm_info)
        
        return self._generate_with_retry(prompt)
    
    def generate_operators(self, algorithm_info, operator_types=["selection"]):
        """生成多目标选择operator"""
        print(f"🔄 生成多目标选择operator")
        
        operators = {}
        for op_type in operator_types:
            if op_type == "selection":
                try:
                    code = self.generate_selection_operator(algorithm_info)
                    if self._validate_code(code):
                        operators[op_type] = code
                        # 记录到历史（评分将在外部设置）
                        code_id = self.prompt_builder.add_generated_code(code, algorithm_info)
                        print(f"✅ 多目标选择operator生成成功")
                    else:
                        print(f"❌ 代码验证失败")
                except Exception as e:
                    print(f"❌ 生成失败: {e}")
            else:
                print(f"⚠️ 只支持selection类型")
        
        return operators
    
    def _generate_with_retry(self, prompt, max_retries=3):
        """带重试的生成"""
        for i in range(max_retries):
            try:
                code = self.llm({"prompt": prompt})
                if code:
                    return code
            except Exception as e:
                print(f"第{i+1}次尝试失败: {e}")
                if i == max_retries - 1:
                    raise
        return ""
    
    def _validate_code(self, code):
        """验证代码"""
        try:
            compile(code, '<string>', 'exec')
            if 'def ' in code and 'return ' in code:
                return True
        except:
            pass
        return False

def demo():
    """多目标选择演示"""
    generator = OperatorGenerator()
    
    # 多目标算法配置
    config = {
        "algorithm_type": "多目标进化算法",
        "application": "MORL",
        "objectives_count": 2,
        "selection_strategy": "权重分解法"
    }
    
    # 生成多目标选择operator
    operators = generator.generate_operators(config, ["selection"])
    
    if "selection" in operators:
        print("\n🎉 多目标选择operator生成成功!")
        print("=" * 40)
        print(operators["selection"])
        print("=" * 40)

if __name__ == "__main__":
    demo()