# LLM-Evolve: LLM驱动的双种群进化算法

## 🎯 项目简介

使用LLM自动生成和进化完整的TSP算法组件，采用**双种群进化框架**：
- **算法组件种群**：LLM生成的完整算法（算子 + 信息加工 + 接受准则）
- **Prompt种群**：指导LLM改进算法的提示词

### 🆕 算法组件包含三部分
1. **邻域算子** (`operator`)：生成邻域解
   ```python
   def operator(solution, dist_matrix, info):
       # solution: 当前解
       # dist_matrix: 距离矩阵
       # info: 搜索信息（进度、温度等）
       return new_solution
   ```

2. **信息加工** (`process_info`)：计算进度、温度比率等信息
   ```python
   def process_info(iteration, total_iterations, T, T_init, 
                    current_cost, best_cost, dist_matrix):
       # 计算搜索进度、温度比率等
       return {'progress': ..., 'temperature_ratio': ...}
   ```

3. **接受准则** (`accept_criterion`)：决定是否接受新解
   ```python
   def accept_criterion(delta, T, info):
       # delta: 成本差
       # T: 当前温度
       # info: 搜索信息
       return True/False  # 是否接受
   ```

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
      ├── all_operators.txt        # 所有代的算子代码
      ├── all_prompts.txt          # 所有代的Prompt
      └── summary.txt              # 实验总结
```

## ⚙️ 配置参数

`src/config.py`：

**EA参数**：
- `MAX_GENERATIONS = 30`：进化代数
- `OPERATOR_POP_SIZE = 10`：算子种群大小
- `PROMPT_POP_SIZE = 8`：Prompt种群大小
- `PROMPT_UPDATE_FREQ = 3`：每N代更新Prompt种群
- `TOP_K_FOR_DIVERSITY = 5`：生成时参考的top K个体数

**并发参数**：
- `MAX_WORKERS_LLM = 10`：LLM API并发数（多线程，IO密集型）
- `MAX_WORKERS_EVAL = 5`：评估并发数（多进程，CPU密集型，建议≤CPU核心数）

**Prompt fitness**：
- `PROMPT_ALPHA = 0.7`：平均性能权重
- `PROMPT_BETA = 0.3`：平均提升权重

**SA参数**：
- `SA_T_INIT = 100`：初始温度
- `SA_T_END = 0.1`：终止温度
- `SA_COOLING_RATE = 0.95`：冷却率
- `SA_MAX_ITER = 100`：每温度最大迭代
- `SA_TIMEOUT = 20`：最大运行时间（秒）

## 📊 输出示例

```
📍 Generation 2/30
============================================================
🔄 混合并发生成 10 个子代...
  1️⃣ 选择父本和Prompt...
  2️⃣ 并发LLM生成（10线程 - IO密集）...
    ✅ [1/10] 生成完成
    ✅ [3/10] 生成完成
    ✅ [2/10] 生成完成
    ...
     ⏱️  LLM生成耗时: 15.3秒
  3️⃣ 并发评估（5进程 - CPU密集）...
    ✅ [1/10] fitness=8123.45
    ...
     ⏱️  评估耗时: 8.7秒
     ⏱️  本代总耗时: 24.0秒
    🎉 发现新最优解: 8123.45
    ✅ [2/10] fitness=8234.56
    ✅ [3/10] fitness=8189.32
    ...

5️⃣ 更新种群: 8个有效子代
   新种群大小: 10

📊 当前最优: 8123.45
📊 历史最优: 8123.45
```

## 🔍 核心特性

1. **批量生成**：每代生成N个子代，父代+子代选择（标准EA框架）
2. **混合并发策略**：⚡ LLM生成用多线程（IO密集），评估用多进程（CPU密集），性能最优
   - 并发LLM API调用（多线程，IO密集型）
   - 并发算子评估（多进程，CPU密集型，绕过GIL）
3. **完整算法生成**：⭐ LLM同时生成3个组件（算子+信息加工+接受准则）
   - 支持自适应策略（根据搜索进度调整）
   - 支持自定义接受准则（不限于Metropolis）
4. **多样性保护**：生成时参考Top K个体，避免简单重复
5. **距离矩阵优化**：预计算距离，算子可访问距离信息做智能决策
6. **信息丰富**：算子可访问迭代次数、温度、进度等信息
7. **解的有效性检查**：evaluator自动检测重复访问的城市
8. **死循环保护**：多层超时机制（总时间、迭代次数、单次operator时间）
9. **双种群共进化**：算法组件和Prompt同时进化
10. **元进化**：使用LLM生成新的改进方向（元Prompt）
11. **日志保存**：自动保存每代进化日志和最优算法
12. **简洁设计**：专注核心功能，代码简洁易读

## 📝 日志系统

每次运行会在 `logs/` 目录下创建一个带时间戳的实验文件夹：

```
logs/exp_20241006_143025/
├── experiment_log.json        # 完整的进化过程（JSON）
│   ├── generations[]          # 每代的详细信息
│   └── best_history[]         # 最优解历史
│
├── best_operator.py           # 最优算子代码（可直接运行）
│
├── all_operators.txt          # 所有代的算子代码（追加模式）
│   ├── 第1代算子种群
│   ├── 第5代算子种群
│   └── 第10代算子种群
│
├── all_prompts.txt            # 所有代的Prompt（追加模式）
│   ├── 第1代Prompt种群
│   ├── 第5代Prompt种群
│   └── 第10代Prompt种群
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


