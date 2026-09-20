# 测试方法与实测结果

[返回项目首页](../README.md)

[评测协议](evaluation.zh-CN.md) · [历史完整结果](results.zh-CN.md) · [六领域扩展结果](extended-results.zh-CN.md) · [新增评测协议](extended-evaluation-protocol.zh-CN.md) · [Gemma 原始集实测](gemma4-results.zh-CN.md) · [支持模型](models.zh-CN.md)

最新核心测试 **161 项通过**。六领域扩展集的三个模型、四种输出方法已完成同页新话语评测并通过证据审计。下面只列直接评分；完整基线、拒绝率、覆盖率、格式失败、内存和原始记录见[扩展结果](extended-results.zh-CN.md)。

| 模型 | 严格正确 / 36 | 动作误选 / 30 个 enum 请求 | 正确动作覆盖 / 15 | 布尔正确 / 6 | 同页 p50 / p95 |
|---|---:|---:|---:|---:|---:|
| Gemma 4 MoE | 31/36（86.1%） | 1/30 | 12/15 | 5/6 | 168.9 / 556.5 ms |
| Qwen3.5-9B-OptiQ-4bit | 30/36（83.3%） | 1/30 | 12/15 | 6/6 | 194.8 / 407.5 ms |
| GLM-4.7-Flash-4bit | 21/36（58.3%） | 8/30 | 9/15 | 2/6 | 170.6 / 330.5 ms |

三者使用相同冻结输入、提示词和阈值。上述时间要求权重已加载、页面前缀已经准备好；每模型 144 条测试记录仍只有 36 个不同场景。Gemma 选错队列首项，Qwen 选错最长续航产品，GLM 有更多错误动作。布尔答案错误独立统计，不计为动作误选。**这些结果不支持无人确认的通用动作执行。** Gemma 另完成 108 次三条件直接评分及 **72/72** 次缓存对照；三种条件均为 31/36 正确、1/30 错误 enum 动作，缓存一致不代表语义正确。

新 wheel 已在仓库外的独立环境安装，14 个运行文件与源码、包内内容逐字节一致；真实 Gemma CLI 调用为示例正确选择 `player.pause`。[安装验证](../benchmarks/results/extended-release-checks/distribution.json)单独记录，不计入模型质量集。

原有 28 题单独保留：Gemma 为 **26/28**，含一次筛选后首项选择错误，即 **1/26 个 enum 请求返回错误动作**，详见[Gemma 原始集报告](gemma4-results.zh-CN.md)。两个数据集不能合并成一个未见测试成绩。

以下详细解释历史 Qwen、GLM 测量和 Qwen 浏览器演示。原有 28 题实测中，**Qwen3.5-9B-OptiQ-4bit 的最终决策准确率为 25/28（89.3%）**，同页新话语的 p50 / p95 为 **171.7 / 176.4 ms**；GLM-4.7-Flash-4bit 为 **14/28（50.0%）**，当前提示词下不推荐直接用于动作执行。

这些是特定机器、模型、英文场景和实现版本的结果。没有证明任意模型兼容、固定 100 ms、零语义错误或概率已校准。中文文档与中文界面文本，也不代表中文指令或中英混合指令已经通过模型评测。

原始评测、截图和录屏使用项目旧称 JEVKit MLX；证据文件保留原名称、源码哈希和记录时间，没有为更名而改写。下文复现命令使用当前 `jev-mlx` 命令、`jev_mlx` 模块和 `JEV_MLX_MODEL` 环境变量。当时更名验证重新做了核心测试与独立 wheel 的真实模型调用，**并非重新运行整套质量评测和浏览器模型测试**，见[更名验证记录](../benchmarks/results/rename-release-checks/verification.json)。

## 到底测了什么

