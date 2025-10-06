# LLM-Evolve: LLM驱动的双种群进化算法

## 🎯 项目简介

使用LLM自动生成和进化TSP算法的邻域算子，采用**双种群进化框架**：
- **算子种群**：LLM生成的TSP邻域算子（2-swap, 2-opt等）
- **Prompt种群**：指导LLM改进算子的提示词

## 🏗️ 架构

```
输入：TSP算例 + Evaluator
     ↓
[初始化]
  - 种子算子 + LLM生成初始种群
  - 预定义Prompt模板
     ↓
[EA主循环 - 每代]
  1. 获取Top K（多样性约束）
  2. 批量生成N个子代:
     - 选择父本算子
     - 选择改进Prompt
     - LLM生成新算子（带diversity约束）
     - 在SA框架中评估
  3. 父代+子代合并选择（保留最优N个）
  4. 定期进化Prompt种群（元Prompt）
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
  ├── logger.py              # 日志保存
  ├── ea_main.py             # EA主循环
  └── run.py                 # 入口

data/
  └── tsp_instances.json     # TSP算例

logs/
  └── exp_YYYYMMDD_HHMMSS/   # 每次实验日志
      ├── experiment_log.json      # 完整进化日志
      ├── best_operator.py         # 最优算子代码
      ├── gen_N_population.json    # 第N代种群快照
      └── summary.txt              # 实验总结
```

## ⚙️ 配置参数

`src/config.py`：

**EA参数**：
- `MAX_GENERATIONS = 10`：进化代数
- `OPERATOR_POP_SIZE = 5`：算子种群大小
- `PROMPT_POP_SIZE = 5`：Prompt种群大小
- `PROMPT_UPDATE_FREQ = 2`：每N代更新Prompt种群
- `TOP_K_FOR_DIVERSITY = 3`：生成时参考的top K个体数

**Prompt fitness**：
- `PROMPT_ALPHA = 0.7`：平均性能权重
- `PROMPT_BETA = 0.3`：平均提升权重

**SA参数**：
- `SA_T_INIT = 100`：初始温度
- `SA_T_END = 10`：终止温度
- `SA_COOLING_RATE = 0.95`：冷却率
- `SA_MAX_ITER = 100`：每温度最大迭代
- `SA_TIMEOUT = 200`：最大运行时间（秒）

## 📊 输出示例

```
📍 Generation 2/10
============================================================
🔄 生成 5 个子代...

  [1/5]
    1️⃣ 父本: op_2, fitness=8234.56
    2️⃣ Prompt: 增加邻域多样性，避免局部最优...
    3️⃣ LLM生成...
    4️⃣ 评估...
    ✅ fitness=8123.45
    🎉 发现新最优解: 8123.45

5️⃣ 更新种群: 4个有效子代
   新种群大小: 5

📊 当前最优: 8123.45
📊 历史最优: 8123.45
```

## 🔍 核心特性

1. **批量生成**：每代生成N个子代，父代+子代选择（标准EA框架）
2. **多样性保护**：生成时参考Top K个体，避免简单重复
3. **解的有效性检查**：evaluator自动检测重复访问的城市
4. **死循环保护**：多层超时机制（总时间、迭代次数、单次operator时间）
5. **双种群共进化**：算子和Prompt同时进化
6. **元进化**：使用LLM生成新的改进方向（元Prompt）
7. **日志保存**：自动保存每代进化日志和最优算子
8. **简洁设计**：专注核心功能，代码简洁易读

## 📝 日志系统

每次运行会在 `logs/` 目录下创建一个带时间戳的实验文件夹：

```
logs/exp_20241006_143025/
├── experiment_log.json        # 完整的进化过程
│   ├── generations[]          # 每代的详细信息
│   └── best_history[]         # 最优解历史
│
├── best_operator.py           # 最优算子代码（可直接运行）
│
├── gen_5_population.json      # 第5代种群快照
├── gen_10_population.json     # 第10代种群快照
│   ├── operators[]            # 所有算子的代码和fitness
│   └── prompts[]              # 所有prompt的文本和fitness
│
└── summary.txt                # 实验总结报告
    ├── 配置参数
    ├── 最优结果
    └── 进化历史
```

**自动保存时机**：
- 发现新最优解时：立即保存
- 每5代：保存种群快照
- 实验结束时：保存完整总结

