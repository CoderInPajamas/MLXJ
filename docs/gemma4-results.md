# Gemma 4 MoE measured results

Measured on 2026-09-20 using the existing local
`gemma-4-26b-a4b-it-4bit` checkpoint. Direct scoring returned **26/28 correct
choices in each cache condition**, with same-page decision latency of
**134.9 ms p50 / 283.9 ms p95**. It also selected the wrong visible course on
one request. This checkpoint is verified for the measured inference and cache
paths, but these results do **not** justify default unattended action execution.

The evidence includes all **336 measured decisions**, **56 cached/fresh numerical
comparisons**, and a separate **12-attempt process cold-start run**. The 28 test
cases are the original frozen regression set, already used in earlier project
evaluations; they are not 336 independent quality cases or a new blind benchmark.
The separate six-domain extension is outside this report.

## Recorded setup and evidence

| Item | Recorded value |
| --- | --- |
| Host | Apple M2 Max, Mac14,6, 12 CPU cores, 64 GiB unified memory; Darwin 25.6.0 |
| Runtime | Python 3.13.2; JEV MLX 0.1.0; MLX / MLX-Metal 0.31.2; MLX-LM 0.31.3; Transformers 5.9.0; Tokenizers 0.22.2; NumPy 2.5.3 |
| Checkpoint | `mlx-community/gemma-4-26b-a4b-it-4bit`, revision `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87` |
| Weights | 14.54 GiB; affine 4-bit, group 64, with 120 explicit 8-bit overrides |
| Measured source | `ba98b71792f418f527146d4a073c9a7f420f9534` (`ba98b71`) |
| Test schedule | 28 cases × 4 methods × 3 conditions × 1 repetition; fixed shuffle seed `20260919` |
| Choice policy | Existing semantic prompt; margin threshold `0.0`; no checkpoint-specific prompt, parser, or generation optimization |
| Baselines | Greedy code generation, maximum 1 token; greedy JSON / JSON-code generation, maximum 96 tokens |

The recorded worktree was dirty. Both evidence audits verified all eight recorded
inference/benchmark source hashes against `ba98b71`; they do not claim that every
untracked or documentation file was part of that commit. Model hashes are in the
[checkpoint record](../benchmarks/results/gemma4-checkpoint.json), with architecture,
template, quantization, license, and cache details in the
[framework audit](gemma4-audit.md).

- Formal test: [metadata](../benchmarks/results/gemma4-test/metadata.json),
  [all trials](../benchmarks/results/gemma4-test/trials.jsonl),
  [original summary](../benchmarks/results/gemma4-test/summary.json),
  [derived report](../benchmarks/results/gemma4-test/derived-report.json),
  [evidence audit](../benchmarks/results/gemma4-test/evidence-audit.json).
- Process cold start: [metadata](../benchmarks/results/gemma4-cold/metadata.json),
  [all trials](../benchmarks/results/gemma4-cold/trials.jsonl),
  [derived report](../benchmarks/results/gemma4-cold/derived-report.json),
  [evidence audit](../benchmarks/results/gemma4-cold/evidence-audit.json).

Both runs passed the evidence-integrity audit. That verifies recorded inputs,
schedule, metric calculations, source hashes, and public-copy identity; it does
not convert model errors into correct choices.

## Loaded-model latency and quality

Each row below contains all 28 cases. Latencies are synchronized wall times in
milliseconds, including invalid generated outputs. No runtime exception occurred.
`kv_cold` keeps weights loaded but bypasses prompt snapshots. `same_page` uses a
separate recorded warmup utterance on the current page. `page_update` warms a
different earlier state, then recomputes the current page from the earlier system
snapshot. Loading and preparation are outside these decision intervals.

| Method | Condition | p50 ms | p95 ms | Correct / 28 | Rejected / 28 | Schema valid / 28 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| direct | kv_cold | 1821.7 | 3050.1 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| direct | same_page | 134.9 | 283.9 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| direct | page_update | 840.1 | 1414.5 | 26 (92.86%) | 10 (35.71%) | 28 (100%) |
| code | kv_cold | 2052.5 | 3847.3 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| code | same_page | 366.9 | 941.7 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| code | page_update | 1149.9 | 2195.2 | 22 (78.57%) | 8 (28.57%) | 23 (82.14%) |
| json | kv_cold | 2282.5 | 3240.3 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json | same_page | 589.8 | 2312.9 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json | page_update | 1160.4 | 2148.9 | 2 (7.14%) | 1 (3.57%) | 2 (7.14%) |
| json_code | kv_cold | 2254.2 | 3616.1 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |
| json_code | same_page | 574.2 | 1823.6 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |
| json_code | page_update | 1375.0 | 3115.4 | 10 (35.71%) | 10 (35.71%) | 12 (42.86%) |

