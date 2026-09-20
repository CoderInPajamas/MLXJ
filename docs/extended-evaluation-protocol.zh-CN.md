# 新增模型与扩展测试集评测协议

[返回项目首页](../README.md)

协议 ID：`extended-evaluation-v1`。2026-09-20 定稿，早于 Gemma 原始测试集运行及所有扩展集推理。本文件规定实验；完成情况另见结果报告。定稿前，Gemma 原始 16 条开发用例已按这些固定设置开始运行。结果中应记录本协议的 Git 提交；后续任何修订均须明确保留。

范围包括：使用已有本地 Gemma MoE 权重运行原始测试集，以及使用三个相同的本地模型权重运行新增六领域扩展集。现有提示词、模型权重、分数处理、拒绝阈值与冻结标签保持不变。本协议不包含模型专用语义提示词或依据测试结果调整阈值。

## 已知信息与独立数据集

原始测试集中较早的 Qwen 和 GLM 结果已经知晓。Gemma 兼容性冒烟运行也已使用**原始开发集的前两条用例**，覆盖全部四种方法和三种缓存条件。它仍是单独的冒烟记录，不是完整开发或测试结果。本协议不会追溯性地预先登记该次运行、原始开发运行、三项 Gemma 集成测试或历史基准。

扩展集是在已知历史结果后编写的，但其标签编写未使用针对扩展用例自身的模型推理。数据冻结时间为 `2026-09-20T06:09:44.415784+00:00`。它是开发后的扩展，不是未受影响的原始基准，也不是独立抽样的总体研究。

| 数据集 | 目录 | 开发用例 | 测试用例 | 测试组成 |
|---|---|---:|---:|---|
| 原始虚构课程／播放器数据集 | `benchmarks/fixtures` | 16 | 28 | 26 条 enum 请求，2 条布尔请求 |
| 六领域扩展集 v1 | `benchmarks/fixtures/extended-v1` | 12 | 36 | 30 条 enum 请求，6 条布尔请求 |

[原始清单](../benchmarks/fixtures/manifest.json)与[扩展清单](../benchmarks/fixtures/extended-v1/manifest.json)是用例身份、数量和精确字节的权威依据。原始文件保持不变。更多细节和标签理由见[扩展集说明](../benchmarks/fixtures/extended-v1/README.zh-CN.md)。

| 文件 | 冻结 SHA-256 |
|---|---|
| 原始 `dev.jsonl` | `610114cd493232ffd05a9dc5ffe6dd355b1bc3d7c1ad62f65ff02f5c413f6e16` |
| 原始 `test.jsonl` | `e86e2278a872ab37b2143a12b2e39fb6dde7a0ffac96afa6cc80c139ddfafce3` |
| 扩展 `dev.jsonl` | `b5c070b8aa40ac313723f996bc9f7c3e406e11fa7332dbf47ab49958d0dd3408` |
| 扩展 `test.jsonl` | `ad804e681bb6906c81dc5da316b61a805dd1dbfc8df20940c7b1cc22776aa25e` |

## 模型权重与固定运行时

使用下列已有本地转换版本，原始文件只读：

| 权重目录名 | 已核验转换版本 |
|---|---|
| `gemma-4-26b-a4b-it-4bit` | `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |
| `Qwen3.5-9B-OptiQ-4bit` | `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| `GLM-4.7-Flash-4bit` | `1454cffb1a21737e162f508e5bc70be9def89276` |

这里的 Gemma 是 `google/gemma-4-26b-a4b-it` 的本地 MLX 转换版本，不是主机上另有的 DiffusionGemma 或修改版 Gemma 转换权重。其本地文本配置启用 MoE，包含 128 个专家并采用 top-8 路由。转换默认使用 4-bit 仿射量化，分组大小为 64，并包含 8-bit 覆盖配置；仅凭文件名不能完整描述量化。精确文件与转换来源见 [Gemma 权重证据](../benchmarks/results/gemma4-checkpoint.json)及 [Qwen／GLM 权重证据](../benchmarks/results/checkpoints.json)。

使用项目独立环境与当前官方 MLX-LM 后端。不修改共享模型环境、权重、系统内存限制或其他正在运行的应用。模型任务串行运行。从每次运行记录实际硬件、依赖版本、模型配置／tokenizer 哈希、量化、源码哈希和加载时间；不得假设它们与历史运行相同。

本计划审查的语义运行时代码具有以下 SHA-256 哈希：

| 源码 | SHA-256 |
|---|---|
| `src/jev_mlx/prompt.py` | `8d0b340fb804a83ad37a6ee6a0feca39b4af061598712a2078ae1903e3c76f6b` |
| `src/jev_mlx/engine.py` | `10aebdb027d54fbc42f49f7a249abc2f4149b613de6d063c5e91fe300ba15baa` |
| `src/jev_mlx/backends/mlx_lm.py` | `9925f8da4c7b8b9ab6c879d0d2f354170365792a5f886b142ca339af5254d84c` |