| 层次 | 样本或检查 | 能说明什么 |
|---|---|---|
| 核心自动化测试 | 最新单次 161 项通过，0 失败、0 错误；不加载 GPU 模型 | 数据约束、评分处理、状态版本、并发过期保护、结果身份与重放保护、HTTP、缓存边界等软件行为 |
| 开发集 | 16 个重新编写的虚构英文场景 | 用于开发提示词；不作为未见测试成绩 |
| 冻结测试集 | 28 个不同英文场景，其中 16 个可执行 enum 请求、10 个 enum 拒绝请求和 2 个布尔答案 | 固定提示词与阈值下的模型语义质量 |
| 六领域扩展集 | 独立的 12 条开发、36 条冻结测试；测试含 30 个 enum 请求和 6 个 boolean 判断 | 三个模型在文档、日历草稿、文件、音乐、商品比较、设置上的新场景表现；不是原始集的追加独立抽样 |
| Qwen/GLM 缓存对照 | 两个模型，各 28 场景 × 2 种复用方式 | 与全新计算相比，缓存复用是否改变候选分数或选择 |
| Gemma 扩展缓存对照 | 36 场景 × 3 条件共 108 次直接决策；36 行 parity 记录含 72 次比较，全通过 | 扩展集上同页复用、页面更新与全新计算的数值一致性；不是新增独立语义样本 |
| 真实浏览器 | Qwen 驱动的 16 场景，另加一次页面变化检查 | 模型选择、实际 DOM 点击、服务端执行回执与可见状态是否衔接正确 |

[最新核心验证](../benchmarks/results/extended-release-checks/core-tests.json)为单次 **161 passed**，pytest 显示 3.76 秒（JUnit 套件记录 3.752 秒），0 失败、0 错误、0 跳过；另有 3 项真实模型测试未选中，lint 通过。HTTP 测试在允许回环端口的环境运行，远程 GitHub CI 尚未执行。

历史更名验证的 **145 项**仍保留：先通过 138 项，7 个 HTTP fixture 因沙盒禁止绑定端口未能建立；重跑 HTTP 后 8 项通过，其中 1 项重复，合计 145 个不同测试。这个历史过程不代表最新 161 项运行也发生过同样错误。

开发集和测试集都是公开的虚构数据，没有从生产对话、录音、截图或日志导出。文件及冻结哈希见[数据清单](../benchmarks/fixtures/manifest.json)，具体输入见[开发集](../benchmarks/fixtures/dev.jsonl)和[测试集](../benchmarks/fixtures/test.jsonl)。覆盖场景包括：

- 不同打开对象或没有对象时，同一句 “Close it” 的含义变化。
- 打开视频库入口与播放某个具体课程的区别。
- “First one” 按当前筛选、排序后的可见顺序选择。
- 视频库、播放器加载中、播放器就绪时，允许动作发生变化。
- “Did you just close it?” 是询问；否定、模糊表达和不存在的目标应被拒绝。
- 候选顺序变化、布尔判断，以及执行阶段的过期结果保护。

开发过程中，Qwen 开发集从 14/16 改善到 15/16，随后冻结通用语义提示词和 `margin_threshold=0.0`，再运行主测试。没有添加针对这些话语的正则规则，也没有在冻结测试集上调整阈值。

## 怎样读质量指标

**最终决策准确率**同时要求选择 ID 和状态正确。例如标注要求 `abstain`，模型却返回 `no_match`，严格评测仍算错，即使两者都不会执行动作。

**原始选择准确率**看 `raw_selected_id`，保留阈值处理前的模型选择。零 margin 的并列选择可能被引擎转为 `abstain`，因此原始与最终准确率不同。执行器拦住一个错误选择，只能算保护生效，不能把模型错误记成答对。

**动作误选率**只看 enum 请求：原始集分母为 26，扩展集为 30；**动作覆盖率**是正确动作选择数除以应可执行 enum 请求，原始集分母为 16，扩展集为 15。模型评测本身不执行这些动作。布尔题单独统计答案准确率，不能把事实答案称为执行动作。

