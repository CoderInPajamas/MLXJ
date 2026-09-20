# Additional model and extended-suite evaluation protocol

Protocol ID: `extended-evaluation-v1`. Finalized 2026-09-20 before the original
Gemma test and all extended-suite inference. This document specifies experiments;
completion belongs in the results. The original 16-case Gemma development run
had already started with these fixed settings before finalization. Record this
protocol's Git commit with results; retain any later amendment explicitly.

The scope is the existing local Gemma MoE checkpoint on the original suite, plus
the same three local checkpoints on the new six-domain extension. Existing
prompts, model weights, score processing, rejection threshold, and frozen labels
remain unchanged. No model-specific semantic prompt or test-driven threshold
adjustment is part of this protocol.

## Prior knowledge and distinct datasets

The original suite's earlier Qwen and GLM outcomes are already known. A Gemma
compatibility smoke run has also used the **first two original development
cases**, all four modes, and all three cache conditions. It remains a separate
smoke record, not a full development or test result. This protocol does not
retroactively preregister that run, the original development run, the three Gemma
integration tests, or the historical benchmark.

The extension was written after the historical results were known, with no
model inference on its own cases used to author labels. Its fixture freeze is
`2026-09-20T06:09:44.415784+00:00`. It is a post-development extension, not an
untouched original benchmark or an independently sampled population study.

| Suite | Directory | Development | Test | Test composition |
|---|---|---:|---:|---|
| Original fictional course/player suite | `benchmarks/fixtures` | 16 | 28 | 26 enum requests and 2 boolean requests |
| Six-domain extension v1 | `benchmarks/fixtures/extended-v1` | 12 | 36 | 30 enum requests and 6 boolean requests |

The [original manifest](../benchmarks/fixtures/manifest.json) and
[extended manifest](../benchmarks/fixtures/extended-v1/manifest.json) are the
authority for case identity, counts, and exact bytes. The original files remain
unchanged. Additional details and label rationales are in the
[extension README](../benchmarks/fixtures/extended-v1/README.md).

| File | Frozen SHA-256 |
|---|---|
| Original `dev.jsonl` | `610114cd493232ffd05a9dc5ffe6dd355b1bc3d7c1ad62f65ff02f5c413f6e16` |
| Original `test.jsonl` | `e86e2278a872ab37b2143a12b2e39fb6dde7a0ffac96afa6cc80c139ddfafce3` |
| Extended `dev.jsonl` | `b5c070b8aa40ac313723f996bc9f7c3e406e11fa7332dbf47ab49958d0dd3408` |
| Extended `test.jsonl` | `ad804e681bb6906c81dc5da316b61a805dd1dbfc8df20940c7b1cc22776aa25e` |

## Checkpoints and fixed runtime

Use these existing local conversions, with original files read-only:

| Checkpoint directory basename | Verified conversion revision |
|---|---|
| `gemma-4-26b-a4b-it-4bit` | `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |
| `Qwen3.5-9B-OptiQ-4bit` | `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| `GLM-4.7-Flash-4bit` | `1454cffb1a21737e162f508e5bc70be9def89276` |

Gemma is the local MLX conversion of `google/gemma-4-26b-a4b-it`, not the separate
DiffusionGemma or modified Gemma conversions also present on the host. Its local
text configuration enables MoE, with 128 experts and top-8 routing. The conversion
uses default 4-bit affine quantization, group size 64, with 8-bit overrides; the
filename alone is not a complete quantization description. Exact files and
conversion provenance are in [Gemma checkpoint evidence](../benchmarks/results/gemma4-checkpoint.json)
and [Qwen/GLM checkpoint evidence](../benchmarks/results/checkpoints.json).

Use the project's independent environment and current official MLX-LM backend.
Do not modify the shared model environment, weights, system memory limits, or
other running applications. Run model jobs sequentially. Record actual hardware,
dependency versions, model configuration/tokenizer hashes, quantization, source
hashes, and load timing from each run; do not assume they match a historical run.

The semantic runtime reviewed for this plan has these SHA-256 hashes:

| Source | SHA-256 |
|---|---|
| `src/jev_mlx/prompt.py` | `8d0b340fb804a83ad37a6ee6a0feca39b4af061598712a2078ae1903e3c76f6b` |
| `src/jev_mlx/engine.py` | `10aebdb027d54fbc42f49f7a249abc2f4149b613de6d063c5e91fe300ba15baa` |
| `src/jev_mlx/backends/mlx_lm.py` | `9925f8da4c7b8b9ab6c879d0d2f354170365792a5f886b142ca339af5254d84c` |

The runner extension adds explicit fixture-directory selection and reporting;
each full run must retain hashes of the runner and metrics implementation too.
If inference behavior changes, retain earlier attempts and start a separately
identified experiment. Do not silently pool results across source revisions.