运行器扩展新增了显式选择测试数据目录及报告功能；每次完整运行也必须保留运行器和指标实现的哈希。如推理行为变化，应保留先前尝试，并开始一个另行标识的实验。不得悄悄合并不同源码版本的结果。

固定设置如下：

- 直接评分 margin 阈值为 **0.0**。选中候选的 margin 恰为零时，结果变为 `abstain`；原始获胜候选保留为 `raw_selected_id`。保留选项 no-match／abstain 获胜时，维持各自状态。
- 使用全部四种方法：`direct`、`code`、`json`、`json_code`。直接评分和编码生成共享同一编码选择提示词。JSON 方法保留相同语义策略、状态与选项，仅要求各自现有的输出格式。
- 使用官方贪心生成，温度为 0；编码生成上限为 1 个 token；JSON 和 JSON-code 上限为 96 个 token。不使用约束解码器、答案修复、重试直到正确、隐藏参数生成或模型专用格式修正。
- 使用现有 tokenizer 聊天模板并设置 `enable_thinking=False`，验证单 token 选项编码，保持官方模型输出头不变。
- 提示词上限 4096 个 token，预填充分块 256 个 token，前缀缓存上限 512 MiB、16 个条目，串行推理。不缓存最终答案。
- 每个用例／方法／缓存条件进行一次计入统计的重复；确定性调度种子为 `20260919`。保留准备调用，但不将其计入决策延迟。
- 缓存一致性：logit 绝对容差为 0.5，相对容差为 0；受限 softmax 绝对容差为 0.1；原始首选 ID 必须完全相同。

`json_code` 最初是在历史 JSON 格式失败后加入的。此次新增实验事先固定全部四种格式，但这不会抹去该格式属于由测试结果启发的补充对照这一来源。

## 计划运行矩阵

开发运行用于检查固定配置，不意味着可以调整本次实验的提示词或阈值。后续任何调参都需要独立计划与重新标识的评测，并保留所有固定配置下的尝试。

| 运行 | 模型 | 数据划分 | 方法 | 条件 | 计入统计的记录 | 额外一致性检查 |
|---|---|---|---|---|---:|---|
| 原始开发集 | Gemma | 16 条开发用例 | 全部四种 | 仅同页面 | 64 | 无 |
| 原始测试集 | Gemma | 28 条测试用例 | 全部四种 | 全部三种 | 336 | 28 条用例，56 次比较 |
| 新进程冷启动 | Gemma | 仅原始测试集第一条 | 全部四种 | 新进程，每方法重复 3 次 | 12 | 无 |
| 扩展开发集 | Gemma、Qwen、GLM | 12 条开发用例 | 全部四种 | 仅同页面 | 每模型 48 条，共 144 条 | 无 |
| 扩展测试集 | Gemma、Qwen、GLM | 36 条测试用例 | 全部四种 | 仅同页面 | 每模型 144 条，共 432 条 | 此次运行不包含 |

主要计划包含 **988 条测量记录**，不含准备调用、单独的数值一致性计算及更早的兼容性冒烟运行。无论模型、输出方法、缓存条件或计时重复多少次，每个测试集的独立质量用例数始终分别为 28 或 36。

对于需要验证新状态下完整缓存覆盖的任一模型，可在**单独输出目录**运行可选的扩展直接评分缓存验证。对全部 36 条测试用例运行全部三种条件并检查一致性：每个选定模型产生 108 条直接评分测量记录和 72 次一致性比较。如果三个模型都运行，则为 324 条记录、216 次比较。启动该阶段前应记录选定模型及理由；保留完整结果，包括失败。不能用此阶段替换不理想的主要运行，也不能悄悄与主要运行的热缓存耗时合并。

本次实验事先选择**只对 Gemma**运行此阶段：它的旋转窗口缓存是兼容性表中的新增支持项，而新的状态结构需要额外数值检查。这增加 108 条测量记录及 72 次比较，计划测量总量为 **1,096**。扩展集的 Qwen 和 GLM 缓存冷态／页面更新条件不在本次实验范围内；它们已有的原始测试集数值证据仍单独保留。

三种权重已加载条件的含义：

| 条件 | 准备步骤与计时工作 |
|---|---|
| `kv_cold` | 权重已加载；计时调用使用 `use_cache=False` |
| `same_page_new_utterance` | 使用用例中不同的预热话语对相同状态／选项预热；测量目标话语 |
| `page_update` | 预热用例中不同的较早状态；测量当前状态，重新计算变化的后缀 |

请求复用缓存不等于证明实际命中：应检查实际 `cache.hit`、作用域、复用／预填充 token 数与内存。数值一致性只针对直接评分，即使同一次运行也测量生成方法。每条一致性用例分别将全新分数与同页面复用、页面更新复用进行比较。

新进程测量使用原始测试集第一条 `test-close-player`。父进程墙钟耗时包含解释器启动、加载、首次决策和进程退出。加载／决策分项需单独记录。不清空操作系统文件系统缓存。每种方法重复三次，不能建立稳定的尾部百分位数，也不能证明完整测试集的语义质量。

## 评分与报告

