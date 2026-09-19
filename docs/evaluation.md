# Reproducing evaluations

The public fixtures are fictional, written specifically for this repository. They
contain no production exports, recordings, screenshots, transcripts, or derived
private examples. The 16 development cases and 28 frozen test cases have separate
utterances and IDs. `benchmarks/fixtures/manifest.json` records the exact SHA-256
hashes. The runner refuses changed fixtures. A small public set is useful for
regression checks; it does not establish general accuracy or safety.

The default margin threshold is **0.0**, fixed before test inference. No test
labels may be used to tune a prompt, threshold, model selection rule, or cache
tolerance and then described as an untouched test result. Development experiments
must precede the test run. Future tuning requires a new held-out split and a new
manifest. The checked-in tests distinguish model decisions from execution guards.

## Run the complete comparison

Run these commands from a source checkout after installing its development and
MLX dependencies. Set `MODEL` to an existing local MLX model directory. The runner
does not download weights or alter the shared model directory.

```sh
export MODEL=/path/to/local/mlx-model
python -m benchmarks.run --model "$MODEL" --split dev --output results/dev-v1
python -m benchmarks.run --model "$MODEL" --split test --repeats 3 \
  --output results/test-v1 --parity
python -m benchmarks.cold_start --model "$MODEL" --repeats 3 \
  --output results/process-cold-v1
```

Use a new output directory for every run; previous attempts cannot be overwritten.
`--limit 4` produces a clearly labeled smoke subset. `--modes direct code json` and
`--conditions kv_cold same_page_new_utterance page_update` choose cohorts;
`--cohorts` is an alias for `--conditions`. Defaults include all three of each.
With one repetition, a full test run makes 252 measured decisions plus recorded
preparation calls. Run one model at a time to avoid competing Metal workloads.
Record other active applications when interpreting results; the runner does not
stop them. Test accuracy uses all attempts; model errors and invalid outputs are
retained. JSON output can be large because each trial retains its evidence.

## What is compared

| Method | Output | Computation |
|---|---|---|
| `direct` | One tokenizer-validated candidate code mapped to a business ID | Official model forward and final-position logits restricted to allowed choices, including no-match and abstention |
| `code` | A single option code | Same model and same semantic/code prompt, official unconstrained greedy generation with `max_tokens=1` |
| `json` | `{"candidate_id":"..."}` | Same model and semantic state/policy, unconstrained greedy JSON generation with a 96-token limit |
| `json_code` (supplementary, opt-in) | `{"choice":"<option code>"}` | Same semantic state/policy/choices, unconstrained greedy JSON generation with a 96-token limit, then exact code-to-ID mapping |

The direct method's restricted vocabulary is an explicit modeling difference.
The one-code baseline can emit a noncandidate token; this is a schema failure,
not silently forced to the closest candidate. JSON must parse with exactly the
expected key and a currently allowed ID. Neither baseline uses a generated-output
grammar. MLX-LM may schedule lookahead work even for `max_tokens=1`; its completed
work is included in timing. The JSON method is ordinary autoregressive generation.
No method's output scores are calibrated correctness probabilities.

The supplementary `json_code` control was added **after** the original Qwen test
run revealed confusion between option codes and business IDs in JSON output.
It is a disclosed follow-up comparison, not part of the original preregistered
three-method run or an untouched blind evaluation. Its purpose is to avoid
claiming a quality advantage based on an unnecessarily difficult output format.
Only the requested output format and its parser differ: the semantic policy,
state, choices, rejection threshold, and original `code`/`json` prompts remain
unchanged. The original JSON failures remain in the original 252-trial report.
JSON-code generation remains autoregressive, and malformed objects or unknown
codes remain schema failures. No grammar forces a valid result.

Run development examples before the unchanged frozen test, keeping both outputs:

```sh
python -m benchmarks.run --model "$MODEL" --split dev --modes json_code \
  --output results/json-code-dev-v1
python -m benchmarks.run --model "$MODEL" --split test --modes json_code \
  --output results/json-code-test-v1
```

Defaults still select the original three methods. Explicitly passing
`--modes direct code json json_code` includes all four and produces 336 measured
decisions per full test repetition; `--modes json_code` alone produces 84.
Run metadata labels this supplementary control and records its origin.

All methods receive the same fixture state, candidate semantics, question, and
utterance. The prompt format differs only as needed for the requested output.
Mode/cohort/case order is shuffled with a fixed seed. The direct engine's margin
threshold and the baselines' generation configuration are recorded. Repetitions
reuse the same inputs, so they measure timing variation, not additional independent
quality samples. Do not inflate the apparent test-set size with repetitions.

| Cohort | Preparation and measured work |
|---|---|
| `kv_cold` | Weights already loaded; decision bypasses all prompt snapshots |
| `same_page_new_utterance` | Separate recorded request warms the same page; measured request uses a different utterance and recomputes its suffix |
| `page_update` | A recorded request warms a different earlier page/version; measured request uses the current state and changed candidates in the same cache namespace |
| `process_cold_start` | Separate Python process per attempt, loading weights and running the first fixture; interpreter startup, model load, inference and exit included |

The process cohort intentionally does not flush the OS filesystem cache. It must
not be labeled a machine boot or cold disk measurement. It uses only the first
fixture and reports that scope. Weights-loaded cohorts record load time separately.
Snapshot preparation latency is outside the measured decision interval, with its
full result/timing retained so prewarming cost remains visible. No final answers
are cached. Cache hits refer to token-prefix computation only.

