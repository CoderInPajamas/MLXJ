# Model compatibility

[Back to home](../README.en.md)

Compatibility means the checkpoint loads through the official MLX-LM implementation,
its tokenizer supports verified one-token codes, real semantic inference runs, and
cached/fresh numerical parity is measured. It does not imply perfect decisions or
compatibility with every conversion of an architecture.

The 0.1 runtime is pinned to MLX 0.31.2 / MLX-LM 0.31.3 / Transformers 5.9.0 /
Tokenizers 0.22.2. The actual host is Apple M2 Max with 64 GiB unified memory and
Python 3.13.2. Full hardware and dependency metadata accompany each run.

The latest [six-domain comparison](extended-results.md) completed all four methods
on a separate 36-case test suite for each of these three checkpoints. Direct
same-page results are below; boolean accuracy is separate from action errors.
The canonical recorded runtime source hashes match `ba98b71`.

| Checkpoint | Correct / 36 | Wrong enum actions / 30 | Correct action coverage / 15 | Boolean correct / 6 |
|---|---:|---:|---:|---:|
| Gemma 4 MoE | 31/36 | 1/30 | 12/15 | 5/6 |
| Qwen3.5-9B-OptiQ-4bit | 30/36 | 1/30 | 12/15 | 6/6 |
| GLM-4.7-Flash-4bit | 21/36 | 8/30 | 9/15 | 2/6 |

All three returned wrong actions on this extension. The earlier Qwen zero-error
observation is specific to the original suite, and none of these results supports
general unattended execution. Gemma's separate extended cache phase completed
108 direct decisions and passed all 72 cached/fresh comparisons; each condition
retained 31/36 correct with one wrong enum action. Qwen/GLM extended cold-KV and
page-update phases are outside this campaign.

The table below preserves verification on the **original 28-case suite**:

| Local checkpoint | Architecture | Quantization | Weight size | Verification |
|---|---|---|---:|---|
| Qwen3.5-9B-OptiQ-4bit | `qwen3_5`, hybrid recurrent + full attention | Mixed 4/8-bit, group 64 | 5.63 GiB | Revised `579daf3` source: 84 direct decisions completed; 56/56 numerical cache comparisons passed. Returned accuracy 25/28 and coverage 17/18 in every condition; no observed false actions. Historical baselines and all errors remain in [results](results.md). |
| GLM-4.7-Flash-4bit | `glm4_moe_lite` | 4-bit, group 64 | 15.70 GiB | Revised `579daf3` runtime: 84 direct decisions completed; 56/56 numerical cache comparisons passed. Semantic quality remains 14/28 correct and 2/28 returned false actions in every condition; **not recommended for direct action execution with this prompt**. Original 25/28 parity failures remain published. See [results](results.md). |
| gemma-4-26b-a4b-it-4bit | `gemma4` / `gemma4_text`, MoE with sliding + full attention | Mixed 4/8-bit, group 64 | 14.54 GiB | `ba98b71`: all 336 decisions across four methods/three conditions completed; direct 26/28 correct per condition, including **one wrong enum action** and one incorrect rejection category. Enum coverage 15/16; boolean accuracy 2/2. All 56 cached/fresh comparisons and three integration tests passed, including a 1,741-token prefix. Same-page direct p50/p95 134.9/283.9 ms; full process cold start 7933.0/8465.9 ms on one case × three repetitions. **Not a default recommendation for automatic execution.** See [Gemma results](gemma4-results.md). |

The compatibility table must be read together with the results document. A tokenizer
check alone is not a real-model validation. Other locally inventoried checkpoints,
including Qwen3.6, other Gemma conversions and Nemotron, are not certified by this release.
Multi-question batching and vision inputs are not supported.

Recorded Qwen and GLM comparison tables describe historical source revisions.
The subsequent `579daf3` cache-boundary change preserves complete page/system
snapshots. Full Qwen and GLM numerical verification passed, each with 56/56
comparisons and identical measured logits to its original valid reference path.
Semantic quality did not improve. Do not treat prior-run latency as revised-runtime
comparison evidence or combine methods measured under different implementations.
Gemma's four-method comparison was recorded together on `ba98b71`; do not combine
its times with the older Qwen/GLM tables to claim cross-model speedups. Gemma's
code/JSON baselines use the existing prompt and strict parser without model-specific
optimization; their format failures remain in every quality denominator.

The recorded real-browser demonstration uses Qwen only. Its 16 scenarios accept
either no-match or abstention for declines and are not a substitute for strict
benchmark accuracy. GLM and Gemma browser operation have not been evaluated.

Exact local checkpoint provenance is recorded in
[`checkpoints.json`](../benchmarks/results/checkpoints.json) for Qwen/GLM and
[`gemma4-checkpoint.json`](../benchmarks/results/gemma4-checkpoint.json) for Gemma. All weight shards were
read and hashed; their SHA256 digests match the local Hugging Face download metadata.
The model basenames alone are insufficient: the upstream Qwen conversion at `main`
has changed since this local copy was downloaded.

| Checkpoint repository | Verified local revision |
|---|---|
| [mlx-community/Qwen3.5-9B-OptiQ-4bit](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit/tree/76b3310ab7aa52a34303c66fc928b6d7239c860c) | `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| [mlx-community/GLM-4.7-Flash-4bit](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit/tree/1454cffb1a21737e162f508e5bc70be9def89276) | `1454cffb1a21737e162f508e5bc70be9def89276` |
| [mlx-community/gemma-4-26b-a4b-it-4bit](https://huggingface.co/mlx-community/gemma-4-26b-a4b-it-4bit/tree/8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87) | `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |

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
Gemma 4's local conversion card declares Apache 2.0, consistent with
[Google's Gemma 4 license page](https://ai.google.dev/gemma/apache_2); its original
base revision is not pinned by the retained conversion card. See the
[Gemma audit](gemma4-audit.md) for the exact provenance boundary.
Those are separate from JEV MLX's MIT license. No Jev weights or training artifacts
are used.
