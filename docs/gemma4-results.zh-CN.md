# Gemma 4 MoE 实测结果

[返回项目首页](../README.md)

2026-09-20 使用已有本地 `gemma-4-26b-a4b-it-4bit` 权重测量。直接评分在**每种缓存条件下均为 26/28 正确**，同页面决策延迟为 **p50 134.9 ms／p95 283.9 ms**。它也在一条请求中选错了可见课程。此权重已验证所测推理和缓存路径，但这些结果**不足以支持默认无人值守地执行动作**。

证据包括全部 **336 次计入统计的决策**、**56 次缓存／全新计算数值比较**，以及独立的 **12 次进程冷启动运行**。28 条测试用例是项目早期评测已经使用的原始冻结回归集；它们不是 336 条独立质量用例，也不是新的盲测基准。单独的六领域扩展集不在本报告范围内。

## 记录的配置与证据

| 项目 | 记录值 |
| --- | --- |
| 主机 | Apple M2 Max，Mac14,6，12 核 CPU，64 GiB 统一内存；Darwin 25.6.0 |
| 运行时 | Python 3.13.2；JEV MLX 0.1.0；MLX／MLX-Metal 0.31.2；MLX-LM 0.31.3；Transformers 5.9.0；Tokenizers 0.22.2；NumPy 2.5.3 |
| 权重 | `mlx-community/gemma-4-26b-a4b-it-4bit`，版本 `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |
| 权重大小与量化 | 14.54 GiB；仿射 4-bit，分组 64，包含 120 项显式 8-bit 覆盖 |
| 测量源码 | `ba98b71792f418f527146d4a073c9a7f420f9534`（`ba98b71`） |
| 测试安排 | 28 条用例 × 4 种方法 × 3 种条件 × 1 次重复；固定打乱种子 `20260919` |
| 选择策略 | 现有语义提示词；margin 阈值 `0.0`；无权重专用提示词、解析器或生成优化 |
| 基线 | 贪心编码生成，最多 1 个 token；贪心 JSON／JSON-code 生成，最多 96 个 token |

记录时工作区存在未提交修改。两项证据审计均验证记录的全部八个推理／基准源码哈希匹配 `ba98b71`；这不代表所有未跟踪文件或文档文件都属于该提交。模型哈希见[权重记录](../benchmarks/results/gemma4-checkpoint.json)，架构、模板、量化、许可与缓存细节见[框架审计](gemma4-audit.zh-CN.md)。

- 正式测试：[元数据](../benchmarks/results/gemma4-test/metadata.json)、[全部试验](../benchmarks/results/gemma4-test/trials.jsonl)、[原始汇总](../benchmarks/results/gemma4-test/summary.json)、[派生报告](../benchmarks/results/gemma4-test/derived-report.json)、[证据审计](../benchmarks/results/gemma4-test/evidence-audit.json)。
- 进程冷启动：[元数据](../benchmarks/results/gemma4-cold/metadata.json)、[全部试验](../benchmarks/results/gemma4-cold/trials.jsonl)、[派生报告](../benchmarks/results/gemma4-cold/derived-report.json)、[证据审计](../benchmarks/results/gemma4-cold/evidence-audit.json)。

两项运行均通过证据完整性审计。它验证已记录输入、运行安排、指标计算、源码哈希，以及公开副本是否一致；不会将模型错误变成正确选择。

## 权重已加载时的延迟与质量

下表每行均包含全部 28 条用例。延迟单位为毫秒，是完成同步后的墙钟耗时，包含无效生成输出。没有发生运行时异常。`kv_cold` 保持权重已加载，但绕过提示词快照。`same_page` 在当前页面上使用一条另行记录的预热话语。`page_update` 预热不同的较早状态，再从较早的系统快照重新计算当前页面。加载与准备不在这些决策计时间隔内。

| 方法 | 条件 | p50 ms | p95 ms | 正确 / 28 | 拒绝 / 28 | 格式有效 / 28 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| direct | kv_cold | 1821.7 | 3050.1 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| direct | same_page | 134.9 | 283.9 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| direct | page_update | 840.1 | 1414.5 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| code | kv_cold | 2052.5 | 3847.3 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| code | same_page | 366.9 | 941.7 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| code | page_update | 1149.9 | 2195.2 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| json | kv_cold | 2282.5 | 3240.3 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json | same_page | 589.8 | 2312.9 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json | page_update | 1160.4 | 2148.9 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json_code | kv_cold | 2254.2 | 3616.1 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |
| json_code | same_page | 574.2 | 1823.6 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |
| json_code | page_update | 1375.0 | 3115.4 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |

拒绝指有效的 `no_match` 或 `abstain`，不包括格式错误的生成。三种条件的质量数量完全相同。百分位数汇总的是 28 个不同输入各一次测量，不是稳定的重复运行尾部估计。同页面准备本身的 p50／p95 耗时另计，不在表内：direct 1735.2／2951.6 ms、code 2059.2／4375.1 ms、JSON 2410.2／5435.4 ms、JSON-code 2293.0／4232.4 ms。全部准备记录保留在试验数据中。

本次运行的每种条件下，直接评分实测 p50 都低于三种基线。这是对此权重、提示词、输入集和主机的结果，不是固定延迟承诺，也不是与经过优化的生成方案比较。直接评分将最后位置词表限制为已验证候选编码。基线生成不使用语法约束或修复步骤，并存在大量格式失败。官方 MLX-LM 可能为单 token 生成安排前瞻计算；计时包含已完成工作。历史 Qwen／GLM 耗时采集于其他源码版本和条件，不能混合用来宣称加速。

## 动作错误、布尔选择与覆盖率

每种条件包含 **26 条 enum 请求**，其中 **16 条可执行请求**，以及 **2 条布尔请求**。下表分别适用于三种条件中的每一种。Enum 错误与覆盖率不包含布尔选择。

| 方法 | Enum 正确 / 26 | 错误 enum 动作 / 26 | 正确可执行 enum 选择 / 16 | 布尔正确 / 2 | no_match / abstain |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 24 (92.31%) | 1 (3.85%) | 15 (93.75%) | 2 (100%) | 9 / 1 |
| code | 20 (76.92%) | 0 (0%) | 13 (81.25%) | 2 (100%) | 8 / 0 |
| json | 2 (7.69%) | 0 (0%) | 1 (6.25%) | 0 (0%) | 0 / 1 |
| json_code | 9 (34.62%) | 0 (0%) | 1 (6.25%) | 1 (50%) | 10 / 0 |

直接评分路径在每种条件下选中 enum 动作 16 次，其中一次错误：即**选中 enum 动作中的 1/16，或 6.25%**。其两项错误为：

- `test-first-filtered`：话语为 “First one”，可见顺序为 Lunar Cartography、Tidal Engines。模型选择 `play_tidal`，而非 `play_lunar`。允许候选列表的顺序与可见列表不同。即使执行保护能阻止实际影响，这仍是模型动作错误。
- `test-close-ambiguous`：话语为 “Close it”，资料库和设置窗口均打开，且没有聚焦窗口。模型返回 `no_match`，而预期为 `abstain`。这是拒绝类别错误，不是错误动作。

第一项错误在三种缓存条件下均出现；聚合审计计为三条错误动作记录，而不是三条独立失败请求。较高的整体选择分数不能掩盖此错误。任何执行器纠正都不计为模型准确率，这些结果也不会使 Gemma 成为自动执行的默认模型。布尔准确率只有两条示例，基本只能说明这两条用例。分数仍是未经校准的候选相对值。

## 全部生成失败均保留计数

正式运行保留了 **0 次运行时失败和 141 条格式无效输出**：三种条件合计 code 15 条、JSON 78 条、JSON-code 48 条。

- **Code：** 每种条件五条无效输出，包括不是允许选项编码的 token `code`、`play` 和 `__`。无效用例为 `test-sort-title`、`test-vague-course`、`test-close-negation`、`test-first-filtered` 和 `test-first-reordered`。此外，在 `test-close-ambiguous` 上返回了 `no_match`，而非 `abstain`。
- **JSON：** 每种条件 26 条无效输出。其中 21 条是没有代码围栏的对象，但 `candidate_id` 中放入选项编码，例如 `{"candidate_id":"2"}`，而非允许的业务 ID；另外五条是带 Markdown 代码围栏的对象。两条有效响应均正确。严格解析器不会推断或修复其意图。
- **JSON-code：** 每种条件 16 条无效输出，全部是带 Markdown 代码围栏的对象。在 12 条有效响应中，模糊关闭与模糊课程请求错误地返回 `no_match`，而非 `abstain`，因此剩下 10 条正确选择。

精确输出、ID 和失败标记见链接的完整试验日志。无效生成仍计入准确率、格式有效率与覆盖率分母，其耗时仍保留在延迟统计中。大多输出无效的 JSON 基线即使没有返回错误动作，也不能证明它是有用或安全的执行器。`json_code` 是已披露的补充输出格式对照，在早期 Qwen 评测后引入；它不属于原始三方法协议。本次评测未加入 Gemma 专用提示词调参、约束解码、编码／ID 修复或代码围栏剥离。

## 输入规模、内存与缓存验证

全部请求包含 2–6 个应用候选，加上两个保留选项；话语为 8–34 个字符，序列化状态为 65–336 个字符。

| 方法 | 提示词 token 数 | 同页面复用 token 数 | 页面更新复用 token 数 | 生成 token 数 |
| --- | ---: | ---: | ---: | ---: |
| direct | 487–629 | 474–614 | 300 | 无 |
| code | 487–629 | 474–614 | 300 | 1 |
| json | 506–648 | 493–633 | 319 | 8–13 |
| json_code | 510–652 | 497–637 | 323 | 6–11 |

冷 KV 试验复用零个 token。审计确认 **112/112 次同页面试验与 112/112 次页面更新试验**均发生预期的实际前缀复用，同时重新计算后缀。这些是 KV 快照，不是缓存最终答案。

实测进程峰值 RSS 为 **11.52 GiB**，MLX 峰值分配为 **14.36 GiB**，记录到的最大 MLX 活跃内存为 **13.97 GiB**，最大保留前缀快照为 **500.31 MiB**。计入统计的试验快照中，观测到的最大分配器缓存为 **3.62 GiB**；一致性检查结束后的最终快照为 **5.89 GiB**。这些是进程／分配器观测，不是可相加或独立的单次调用内存成本。RSS 与 MLX 内存存在重叠。权重已加载运行另行记录模型初始化耗时为 **5672.3 ms**；这不是完整进程冷启动测量。

[一致性日志](../benchmarks/results/gemma4-test/parity.jsonl)包含 28 条记录，每条将同页面和变化页面分数分别与全新计算比较：**56/56 次比较通过**，获胜 ID 相同。记录的限值为返回 logit 绝对差 ≤ 0.5、受限分数差 ≤ 0.1，相对容差为零。此外，[三项实机模型集成测试](../benchmarks/results/gemma4-model-tests.json)总计 41.62 秒通过。其旋转缓存用例使用 1,741 个 token 的稳定前缀，同页面及页面更新比较中，logit／分数最大差均为 0.0。这不能验证 4,096 token 上限内的所有提示词、其他转换权重、批处理或多模态输入。

## 独立进程冷启动

这里是**每种方法三个全新 Python 进程**，合计 12 个，只使用 `test-close-player`。父进程墙钟耗时包含解释器启动、模型加载、首次决策、进程退出和结果收集。没有清空操作系统文件系统缓存。三次重复不足以获得稳定的 p95 估计，这一条请求也不会增加独立语义质量覆盖。

| 方法 | 父进程 p50 ms | 父进程 p95 ms | 正确 / 3 | 格式有效 / 3 | 拒绝 / 3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 7933.0 | 8465.9 | 3 | 3 | 0 |
| code | 8621.1 | 10052.9 | 3 | 3 | 0 |
| json | 9041.5 | 10456.7 | 0 | 0 | 0 |
| json_code | 8784.9 | 9284.6 | 0 | 0 | 0 |

没有运行时失败或返回的错误动作。全部三次 JSON 尝试返回 `{"candidate_id":"2"}`，全部三次 JSON-code 尝试返回带围栏的 `{"choice":"2"}`；六次均保留为格式失败。direct／code 的 enum 覆盖率为 3/3，JSON／JSON-code 为 0/3。没有布尔请求。不同格式的提示词长度为 571–594 个 token，前缀复用为零。冷启动工作进程不记录候选数／话语长度／状态大小列；这些输入仍以指定的冻结用例为依据。各工作进程中的最高 RSS 为 11.98 GiB，MLX 峰值分配为 13.88 GiB，没有保存前缀快照。

## 开发边界与复现

[24 次冒烟运行](../benchmarks/results/gemma4-moe-smoke/summary.json)使用两条开发用例、四种方法和三种缓存条件。[64 次开发运行](../benchmarks/results/gemma4-dev/summary.json)在同页面条件下使用全部 16 条开发用例与四种方法。它们是独立记录的运行，不是额外冻结测试试验。其输出与失败保持不变。冻结测试沿用现有阈值和语义提示词。以后任何模型专用调参，都需要独立声明的开发流程及后续留出评测。

使用已核验权重，每次运行使用新的输出目录。若要精确复现源码版本，单独检出 `ba98b71`，安装固定版本依赖，一次只运行一个模型任务：

```sh
export MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit
python -m benchmarks.run --model "$MODEL" --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --repeats 1 --output runs/gemma4-dev-reproduction
python -m benchmarks.run --model "$MODEL" --split test \
  --modes direct code json json_code --repeats 1 --parity \
  --output runs/gemma4-test-reproduction
python -m benchmarks.cold_start --model "$MODEL" --split test \
  --modes direct code json json_code --repeats 3 \
  --output runs/gemma4-cold-reproduction
python -m benchmarks.audit runs/gemma4-test-reproduction --source-revision ba98b71
python -m benchmarks.audit runs/gemma4-cold-reproduction --source-revision ba98b71
JEV_TEST_MODEL="$MODEL" python -m pytest tests/test_model.py -q
```

当前[报告脚本](../scripts/summarize_extended.py)可以从这些日志派生 enum 与布尔汇总，不修改原始日志。指标定义和计时边界见完整[评测协议](evaluation.zh-CN.md)。