旧记录的 `false_action` 和 `executable_request_coverage` 是混合口径：28 题包含两个布尔答案，18 个期望 `selected` 实际是 16 个动作加 2 个答案。旧数字保留并明确标为“混合选择”，按类型拆分来自[只读派生报告](../benchmarks/results/legacy-kind-breakdown.json)，没有改写原始记录。**拒绝率**仍统计全部请求中的 `no_match` 与 `abstain`，**弃权率**只统计 `abstain`。

扩展集的 6 个布尔问题中，4 个应选择真/假答案、2 个应因信息不足而弃权。其历史混合选择分母为 19，即 15 个动作加 4 个答案，不是 19 个可执行动作。扩展结果使用按类型拆分的口径。

`scores` 是候选范围内的 softmax 分数；`margin` 是最高与次高原始 logit 的差。它们都不是“正确概率”，不同模型的 logit 数值也不宜直接比较。

## Qwen/GLM 缓存修订结果（历史运行）

以下来自 [Qwen 最终汇总](../benchmarks/results/qwen9b-cache-fixed/summary.json)和 [GLM 最终汇总](../benchmarks/results/glm-cache-fixed/summary.json)。每个模型都运行三种缓存条件，每种 28 次；三组质量相同，因此这里只列一组分母。

| 指标 | Qwen3.5-9B-OptiQ-4bit | GLM-4.7-Flash-4bit |
|---|---:|---:|
| 最终决策准确率 | **25/28（89.3%）** | **14/28（50.0%）** |
| 原始选择准确率 | 26/28（92.9%） | 15/28（53.6%） |
| 最终动作误选率（enum） | 0/26（0%） | 2/26（7.7%） |
| 原始动作误选率（enum） | 0/26（0%） | 3/26（11.5%） |
| 拒绝率 | 11/28（39.3%） | 16/28（57.1%） |
| 弃权率 | 1/28（3.6%） | 12/28（42.9%） |
| 可执行 enum 动作覆盖率 | 15/16（93.8%） | 8/16（50.0%） |
| 布尔答案准确率 | 2/2 | 2/2 |
| 历史混合选择覆盖率 | 17/18（94.4%） | 10/18（55.6%） |
| 输出结构有效 | 28/28 | 28/28 |
| 运行异常 | 0/28 | 0/28 |

GLM 返回了 10 个动作和 2 个布尔答案，其中两个动作错误。旧值 2/12（16.7%）是已返回选择的混合错误率；只看已返回动作则是 2/10（20%）。Qwen 在 26 个 enum 场景上没有动作误选，但不能据此承诺真实应用中不会误操作。

每个模型的 84 条记录等于 **同样的 28 场景 × 3 种缓存条件**。它们不是 84 个独立语义样本，两个模型也共享这套 28 场景。增加 `--repeats` 可以获得更多计时观察，不能把重复题目算作新测试题。

耗时单位为毫秒。每个单元格为 **p50 / p95**，各来自 28 次调用；MLX 计算在计时结束前完成同步求值。

| 缓存条件 | Qwen | GLM |
|---|---:|---:|
| 权重已加载、KV 冷：`kv_cold` | 2159.9 / 2406.6 | 1837.6 / 2154.5 |
| 同页新话语：`same_page_new_utterance` | **171.7 / 176.4** | **147.8 / 170.6** |
| 页面变化后的首次决策：`page_update` | 1050.2 / 1294.5 | 927.4 / 1246.5 |

同页复用的是完整页面前缀，页面变化时只复用变化前的稳定系统前缀，并重新计算页面与话语后缀。没有缓存最终答案冒充模型加速。页面更新和 KV 冷状态仍需约一至数秒；这些数据不支持“固定 100 ms”。

实测机器为 Apple M2 Max、64 GiB 统一内存，Python 3.13.2、MLX 0.31.2、MLX-LM 0.31.3。Qwen 是混合 4/8-bit、group size 64；GLM 是 4-bit、group size 64。测试输入每题 2–6 个业务候选，另加两个拒绝候选，话语为 8–34 个英文字符。当前实现串行推理，最多 64 个业务候选、4096 个提示词 token，前缀缓存最多 512 MiB / 16 条。完整模型哈希、内存口径和硬件信息见[完整报告](results.zh-CN.md)及[模型来源](../benchmarks/results/checkpoints.json)。

