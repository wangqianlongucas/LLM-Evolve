# 多目标进化算法选择器

使用阿里云LLM自动生成多目标进化算法的父本选择operator，专用于**MORL(多目标强化学习)**。

## 🎯 任务目标

**输入**：
1. `objectives`: `[[O1, O2], [O1, O2], ...]` - 每个个体的目标值（多目标优化）
2. `weights`: `[[w1, w2], [w1, w2], ...]` - 每个个体当前最匹配的权重组合（类似MOEA/D）

**输出**：
- `[0, 2, 5, 8]` - 下一步进化的个体索引列表

**应用场景**：多目标强化学习(MORL)中的父本选择

## ⚡ 快速使用

```python
from operator_generator import OperatorGenerator

# 1. 初始化
generator = OperatorGenerator()

# 2. 算法配置
config = {
    "algorithm_type": "多目标进化算法",
    "application": "MORL",
    "objectives_count": 2
}

# 3. 生成选择器
operators = generator.generate_operators(config, ["selection"])

# 4. 使用
exec(operators["selection"])
selected_indices = selection_operator(objectives, weights)
```

## 📊 输入格式示例

```python
# 个体的目标值 (每行一个个体)
objectives = [
    [0.8, 0.3],  # 个体0: 目标1=0.8, 目标2=0.3
    [0.2, 0.9],  # 个体1: 目标1=0.2, 目标2=0.9
    [0.6, 0.6],  # 个体2: 目标1=0.6, 目标2=0.6
]

# 对应的权重组合
weights = [
    [0.7, 0.3],  # 个体0: 偏向目标1
    [0.3, 0.7],  # 个体1: 偏向目标2  
    [0.5, 0.5],  # 个体2: 平衡权重
]

# 输出: [1, 2] 表示选中个体1和个体2
```

## 🔧 配置

在 `config.py` 中配置你的API密钥：
```python
API_KEY = "sk-your-api-key"
```

## 🚀 运行

```bash
python quick_start.py  # 5分钟快速开始
python demo.py         # 完整演示
```

专注核心：**多目标优化的智能父本选择**。
