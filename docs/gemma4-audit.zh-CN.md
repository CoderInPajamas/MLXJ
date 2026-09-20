# Gemma 4 MoE 框架与权重审计

[返回项目首页](../README.zh-CN.md)

审计日期：2026-09-20。本次审计涵盖已有本地 `gemma-4-26b-a4b-it-4bit` 权重的纯文本用途。阅读源码、配置与 tokenizer 文件不能证明语义准确率或缓存数值一致性；这些结论需要另行记录的模型运行支持。已完成的 [Gemma 结果](gemma4-results.zh-CN.md)现已报告完整原始 28 条用例比较、缓存一致性和独立进程冷启动，包括观测到的错误动作及全部生成格式失败。

## 官方框架支持

项目隔离环境包含 MLX 0.31.2、MLX-LM 0.31.3、Transformers 5.9.0 与 Tokenizers 0.22.2。MLX-LM 0.31.3 已包含 [`gemma4.py`](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/gemma4.py) 和 [`gemma4_text.py`](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/gemma4_text.py)。此纯文本评分路径无需升级框架、私有模型实现或修改共享环境。

配置声明为 `Gemma4ForConditionalGeneration`，外层模型类型为 `gemma4`，文本模型类型为 `gemma4_text`。官方加载器分派到 Gemma 包装层；该层的权重清理会丢弃视觉／音频组件，其 `__call__(inputs, cache=...)` 返回文本模型 logits。转换说明卡中的 `mlx-vlm` 示例用于多模态；这并不意味着官方 MLX-LM 文本路径需要 `mlx-vlm`。本项目不声称评测了该权重的图像、视频或音频能力。

文本配置包含 30 层、128 个专家和 top-8 专家路由。词表大小为 262,144，隐藏层维度为 2,816，该权重没有共享 KV 层或逐层输入嵌入。这些是配置事实，不是实测活跃参数数量或性能预测。

## 量化与输出分数

权重使用仿射量化，默认 4-bit、分组大小 64，并为稠密前馈投影及路由投影配置了 120 项显式 8-bit 覆盖。尽管目录名后缀为 `4bit`，它实际是混合 4／8-bit。官方加载器保留这些覆盖配置。权重索引包含绑定嵌入的量化权重、缩放因子与偏置。

由于 `tie_word_embeddings` 为 true，官方模型通过 `embed_tokens.as_linear(...)` 生成词表 logits，然后应用配置的 `final_logit_softcapping=30.0`。本项目从此返回张量中选取已验证候选的位置，不得绕过模型 softcap，也不得替换官方量化输出头。

因此，对此模型而言，API 的 `raw_scores` 指模型返回的、已经过 softcap 但尚未经本项目候选 softmax 的 logits。它们不是无界的 softcap 前投影值，也不是校准后的正确概率。不能假设不同模型架构之间的 logit margin 可直接比较。

## 模板与候选编码检查

本地模板接受 `system` 与 `developer` 消息。在 `enable_thinking=False` 时，其 assistant 前缀以原生空思考通道 `<|turn>model\n<|channel>thought\n<channel|>` 结尾。项目原样使用该权重模板，包括此前缀。

仅用 CPU 的 tokenizer 检查设置为 `local_files_only=True` 和 `trust_remote_code=False`，成功使用现有语义提示词编译全部 16 条开发请求及 28 条冻结测试请求。直接评分提示词长度：开发集 490–573 个 token，测试集 487–629 个 token。另一个最大候选规模请求也通过全部 66 个编码检查：64 个应用候选，加上不匹配和弃权。每个编码都唯一、可往返编码／解码，追加到实际提示词后仍为单 token。这验证的是编码契约，不代表模型会选择预期选项。

## 滑动窗口缓存边界

官方缓存工厂创建 25 个 `RotatingKVCache` 条目，`max_size=1024`、`keep=0`，另有 5 个完整注意力 `KVCache` 条目。这是滑动窗口／完整注意力结构，不是 Qwen 的注意力／循环状态混合缓存。旋转缓存除 key／value 数组外，还跟踪逻辑偏移量和环形位置；窗口填满后，不能任意裁剪。

项目的完整系统／页面快照保留官方缓存对象及其元数据。同页面请求复制完整页面快照；页面变化时从完整的较早系统快照重新开始。不引入自定义注意力掩码、手动环形缓存修改或最终答案缓存。