## 已知错误，不用保护逻辑冲掉模型错误

Qwen 的三个最终错误在三种缓存条件下都存在：

| 场景 | 期望 | 实际 |
|---|---|---|
| 两个窗口打开、没有焦点：“Close it” | `abstain`，需要澄清 | `no_match` |
| 多个课程可选：“Play something” | `abstain`，需要澄清 | `no_match` |
| 列表重新排序：“First one” | `play_lunar` | 原始并列处理选对，但 margin 为 0，最终 `abstain` |

第三项的 `play_lunar`、`sort_title`、`__no_match__` 都得到 22.25 的 logit。引擎对完全并列弃权，所以不能把原始 26/28 写成最终准确率。

GLM 的两个最终误操作是：多窗口歧义下错误选择 `close_settings`，以及播放器加载中收到暂停请求却选择 `back_to_library`。它还有一次原始错误选择 `open_library` 被零 margin 转为弃权；这次不计入最终误操作，但仍保留为原始模型错误。模型能加载、能输出合法候选、缓存数值一致，并不意味着语义质量足够用于动作执行。

全部逐题输入、输出、原始分数和错误都保存在 [Qwen 逐条记录](../benchmarks/results/qwen9b-cache-fixed/trials.jsonl)与 [GLM 逐条记录](../benchmarks/results/glm-cache-fixed/trials.jsonl)。

## Qwen/GLM 缓存为什么说 112 次对照通过

每个模型对 28 个场景分别比较“同页复用 vs 全新计算”和“页面更新复用 vs 全新计算”，所以是 **2 个模型 × 28 场景 × 2 种对照 = 112/112 通过**。所有这些对照的最大候选 logit 差和 softmax 分数差实测都为 0，原始最高候选一致。记录保留了预先设定的容差：logit 绝对误差 0.5、相对误差 0，分数绝对误差 0.1。

这不是 112 个不同语义问题，也不是所有未来输入都保证逐位相同。证据见 [Qwen 对照](../benchmarks/results/qwen9b-cache-fixed/parity.jsonl)和 [GLM 对照](../benchmarks/results/glm-cache-fixed/parity.jsonl)。

旧实现曾在 GLM 的 28 个缓存场景中有 **25 个对照失败**：同页复用一致，但页面变化后任意共同前缀的部分复用出现差异，最大 logit 差为 5.5，且 1 题最高候选改变。修订 `579daf3` 只接受完整系统或页面快照边界的复用，再完成以上复测；没有改变语义提示词或阈值。[旧版失败记录](../benchmarks/results/glm-test/parity.jsonl)仍保留，差异原因没有被未经证实地归为框架 bug。

## 与生成一个编号、生成 JSON 的比较

主对照在旧实现 `a743972` 上使用同一个 Qwen 模型，包含直接读候选 logits、官方生成接口只生成一个编号，以及生成带业务 ID 的 JSON。下面是**当时同一轮**同页新话语结果，不能与上面的修订后耗时拼接计算加速比。

| 历史方法 | 最终准确率 | 错误选择（混合） | 选择覆盖（混合） | 同页 p50 / p95（ms） |
|---|---:|---:|---:|---:|
| 直接候选评分 | 25/28 | 0/28 | 17/18 | 196.3 / 202.7 |
| 只生成一个编号 | 26/28 | 0/28 | 18/18 | 445.4 / 693.9 |
| 生成业务 ID JSON | 6/28 | 0/28 | 0/18 | 604.3 / 1304.8 |

原 JSON 基线在三个条件中共有 66/84 次结构不合法，主要把内部编号写进了要求业务 ID 的字段；没有有效动作输出不能解读为安全或准确。原始文本全部保留。[主对照记录](../benchmarks/results/qwen9b-test-v1/summary.json)也显示：KV 冷时直接评分的 p95 为 3751.7 ms，比编号基线的 3243.2 ms 更慢，不能只展示有利的热缓存结果。

