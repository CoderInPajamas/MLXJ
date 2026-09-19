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
| Qwen3.5-9B-OptiQ-4bit | `qwen3_5`, hybrid recurrent + full attention | Mixed 4/8-bit, group 64 | 5.63 GiB | See the completed run and parity evidence in [results](results.md) |
| GLM-4.7-Flash-4bit | `glm4_moe_lite` | 4-bit | 15.70 GiB | See the completed run and parity evidence in [results](results.md) |

The compatibility table must be read together with the results document. A tokenizer
check alone is not a real-model validation. Other locally inventoried checkpoints,
including Qwen3.6, Gemma and Nemotron conversions, are not certified by this release.
Multi-question batching and vision inputs are not supported.

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
the local directory to JEVKit. The package neither includes nor modifies model weights.
It disables remote tokenizer code. The default prompt limit is 4,096 tokens; prompts
over that bound fail explicitly. In addition to weights, allow memory for snapshots,
temporary compute arrays, the allocator and your other applications. No system
memory limit or shared environment is changed by the package.

The Qwen base checkpoint is under [Apache 2.0](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/LICENSE),
also declared by the [OptiQ conversion card](https://huggingface.co/mlx-community/Qwen3.5-9B-OptiQ-4bit).
The [GLM base card](https://huggingface.co/zai-org/GLM-4.7-Flash) and
[MLX conversion card](https://huggingface.co/mlx-community/GLM-4.7-Flash-4bit) declare MIT.
Those are separate from JEVKit's MIT license. No Jev weights or training artifacts
are used.