Fixed settings are:

- Direct margin threshold **0.0**. A selected candidate with an exact zero margin
  becomes `abstain`; retain the original winner as `raw_selected_id`. Reserved
  no-match/abstain winners retain their own statuses.
- All four modes: `direct`, `code`, `json`, `json_code`. Direct and code share the
  same code-choice prompt. JSON modes retain the same semantic policy, state, and
  choices while requesting their respective existing output formats.
- Greedy official generation, temperature 0; code limit 1 generated token;
  JSON and JSON-code limits 96 tokens. No constrained decoder, answer repair,
  retry-until-correct, hidden parameter generation, or model-specific format fix.
- Existing tokenizer chat template with `enable_thinking=False`, verified
  single-token option codes, and the official model output head unchanged.
- Prompt limit 4096 tokens, prefill chunks 256 tokens, prefix cache 512 MiB and
  16 entries, serial inference. No final-answer cache.
- One measured repeat per case/mode/cache condition; deterministic scheduling
  seed `20260919`. Keep preparation calls but exclude them from decision latency.
- Cache parity: logit absolute tolerance 0.5, relative tolerance 0; restricted
  softmax absolute tolerance 0.1; exact agreement of the raw top-choice ID.

`json_code` was originally introduced after historical JSON format failures.
All four formats are now fixed prospectively for this additional campaign, but
that does not erase the supplementary, test-informed origin of the format.

## Planned run matrix

Development runs check the fixed configuration; they are not permission to tune
this campaign's prompt or threshold. Any later tuning requires a separate plan
and a newly identified evaluation, preserving all fixed-configuration attempts.

| Run | Models | Split | Modes | Conditions | Measured rows | Extra parity |
|---|---|---|---|---|---:|---|
| Original development | Gemma | 16 dev | All four | Same-page only | 64 | None |
| Original test | Gemma | 28 test | All four | All three | 336 | 28 cases, 56 comparisons |
| Fresh-process cold start | Gemma | First original test case only | All four | New process, 3 repeats/mode | 12 | None |
| Extended development | Gemma, Qwen, GLM | 12 dev | All four | Same-page only | 48/model, 144 total | None |
| Extended test | Gemma, Qwen, GLM | 36 test | All four | Same-page only | 144/model, 432 total | None in this run |

The primary plan contains **988 measured rows**, excluding preparation calls,
separate numerical parity passes, and the earlier compatibility smoke run.
Each suite's number of unique quality examples remains 28 or 36, regardless of
models, output methods, cache conditions, or repeated timing observations.

An optional extended direct-cache verification may run in a **separate output
directory** for any checkpoint needing full cache coverage on the new states.
Run all 36 test cases under all three conditions plus parity: 108 measured direct
rows and 72 parity comparisons per chosen model. If run for all three models,
that is 324 rows and 216 comparisons. Record the chosen models and reason before
launching that phase; retain the complete results, including failures. It cannot
replace an unfavorable primary run or be silently merged with its warm timings.

For this campaign, this phase is selected for **Gemma only**, prospectively: its
rotating-window cache is newly supported in the compatibility table and the new
state shapes warrant additional numerical checks. This adds 108 measured rows
and 72 comparisons, bringing planned measurements to **1,096**. Extended Qwen
and GLM cache-cold/update cohorts are outside this campaign; their existing
original-suite numerical evidence remains separate.

The three loaded-model conditions mean:

| Condition | Preparation and measured work |
|---|---|
| `kv_cold` | Weights already loaded; measured call uses `use_cache=False` |
| `same_page_new_utterance` | Warm up the same state/choices with the fixture's different warmup utterance; measure the target utterance |
| `page_update` | Warm up the fixture's distinct earlier state; measure the current state, recomputing its changed suffix |

Requested cache reuse is not proof of a hit: inspect actual `cache.hit`, scope,
reused/prefill token counts, and memory. Numerical parity is direct scoring only,
even when a run also measures generation modes. Each parity case compares fresh
scores separately against same-page reuse and page-update reuse.

Fresh-process measurement uses `test-close-player`, the first original test
fixture. Its parent wall time includes interpreter startup, loading, first
decision, and process shutdown. Record load/decision components separately.
Operating-system filesystem caches are not flushed. Three repeats per method
cannot establish a stable tail percentile or full-suite semantic quality.

## Scoring and reporting

Keep original and extended results in separate tables. Exact accuracy requires
the expected status and, for a selected result, the correct stable candidate ID.
No-match and abstain are different labels. Report raw-choice accuracy separately
from returned-decision accuracy, retaining zero-margin rejections, invalid JSON,
unrecognized generated codes, truncation, loading errors, preparation errors,
and runtime failures. An executor cannot upgrade an incorrect model choice.

