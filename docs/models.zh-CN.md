# 模型兼容性

[返回项目首页](../README.zh-CN.md)

这里的兼容性是指：检查点能够通过官方 MLX-LM 实现加载，分词器支持经过验证的单 token 编码，真实语义推理能够运行，并且测量过缓存与全新计算的数值一致性。它不代表决策总是正确，也不代表同一架构的所有转换版本都兼容。

0.1 版运行环境固定为 MLX 0.31.2 / MLX-LM 0.31.3 / Transformers 5.9.0 / Tokenizers 0.22.2。实际测试主机为配备 64 GiB 统一内存的 Apple M2 Max，Python 版本为 3.13.2。每次运行都附带完整的硬件与依赖元数据。

最新的[六领域对比](extended-results.zh-CN.md)在独立的 36 题测试集上，完成了以下三个检查点的全部四种方法测试。下表列出同页面直接评分结果；布尔题准确率与动作错误分开统计。所记录的标准运行时代码哈希与 `ba98b71` 一致。

| 检查点 | 正确数 / 36 | 枚举动作误选 / 30 | 正确动作覆盖 / 15 | 布尔题正确数 / 6 |
|---|---:|---:|---:|---:|
| Gemma 4 MoE | 31/36 | 1/30 | 12/15 | 5/6 |
| Qwen3.5-9B-OptiQ-4bit | 30/36 | 1/30 | 12/15 | 6/6 |
| GLM-4.7-Flash-4bit | 21/36 | 8/30 | 9/15 | 2/6 |

三个模型在扩展测试中都返回过错误动作。此前 Qwen 零误操作的观察仅适用于原始测试集，这些结果均不足以支持通用的无人值守执行。Gemma 另行完成了扩展缓存阶段的 108 次直接决策，72 次缓存／全新计算对照全部通过；每种条件都保持 31/36 正确，并出现一次枚举动作误选。本轮实验未包含 Qwen／GLM 扩展测试集的 KV 冷缓存和页面更新阶段。

下表保留了在**原始 28 题测试集**上的验证结果：

| 本地检查点 | 架构 | 量化 | 权重大小 | 验证情况 |
|---|---|---|---:|---|
| Qwen3.5-9B-OptiQ-4bit | `qwen3_5`，循环状态与全注意力混合架构 | 混合 4/8-bit，分组大小 64 | 5.63 GiB | 修订后的 `579daf3` 源码：完成 84 次直接决策；56/56 次缓存数值对照通过。每种条件的返回结果准确率均为 25/28，覆盖率为 17/18；未观察到误操作。历史基线与所有错误均保留在[结果报告](results.zh-CN.md)中。 |
| GLM-4.7-Flash-4bit | `glm4_moe_lite` | 4-bit，分组大小 64 | 15.70 GiB | 修订后的 `579daf3` 运行时：完成 84 次直接决策；56/56 次缓存数值对照通过。每种条件的语义质量仍为 14/28 正确，返回的误操作为 2/28；**不建议在当前提示词下直接执行动作**。原先 25/28 次一致性验证失败的记录仍公开保留。详见[结果报告](results.zh-CN.md)。 |
| gemma-4-26b-a4b-it-4bit | `gemma4` / `gemma4_text`，滑动窗口与全注意力混合的 MoE | 混合 4/8-bit，分组大小 64 | 14.54 GiB | `ba98b71`：完成四种方法、三种条件下的全部 336 次决策；每种条件直接评分均为 26/28 正确，错误包括**一次枚举动作误选**和一次拒绝类别错误。枚举动作覆盖率 15/16；布尔题准确率 2/2。全部 56 次缓存／全新计算对照与三项集成测试通过，其中包含 1,741 token 的前缀。同页面直接评分 p50/p95 为 134.9/283.9 ms；完整进程冷启动为 7933.0/8465.9 ms，基于一道题重复三次。**不作为自动执行的默认推荐**。详见 [Gemma 结果](gemma4-results.zh-CN.md)。 |

兼容性表必须结合结果文档阅读。仅检查分词器不构成真实模型验证。本地已清点的其他检查点，包括 Qwen3.6、其他 Gemma 转换版本和 Nemotron，未通过本版本认证。不支持多题批处理与视觉输入。

已记录的 Qwen 和 GLM 对比表对应历史代码修订。后续的 `579daf3` 缓存边界修改保留了完整的页面／系统快照。Qwen 和 GLM 的完整数值验证均通过，各自完成 56/56 次对照，测得的 logits 与原先有效的参考路径完全相同。语义质量没有改善。不要把旧运行的延迟作为修订后运行时的对比证据，也不要合并在不同实现下测量的方法。Gemma 的四种方法是在 `ba98b71` 上一同测量的；不要将其耗时与更早的 Qwen／GLM 表格组合，宣称跨模型加速。Gemma 的选项编码／JSON 基线沿用现有提示词与严格解析器，未针对模型优化；所有格式失败都计入质量指标的分母。

已记录的真实浏览器演示只使用 Qwen。其 16 个场景在应拒绝时，接受 no-match 或 abstain 中任一种结果，不能替代严格的基准准确率。GLM 和 Gemma 的浏览器操作尚未评测。

Qwen／GLM 的本地检查点精确来源记录在 [`checkpoints.json`](../benchmarks/results/checkpoints.json)，Gemma 的记录在 [`gemma4-checkpoint.json`](../benchmarks/results/gemma4-checkpoint.json)。已读取并计算所有权重分片的哈希；其 SHA256 摘要与本地 Hugging Face 下载元数据一致。仅凭模型目录名不足以识别检查点：本地副本下载后，上游 Qwen 转换版本的 `main` 已发生变化。

| 检查点仓库 | 已验证的本地修订 |
|---|---|
| [mlx-community/Qwen3.5-9B-OptiQ-4bit](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit/tree/76b3310ab7aa52a34303c66fc928b6d7239c860c) | `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| [mlx-community/GLM-4.7-Flash-4bit](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit/tree/1454cffb1a21737e162f508e5bc70be9def89276) | `1454cffb1a21737e162f508e5bc70be9def89276` |
| [mlx-community/gemma-4-26b-a4b-it-4bit](https://huggingface.co/mlx-community/gemma-4-26b-a4b-it-4bit/tree/8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87) | `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |

要精确复现，请单独获取对应修订、核对哈希，再将本地目录传给 JEV MLX。本软件包既不包含也不修改模型权重，并禁用分词器远程代码。默认提示词上限为 4,096 token，超过上限会明确报错。除权重外，还需要为快照、临时计算数组、分配器以及其他应用预留内存。软件包不会更改系统内存限制或共享环境。

Qwen 基础检查点采用 [Apache 2.0](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/LICENSE)，[OptiQ 转换模型卡](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit)也声明了该许可证。[GLM 基础模型卡](https://huggingface.co/zai-org/GLM-4.7-Flash)和 [MLX 转换模型卡](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit)声明采用 MIT。Gemma 4 的本地转换模型卡声明采用 Apache 2.0，与 [Google 的 Gemma 4 许可证页面](https://ai.google.dev/gemma/apache_2)一致；保留的转换模型卡未固定其原始基础模型修订。精确的来源验证边界见 [Gemma 审查](gemma4-audit.zh-CN.md)。这些许可证独立于 JEV MLX 自身的 MIT 许可证。项目未使用任何 Jev 权重或训练产物。
