"""
快速开始 - 多目标进化算法选择器
"""

from operator_generator import OperatorGenerator

print("🚀 多目标进化算法选择器 - 快速开始")
print("=" * 40)

# 1. 创建生成器
generator = OperatorGenerator()

# 2. 定义多目标算法信息
algorithm_info = {
    "algorithm_type": "多目标进化算法",
    "application": "MORL (多目标强化学习)",
    "objectives_count": 2,
    "selection_strategy": "基于权重分解",
    "description": "根据个体目标值和权重选择父本"
}

print("算法信息:", algorithm_info)

# 3. 生成多目标选择operator
operators = generator.generate_operators(algorithm_info, ["selection"])

if "selection" in operators:
    print("\n✅ 生成成功!")
    print("生成的多目标选择代码:")
    print("-" * 30)
    print(operators["selection"])
    print("-" * 30)
    
    # 4. 使用生成的代码
    exec(operators["selection"])
    
    # 5. 测试数据 - 多目标场景
    objectives = [
        [0.8, 0.2],  # 个体0: [目标1, 目标2]
        [0.3, 0.9],  # 个体1  
        [0.6, 0.5],  # 个体2
        [0.9, 0.1],  # 个体3
    ]
    
    weights = [
        [0.7, 0.3],  # 个体0对应权重
        [0.3, 0.7],  # 个体1对应权重
        [0.5, 0.5],  # 个体2对应权重 
        [0.8, 0.2],  # 个体3对应权重
    ]
    
    print(f"输入数据:")
    print(f"  目标值: {objectives}")
    print(f"  权重: {weights}")
    
    # 6. 调用生成的选择函数
    selected_indices = selection_operator(objectives, weights)
    
    print(f"\n🎯 选择结果: {selected_indices}")
    print("选中的个体详情:")
    for idx in selected_indices:
        if idx < len(objectives):
            print(f"  个体{idx}: 目标={objectives[idx]}, 权重={weights[idx]}")

else:
    print("❌ 生成失败")

print("\n🎉 完成! 这就是多目标进化算法的LLM选择器!")