看到原 JSON 测试失败后，新增了输出 `{"choice":"0"}` 的 `json_code` 格式对照。它在同一冻结集得到 26/28、混合错误选择 1/28（enum 动作错误 1/26）、结构有效 28/28，同页 p50 / p95 为 529.4 / 953.6 ms；误操作是把 “Play something” 转成播放某课程。**这是看过测试结果后加入的补充格式实验，不是未接触测试集的独立盲测**，见[补充记录](../benchmarks/results/qwen9b-jsoncode-test/summary.json)。

直接评分使用官方模型原有量化输出头，读取最后位置候选 logits，不生成后续文本；底层仍然是因果语言模型的下一 token 计算。官方 `max_tokens=1` 生成路径可能还有下一步预取计算，计时包含实际完成的计算。因此这些对照说明当前接口路径的表现，不能证明本项目拥有独有的无自回归架构，也不能证明比经过同样优化的单步 argmax 必然更快。

## 进程冷启动是另一个指标

权重已加载但 KV 冷，不等于新进程冷启动。另行测了 Qwen 每种方法 3 次、GLM 每种方法 2 次的新进程启动，四种方法合计 20 次。外层计时包括进程启动、加载、首次决策和退出，只使用第一道测试题，未清空操作系统文件缓存。

其中直接评分的外层耗时 p50 / p95：Qwen 为 4897.3 / 4928.1 ms，GLM 为 8726.6 / 8848.2 ms。每组仅 2–3 个样本，不能称为稳定的 p95；20 次没有进程运行异常，也不等于 20 次模型回答都正确。格式和语义失败均保留在 [Qwen 冷启动记录](../benchmarks/results/qwen9b-cold/summary.json)、[GLM 冷启动记录](../benchmarks/results/glm-cold/summary.json)及[完整解释](results.zh-CN.md)。

## 真实浏览器怎么测

使用真实本地 Qwen 后端和 Chromium，在虚构应用 Morrow Studio 中输入话语，由模型选择当前允许的动作，再点击对应 DOM 按钮，取得服务端一次性执行回执，并检查页面状态。模型、浏览器点击和执行都是真实的；桌面、课程和播放器是公开的模拟应用，不是任意网站操作，也不是截图视觉识别。

16 个场景覆盖空桌面拒绝关闭、打开课程库、筛选课程、按可见顺序播放、暂停、继续、回退、关闭、询问不执行、否定不执行、目标不存在、模糊请求、笔记窗口，以及加载状态下拒绝暂停。排序等准备动作单独记录，没有算作模型选择成绩。

结果为 **16/16 场景通过，10 次模型动作获得 DOM 执行回执，6 次拒绝，0 个浏览器错误**。浏览器演示对拒绝允许 `no_match` 或 `abstain`，比冻结基准的严格状态匹配更宽；不能用 16/16 覆盖前面的 25/28，更不能写成通用模型准确率 100%。GLM 和 Gemma 尚未完成同样的真实浏览器测试；六领域评测只选择候选，不操作真实应用。

另一次并发检查证明：决策请求尚未完成时页面切换为笔记窗口，旧选择 `open.library` 最终标记 `stale`，没有执行。记录证明请求与页面更新重叠；GPU 实际计算区间的重叠没有单独测量。加载中允许候选只有关闭播放器，“Pause it” 返回 `no_match`，未执行。

查看[完整浏览器记录](assets/browser-demo/browser-transcript.json)、[实际录屏](assets/browser-demo/video/page@9986ccf6fcac324ee3a7302c87bf305e.webm)和[播放器截图](assets/browser-demo/03b-player-control.png)。第一次采集因读取隐藏元素文本及整理录像路径的问题失败，原始媒体与[失败说明](assets/browser-initial/harness-failure-note.json)也保留；修复的是采集脚本，没有改模型提示词或阈值，该失败没有伪装成模型成绩。