Rejection means a valid `no_match` or `abstain`, not malformed generation. The
quality counts were identical across the three conditions. Percentiles summarize
28 different inputs with one measurement each; they are not stable repeated-run
tail estimates. Same-page preparation itself cost the following p50/p95, outside
the table: direct 1735.2/2951.6 ms, code 2059.2/4375.1 ms, JSON 2410.2/5435.4 ms,
and JSON-code 2293.0/4232.4 ms. All preparation records remain in the trials.

Direct scoring had lower measured p50 than the three baselines in each condition
of this run. That is a result for this checkpoint, prompt, input set, and host,
not a fixed latency promise or an optimized-generation comparison. Direct scoring
restricts the final-position vocabulary to verified candidate codes. The baselines
generate without a grammar or repair step, and have substantial format failures.
Official MLX-LM can schedule lookahead work for one-token generation; completed
work is included in timing. Historical Qwen/GLM times were collected under other
source revisions and conditions and must not be combined into a speedup claim.

## Action errors, boolean choices, and coverage

Each condition contains **26 enum requests**, including **16 executable requests**,
and **2 boolean requests**. This table applies separately to each of the three
conditions. Enum errors and coverage exclude boolean selections.

| Method | Enum correct / 26 | Wrong enum actions / 26 | Correct executable enum choices / 16 | Boolean correct / 2 | no_match / abstain |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 24 (92.31%) | 1 (3.85%) | 15 (93.75%) | 2 (100%) | 9 / 1 |
| code | 20 (76.92%) | 0 (0%) | 13 (81.25%) | 2 (100%) | 8 / 0 |
| json | 2 (7.69%) | 0 (0%) | 1 (6.25%) | 0 (0%) | 0 / 1 |
| json_code | 9 (34.62%) | 0 (0%) | 1 (6.25%) | 1 (50%) | 10 / 0 |

The direct path selected an enum action 16 times per condition, with one wrong
action: **1/16, or 6.25%, of its enum selections**. Its two errors were:

- `test-first-filtered`: “First one” with the visible order Lunar Cartography,
  then Tidal Engines. It selected `play_tidal` instead of `play_lunar`. The allowed
  candidate list had a different order from the visible list. This is a model
  action error even if an execution guard could prevent its effect.
- `test-close-ambiguous`: “Close it” with library and settings windows open and
  no focused window. It returned `no_match` instead of the required `abstain`.
  This is an incorrect rejection category, not a false action.

The first error recurs in all three cache conditions; the aggregate audit counts
three wrong-action records, not three independent failing requests. A high overall
choice score must not conceal this error. No executor correction is credited as
model accuracy, and these results do not make Gemma the default for automatic
execution. Boolean accuracy has only two examples and establishes little beyond
those cases. Scores remain uncalibrated candidate-relative values.

## All generation failures remain counted

The formal run retained **0 runtime failures and 141 schema-invalid outputs**:
15 code, 78 JSON, and 48 JSON-code records across the three conditions.

- **Code:** five invalid outputs per condition, including the tokens `code`,
  `play`, and `__`, which are not allowed option codes. The invalid cases are
  `test-sort-title`, `test-vague-course`, `test-close-negation`,
  `test-first-filtered`, and `test-first-reordered`. It also returned `no_match`
  instead of `abstain` on `test-close-ambiguous`.
- **JSON:** 26 invalid outputs per condition. Twenty-one are unfenced objects
  with an option code in `candidate_id`, such as `{"candidate_id":"2"}`, rather
  than a permitted business ID; five are Markdown-fenced objects. The two valid
  responses were correct. The strict parser does not infer or repair their intent.
- **JSON-code:** 16 invalid outputs per condition, all Markdown-fenced objects.
  Among the 12 valid responses, the ambiguous close and vague-course requests
  incorrectly returned `no_match` instead of `abstain`, leaving 10 correct choices.

The exact outputs, IDs, and failure flags are in the linked full trial log.
Invalid generations remain in accuracy, schema, and coverage denominators and
their elapsed times remain in latency statistics. Zero returned wrong actions
from a mostly invalid JSON baseline is not evidence of a useful or safe executor.
`json_code` is a disclosed supplementary output-format control, introduced after
an earlier Qwen evaluation; it is not part of the original three-method protocol.
No Gemma-specific prompt tuning, constrained decoding, code/ID repair, or fence
stripping was added for this evaluation.

## Input size, memory, and cache validation

All requests contained 2–6 application candidates, plus the two reserved choices;
utterances were 8–34 characters and serialized states were 65–336 characters.