原始结果与扩展结果使用不同表格。严格准确率要求状态符合预期；若为选择结果，则稳定候选 ID 也必须正确。`no_match` 和 `abstain` 是不同标签。原始选择准确率与返回决策准确率分别报告，保留零 margin 拒绝、无效 JSON、无法识别的生成编码、截断、加载错误、准备错误和运行时失败。执行器不能将错误模型选择改算为正确。

每种方法和条件均应报告 p50／p95、尝试数量、准确率、拒绝／弃权、格式有效性、正确选择覆盖率、原始与返回错误率、内存及失败。保留每次 `wall_ms` 观测；当前百分位数使用线性插值，包含已完成但语义错误或格式无效的响应。异常有独立的失败延迟。MLX 值与缓存在后端计时结束前完成计算并同步。生命周期 RSS、MLX 活跃内存、分配器缓存和 MLX 峰值内存是不同测量，不能当作互不重叠的内存分配相加。

**Enum 动作指标与布尔回答指标分开：**

| 测试集 | Enum 请求 | 可正确执行的 enum 动作机会 | 布尔请求 | 预期选中的布尔回答 | 聚合预期 `selected` |
|---|---:|---:|---:|---:|---:|
| 原始 | 26 | 16 | 2 | 2 | 18 |
| 扩展 | 30 | 15 | 6 | 4 | 19 |

现有聚合 `executable_request_coverage` 的分母包含布尔回答，为 18 或 19，而不是真实应用动作数量。同样，通用 `false_action` 指标也包含错误选中的布尔回答。关于动作错误的陈述应使用按类型拆分的 enum 结果；布尔错误应称为分类错误。未知布尔状态需要弃权；已知命题为假则是合法的选中回答。

测试数据运行器**不会**执行浏览器、日历、文件系统操作、购买或任何其他应用副作用。正确的测试标签不等于浏览器执行回执。已有浏览器视频属于单独的历史证据；这些运行不能证明 Gemma 或 GLM 执行了浏览器操作。英文输入结果也不能证明中文或混合语言理解能力。

不能把退出码为零解读为模型质量完美：格式无效或语义错误的响应可以在没有运行时异常的情况下完成。同样，`complete=true` 表示各阶段已完成，而非所有答案正确。完整运行必须保留全部预期记录和请求的一致性记录，才能标记完成；中断或子集运行须明确标注未完成或仅为冒烟测试。

任何速度比较都必须使用相同源码版本、相同条件下的实测路径，并在延迟旁同时报告质量与覆盖率。不得将新 Gemma 或扩展集耗时与历史 Qwen／GLM 耗时合并来宣称加速。单 token 官方生成可能安排前瞻计算；同步计时包含此工作。直接读取 logits 仍然是因果模型计算，不能证明其拥有独有的非自回归架构，也不能证明固定 100 ms 上限。

## 复现命令

在项目独立环境中，从仓库根目录运行。将模型根目录占位符替换为包含已核验本地权重的目录。每次尝试使用全新输出目录，绝不覆盖证据。

```bash
source .venv/bin/activate
MODEL_ROOT=/absolute/path/to/local/models
GEMMA_MODEL="$MODEL_ROOT/gemma-4-26b-a4b-it-4bit"

python -m benchmarks.run --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/gemma-original-dev-v1

python -m benchmarks.run --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split test \
  --modes direct code json json_code \
  --conditions kv_cold same_page_new_utterance page_update \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --parity --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/gemma-original-test-v1

python -m benchmarks.cold_start --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split test \
  --modes direct code json json_code --repeats 3 \
  --output results/gemma-original-cold-v1
```

对三个权重依次串行运行扩展集：

```bash
for checkpoint_name in gemma-4-26b-a4b-it-4bit Qwen3.5-9B-OptiQ-4bit GLM-4.7-Flash-4bit
do
  python -m benchmarks.run --model "$MODEL_ROOT/$checkpoint_name" \
    --fixtures-dir benchmarks/fixtures/extended-v1 --split dev \
    --modes direct code json json_code --conditions same_page_new_utterance \
    --margin-threshold 0 --repeats 1 --seed 20260919 \
    --output "results/extended-v1-$checkpoint_name-dev"

  python -m benchmarks.run --model "$MODEL_ROOT/$checkpoint_name" \
    --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
    --modes direct code json json_code --conditions same_page_new_utterance \
    --margin-threshold 0 --repeats 1 --seed 20260919 \
    --output "results/extended-v1-$checkpoint_name-test"
done
```

对于单独声明的可选直接评分缓存阶段，启动前选定模型路径与独立输出名称：

```bash
export JEV_MLX_MODEL="$GEMMA_MODEL"
python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
  --modes direct --conditions kv_cold same_page_new_utterance page_update \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --parity --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/extended-v1-gemma-direct-cache
```

这些参数已对照 `benchmarks.run` 和 `benchmarks.cold_start` 检查，包括 `--fixtures-dir`。运行元数据内嵌测试数据清单；应保留 `metadata.json`、`trials.jsonl`、`summary.json`、请求生成的 `parity.jsonl`，以及权重来源和定稿协议。不得修改测试数据清单，使已变化的数据集通过校验。