28 条冻结提示词均短于 1,024 个 token，因此单凭它们的一致性检查，不能覆盖环形回绕后的旋转缓存。额外的可选测试 `test_real_cache_parity_beyond_1024_token_prefix` 构造超过 1,536 个 token 的虚构页面前缀，评估该页面上的另一条话语，然后将长共享文本后的可见列表逆序。它检查实际页面复用和较早系统边界，将两次决策分别与全新计算比较，沿用现有限值：logit 绝对差不超过 0.5、受限分数差不超过 0.1，原始获胜 ID 完全一致。

[已记录的实机模型集成运行](../benchmarks/results/gemma4-model-tests.json)完成了 `tests/test_model.py` 中全部三项测试：**3 项通过、0 项失败、0 项跳过，总计 41.62 秒**。这是测试集总耗时，不是单次决策延迟。回绕用例使用 **1,741 个 token 的稳定页面前缀**，确认实际页面前缀复用，以及页面更新后的系统前缀复用。两次缓存结果都与各自全新计算保留了相同的原始获胜 ID。

| 与全新计算的缓存比较 | 返回 logit 最大差 | 受限分数最大差 |
| --- | ---: | ---: |
| 同页面，不同话语 | 0.0 | 0.0 |
| 长共享前缀后的页面更新 | 0.0 | 0.0 |

记录包含测试源码和源 JUnit 哈希，以及输出的 JUnit 属性。这些结果覆盖所构造的前缀与更新，而非后端 4,096 token 上限以内的所有提示词、批处理形状或模型配置。完整 4,096 token 范围仍未验证。通过这些集成不变量，不能证明普遍语义准确率或有效 JSON 生成能力。

等待其他模型任务完成后，串行复现集成运行：

```sh
JEV_TEST_MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit \
  python -m pytest tests/test_model.py \
  -q --junitxml=runs/gemma4-model-tests.xml
```

## 初步开发证据

两个已完成开发运行分别保留：

- [冒烟运行](../benchmarks/results/gemma4-moe-smoke/summary.json)：两条开发用例、四种输出方法、三种缓存条件、重复一次；共 24 次尝试。
- [开发运行](../benchmarks/results/gemma4-dev/summary.json)：全部 16 条原始开发用例、四种输出方法、同页面／新话语条件、重复一次；共 64 次尝试。

它们的目录保留元数据和单次试验，包括无效生成输出。这些仍是初步开发结果，与已完成的 [336 次冻结测试运行](../benchmarks/results/gemma4-test/summary.json)及 [12 次进程冷启动运行](../benchmarks/results/gemma4-cold/summary.json)分开。后两项均通过证据完整性审计，记录的源码哈希匹配 `ba98b71`。全部 56 次缓存／全新计算比较通过。每种缓存条件下，直接评分 28 条请求中有 26 条正确，包含一次错误选中的 enum 动作和一次错误拒绝类别；数值一致性不会使这些语义决策变成正确。完整方法、条件、质量分母、耗时、失败与范围限制见[结果报告](gemma4-results.zh-CN.md)。

## 权重来源与许可证

本地下载元数据标识为 [`mlx-community/gemma-4-26b-a4b-it-4bit`](https://huggingface.co/mlx-community/gemma-4-26b-a4b-it-4bit)，版本为 `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87`。保留的转换说明卡称其使用 `mlx-vlm` 0.4.3 从 `google/gemma-4-26b-a4b-it` 转换，但未固定原始 Google 权重版本。不要从如今已变化的上游模型卡推断原版本。

本地转换说明卡声明 Apache-2.0。[Google 模型卡](https://huggingface.co/google/gemma-4-26B-A4B-it)及 [Google 的 Gemma 4 许可页面](https://ai.google.dev/gemma/apache_2)也标明 Apache License 2.0。模型权重不包含在本项目以 MIT 许可发布的源码中。

本地 README、配置、tokenizer 配置、聊天模板、生成配置与权重索引，分别匹配本地 Hugging Face 下载元数据中的 Git blob 摘要。独立[权重记录](../benchmarks/results/gemma4-checkpoint.json)记录实际文件哈希及其与下载摘要的比较，不修改较早的权重记录。本地下载元数据是来源记录，并非证明最初权重制作者身份的密码学证明。

本审计不会将成功加载、tokenizer 检查或无效 JSON 生成响应改算为正确语义决策。生成基线保留原始输出与严格解析结果；不会为此权重加入编码／ID 修复或 Markdown 代码围栏剥离。
