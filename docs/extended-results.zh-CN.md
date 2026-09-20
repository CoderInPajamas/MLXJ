<p align="center"><strong>简体中文</strong> · <a href="extended-results.md">English</a></p>

# 六领域扩展评测报告

[返回中文首页](../README.md) · [中文测试说明](testing.zh-CN.md)

**三模型同页新话语对比，以及 Gemma 单独进行的扩展缓存验证，均已完成并通过审计**：共 684 次正式测量、72 次缓存数值对照。这些测量重复使用 12 个开发场景和 36 个测试场景，并不是 684 个独立的质量样本。

三个模型在新增的 36 题中都出现了动作错误。下表是相同冻结场景、相同“同页面、新话语”条件下的直接评分结果；后文完整列出四种方法的对比与失败。

| 模型 | 严格正确 / 36 | 动作误选 / 30 个 enum 请求 | 正确动作覆盖 / 15 | 布尔正确 / 6 | 同页 p50 / p95，ms |
|---|---:|---:|---:|---:|---:|
| Gemma | **31/36 (86.1%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **5/6 (83.3%)** | **168.9 / 556.5** |
| Qwen | **30/36 (83.3%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **6/6** | **194.8 / 407.5** |
| GLM | **21/36 (58.3%)** | **8/30 (26.7%)** | **9/15 (60.0%)** | **2/6 (33.3%)** | **170.6 / 330.5** |

Gemma 的单编号基线比直接评分少答对一题，出现三个无效输出，没有格式有效但选错动作的结果。Qwen 的直接评分与单编号基线逐题结果完全相同，包括一次错误的商品选择。GLM 的语义错误和格式失败较多，当前配置不适合无人确认的动作执行。这个小样本既不足以给出通用模型排名，也不支持固定 100 ms 的延迟承诺。

本报告依据[固定的新增评测协议（英文）](extended-evaluation-protocol.md)，评估[六领域虚构场景集（英文说明）](../benchmarks/fixtures/extended-v1/README.md)。[Gemma 原始 28 题报告（英文）](gemma4-results.md)和[历史 Qwen/GLM 报告（英文）](results.md)使用不同的数据集或运行记录，不能当成额外样本并入这里的百分比。

[完整新增实验审计](../benchmarks/results/extended-campaign.json)覆盖十次正式运行：**1096/1096 次测量完成**，无运行异常或准备阶段异常，**128/128 次缓存数值对照通过**。这些总数包含本扩展集、Gemma 原始集和进程启动实验，表示工作量，不是准确率的分母，也不是独立题目数。

## 范围、来源与完成情况

扩展集包含 12 个开发场景和 36 个冻结测试场景，覆盖文档、本地日历草稿、文件列表、音乐队列、商品比较和本地设置六个领域，每个领域有六个测试场景。所有场景都是虚构的英文、单轮、单步选择，不涉及生产数据或外部操作。编写时已经知道项目的历史测试结果，但在对这些新场景进行推理前完成了冻结。因此，这是开发后的扩展评测，不是对总体随机抽样的研究，也不是最初的未见测试集。

[数据清单](../benchmarks/fixtures/extended-v1/manifest.json)记录的冻结时间为 `2026-09-20T06:09:44.415784+00:00`，测试文件 SHA-256 为 `ad804e681bb6906c81dc5da316b61a805dd1dbfc8df20940c7b1cc22776aa25e`。观察到本次开发集或测试集结果后，没有修改提示词、阈值、标签或格式解析器。开发阶段表现不佳的基线也保留原配置，继续完成评测。

| 阶段 | Gemma | Qwen | GLM |
|---|---|---|---|
| 扩展开发集，12 题 × 4 种方法 | 完成，48/48 | 完成，48/48 | 完成，48/48 |
| 扩展测试集，36 题 × 4 种方法 | 完成，144/144 | 完成，144/144 | 完成，144/144 |
| 扩展直接评分，3 种缓存条件及数值对照 | 完成，108/108 次决策 + 72/72 次对照 | 不在本次实验范围内 | 不在本次实验范围内 |

四方法对比**只使用同页面新话语条件**，每项正式测量一次，调度种子为 `20260919`，margin 阈值为 `0.0`。准备请求另行记录。每个模型的 144 条测试记录仍然只对应 **36 个不同的质量场景**；更换模型或输出方法也不会增加独立样本数。

实测 Gemma 检查点为 `gemma-4-26b-a4b-it-4bit`，已核验的转换版本是 `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87`：默认采用 4-bit affine 量化、group size 64，部分层覆盖为 8-bit。完整权重和 tokenizer 哈希见[检查点来源记录](../benchmarks/results/gemma4-checkpoint.json)。Qwen 使用 `Qwen3.5-9B-OptiQ-4bit`，已核验本地转换版本 `76b3310ab7aa52a34303c66fc928b6d7239c860c`，混合 4/8-bit 量化、group size 64，见[检查点证据](../benchmarks/results/checkpoints.json)。同一证据文件还记录了 `GLM-4.7-Flash-4bit`，默认 4-bit、group size 64。

本扩展实验以 **`ba98b71` 为源码核验基准版本**。七次已完成运行中，每次记录的八个推理与 benchmark 源码哈希都匹配该版本。元数据中的 HEAD 保留原值：Gemma 开发和测试为 `7174e56`，Qwen、GLM 及 Gemma 缓存运行是 `efed866`，并记录了工作区存在未提交改动。这些文档更新期间的 HEAD 不替代实际核验过的源码身份，也不意味着推理实现不同。

实测机器为 Apple M2 Max（`Mac14,6`），12 个 CPU 核心、64 GiB 统一内存，系统 Darwin 25.6.0 arm64，Python 3.13.2。依赖为 MLX/MLX-Metal 0.31.2、MLX-LM 0.31.3、Transformers 5.9.0、Tokenizers 0.22.2、NumPy 2.5.3。模型任务依次运行；这些记录不能证明机器上没有其他活动。

Gemma 的[开发集派生指标](../benchmarks/results/extended-v1-gemma4-dev/derived-report.json)和[测试集派生指标](../benchmarks/results/extended-v1-gemma4-test/derived-report.json)均已保留，审计通过，没有运行或准备阶段异常。Qwen 的[开发集](../benchmarks/results/extended-v1-qwen9b-dev/derived-report.json)和[测试集](../benchmarks/results/extended-v1-qwen9b-test/derived-report.json)分别保留证据，也通过完整性审计且无上述异常。GLM 的[开发集](../benchmarks/results/extended-v1-glm-dev/derived-report.json)和[测试集](../benchmarks/results/extended-v1-glm-test/derived-report.json)同样通过审计，无运行或准备阶段异常。三个模型共 576 次开发与测试测量全部保留，包括每次失败。

## 分母与指标含义

测试集有 30 个 enum 请求：15 个要求执行动作，15 个要求拒绝。六个 boolean 问题中，两个应回答真、两个应回答假、两个应因信息不足而弃权。因此，19 个预期为 selected 的选择实际是 **15 个动作加四个事实答案**。开发集则包含七个可执行 enum 请求、四个 enum 拒绝请求，以及一个应选择真/假答案的 boolean 问题。

严格准确率要求状态和选中 ID 都正确，其中包括区分 `no_match`（不匹配）与 `abstain`（弃权、需要澄清）。下文的动作错误只统计 enum 请求；boolean 错答属于分类错误。历史通用指标字段 `false_action` 可能混合两类结果，因此这里不把它直接解释成纯动作误选率。正确动作覆盖率统计执行器介入前选对的 enum 动作。执行器限制或拒绝执行，不能让一个错误的模型答案变成正确。

这套场景**不驱动浏览器，也不执行应用操作**。动作 ID 不等于执行回执。历史 Qwen 浏览器录像不能证明 Gemma 或 GLM 的浏览器操作能力；英文场景成绩也不能证明中文或中英混合输入的质量。分数和 margin 仍是未经校准的模型输出，不能称为正确概率。

## Gemma 开发集：完整保留四种方法的结果

每种方法都在同一页面条件下运行了全部 12 个开发集案例。模型原始选择与最终返回结果的准确率一致。单编号生成的失败案例为 `ext1-dev-music-unspecified-track`：原始输出是 `AB`，而不是有效的弃权编号。业务 ID JSON 产生了 12 个无效响应，编号 JSON 产生了八个。开发集的全部 21 个错误结果都是格式错误，没有运行时异常。

| 方法 | 严格准确率 | enum 动作误选 / 11 | 动作覆盖 / 7 | boolean 正确 / 1 | 格式有效 / 12 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | 12/12 (100%) | 0/11 | 7/7 | 1/1 | 12/12 | 161.9 / 573.0 |
| 单编号 | 11/12 (91.7%) | 0/11 | 7/7 | 1/1 | 11/12 | 433.4 / 850.8 |
| 业务 ID JSON | 0/12 | 0/11 | 0/7 | 0/1 | 0/12 | 782.5 / 2049.6 |
| 编号 JSON | 4/12 (33.3%) | 0/11 | 0/7 | 0/1 | 4/12 | 653.8 / 1836.1 |

直接评分拒绝了 4/12 (33.3%) 个请求，其中 1/12 为弃权 (8.3%)；单编号拒绝了 3/12 (25.0%)，没有弃权；业务 ID JSON 没有有效的拒绝结果；编号 JSON 拒绝了 4/12，其中一个为弃权。无效输出不算成功拒绝。完整的[开发集试验记录](../benchmarks/results/extended-v1-gemma4-dev/trials.jsonl)保留了每次失败的原始文本。

## Gemma 冻结测试集：统一的热缓存条件

下表每行包含同一进程、同一次运行中的 36 次正式测试调用。最终返回结果与模型原始选择的准确率一致；零 margin 弃权策略没有改变直接评分的结果。样本量较小且只运行了一轮，因此这些分位数用于描述本次观测，不能作为稳定的尾部延迟或泛化能力估计。

| 方法 | 严格准确率 / 36 | enum 动作误选 / 30 | 正确动作覆盖 / 15 | boolean 正确 / 6 | 格式有效 / 36 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | **31/36 (86.1%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **5/6 (83.3%)** | 36/36 | **168.9 / 556.5** |
| 单编号 | 30/36 (83.3%) | 0/30 | 12/15 (80.0%) | 5/6 (83.3%) | 33/36 (91.7%) | 429.4 / 795.9 |
| 业务 ID JSON | 0/36 | 0/30 | 0/15 | 0/6 | 0/36 | 641.4 / 2292.4 |
| 编号 JSON | 14/36 (38.9%) | 0/30 | 1/15 (6.7%) | 2/6 (33.3%) | 17/36 (47.2%) | 579.4 / 2383.7 |

| 方法 | 拒绝 / 36 | 弃权 / 36 | 格式无效 / 36 | 运行时错误 | 选错的 boolean 答案 |
|---|---:|---:|---:|---:|---:|
| 直接评分 | 18/36 (50.0%) | 5/36 (13.9%) | 0/36 | 0 | 1 |
| 单编号 | 16/36 (44.4%) | 3/36 (8.3%) | 3/36 | 0 | 1 |
| 业务 ID JSON | 0/36 | 0/36 | 36/36 | 0 | 0 |
| 编号 JSON | 14/36 (38.9%) | 5/36 (13.9%) | 19/36 | 0 | 1 |

全部 144 次尝试均已保留：75 次正确，**69 次错误**，其中包括 58 次格式错误和 11 次格式有效但语义错误的结果。四次错误的已选结果包括直接评分的一次 enum 动作误选，以及三种方法对同一个 boolean 问题给出的错误答案；不能将其算作四个不同的动作错误。业务 ID JSON 的动作误选为零，同时有效响应也为零，因此不能据此认定它安全或具有实用决策能力。

在本次热缓存测试中，直接评分比官方单编号生成路径更快，严格匹配的正确结果也多一个。不过，在单编号路径输出无效内容的一个案例中，直接评分返回了错误动作。因此，两条路径的质量与失败表现并不完全相同。官方生成即使设置 `max_tokens=1`，也可能安排下一步的预取计算；同步计时包含了这部分开销。这一比较不能证明直接评分优于同样经过优化的单步 argmax 实现，也不能证明非自回归方式在所有情形下都更有优势。

## Gemma 直接评分的全部测试失败

下列案例名省略了共同前缀 `ext1-test-`。完整状态、允许的候选、分数、预期标签和输出均在[测试试验记录](../benchmarks/results/extended-v1-gemma4-test/trials.jsonl)中。

| 案例 | 预期结果 | 原始胜出候选与最终返回决策 | 原始 margin |
|---|---|---|---:|
| `documents-dismiss-editor` | 选择 `document.cinder.close` | `__no_match__` → 不匹配 | 9.0625 |
| `music-queue-first` | 选择 `track.velour.play` | `track.marble.play` → 选错曲目 | 6.0009 |
| `comparison-remove-focused` | 选择 `compare.mistral.remove` | `__abstain__` → 弃权 | 4.5156 |
| `comparison-unknown-warranty` | 弃权：没有保修信息 | `false` → 选择了 boolean 答案 | 16.1250 |
| `settings-vague-accessibility` | 弃权：存在多种可能的修改，但用户未指明 | `__no_match__` → 不匹配 | 12.6758 |

筛选和排序之后，队列中可见的第一首曲目是 Velour Tide；Marble Rain 在候选编号中排第一，但在可见队列中并不是第一首。这是一次真实的动作误选，没有经过执行器纠正。保修信息未知时，模型根据缺失的数据编造了否定的事实性答案；较大的 margin 并不能使答案变得可靠。关闭当前文档和移除当前产品的错误则拒绝了本可执行的请求。对于模糊的无障碍设置请求，虽然两种拒绝结果都不会执行动作，但返回错误的拒绝类型仍然属于严格标签错误。

直接评分按领域的准确率为：文档 5/6、日历草稿 6/6、文件 6/6、音乐 5/6、产品比较 4/6、设置 5/6。每个领域只有六个案例，这些数字仅描述本次结果，不能证明模型在整个应用领域都可靠。

## 基线的语义错误与格式错误

单编号路径出现了三个格式有效的语义错误：`documents-dismiss-editor` 返回不匹配，`comparison-unknown-warranty` 返回 false，`settings-vague-accessibility` 返回不匹配。另有三个失败是无效的单 token 输出：

| 案例 | 原始输出 | 要求的结果 |
|---|---|---|
| `music-queue-first` | `{"` | `track.velour.play` |
| `comparison-remove-focused` | `AB` | `compare.mistral.remove` |
| `music-unspecified-track` | `AB` | 弃权 |

业务 ID JSON 在**全部 36 个案例**中均未满足严格输出约定：19 个不带 Markdown 代码围栏的 JSON 对象把内部数字编号填入了 `candidate_id`；17 个响应被包在 Markdown 代码围栏中。在这些带围栏的响应中，11 个还使用了数字编号，六个包含业务 ID。`{"candidate_id":"2"}` 或带有 `"candidate_id":"playback.resume"` 的代码围栏对象等输出均保留为无效；评测器不会在事后去掉代码围栏或重新解释 ID。`music-queue-first` 的带围栏业务 ID 响应还指定了错误的曲目，因此仅修复格式也不能让全部响应变为正确。

编号 JSON 有 19 次格式错误：18 个带代码围栏的对象，以及 `music-queue-first` 上一个生成到 96 token 长度上限的响应。该响应先输出带代码围栏的 `{"choice":"code:0"}`，随后继续生成解释文本。另外三个错误的响应格式有效：`comparison-remove-focused` 返回弃权，`comparison-unknown-warranty` 返回 false，`settings-vague-accessibility` 返回不匹配。15 个可执行的 enum 请求中，它只有一个选择了正确动作。

这些严格判定的失败反映了当前固定输出指令与解析器的表现，不能据此认定 JSON 生成本身无法完成任务。编号 JSON 格式此前已披露为参考历史测试结果设计的对照项；本次扩展评测开始推理之前，四种格式均已固定。没有使用修复解析器或重新调优的提示词来替换这些失败的基线尝试。

## Qwen 开发集：保持配置不变

Qwen 完成了 48/48 次开发集调用。直接评分与单编号路径出现了相同的两个错误：`ext1-dev-files-last-visible` 选择了 `file.fern.open`，而非 `file.quartz.open`；`ext1-dev-music-unspecified-track` 返回了不匹配，而非弃权。直接评分对应的 margin 分别为 1.5 和 2.375。编号 JSON 同样选错了文件，并对未明确指定曲目的请求输出了无效的 `{"choice":"NO_MATCH"}`。业务 ID JSON 有六次格式错误，全部是在 `candidate_id` 中填入了数字编号；所有格式有效的 JSON 结果都正确。

| 方法 | 严格准确率 / 12 | enum 动作误选 / 11 | 动作覆盖 / 7 | boolean 正确 / 1 | 格式有效 / 12 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 12/12 | 188.9 / 369.3 |
| 单编号 | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 12/12 | 414.4 / 557.3 |
| 业务 ID JSON | 6/12 (50.0%) | 0/11 | 1/7 | 1/1 | 6/12 | 545.6 / 1047.0 |
| 编号 JSON | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 11/12 | 579.1 / 880.6 |

直接评分与单编号各拒绝了 4/12 个请求，没有弃权；业务 ID JSON 拒绝了 4/12，其中一个为弃权；编号 JSON 拒绝了 3/12，没有弃权。所有方法共出现 12 个错误结果：七个格式错误、五个格式有效的语义错误。三种方法对同一文件的误选不能算作三个不同的失败案例。全部[开发集输出](../benchmarks/results/extended-v1-qwen9b-dev/trials.jsonl)在使用原配置运行测试集之前就已保留。

## Qwen 冻结测试集：全部四种方法

Qwen 完成了 144/144 次调用，没有异常。在全部 36 个案例中，直接评分与单编号返回的状态和 ID 完全一致，包括其中的六个错误。原始选择与最终返回结果的质量一致；正式计入评测的直接评分结果没有零 margin，也没有因阈值而发生状态改变。部分准备调用中出现的零 margin 不属于测试决策，因此不计入这些质量指标。

| 方法 | 严格准确率 / 36 | enum 动作误选 / 30 | 正确动作覆盖 / 15 | boolean 正确 / 6 | 格式有效 / 36 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | **30/36 (83.3%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **6/6** | 36/36 | **194.8 / 407.5** |
| 单编号 | 30/36 (83.3%) | 1/30 (3.3%) | 12/15 (80.0%) | 6/6 | 36/36 | 453.4 / 721.4 |
| 业务 ID JSON | 17/36 (47.2%) | 0/30 | 1/15 (6.7%) | 5/6 (83.3%) | 20/36 (55.6%) | 645.7 / 1280.0 |
| 编号 JSON | 30/36 (83.3%) | 1/30 (3.3%) | 13/15 (86.7%) | 5/6 (83.3%) | 36/36 | 586.7 / 1133.7 |

| 方法 | 拒绝 / 36 | 弃权 / 36 | 格式无效 / 36 | 运行时错误 | 选错的 boolean 答案 |
|---|---:|---:|---:|---:|---:|
| 直接评分 | 19/36 (52.8%) | 3/36 (8.3%) | 0/36 | 0 | 0 |
| 单编号 | 19/36 (52.8%) | 3/36 (8.3%) | 0/36 | 0 | 0 |
| 业务 ID JSON | 14/36 (38.9%) | 4/36 (11.1%) | 16/36 | 0 | 1 |
| 编号 JSON | 17/36 (47.2%) | 7/36 (19.4%) | 0/36 | 0 | 1 |

共有 **37 个错误结果**：16 个格式错误、21 个格式有效的语义错误，因此四种方法合计正确 107/144 次。五次错误的已选结果包括同一电池续航案例上的三次 enum 误选，以及同一保修信息未知案例上的两次 boolean 误选；不能算作五次独立的误操作。在本次测试中，直接评分与单编号的结果完全一致，同时热缓存延迟的中位数和 p95 更低；模型选错的动作在两条路径中都仍然是错的。编号 JSON 比直接评分多覆盖了一个可执行请求，但少答对了一个 boolean 问题，因此总体准确率相同并不意味着行为相同。

## Qwen 直接评分与单编号的全部测试失败

案例名省略了 `ext1-test-`。直接评分与单编号在每个案例中都返回相同结果；下列 margin 仅属于直接评分。每个结果的格式都有效，因此不能因为应用可能拒绝执行，就将这些错误重新计为正确。

| 案例 | 预期结果 | 两种方法共同的原始胜出候选与返回决策 | 直接评分 margin |
|---|---|---|---:|
| `documents-dismiss-editor` | `document.cinder.close` | `__no_match__` → 不匹配 | 1.125 |
| `calendar_drafts-discard-ambiguous` | 弃权 | `__no_match__` → 不匹配 | 3.625 |
| `files-duplicate-name` | 弃权 | `__no_match__` → 不匹配 | 1.625 |
| `music-unspecified-track` | 弃权 | `__no_match__` → 不匹配 | 1.750 |
| `comparison-remove-focused` | `compare.mistral.remove` | `__no_match__` → 不匹配 | 0.500 |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.kestrel.inspect` → 选错产品 | 2.375 |

电池续航状态明确列出了 Nimbus 为 18 小时、Kestrel 为 12 小时；即使格式有效，该选择仍然错误。两个可执行请求被错误拒绝，三个存在歧义的案例返回了错误的拒绝类型。直接评分按领域的准确率为：文档 5/6、日历草稿 5/6、文件 5/6、音乐 5/6、产品比较 4/6、设置 6/6。原始 28 案例 Qwen 测试中未观测到动作误选的结果，不能套用到本次扩展评测。

Qwen 业务 ID JSON 的 16 个无效响应均为不带代码围栏的对象，其中 `candidate_id` 包含数字编号，而不是合法的业务 ID 或拒绝 ID。另有三个格式有效的错误：`calendar_drafts-discard-ambiguous` 返回不匹配而非弃权，`settings-unsupported-size` 返回弃权而非不匹配，`comparison-unknown-warranty` 返回 false 而非弃权。

编号 JSON 的六个错误结果格式均有效：

| 案例 | 预期结果 | 返回的候选或状态 |
|---|---|---|
| `calendar_drafts-discard-ambiguous` | 弃权 | 不匹配 (`__no_match__`) |
| `comparison-remove-focused` | `compare.mistral.remove` | 弃权 (`__abstain__`) |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.mistral.inspect`，与直接评分和单编号不同的另一个错误产品 |
| `comparison-unknown-warranty` | 弃权 | 选择 boolean `false` |
| `settings-unsupported-size` | 不匹配 | 弃权 (`__abstain__`) |
| `comparison-price-question` | 不匹配 | 弃权 (`__abstain__`) |

状态中列出的 Mistral 电池续航为九小时。没有通过调整提示词、阈值或解析器来修复这些错误。所有分数、原始 JSON 和生成的编号都保留在 [Qwen 测试试验记录](../benchmarks/results/extended-v1-qwen9b-test/trials.jsonl)中。

## GLM 开发集：策略的影响与格式失败

GLM 完成了全部 48 次开发集调用，没有运行时异常。直接评分的最终返回结果答对了
9/12，而原始最高分选项答对了 10/12。在 `ext1-dev-music-open-queue` 和
`ext1-dev-calendar_drafts-preset-time` 上，零 margin 弃权策略把正确的原始动作
变成了错误的拒绝结果。在 `ext1-dev-music-unspecified-track` 上，原始最高分选项
错误地选择了 `track.copper.play`，策略则返回了预期的弃权。最后这一项返回正确，
来自策略保护，不能算作原始模型答对。直接评分的另一项错误出现在
`ext1-dev-files-last-visible`：选择了 `file.fern.open`，而正确答案是
`file.quartz.open`（margin 为 1.0）。

| 方法 | 严格准确率 / 12 | enum 动作误选 / 11 | 动作覆盖率 / 7 | boolean 正确数 / 1 | 格式有效 / 12 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | 9/12（75.0%） | 1/11 | 4/7（57.1%） | 1/1 | 12/12 | 209.1 / 479.3 |
| 单编号 | 0/12 | 0/11 | 0/7 | 0/1 | 0/12 | 350.6 / 386.9 |
| 业务 ID JSON | 8/12（66.7%） | 3/11 | 7/7 | 0/1 | 12/12 | 635.1 / 2251.2 |
| 编号 JSON | 2/12（16.7%） | 0/11 | 2/7（28.6%） | 0/1 | 2/12 | 604.7 / 2462.8 |

直接评分拒绝了 6/12，其中三次为弃权；业务 ID JSON 拒绝了 1/12，没有弃权。
两种生成编号的格式都没有产生有效的拒绝结果。汇总所有方法，共有 29 个错误结果：
22 个格式失败和七个格式有效的语义错误。直接评分的原始 enum 动作误选为 2/11，
经过策略处理后为 1/11。

业务 ID JSON 在开发集上的四个错误都是格式有效的选择：对过去是否保存的询问，
选择了 `document.save`；对否定移除的表达，选择了 `compare.sprout.remove`；
对未指定曲目的请求，选择了 `track.copper.play`；对实际为 false 的提醒事实，
回答了 true。单编号在全部 12 个案例中的输出均无效。编号 JSON 的两个有效回答
都为 `{"choice":"0"}`，分别对应深色主题和预设草稿时间；其余十个回答在编号字段
中填入了业务 ID 或拒绝 ID。[开发集逐次记录](../benchmarks/results/extended-v1-glm-dev/trials.jsonl)
保留了所有输出和策略修改。

## GLM 冻结测试集：全部四种方法

全部 144 次测量调用均已完成。直接评分的原始准确率为 **24/36（66.7%）**，
**最终返回结果的准确率为 21/36（58.3%）**。固定的零 margin 策略拦截了四个
原始选择：其中三个正确、一个错误。那个错误选择被改为弃权后，答案仍然错误。
最终返回的 enum 动作误选为 **8/30**；原始 enum 动作误选为 **9/30**。
策略拦住错误选择，不能算模型答对。

| 方法 | 严格准确率 / 36 | enum 动作误选 / 30 | 正确动作覆盖率 / 15 | boolean 正确数 / 6 | 格式有效 / 36 | p50 / p95，ms |
|---|---:|---:|---:|---:|---:|---:|
| 直接评分 | **21/36（58.3%）** | **8/30（26.7%）** | **9/15（60.0%）** | **2/6（33.3%）** | 36/36 | **170.6 / 330.5** |
| 单编号 | 0/36 | 0/30 | 0/15 | 0/6 | 0/36 | 320.0 / 427.1 |
| 业务 ID JSON | 20/36（55.6%） | 13/30（43.3%） | 14/15（93.3%） | 3/6（50.0%） | 36/36 | 533.1 / 1292.1 |
| 编号 JSON | 1/36（2.8%） | 0/30 | 1/15（6.7%） | 0/6 | 1/36（2.8%） | 480.5 / 913.7 |

| 方法 | 拒绝 / 36 | 弃权 / 36 | 格式无效 / 36 | 运行时错误 | 已选择但错误的 boolean 答案数 |
|---|---:|---:|---:|---:|---:|
| 直接评分 | 14/36（38.9%） | 5/36（13.9%） | 0/36 | 0 | 3 |
| 单编号 | 0/36 | 0/36 | 36/36 | 0 | 0 |
| 业务 ID JSON | 3/36（8.3%） | 0/36 | 0/36 | 0 | 3 |
| 编号 JSON | 0/36 | 0/36 | 35/36 | 0 | 0 |

共有 **102 个错误结果**：71 个格式失败和 31 个格式有效的语义错误；四种方法
合计答对 42/144。27 个错误的已选择结果由各方法中的 21 个 enum 错误和六个
boolean 错误组成，并不是 27 个独立的动作错误。业务 ID JSON 的较高动作覆盖率
伴随着 13 个动作误选；两种编号格式虽然没有错误选择，却几乎不产生可用输出。

## GLM 直接评分的全部测试失败

下表案例名省略了 `ext1-test-` 前缀。全部 15 个输出都符合直接评分的格式约定。
四个零 margin 案例明确区分了原始选择和最终返回的弃权；其余十一个都是错误的
已选择结果。

| 案例 | 预期结果 | 原始最高分选项 → 最终返回决策 | Margin |
|---|---|---|---:|
| `documents-dismiss-editor` | `document.cinder.close` | 正确的 `document.cinder.close` → 弃权 | 0 |
| `calendar_drafts-discard-ambiguous` | 弃权 | `draft.stencil.discard` → 选择 | 1.0 |
| `calendar_drafts-reminder-present`（boolean） | `true` | 正确的 `true` → 弃权 | 0 |
| `files-first-filtered` | `file.willow.open` | 错误的 `file.reed.open` → 弃权 | 0 |
| `files-first-reordered` | `file.reed.open` | 正确的 `file.reed.open` → 弃权 | 0 |
| `files-duplicate-name` | 弃权 | `file.outline_work.open` → 选择 | 1.5 |
| `files-entry-not-content` | 不匹配 | `activity.open` → 选择 | 1.0 |
| `music-queue-first` | `track.velour.play` | `filter.all` → 选择 | 0.5 |
| `music-unspecified-track` | 弃权 | `track.velour.play` → 选择 | 0.5 |
| `music-pause-loading` | 不匹配 | `player.close` → 选择 | 0.5 |
| `music-is-paused`（boolean） | `true` | `false` → 选择 | 0.5 |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.mistral.inspect` → 选择 | 1.5 |
| `comparison-lowest-price` | `product.kestrel.inspect` | `product.mistral.inspect` → 选择 | 2.0 |
| `comparison-unknown-warranty`（boolean） | 弃权 | `false` → 选择 | 2.0 |
| `settings-notifications-unknown`（boolean） | 弃权 | `false` → 选择 | 2.5 |

直接评分按领域的准确率分别为：文档 5/6、日历草稿 4/6、文件 2/6、音乐 2/6、
产品比较 3/6、设置 5/6。成功加载这个模型检查点并复用其缓存，并不能证明它具备
足够的语义判断质量。

## GLM 基线失败：JSON 有效不代表选择正确

业务 ID JSON 基线没有格式错误。它的 16 个失败结果都是格式有效、但选择错误：

| 案例 | 预期结果 | 返回的业务 ID |
|---|---|---|
| `documents-dismiss-empty` | 不匹配 | `documents.open` |
| `documents-negated-close` | 不匹配 | `document.cinder.close` |
| `calendar_drafts-discard-ambiguous` | 弃权 | `draft.lantern.discard` |
| `calendar_drafts-discard-question` | 不匹配 | `draft.discard` |
| `calendar_drafts-negated-move` | 不匹配 | `draft.discard` |
| `files-first-filtered` | `file.willow.open` | `file.reed.open` |
| `files-missing-file` | 不匹配 | `file.reed.open` |
| `files-duplicate-name` | 弃权 | `file.outline_work.open` |
| `music-unspecified-track` | 弃权 | `track.velour.play` |
| `comparison-price-question` | 不匹配 | `product.nimbus.inspect` |
| `comparison-absent-product` | 不匹配 | `compare.kestrel.add` |
| `settings-unsupported-size` | 不匹配 | `text.small` |
| `settings-vague-accessibility` | 弃权 | `text.large` |
| `comparison-unknown-warranty`（boolean） | 弃权 | `true` |
| `settings-contrast-disabled`（boolean） | `false` | `true` |
| `settings-notifications-unknown`（boolean） | 弃权 | `false` |

单编号在全部 36 个请求上失败。每个原始输出都是一个生成 token：`__`（12 次）、
`code`（5 次）、`true`（4 次）；`false`、`sounds`、`product`、`play`、`file`、
`draft`（各两次）；以及 `document`、`documents`、`compare`（各一次）。
没有一个是合法的数字选项编号。`finish_reason=length` 是预设的单 token 上限
导致的；这些输出既不是空输出，也不是 Markdown 代码围栏。我们不推测继续生成
更长文本后模型会说什么。

编号 JSON 只有一个有效回答：在 `documents-open-feature` 上返回
`{"choice":"1"}`；另有 **35 个无效回答**：

- 30 个不带围栏的 JSON 对象在 `choice` 中填入了业务 ID、拒绝 ID、`true` 或
  `false`，而非数字选项编号。
- `comparison-remove-focused` 和 `music-unspecified-track` 使用了 `NO_MATCH`。
- `settings-unsupported-size` 和 `comparison-price-question` 使用了 `5`，
  超出了各自允许的 `0`–`4` 编号范围。
- `calendar_drafts-discard-ambiguous` 输出了带代码围栏的对象，其中 `choice`
  的值为业务 ID `draft.lantern.discard`。

全部 36 个编号 JSON 回答都正常结束，未触及 96 token 上限。评测器保留这些
不符合格式约定的失败结果，不猜测模型原本想选哪一项。完整原始文本、候选项、
分数和预期标签均见 [GLM 测试逐次记录](../benchmarks/results/extended-v1-glm-test/trials.jsonl)。

## 输入规模、缓存观察与内存

Gemma、Qwen 和 GLM 的已完成运行均核实了状态前缀命中：**每个模型的开发集 48/48 次、测试集 144/144 次**。这证明实际复用了前缀，本身并不证明数值与全新计算一致。后文单独的 Gemma 缓存阶段验证数值一致性。不能从四方法的同页结果表推断 KV 冷状态、页面更新或进程启动耗时。

三个模型收到相同的测试状态和话语文本：每题 2–3 个业务候选，另加两个拒绝候选；英文话语长度为 13–54 个字符，序列化状态为 135–436 个字符。Gemma 直接评分和单编号的提示词为 499–624 tokens，业务 ID JSON 为 518–643，编号 JSON 为 522–647。各方法实测复用的状态前缀为 486–627 tokens，每次需要预填充 13–21 个提示词后缀 token；生成方法还会额外计算输出 token。Gemma 开发集各方法提示词为 503–600 tokens，话语为 17–44 个字符，序列化状态为 147–293 个字符。

Qwen 测试集直接评分与单编号提示词为 490–617 tokens，业务 ID JSON 为 507–634，编号 JSON 为 512–639；复用前缀为 477–619 tokens，提示词后缀为 13–21 tokens。Qwen 开发集各方法提示词为 493–587 tokens，后缀为 14–24 tokens。GLM 测试集直接评分与单编号提示词为 461–583 tokens，业务 ID JSON 为 478–600，编号 JSON 为 483–605；复用前缀为 455–592 tokens，后缀为 6–14 tokens。GLM 开发集提示词为 464–546 tokens，后缀为 7–15 tokens。

| 测量项 | Gemma 开发集 | Gemma 测试集 | Qwen 开发集 | Qwen 测试集 |
|---|---:|---:|---:|---:|
| 引擎构建与加载 | 5193.4 ms | 5433.8 ms | 3795.5 ms | 2954.8 ms |
| 进程生命周期内峰值 RSS | 10.966 GiB | 10.609 GiB | 6.271 GiB | 6.230 GiB |
| 进程生命周期内 MLX 峰值 | 14.375 GiB | 14.362 GiB | 6.696 GiB | 6.719 GiB |
| 记录到的 MLX 活跃内存最大值 | 13.926 GiB | 13.976 GiB | 6.080 GiB | 6.103 GiB |
| 记录到的 MLX 分配器缓存最大值 | 1.884 GiB | 2.819 GiB | 1.910 GiB | 2.020 GiB |
| 保存的前缀快照缓存最大值 | 0.448 GiB | 0.499 GiB | 0.451 GiB | 0.474 GiB |

| 测量项 | GLM 开发集 | GLM 测试集 |
|---|---:|---:|
| 引擎构建与加载 | 6790.0 ms | 6287.0 ms |
| 进程生命周期内峰值 RSS | 10.653 GiB | 11.357 GiB |
| 进程生命周期内 MLX 峰值 | 16.494 GiB | 16.531 GiB |
| 记录到的 MLX 活跃内存最大值 | 16.129 GiB | 16.167 GiB |
| 记录到的 MLX 分配器缓存最大值 | 1.274 GiB | 1.664 GiB |
| 保存的前缀快照缓存最大值 | 0.423 GiB | 0.462 GiB |

这些最大值覆盖整个进程和其中所有方法，并不是各方法独立运行时的分配量。RSS 与 MLX 内存会在统一内存中重叠，不能相加。报告中的决策耗时百分位数不包含加载和已记录的预热开销。快照缓存仍受 512 MiB / 16 条目的上限约束。

元数据保留精确字节数：[Gemma 开发集](../benchmarks/results/extended-v1-gemma4-dev/metadata.json)、[Gemma 测试集](../benchmarks/results/extended-v1-gemma4-test/metadata.json)、[Qwen 开发集](../benchmarks/results/extended-v1-qwen9b-dev/metadata.json)、[Qwen 测试集](../benchmarks/results/extended-v1-qwen9b-test/metadata.json)、[GLM 开发集](../benchmarks/results/extended-v1-glm-dev/metadata.json)、[GLM 测试集](../benchmarks/results/extended-v1-glm-test/metadata.json)。

## Gemma 扩展缓存验证：单独运行，已完成

事先选定的缓存阶段完成了 **108/108 次直接评分调用**，即相同 36 个场景分别在三种缓存条件下运行。使用的冻结场景、源码哈希、提示词、阈值和硬件相同。108 条记录的原始分数字典和最终返回的状态/ID，都与此前同页对比中对应的直接评分结果完全一致。因此，每种条件均保持 31/36 正确、30 个 enum 请求中有一个错误动作、12/15 正确动作覆盖、5/6 布尔正确、18/36 拒绝、5/36 弃权。缓存一致性也会保留模型原有的错误。

| 直接评分条件 | 测量次数 | 观察到的缓存行为 | p50 / p95，ms |
|---|---:|---|---:|
| 权重已加载，KV 冷状态 | 36/36 | 无命中，复用 0 tokens | **1949.9 / 3709.8** |
| 页面更新后的首次决策 | 36/36 | 系统前缀命中，复用 300 tokens | **831.1 / 1495.3** |
| 同页面，新话语 | 36/36 | 状态前缀命中，复用 486–604 tokens | **166.1 / 520.7** |

数值检查包含 **36 行场景记录，共 72 次对照**：一类将全新计算与复用状态快照对照；另一类在上一页面改变后，将全新计算与复用系统前缀快照对照。**72 次全部通过**，最高候选相同，候选 logit 与 softmax 分数的最大绝对差均为 **0.0**。这些最大差异经过逐条原始分数字典的独立重算。预先设定的容差为 logit `atol=0.5`、`rtol=0`，分数 `atol=0.1`；实际观察到的差异是零，不只是低于容差。全部缓存命中与作用范围检查通过，没有运行异常或输出格式错误。

这个独立进程的引擎构建与加载耗时为 7060.6 ms。进程生命周期内峰值 RSS 为 10.702 GiB，MLX 峰值为 14.357 GiB；记录到的最大 MLX 活跃内存为 13.964 GiB，分配器缓存为 11.087 GiB，保存的前缀快照缓存为 0.487 GiB。MLX 分配器缓存与应用的 512 MiB 前缀缓存上限是不同口径；这些内存量可能重叠，不能求和。提示词长度为 499–624 tokens。决策耗时百分位数不含加载和已记录的准备阶段；KV 冷状态也不是新进程启动耗时。

[派生报告](../benchmarks/results/extended-v1-gemma4-cache/derived-report.json)、[原始逐条记录](../benchmarks/results/extended-v1-gemma4-cache/trials.jsonl)、[数值对照字典](../benchmarks/results/extended-v1-gemma4-cache/parity.jsonl)和[完整性审计](../benchmarks/results/extended-v1-gemma4-cache/evidence-audit.json)保留了这次单独运行的全部结果。其同页耗时 166.1/520.7 ms 不替代此前四方法对比中的 168.9/556.5 ms；本缓存进程没有重跑生成基线。Qwen/GLM 在扩展集上的完整缓存条件矩阵不在本次范围内，其历史 28 题的缓存证据不能写成本扩展集上的实测结果。

## 比较结果的适用范围

已完成的同页对比中，所有模型都出现了动作错误，格式遵循程度也有明显差异。选中允许列表中的候选，或生成有效 JSON，都不保证选择在语义上正确。

三个模型的直接评分同页延迟中位数都低于本次测试的生成方法。这是当前实现和输入规模下的实测现象，没有与另行优化的单 token argmax 基线比较。不同方法的质量和失败类型不同，GLM 尤其明显。不能将这里的扩展集成绩与另一模型较早的 28 题成绩混在一起排名，也不能用这些结果证明实际应用或浏览器执行能力。

## 复现已完成的同页评测

使用已核验的本地检查点，并为每次运行指定一个新的输出目录。下列命令会实际加载模型；检查文档本身不会执行这些实验。

```bash
export JEV_MLX_MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit
python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/reproduce-extended-gemma-dev

python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/reproduce-extended-gemma-test
```

测试 Qwen 或 GLM 时，改用已核验的 `Qwen3.5-9B-OptiQ-4bit` 或 `GLM-4.7-Flash-4bit` 路径，保留相同参数并指定新的输出目录；三模型完整循环命令见评测协议。

保留每次调用和原始输出、元数据、汇总与完整性审计。新运行应与已公开的这些尝试分开记录；重复输入仍然是相同的 36 个质量场景。完整实验及单独缓存阶段的命令见[评测协议（英文）](extended-evaluation-protocol.md)。
