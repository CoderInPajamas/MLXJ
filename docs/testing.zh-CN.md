# 测试方法与实测结果

[English: evaluation protocol](evaluation.md) · [English: full results](results.md) · [支持模型](models.md)

本项目已经完成核心自动化测试、两个本地模型的冻结集评测、缓存对照和真实浏览器演示。当前实测中，**Qwen3.5-9B-OptiQ-4bit 的最终决策准确率为 25/28（89.3%）**，同页新话语的 p50 / p95 为 **171.7 / 176.4 ms**；GLM-4.7-Flash-4bit 为 **14/28（50.0%）**，当前提示词下不推荐直接用于动作执行。

这些是特定机器、模型、英文场景和实现版本的结果。没有证明任意模型兼容、固定 100 ms、零语义错误或概率已校准。中文文档和界面的中英切换，也不代表中文指令或中英混合指令已经通过模型评测。

原始评测、截图和录屏使用项目旧称 JEVKit MLX；证据文件保留原名称、源码哈希和记录时间，没有为更名而改写。下文复现命令使用当前 `jev-mlx` 命令、`jev_mlx` 模块和 `JEV_MLX_MODEL` 环境变量。更名后重新做了核心测试与独立 wheel 的真实模型调用，**没有重新运行整套质量评测和浏览器模型测试**，见[更名验证记录](../benchmarks/results/rename-release-checks/verification.json)。

## 到底测了什么

| 层次 | 样本或检查 | 能说明什么 |
|---|---|---|
| 核心自动化测试 | 145 个不同测试通过；使用可控假后端，不要求 Metal | 数据约束、评分处理、状态版本、并发过期保护、结果身份与重放保护、HTTP、缓存边界等软件行为 |
| 开发集 | 16 个重新编写的虚构英文场景 | 用于开发提示词；不作为未见测试成绩 |
| 冻结测试集 | 28 个不同英文场景，其中 18 个可执行请求、10 个应拒绝请求 | 固定提示词与阈值下的模型语义质量 |
| 最终缓存对照 | 两个模型，各 28 场景 × 2 种复用方式 | 与全新计算相比，缓存复用是否改变候选分数或选择 |
| 真实浏览器 | Qwen 驱动的 16 场景，另加一次页面变化检查 | 模型选择、实际 DOM 点击、服务端执行回执与可见状态是否衔接正确 |

核心测试的最近一次发布验证先有 138 个通过、7 个 HTTP fixture 因沙盒禁止绑定回环端口而未能建立；在允许临时本地端口的环境重跑 HTTP 测试，8 个通过，其中 1 个此前已通过。合计是 **145 个不同测试通过**，不是 146 个，也不是一次无条件通过的单次运行。该记录同时保存了 lint 通过结果；GitHub CI 已配置，但尚未在远程执行。

开发集和测试集都是公开的虚构数据，没有从生产对话、录音、截图或日志导出。文件及冻结哈希见[数据清单](../benchmarks/fixtures/manifest.json)，具体输入见[开发集](../benchmarks/fixtures/dev.jsonl)和[测试集](../benchmarks/fixtures/test.jsonl)。覆盖场景包括：

- 不同打开对象或没有对象时，同一句 “Close it” 的含义变化。
- 打开视频库入口与播放某个具体课程的区别。
- “First one” 按当前筛选、排序后的可见顺序选择。
- 视频库、播放器加载中、播放器就绪时，允许动作发生变化。
- “Did you just close it?” 是询问；否定、模糊表达和不存在的目标应被拒绝。
- 候选顺序变化、布尔判断，以及执行阶段的过期结果保护。

开发过程中，Qwen 开发集从 14/16 改善到 15/16，随后冻结通用语义提示词和 `margin_threshold=0.0`，再运行主测试。没有添加针对这些话语的正则规则，也没有在冻结测试集上调整阈值。

## 怎样读质量指标

**最终决策准确率**同时要求动作 ID 和状态正确。例如标注要求 `abstain`，模型却返回 `no_match`，严格评测仍算错，即使两者都不会执行动作。

**原始选择准确率**看 `raw_selected_id`，保留阈值处理前的模型选择。零 margin 的并列选择可能被引擎转为 `abstain`，因此原始与最终准确率不同。执行器拦住一个错误选择，只能算保护生效，不能把模型错误记成答对。

**误操作率**是返回错误可执行动作的请求数除以全部 28 个请求；下表另外列出原始选择的误操作率。它表示模型输出会触发的错误动作，质量评测本身不执行这些动作。**拒绝率**统计 `no_match` 与 `abstain`，既包含合理拒绝，也包含错误拒绝；**弃权率**只统计 `abstain`。**可执行请求覆盖率**是返回正确可执行选择的请求数除以 18 个应可执行请求，不能用总选择数量代替。