# NEXT
## A. Prompt 侧：显式上下文 + 随机模板 + 渲染评测 + 元提示库

1. **把评测详情渲染进 prompt**
   在 `_generate_offspring` 组装用户提示时，附上一段**表格**（来自最近 N 个候选的 `details` + 失败原因 Top-K）。数据从 `logger`/最近一代 `offspring_list` 抽取。论文明确建议“Rendered evaluation results”。
   落点：`ea_main.py` 里 `_generate_offspring(...)` 拼装 `user_prompt` 的地方。

2. **模板随机化（Stochastic formatting）**
   新增 `prompt_templates.yaml`：同一语义的多种句式+概率；每次采样 1 份合成 `user_prompt`。
   落点：`prompt_population.select_prompt()` 返回后，再套模板；或在 `PromptPopulation.initialize()` 时就扩增。

3. **元提示进化：独立库 + 适应度**
   你已有 `generate_new_prompt()`，将其产物**单独**存放（`meta_prompt_db.jsonl`），按“使用带来的相对提升（已记录）+ 多样性”更新适应度，再与普通 prompt 共竞。 

4. **更强的父代上下文**
   `operator_population.generate_random_operator()` 已把 top-K 片段注入 `diversity_hint`，建议再加**行为统计**（见 §C），以便 LLM 规避已见策略。

## B. 生成输出：兼容 Diff（SEARCH/REPLACE）

* 在 `llm_client` 的 `_extract_operator()` 前先检测是否包含
  `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE`。若有，调用一个 `apply_patch(parent_code, diff_text)` 产生新代码；否则走你现在的“提取 `def operator`”路径。论文给了格式定义与示例。
  落点：`llm_client.py`（或你已替换版）。

## C. 评测：级联 + 行为特征

1. **三级评测（建议数值）**

* **Tier-0**：10 城市、100 次 `operator` 调用自检（合法排列 + 单次<5ms + 不报错）；不合格直接淘汰。
* **Tier-1**：在 1–2 个小实例上跑 `SA`（`max_iter` 减半，`timeout`=3s）。
* **Tier-2**：通过者再上你当前全量设置。
  落点：`evaluate_operator` 外围加壳或拆为 `evaluate_tiered(...)`。 

2. **行为特征（用于 MAP-Elites 与多样性）**
   记录：

* 平均改动跨度（索引距离 / 2-opt 段长均值）；
* 接受率曲线（随温度/时间）；
* 单步 `operator` 耗时均值/95 分位；
* 生成解的 Hamming 距离均值（对当前/最佳）。
  落点：`sa_framework.simulated_annealing` 内计数并返回，或在 `evaluate_operator` 汇总。

## D. 进化策略：MAP-Elites + 岛屿

* 以（改动跨度, 接受率）或（改动跨度, 时间）做 2D 网格，每格仅保“精英”（最低 avg_cost）。每代子代先尝试填充/挑战其格。
* 维护 2–4 个“岛屿”（各自运行若干代），周期性交换前 10% 精英。
  落点：扩展 `operator_population.update_population()` 与 `EAController.run()` 的种群维护；支持“按行为落格”。  

## E. 并行/异步

* 评测并行：`ProcessPoolExecutor(max_workers=4–8)` 包装 `evaluate_operator`（每子进程独立超时）。
* 进一步做成 **async 管线**（生成/评测/选择解耦），与论文一致。
  落点：`ea_main.py` 里一代循环对 `offspring_list` 评测处。

## F. 多模型级联

* `LLM_FAST`：温度略高，生成 4–8 个候选；
* `LLM_STRONG`：对 top-M 候选做“自审 + 最小修补（diff）”；
* 失败/报错样本用强模型“只修 bug”模式再试一次（不追求创新）。
  落点：`config.py` 增加第二模型名；`llm_client` 增加 `generate_strict/critique` 接口。

## G. 程序数据库（持久化 & 取样）

* 新建 `program_db.jsonl`（或 SQLite）：字段含 `sha, code, metrics(avg_cost/time/gap), behaviors, errors, ancestry(parent_id), prompt_id, ts`。
* 抽样策略：从（高分、低分、稀有行为）各取一部分，喂进 prompt 的“Prior programs + Current program”段落。论文强调“把历史程序（不同定义的‘好’）放进上下文能提高多样性”。
  落点：`logger.py` 旁新建 `program_db.py`；在 `ea_main.py` 每次评测成功/失败都落 DB。

## H. 安全与稳健性（建议保留）

* 你当前评测在主进程 `exec`，建议切到**子进程沙箱 + 受限内置**（防卡死/资源滥用）。落点：`evaluator.py`。

## I. 实例与级别（配合评测级联）

* 你已提供 `tsp_instances.json`，建议按难度分层（如 eil51/berlin52→st70），用于 Tier-1/2。 
* `run.py` 现默认 `limit=2`，可以在 Tier-2 才扩大。