| Method | Prompt tokens | Same-page reused tokens | Page-update reused tokens | Generated tokens |
| --- | ---: | ---: | ---: | ---: |
| direct | 487–629 | 474–614 | 300 | None |
| code | 487–629 | 474–614 | 300 | 1 |
| json | 506–648 | 493–633 | 319 | 8–13 |
| json_code | 510–652 | 497–637 | 323 | 6–11 |

Cold-KV trials reused zero tokens. The audit confirmed actual expected prefix
reuse in **112/112 same-page and 112/112 page-update trials**, with fresh suffix
computation. These are KV snapshots, not cached final answers.

The measured process peak RSS was **11.52 GiB**, MLX peak allocation **14.36 GiB**,
maximum recorded active MLX memory **13.97 GiB**, and maximum retained prefix
snapshots **500.31 MiB**. The maximum allocator cache observed in measured trial
snapshots was **3.62 GiB**; the final snapshot after parity was **5.89 GiB**. These
are process/allocator observations, not additive or independent per-call memory
costs. RSS and MLX memory overlap. The loaded-model run separately recorded model
initialization at **5672.3 ms**; this is not the full process cold-start measure.

The [parity log](../benchmarks/results/gemma4-test/parity.jsonl) contains 28 rows,
each comparing same-page and changed-page scores against fresh computation:
**56/56 comparisons passed**, with identical winning IDs. The recorded limits
were absolute returned-logit difference ≤ 0.5 and restricted-score difference
≤ 0.1, with relative tolerance zero. Separately,
[three real-model integration tests](../benchmarks/results/gemma4-model-tests.json)
passed in 41.62 seconds total. Their rotating-cache case used a 1,741-token stable
prefix and measured maximum logit/score differences of 0.0 for both same-page and
page-update comparisons. This does not verify every prompt up to the 4,096-token
limit, other conversions, batching, or multimodal inputs.

## Separate process cold start

These are **three fresh Python processes per method**, 12 total, using only
`test-close-player`. Parent wall time includes interpreter startup, model loading,
the first decision, process shutdown, and result collection. OS filesystem caches
were not flushed. Three repetitions are insufficient for stable p95 estimates,
and this one request adds no independent semantic-quality coverage.

| Method | Parent p50 ms | Parent p95 ms | Correct / 3 | Schema valid / 3 | Rejected / 3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 7933.0 | 8465.9 | 3 | 3 | 0 |
| code | 8621.1 | 10052.9 | 3 | 3 | 0 |
| json | 9041.5 | 10456.7 | 0 | 0 | 0 |
| json_code | 8784.9 | 9284.6 | 0 | 0 | 0 |

There were no runtime failures or returned wrong actions. All three JSON attempts
returned `{"candidate_id":"2"}` and all three JSON-code attempts returned a fenced
`{"choice":"2"}`; all six remain schema failures. The direct/code enum coverage
was 3/3; JSON/JSON-code coverage was 0/3. There were no boolean requests. Prompt
length was 571–594 tokens across formats, with zero prefix reuse. The cold workers
do not record candidate/utterance/state-size columns; the named frozen fixture
remains the source for those inputs. Peak RSS across workers was 11.98 GiB and
peak MLX allocation 13.88 GiB, with no saved prefix snapshots.

## Development boundary and reproduction

The [24-attempt smoke run](../benchmarks/results/gemma4-moe-smoke/summary.json)
used two development cases, four methods, and three cache conditions. The
[64-attempt development run](../benchmarks/results/gemma4-dev/summary.json)
used all 16 development cases and four methods in the same-page condition. They
are independent recorded runs, not extra frozen-test trials. Their output and
failures remain unchanged. The frozen test retained the existing threshold and
semantic prompt. Any future model-specific tuning needs a separately declared
development procedure and subsequent held-out evaluation.

Use the verified checkpoint and a new output directory for every run. For an
exact source reproduction, use a separate checkout at `ba98b71`, install the
pinned dependencies, and run one model job at a time:

```sh
export MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit
python -m benchmarks.run --model "$MODEL" --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --repeats 1 --output runs/gemma4-dev-reproduction
python -m benchmarks.run --model "$MODEL" --split test \
  --modes direct code json json_code --repeats 1 --parity \
  --output runs/gemma4-test-reproduction
python -m benchmarks.cold_start --model "$MODEL" --split test \
  --modes direct code json json_code --repeats 3 \
  --output runs/gemma4-cold-reproduction
python -m benchmarks.audit runs/gemma4-test-reproduction --source-revision ba98b71
python -m benchmarks.audit runs/gemma4-cold-reproduction --source-revision ba98b71
JEV_TEST_MODEL="$MODEL" python -m pytest tests/test_model.py -q
```

The current [reporting script](../scripts/summarize_extended.py) can derive enum and
boolean summaries from those logs without altering them. See the complete
[evaluation protocol](evaluation.md) for metric definitions and timing boundaries.
