# LLM-Evolve: LLM驱动的双种群进化算法

## 🎯 项目简介

使用LLM自动生成和进化TSP算法的邻域算子，采用**双种群进化框架**：
- **算子种群**：LLM生成的TSP邻域算子（2-swap, 2-opt等）
- **Prompt种群**：指导LLM改进算子的提示词

## 🏗️ 架构

```
输入：TSP算例 + Evaluator
     ↓
[EA主循环]
  1. 选择父本算子
  2. 选择改进Prompt
  3. LLM生成新算子
  4. 在SA框架中评估
  5. 更新双种群
     ↓
输出：最优邻域算子
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API Key
修改 `src/config.py`：
```python
API_KEY = "your-api-key"
```

### 3. 运行
```bash
cd src
python run.py
```

## 📂 文件结构

```
src/
  ├── config.py              # 配置（API、EA参数）
  ├── llm_client.py          # LLM调用
  ├── tsp_problem.py         # TSP问题定义
  ├── sa_framework.py        # 模拟退火框架
  ├── evaluator.py           # 算子评估（带解的有效性检查）
  ├── operator_population.py # 算子种群
  ├── prompt_population.py   # Prompt种群
  ├── ea_main.py             # EA主循环
  └── run.py                 # 入口

data/
  └── tsp_instances.json     # TSP算例
```

## ⚙️ 配置参数

`src/config.py`：
- `MAX_GENERATIONS = 50`：进化代数
- `OPERATOR_POP_SIZE = 10`：算子种群大小
- `PROMPT_POP_SIZE = 8`：Prompt种群大小
- `PROMPT_ALPHA = 0.7`：Prompt fitness中性能权重
- `PROMPT_BETA = 0.3`：Prompt fitness中提升权重

## 📊 输出示例

```
Generation 10/50
1️⃣ 父本: op_5, fitness=8234.56
2️⃣ Prompt: 增加邻域多样性，避免局部最优
3️⃣ LLM生成新算子...
4️⃣ 评估新算子...
5️⃣ ✅ 接受新个体: fitness=7982.31
   🎉 发现新最优解: 7982.31
```

## 🔍 核心特性

1. **解的有效性检查**：evaluator自动检测重复访问的城市
2. **双种群共进化**：算子和Prompt同时进化
3. **元进化**：使用LLM生成新的改进方向（元Prompt）
4. **简洁设计**：专注核心功能，代码简洁易读

