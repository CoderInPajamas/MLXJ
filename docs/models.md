# Model compatibility

Compatibility means the checkpoint loads through the official MLX-LM implementation,
its tokenizer supports verified one-token codes, real semantic inference runs, and
cached/fresh numerical parity is measured. It does not imply perfect decisions or
compatibility with every conversion of an architecture.

The 0.1 runtime is pinned to MLX 0.31.2 / MLX-LM 0.31.3 / Transformers 5.9.0 /
Tokenizers 0.22.2. The actual host is Apple M2 Max with 64 GiB unified memory and
Python 3.13.2. Full hardware and dependency metadata accompany each run.

| Local checkpoint | Architecture | Quantization | Weight size | Verification |
|---|---|---|---:|---|
| Qwen3.5-9B-OptiQ-4bit | `qwen3_5`, hybrid recurrent + full attention | Mixed 4/8-bit, group 64 | 5.63 GiB | Revised `579daf3` source: 84 direct decisions completed; 56/56 numerical cache comparisons passed. Returned accuracy 25/28 and coverage 17/18 in every condition; no observed false actions. Historical baselines and all errors remain in [results](results.md). |
| GLM-4.7-Flash-4bit | `glm4_moe_lite` | 4-bit, group 64 | 15.70 GiB | Revised `579daf3` runtime: 84 direct decisions completed; 56/56 numerical cache comparisons passed. Semantic quality remains 14/28 correct and 2/28 returned false actions in every condition; **not recommended for direct action execution with this prompt**. Original 25/28 parity failures remain published. See [results](results.md). |

The compatibility table must be read together with the results document. A tokenizer
check alone is not a real-model validation. Other locally inventoried checkpoints,
including Qwen3.6, Gemma and Nemotron conversions, are not certified by this release.
Multi-question batching and vision inputs are not supported.

Recorded Qwen and GLM comparison tables describe historical source revisions.
The subsequent `579daf3` cache-boundary change preserves complete page/system
snapshots. Full Qwen and GLM numerical verification passed, each with 56/56
comparisons and identical measured logits to its original valid reference path.
Semantic quality did not improve. Do not treat prior-run latency as revised-runtime
comparison evidence or combine methods measured under different implementations.

The recorded real-browser demonstration uses Qwen only. Its 16 scenarios accept
either no-match or abstention for declines and are not a substitute for strict
benchmark accuracy. GLM browser operation has not been evaluated.

Exact local checkpoint provenance is recorded in
[`checkpoints.json`](../benchmarks/results/checkpoints.json). All weight shards were
read and hashed; their SHA256 digests match the local Hugging Face download metadata.
The model basenames alone are insufficient: the upstream Qwen conversion at `main`
has changed since this local copy was downloaded.

| Checkpoint repository | Verified local revision |
|---|---|
| [mlx-community/Qwen3.5-9B-OptiQ-4bit](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit/tree/76b3310ab7aa52a34303c66fc928b6d7239c860c) | `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| [mlx-community/GLM-4.7-Flash-4bit](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit/tree/1454cffb1a21737e162f508e5bc70be9def89276) | `1454cffb1a21737e162f508e5bc70be9def89276` |

For exact reproduction, obtain that revision separately, compare hashes, and pass
the local directory to JEV MLX. The package neither includes nor modifies model weights.
It disables remote tokenizer code. The default prompt limit is 4,096 tokens; prompts
over that bound fail explicitly. In addition to weights, allow memory for snapshots,
temporary compute arrays, the allocator and your other applications. No system
memory limit or shared environment is changed by the package.

The Qwen base checkpoint is under [Apache 2.0](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/LICENSE),
also declared by the [OptiQ conversion card](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit).
The [GLM base card](https://huggingface.co/zai-org/GLM-4.7-Flash) and
[MLX conversion card](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit) declare MIT.
Those are separate from JEV MLX's MIT license. No Jev weights or training artifacts
are used.