Report p50/p95, attempt counts, accuracy, rejection/abstention, format validity,
correct-choice coverage, raw and returned error rates, memory, and failures for
each method and condition. Preserve individual `wall_ms` observations; current
percentiles use linear interpolation and include completed but semantically
wrong or schema-invalid responses. Exceptions have their own failure latency.
MLX values and caches are evaluated and synchronized before backend timing ends.
Lifetime RSS, active MLX memory, allocator cache, and peak MLX memory are distinct
measurements and must not be added as if disjoint memory allocations.

**Separate enum action metrics from boolean answer metrics:**

| Test suite | Enum requests | Correct enum action opportunities | Boolean requests | Expected selected boolean answers | Aggregate expected `selected` |
|---|---:|---:|---:|---:|---:|
| Original | 26 | 16 | 2 | 2 | 18 |
| Extended | 30 | 15 | 6 | 4 | 19 |

The existing `executable_request_coverage` aggregate denominator includes
boolean answers; it is 18 or 19, not a count of real application actions.
Likewise the generic `false_action` metric includes an incorrect selected
boolean answer. Use kind-separated enum results for action-error statements,
and label boolean errors as classification errors. An unknown boolean state
requires abstention; a known false proposition is a legitimate selected answer.

The fixture runner does **not** execute a browser, calendar, filesystem action,
purchase, or other application effect. A correct fixture label is not a browser
execution receipt. The existing browser video is separate historical evidence;
these runs cannot establish Gemma or GLM browser execution. English input results
also cannot establish Chinese or mixed-language understanding.

Never interpret a zero exit code as perfect model quality: schema-invalid or
semantically wrong responses can complete without runtime exceptions. Likewise
`complete=true` describes completed phases, not all-correct answers. Full runs
must retain all expected rows and requested parity records before being labeled
complete; interrupted or subset runs stay explicitly incomplete or smoke-only.

Any speed comparison must use measured paths from the same source version and
condition, with quality and coverage alongside latency. Do not combine new
Gemma or extension timings with historical Qwen/GLM timings to claim a speedup.
One-token official generation may schedule lookahead work; this is included in
its synchronized timing. Direct logits are still a causal model computation,
not proof of an exclusive non-autoregressive architecture or a fixed 100 ms bound.

## Reproduction commands

Run from the repository root in the project's independent environment. Replace
the model-root placeholder with the directory containing the verified local
checkpoints. Use a fresh output directory per attempt; never overwrite evidence.

```bash
source .venv/bin/activate
MODEL_ROOT=/absolute/path/to/local/models
GEMMA_MODEL="$MODEL_ROOT/gemma-4-26b-a4b-it-4bit"

python -m benchmarks.run --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/gemma-original-dev-v1

python -m benchmarks.run --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split test \
  --modes direct code json json_code \
  --conditions kv_cold same_page_new_utterance page_update \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --parity --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/gemma-original-test-v1

python -m benchmarks.cold_start --model "$GEMMA_MODEL" \
  --fixtures-dir benchmarks/fixtures --split test \
  --modes direct code json json_code --repeats 3 \
  --output results/gemma-original-cold-v1
```

Run the extension sequentially for each of the three checkpoints:

```bash
for checkpoint_name in gemma-4-26b-a4b-it-4bit Qwen3.5-9B-OptiQ-4bit GLM-4.7-Flash-4bit
do
  python -m benchmarks.run --model "$MODEL_ROOT/$checkpoint_name" \
    --fixtures-dir benchmarks/fixtures/extended-v1 --split dev \
    --modes direct code json json_code --conditions same_page_new_utterance \
    --margin-threshold 0 --repeats 1 --seed 20260919 \
    --output "results/extended-v1-$checkpoint_name-dev"

  python -m benchmarks.run --model "$MODEL_ROOT/$checkpoint_name" \
    --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
    --modes direct code json json_code --conditions same_page_new_utterance \
    --margin-threshold 0 --repeats 1 --seed 20260919 \
    --output "results/extended-v1-$checkpoint_name-test"
done
```

For the separately declared optional direct-cache phase, choose a model path
and a distinct output name before launching:

```bash
export JEV_MLX_MODEL="$GEMMA_MODEL"
python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
  --modes direct --conditions kv_cold same_page_new_utterance page_update \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --parity --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/extended-v1-gemma-direct-cache
```

These arguments were checked against `benchmarks.run` and
`benchmarks.cold_start`, including `--fixtures-dir`. Run metadata embeds the
fixture manifest; retain `metadata.json`, `trials.jsonl`, `summary.json`, and any
requested `parity.jsonl`, plus checkpoint provenance and the finalized protocol.
Do not edit the fixture manifests to make an altered dataset pass validation.