## Metrics and artifacts

`trials.jsonl` records every completed attempt, its ground truth, raw prediction,
scores when available, elapsed wall time, cache information, input sizes, memory,
and any exception. Invalid outputs retain raw text. Preparation failures are
explicit failures rather than silently replaced with fresh successful decisions.
`summary.json` is checkpointed after each trial and labels incomplete runs.
`metadata.json` includes fixture hashes, model name, run configuration, dependency
versions, hardware, source commit/dirty status, and SHA-256 hashes of the prompt,
backend, contracts, engine, and benchmark implementation. Model configuration and
tokenizer hashes, quantization settings, and runtime identity are retained in
backend outputs. Absolute model paths and the home directory are redacted.

Metrics use these denominators:

- **Accuracy:** exact expected status and, for selections, business ID, divided by
  all attempts. No-match and abstain are distinct labels.
- **False action rate:** incorrect model selections divided by all attempts;
  the conditional rate among selections is also reported. A host blocking the
  action never turns it into a correct model prediction.
- **Raw choice accuracy / raw false action rate:** use `raw_selected_id` before
  the score-margin abstention policy, with the same all-attempt denominator.
  Reserved IDs map to their distinct no-match/abstain statuses. A wrong raw
  action followed by policy abstention remains a raw error and raw false action;
  a correct raw action followed by abstention is raw-correct but not a correct
  returned action. Invalid generated output, missing raw choice, and exceptions
  count as raw-incorrect and do not count as raw action selections. These fields
  separate model top-choice quality from both margin rejection and executor guards.
- **Rejection rate:** valid no-match or abstain outputs divided by all attempts.
  Abstention is also reported separately.
- **Executable-request coverage:** correct selections divided by requests with
  an executable labeled action. A wrong selection does not count as coverage.
  Selection rate on executable requests is reported separately.
- **Schema validity:** valid allowed IDs or reserved rejection outcomes divided
  by all attempts. Exceptions and invalid generated output fail this metric.
- **Latency:** p50 and p95 with linear interpolation, grouped by method and
  cohort. Successful-call latencies include invalid semantic/schema outputs.
  Failed-call latencies have a separate distribution and count. Quality metrics
  always include failures. With small cohorts, percentiles are descriptive only.
- **Memory:** process lifetime peak RSS and available MLX active, peak, and cache
  memory. Peaks are cumulative within a process and are not independent per-call
allocation measurements; do not sum RSS and MLX memory as independent pools.

Earlier run summaries remain immutable. To calculate the added raw-choice fields
from their recorded trials without rerunning inference or overwriting evidence:

```sh
python -m benchmarks.recompute results/test-v1 --output results/test-v1-derived.json
```

The derived report records the source trial and metric-code SHA-256 hashes and
original completion state.
Reporting code can also call `benchmarks.metrics.summarize(rows)` or
`grouped_summary(rows)` directly. Existing status-based metrics retain their
original definitions; the derived report adds raw-choice metrics alongside them.

Before publication, compare reviewed copies with the original run and verify its
schedule, frozen labels, metric totals, retained invalid outputs, and actual
prefix reuse without loading a model:

```sh
python -m benchmarks.audit runs/example --public benchmarks/results/example \
  --source-revision '<recorded-source-commit>'
```

The audit exits unsuccessfully on incomplete runs, evidence-copy differences,
incorrect derived totals, missing preparation costs, or a declared cache cohort
without the expected reuse. Recorded model errors remain valid evidence and are
counted in its report. Derived metric reports are verified against the source
trial hash instead of being mistaken for immutable copies of original outputs.

The backend synchronizes actual MLX computations before returning. Outer wall
time includes request/result orchestration. Process cold-start wall time is
measured by the parent process. Model loading failures and subprocess timeouts
are preserved. Exceptions are never replaced by a guessed decision.

`--parity` writes `parity.jsonl`, comparing full-fresh candidate logits with a
same-page cached pass and a pass after a page update. Defaults are absolute
tolerance 0.5 and relative tolerance 0.0 for raw logits, maximum restricted-softmax
score difference 0.1, and the same winning code. These defaults match the optional
real-model tests and were set before frozen test inference. Each row records
tolerances, maximum absolute/score differences, both sets of scores, and whether
the winning code agrees. Any mismatch or exception makes the command exit with a
nonzero status; `summary.json` records parity pass/failure counts, and the run
remains incomplete until the requested parity phase finishes.
Report both numerical parity and decision parity. A numerically close tie can
still change the selected action. This check does not prove every model/cache
architecture correct. Deterministic stale-result execution tests are separate
from semantic model accuracy.

## Interpreting a release result

Publish the full frozen split, all methods and cohorts, failures, commands,
hardware, and dependency/model identity together. Compare against the strongest
measured baseline at an explicitly stated quality level. A small warm-prefix
number alone does not establish an overall advantage. State whether speed or
quality advantages were actually demonstrated; negative results are results.
Keep each model's measurements separate and distinguish real inference support
from a checkpoint that was merely found on disk. Browser demonstrations show
selected action, executed receipt, and DOM/state outcome separately; executor
guards cannot substitute for model quality evaluation.
