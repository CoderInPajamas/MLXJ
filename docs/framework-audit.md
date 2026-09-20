# Framework audit for 0.1

[Back to home](../README.en.md)

Verified against the installed MLX **0.31.2** and MLX-LM **0.31.3** source, then
installed those versions into a separate project environment. The shared reference
environment and model files are read-only. No custom Metal kernels or attention
masks are introduced.

| Requirement | Official implementation reused | 0.1 choice |
|---|---|---|
| Load local weights and tokenizer | `mlx_lm.load`, `utils.load_model` | Local directory only; remote code disabled |
| Quantized layers and output head | MLX-LM loader and each model's `__call__` | Preserve the full official head, select logits afterward |
| Model-specific cache | `models.cache.make_prompt_cache` | Includes Qwen3.5 `ArraysCache` and `KVCache` |
| Prefix lookup / snapshots | `LRUPromptCache`, internally `PromptTrie` | Bounded token-keyed snapshots, copied on retrieval |
| Hybrid rollback | `can_trim_prompt_cache` returns false for recurrent caches | Save system and page prefixes before the changing suffix |
| Segmented prefill | Official model calls and cache state evaluation | Bounded chunks, no reimplemented transformer |
| Generated baselines | `stream_generate`, greedy `make_sampler` | One code and actual structured JSON |
| Parallel questions | Official `BatchGenerator`, cache `merge` / `extract` | Audited but deferred; 0.1 serializes GPU requests |

The Qwen3.5 source creates one two-array recurrent cache for each linear layer and
a KV cache for each full-attention layer. `LRUPromptCache.fetch_nearest_cache`
deep-copies saved caches. It can trim only when every constituent cache supports
trimming; otherwise it returns a saved shorter prefix. The final SDK accepts only
exact page or exact system snapshots. They use separate namespaces in one bounded
official LRU, so inserting a trimmable page cannot remove the saved system prefix.
In the pinned 0.31.3 implementation, only exact retrieval has an empty suffix;
trimmed retrieval always leaves at least one suffix token. The SDK discards those
partial matches after a GLM page-update parity failure demonstrated that they
could change numerical results. This observation does not establish a framework
bug or its numerical cause. No later state survives a changed earlier token.

Source inspection also confirms that `generate_step(max_tokens=1)` schedules a
subsequent `_step` before yielding the first token. Our direct scorer instead runs
prefill and a final-position forward call and reads candidate logits, with no
generated continuation. This is still causal language-model inference over a
prompt, not a newly trained non-autoregressive architecture. `mx.eval` and
`mx.synchronize` bracket measurements, including scheduled baseline work.

The token compiler verifies unique single-token code encodings, decoding round
trips, and continuation tokenization in the actual chat prompt. Prefixes are
checked at token level, including boundaries where BPE might merge text. Only KV
and recurrent state are stored; every utterance is evaluated anew.

References: [MLX-LM repository](https://github.com/ml-explore/mlx-lm),
[cache source](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/cache.py),
[generation source](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/generate.py),
[Qwen3.5 source](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/qwen3_5.py).
The exact installed source and dependency versions are the basis of this audit;
upstream main may change.