`scores` 是候选范围内的 softmax 分数；`margin` 是最高与次高原始 logit 的差。它们都不是“正确概率”，两个模型的 logit 数值也不宜直接比较。

## 最终缓存修订后的两个模型

以下来自 [Qwen 最终汇总](../benchmarks/results/qwen9b-cache-fixed/summary.json)和 [GLM 最终汇总](../benchmarks/results/glm-cache-fixed/summary.json)。每个模型都运行三种缓存条件，每种 28 次；三组质量相同，因此这里只列一组分母。

| 指标 | Qwen3.5-9B-OptiQ-4bit | GLM-4.7-Flash-4bit |
|---|---:|---:|
| 最终决策准确率 | **25/28（89.3%）** | **14/28（50.0%）** |
| 原始选择准确率 | 26/28（92.9%） | 15/28（53.6%） |
| 最终误操作率 | 0/28（0%） | 2/28（7.1%） |
| 原始选择误操作率 | 0/28（0%） | 3/28（10.7%） |
| 拒绝率 | 11/28（39.3%） | 16/28（57.1%） |
| 弃权率 | 1/28（3.6%） | 12/28（42.9%） |
| 可执行请求覆盖率 | 17/18（94.4%） | 10/18（55.6%） |
| 输出结构有效 | 28/28 | 28/28 |
| 运行异常 | 0/28 | 0/28 |

GLM 返回了 12 个动作，其中 2 个错误；按“已经选择动作”作为分母，其误操作率是 2/12（16.7%）。Qwen 在这 28 个场景上没有出现错误动作，但不能据此承诺真实应用中不会误操作。

每个模型的 84 条记录等于 **同样的 28 场景 × 3 种缓存条件**。它们不是 84 个独立语义样本，两个模型也共享这套 28 场景。增加 `--repeats` 可以获得更多计时观察，不能把重复题目算作新测试题。

耗时单位为毫秒。每个单元格为 **p50 / p95**，各来自 28 次调用；MLX 计算在计时结束前完成同步求值。

| 缓存条件 | Qwen | GLM |
|---|---:|---:|
| 权重已加载、KV 冷：`kv_cold` | 2159.9 / 2406.6 | 1837.6 / 2154.5 |
| 同页新话语：`same_page_new_utterance` | **171.7 / 176.4** | **147.8 / 170.6** |
| 页面变化后的首次决策：`page_update` | 1050.2 / 1294.5 | 927.4 / 1246.5 |

同页复用的是完整页面前缀，页面变化时只复用变化前的稳定系统前缀，并重新计算页面与话语后缀。没有缓存最终答案冒充模型加速。页面更新和 KV 冷状态仍需约一至数秒；这些数据不支持“固定 100 ms”。

实测机器为 Apple M2 Max、64 GiB 统一内存，Python 3.13.2、MLX 0.31.2、MLX-LM 0.31.3。Qwen 是混合 4/8-bit、group size 64；GLM 是 4-bit、group size 64。测试输入每题 2–6 个业务候选，另加两个拒绝候选，话语为 8–34 个英文字符。当前实现串行推理，最多 64 个业务候选、4096 个提示词 token，前缀缓存最多 512 MiB / 16 条。完整模型哈希、内存口径和硬件信息见[完整报告](results.md)及[模型来源](../benchmarks/results/checkpoints.json)。

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

## 缓存为什么说 112 次对照通过

每个模型对 28 个场景分别比较“同页复用 vs 全新计算”和“页面更新复用 vs 全新计算”，所以是 **2 个模型 × 28 场景 × 2 种对照 = 112/112 通过**。所有这些对照的最大候选 logit 差和 softmax 分数差实测都为 0，原始最高候选一致。记录保留了预先设定的容差：logit 绝对误差 0.5、相对误差 0，分数绝对误差 0.1。

这不是 112 个不同语义问题，也不是所有未来输入都保证逐位相同。证据见 [Qwen 对照](../benchmarks/results/qwen9b-cache-fixed/parity.jsonl)和 [GLM 对照](../benchmarks/results/glm-cache-fixed/parity.jsonl)。

旧实现曾在 GLM 的 28 个缓存场景中有 **25 个对照失败**：同页复用一致，但页面变化后任意共同前缀的部分复用出现差异，最大 logit 差为 5.5，且 1 题最高候选改变。修订 `579daf3` 只接受完整系统或页面快照边界的复用，再完成以上复测；没有改变语义提示词或阈值。[旧版失败记录](../benchmarks/results/glm-test/parity.jsonl)仍保留，差异原因没有被未经证实地归为框架 bug。

## 与生成一个编号、生成 JSON 的比较

