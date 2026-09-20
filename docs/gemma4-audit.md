# Gemma 4 MoE framework and checkpoint audit

Audit date: 2026-09-20. This audit covers text-only use of the existing local
`gemma-4-26b-a4b-it-4bit` checkpoint. Reading source, configuration, and tokenizer
files does not establish semantic accuracy or numerical cache parity. Those
claims require the separately recorded model runs.

## Official framework support

The project's isolated environment contains MLX 0.31.2, MLX-LM 0.31.3,
Transformers 5.9.0, and Tokenizers 0.22.2. MLX-LM 0.31.3 already includes
[`gemma4.py`](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/gemma4.py)
and [`gemma4_text.py`](https://github.com/ml-explore/mlx-lm/blob/v0.31.3/mlx_lm/models/gemma4_text.py).
No framework upgrade, private model implementation, or shared-environment change
is needed for this text-only scoring path.

The configuration declares `Gemma4ForConditionalGeneration`, outer model type
`gemma4`, and text model type `gemma4_text`. The official loader dispatches to
the Gemma wrapper, whose sanitization discards vision/audio components and whose
`__call__(inputs, cache=...)` returns the text model's logits. The conversion
card's `mlx-vlm` example is for multimodal use; it does not make `mlx-vlm` a
requirement for this official MLX-LM text path. This project does not claim to
evaluate the checkpoint's image, video, or audio behavior.

The text configuration has 30 layers, 128 experts, and top-8 expert routing.
It uses a 262,144-token vocabulary, hidden size 2,816, and no shared-KV layers
or per-layer input embeddings in this checkpoint. These are configuration
facts, not measured active-parameter counts or a performance prediction.

## Quantization and output scores

The checkpoint uses affine quantization with a default of 4 bits and group size
64, plus 120 explicit 8-bit overrides for dense feed-forward projections and
router projections. It is mixed 4/8-bit, despite the directory's `4bit` suffix.
The official loader retains those overrides. The weight index includes the tied
embedding's quantized weights, scales, and biases.

The official model produces vocabulary logits through
`embed_tokens.as_linear(...)`, since `tie_word_embeddings` is true, and then
applies its configured `final_logit_softcapping=30.0`. The project selects the
verified candidate positions from this returned tensor. It must not bypass
the model's softcap or replace the official quantized output head.

For this model, the API's `raw_scores` therefore mean the model's returned,
softcapped logits before the project's candidate softmax. They are not unbounded
pre-softcap projections or calibrated correctness probabilities. Logit margins
should not be assumed comparable across different model architectures.

## Template and candidate-code checks

The local template accepts `system` and `developer` messages. With
`enable_thinking=False`, its assistant prefix ends in the native empty thought
channel, `<|turn>model\n<|channel>thought\n<channel|>`. The project uses the
checkpoint's template unchanged, including that prefix.

CPU-only tokenizer checks used `local_files_only=True` and
`trust_remote_code=False`. They successfully compiled all 16 development and
28 frozen test requests with the existing semantic prompt. Direct prompt lengths
were 490–573 tokens for development and 487–629 for test. A separate maximum-size
request also passed all 66 code checks: 64 application candidates plus no-match
and abstention. Each code is unique, round-trips, and remains one token when
appended to the actual prompt. This verifies the encoding contract, not that
the model chooses the intended option.

## Sliding-window cache boundary

The official cache factory creates 25 `RotatingKVCache` entries with
`max_size=1024` and `keep=0`, plus five full-attention `KVCache` entries. This is
sliding/full attention, not Qwen's attention/recurrent cache mixture. The
rotating cache tracks the logical offset and ring position in addition to its
key/value arrays; after the window fills, it is not arbitrarily trimmable.

The project's complete system/page snapshots retain the official cache objects
and their metadata. Same-page requests copy a complete page snapshot; changed
pages restart from the complete earlier system snapshot. No custom attention
mask, manual ring-cache surgery, or completed-answer cache is introduced.

The 28 frozen prompts are all shorter than 1,024 tokens, so their parity checks
alone do not cover a rotating cache after wraparound. The additional opt-in test
`test_real_cache_parity_beyond_1024_token_prefix` constructs a fictional page
prefix longer than 1,536 tokens, evaluates a different utterance on that page,
then reverses a visible list after the long shared text. It checks actual page
reuse and the earlier system boundary, comparing both decisions against fresh
computation with the existing limits: absolute logit difference at most 0.5,
restricted-score difference at most 0.1, and identical raw winning ID.

Run it sequentially after other model jobs finish:

```sh
JEV_TEST_MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit \
  python -m pytest tests/test_model.py \
  -k beyond_1024_token_prefix -q \
  --junitxml=results/gemma4-long-prefix.xml
```

The JUnit properties include prefix length and both numerical differences.
Adding this test is not evidence that it passed. Even a passing result would
cover this constructed prefix and update only, not every supported prompt
length, batch shape, or model configuration.

## Checkpoint provenance and license

The local download metadata identifies
[`mlx-community/gemma-4-26b-a4b-it-4bit`](https://huggingface.co/mlx-community/gemma-4-26b-a4b-it-4bit)
at revision `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87`. Its retained conversion
card says it was converted from `google/gemma-4-26b-a4b-it` using `mlx-vlm` 0.4.3;
that card does not pin the original Google checkpoint revision. Do not infer
one from today's upstream model card, which has since changed.

The local conversion card declares Apache-2.0. The
[Google model card](https://huggingface.co/google/gemma-4-26B-A4B-it) and
[Google's Gemma 4 license page](https://ai.google.dev/gemma/apache_2) also identify
Apache License 2.0. Model weights remain external to this project's MIT-licensed
source release.

The local README, configuration, tokenizer configuration, chat template,
generation configuration, and weight index each matched the Git blob digest
stored in their local Hugging Face download metadata. The independent
[checkpoint record](../benchmarks/results/gemma4-checkpoint.json) records actual
file hashes and comparison with those download digests, without changing older
checkpoint records. Local download metadata is a provenance record, not a
cryptographic attestation of who originally produced the weights.

This audit does not upgrade a successful load, a tokenizer check, or an invalid
generated JSON response into a correct semantic decision. Generation baselines
retain their original output and strict parser results; no code-versus-ID repair
or Markdown-fence stripping is introduced for this checkpoint.