## 在自己的机器上复现

以下命令在仓库根目录执行。使用独立虚拟环境，不修改共享 Python 环境或模型文件；模型路径替换为自己已有的本地 MLX 权重。一次只运行一个模型任务，避免把其他 GPU 负载混入计时。

先运行无需模型的核心测试：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -m 'not model' -q
python -m ruff check src tests benchmarks scripts examples
```

Apple Silicon 上安装真实推理依赖，运行一个决策和可选模型集成测试：

```bash
python -m pip install -e '.[mlx,dev,browser]'
export JEV_MLX_MODEL=/absolute/path/to/Qwen3.5-9B-OptiQ-4bit
jev-mlx decide --request examples/decision.json
JEV_TEST_MODEL="$JEV_MLX_MODEL" python -m pytest tests/test_model.py -q
```

先跑开发集；若要调整提示词或阈值，只使用开发集。再以固定配置运行完整冻结集与缓存对照：

```bash
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split dev \
  --modes direct --repeats 1 --output results/local-qwen-dev

python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct --conditions kv_cold same_page_new_utterance page_update \
  --repeats 1 --margin-threshold 0 --parity \
  --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/local-qwen-direct-test
```

运行同模型三方法对照，以及单独的新进程冷启动检查：

```bash
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct code json --repeats 1 \
  --output results/local-qwen-comparison

python -m benchmarks.cold_start --model "$JEV_MLX_MODEL" \
  --modes direct code json json_code --repeats 3 \
  --output results/local-qwen-process-cold
```

这些命令运行当前源码，不能保证重现历史源码的同一耗时。换 GLM 时设置新的 `JEV_MLX_MODEL` 并使用新的输出目录；原 GLM 冷启动记录每种方法只重复 2 次。查看输出中的 `metadata.json`、`trials.jsonl`、`summary.json` 和 `parity.jsonl`，保留失败与完整输入，比较模型身份、源码哈希和缓存命中条件后再比较速度。

复现六领域扩展时，显式传入 `--fixtures-dir benchmarks/fixtures/extended-v1`，先跑其独立开发集，再跑冻结测试集；本次三模型四方法对照只使用 `--conditions same_page_new_utterance`。完整命令与另外声明的 Gemma 缓存阶段见[固定协议](extended-evaluation-protocol.zh-CN.md)，实际完成范围见[扩展报告](extended-results.zh-CN.md)。不要修改冻结文件或根据这些已公开测试结果调整阈值后仍称其为未见评测。

运行浏览器测试时，终端一启动服务：

```bash
source .venv/bin/activate
export JEV_MLX_MODEL=/absolute/path/to/Qwen3.5-9B-OptiQ-4bit
jev-mlx serve --port 8765
```

终端二安装测试用 Chromium 并执行采集：

```bash
source .venv/bin/activate
export PLAYWRIGHT_BROWSERS_PATH=.cache/playwright
python -m playwright install chromium --only-shell
python examples/browser_smoke.py --url http://127.0.0.1:8765 \
  --output output/browser-local
```

浏览器输出目录必须为空。每次改用新的目录，原始 `docs/assets` 证据不会被覆盖。这个脚本检查已知演示流程；自行在界面输入别的话语属于探索，不自动计入冻结测试成绩。

## 中文与中英混合能力还需要怎样验证

现有冻结模型评测以英文、单轮、单步动作作为范围。可以自行尝试中文指令，但目前没有中文或中英混合指令的准确率、误操作率和延迟结论。文档翻译、界面文本与模型理解能力是不同的验证对象。

要扩展中文，应另写公开虚构的中文开发集和冻结测试集，覆盖指代、否定、疑问、顺序、歧义及中英混合课程名；用开发集调整后固定提示词、阈值与数据哈希，再分别报告中文、英文和混合输入结果。不要直接修改现有冻结文件，或把人工挑出的成功演示当成完整评测。
