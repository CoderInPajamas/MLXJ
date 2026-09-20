# 0.1 版框架审查

[返回项目首页](../README.zh-CN.md)

已根据安装的 MLX **0.31.2** 和 MLX-LM **0.31.3** 源码完成验证，并将这些版本安装到独立的项目环境中。共享参考环境与模型文件均只读访问。没有引入自定义 Metal 内核或注意力掩码。

| 需求 | 复用的官方实现 | 0.1 版选择 |
|---|---|---|
| 加载本地权重与分词器 | `mlx_lm.load`、`utils.load_model` | 仅接受本地目录；禁用远程代码 |
| 量化层与输出头 | MLX-LM 加载器及各模型的 `__call__` | 保留完整官方输出头，随后提取 logits |
| 模型专用缓存 | `models.cache.make_prompt_cache` | 包括 Qwen3.5 的 `ArraysCache` 和 `KVCache` |
| 前缀查找／快照 | `LRUPromptCache`，内部使用 `PromptTrie` | 有容量上限、以 token 序列为键的快照，取出时复制 |
| 混合状态回滚 | 循环缓存的 `can_trim_prompt_cache` 返回 false | 在变化的后缀之前保存系统前缀与页面前缀 |
| 分段预填充 | 官方模型调用与缓存状态求值 | 使用有界分块，不重新实现 transformer |
| 生成式基线 | `stream_generate`、贪心 `make_sampler` | 单个选项编码与实际生成的结构化 JSON |
| 多题并行 | 官方 `BatchGenerator`、缓存 `merge` / `extract` | 已审查但暂缓实现；0.1 串行处理 GPU 请求 |

Qwen3.5 源码为每个线性层创建包含两个数组的循环缓存，为每个全注意力层创建 KV 缓存。`LRUPromptCache.fetch_nearest_cache` 会深拷贝已保存的缓存。只有所有组成缓存都支持裁剪时才可裁剪，否则会返回已保存的较短前缀。最终 SDK 只接受精确匹配的页面快照或系统快照。两者在同一个有界官方 LRU 中使用独立命名空间，因此插入可裁剪的页面缓存不会替换已保存的系统前缀。在固定的 0.31.3 实现中，只有精确匹配返回的后缀为空；裁剪后返回的结果始终至少保留一个后缀 token。GLM 页面更新的一致性验证失败证明，部分匹配可能改变数值结果，因此 SDK 丢弃了这些匹配。该观察不能证明框架存在缺陷，也不能确定数值差异的原因。更早的 token 一旦改变，之后的状态均不再保留。

源码检查还确认，`generate_step(max_tokens=1)` 会在返回第一个 token 之前调度下一次 `_step`。我们的直接评分器改为执行预填充和最终输入位置的前向调用，然后读取候选 logits，不使用生成的后续文本。这仍然是对提示词进行因果语言模型推理，并不是新训练的非自回归架构。测量前后使用 `mx.eval` 和 `mx.synchronize`，也覆盖基线已调度的计算。

编码编译器验证单 token 编码的唯一性、编码与解码往返一致性，以及实际聊天提示词中的续写分词。前缀在 token 层面检查，包括 BPE 可能合并文本的边界。缓存仅保存 KV 与循环状态；每条新话语都会重新求值。

参考：[MLX-LM 仓库](https://github.com/ml-explore/mlx-lm)、[缓存源码](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/cache.py)、[生成源码](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/generate.py)、[Qwen3.5 源码](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/qwen3_5.py)。本次审查以实际安装的源码和依赖版本为依据；上游 main 可能变化。