主对照在旧实现 `a743972` 上使用同一个 Qwen 模型，包含直接读候选 logits、官方生成接口只生成一个编号，以及生成带业务 ID 的 JSON。下面是**当时同一轮**同页新话语结果，不能与上面的修订后耗时拼接计算加速比。

| 历史方法 | 最终准确率 | 误操作 | 可执行覆盖 | 同页 p50 / p95（ms） |
|---|---:|---:|---:|---:|
| 直接候选评分 | 25/28 | 0/28 | 17/18 | 196.3 / 202.7 |
| 只生成一个编号 | 26/28 | 0/28 | 18/18 | 445.4 / 693.9 |
| 生成业务 ID JSON | 6/28 | 0/28 | 0/18 | 604.3 / 1304.8 |

原 JSON 基线在三个条件中共有 66/84 次结构不合法，主要把内部编号写进了要求业务 ID 的字段；没有有效动作输出不能解读为安全或准确。原始文本全部保留。[主对照记录](../benchmarks/results/qwen9b-test-v1/summary.json)也显示：KV 冷时直接评分的 p95 为 3751.7 ms，比编号基线的 3243.2 ms 更慢，不能只展示有利的热缓存结果。

看到原 JSON 测试失败后，新增了输出 `{"choice":"0"}` 的 `json_code` 格式对照。它在同一冻结集得到 26/28、误操作 1/28、结构有效 28/28，同页 p50 / p95 为 529.4 / 953.6 ms；误操作是把 “Play something” 转成播放某课程。**这是看过测试结果后加入的补充格式实验，不是未接触测试集的独立盲测**，见[补充记录](../benchmarks/results/qwen9b-jsoncode-test/summary.json)。

直接评分使用官方模型原有量化输出头，读取最后位置候选 logits，不生成后续文本；底层仍然是因果语言模型的下一 token 计算。官方 `max_tokens=1` 生成路径可能还有下一步预取计算，计时包含实际完成的计算。因此这些对照说明当前接口路径的表现，不能证明本项目拥有独有的无自回归架构，也不能证明比经过同样优化的单步 argmax 必然更快。

## 进程冷启动是另一个指标

权重已加载但 KV 冷，不等于新进程冷启动。另行测了 Qwen 每种方法 3 次、GLM 每种方法 2 次的新进程启动，四种方法合计 20 次。外层计时包括进程启动、加载、首次决策和退出，只使用第一道测试题，未清空操作系统文件缓存。

其中直接评分的外层耗时 p50 / p95：Qwen 为 4897.3 / 4928.1 ms，GLM 为 8726.6 / 8848.2 ms。每组仅 2–3 个样本，不能称为稳定的 p95；20 次没有进程运行异常，也不等于 20 次模型回答都正确。格式和语义失败均保留在 [Qwen 冷启动记录](../benchmarks/results/qwen9b-cold/summary.json)、[GLM 冷启动记录](../benchmarks/results/glm-cold/summary.json)及[完整解释](results.md)。

## 真实浏览器怎么测

使用真实本地 Qwen 后端和 Chromium，在虚构应用 Morrow Studio 中输入话语，由模型选择当前允许的动作，再点击对应 DOM 按钮，取得服务端一次性执行回执，并检查页面状态。模型、浏览器点击和执行都是真实的；桌面、课程和播放器是公开的模拟应用，不是任意网站操作，也不是截图视觉识别。

16 个场景覆盖空桌面拒绝关闭、打开课程库、筛选课程、按可见顺序播放、暂停、继续、回退、关闭、询问不执行、否定不执行、目标不存在、模糊请求、笔记窗口，以及加载状态下拒绝暂停。排序等准备动作单独记录，没有算作模型选择成绩。

结果为 **16/16 场景通过，10 次模型动作获得 DOM 执行回执，6 次拒绝，0 个浏览器错误**。浏览器演示对拒绝允许 `no_match` 或 `abstain`，比冻结基准的严格状态匹配更宽；不能用 16/16 覆盖前面的 25/28，更不能写成通用模型准确率 100%。GLM 尚未完成同样的真实浏览器测试。

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

现有冻结模型评测以英文、单轮、单步动作作为范围。可以自行尝试中文指令，但目前没有中文或中英混合指令的准确率、误操作率和延迟结论。文档翻译、按钮翻译、语言切换和模型理解能力是不同的验证对象。

要扩展中文，应另写公开虚构的中文开发集和冻结测试集，覆盖指代、否定、疑问、顺序、歧义及中英混合课程名；用开发集调整后固定提示词、阈值与数据哈希，再分别报告中文、英文和混合输入结果。不要直接修改现有冻结文件，或把人工挑出的成功演示当成完整评测。
