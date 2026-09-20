# Recorded results for 0.1

The completed three-model, four-method warm comparison is in the
[36-case extended results](extended-results.md), under the
[fixed evaluation protocol](extended-evaluation-protocol.md). Direct accuracy was
31/36 for Gemma, 30/36 for Qwen, and 21/36 for GLM; wrong enum actions were
respectively 1/30, 1/30, and 8/30. Boolean accuracy is separate: 5/6, 6/6, and 2/6.
All three made action errors; the original Qwen zero-error observation below did
not generalize to the new cases. Gemma's separate extended cache phase completed
108 decisions and all 72 cached/fresh comparisons, with the same 31/36 correct
and 1/30 wrong enum actions in each condition. All 1,096 measurements planned in
the additional campaign are complete; repeated conditions are not new quality
examples. The latest core check is 161 passed. The rebuilt wheel passed a fresh
independent install and a real Gemma CLI call; all 14 runtime files match the
source and archive bytes. See [distribution verification](../benchmarks/results/extended-release-checks/distribution.json).

The [Gemma original-suite report](gemma4-results.md) separately records 26/28
correct, including one wrong filtered-first action among 26 enum requests.
Keep both datasets and their runtime revisions separate. This page preserves
the historical Qwen/GLM results and release verification below.

The project is now named **JEV MLX**. The historical Qwen/GLM measurements,
original release-candidate checks, screenshots, and recordings were collected under its former name,
**JEVKit MLX**. Their metadata still identifies `jevkit-mlx`, the `jevkit_mlx`
module, original source paths, and recorded commit/file hashes. Those evidence
files and media have not been rewritten or renamed to imply a new measurement.
Current reproduction commands use the `jev-mlx` CLI, the `jev_mlx` Python module,
and `JEV_MLX_MODEL`. Separate verification of the
renamed package is recorded in
[rename release checks](../benchmarks/results/rename-release-checks/verification.json).

On the original 28-case suite, the revised cache runtime produced consistent
local decisions across fresh and reused prefixes, with clear semantic limits.
Qwen direct decisions reached
**25/28 correct (89.3%)** in each cache condition, with warm-page **171.7 / 176.4 ms
p50 / p95** and no observed false actions. GLM reached **14/28 (50.0%)** with two
false actions per condition. Both checkpoints passed all 56 revised-cache parity
comparisons; numerical correctness does not establish semantic reliability.

All numbers below are measured attempts, not projections. The primary run,
its original JSON failures, and the later JSON format control are retained.
GLM's 112 warm-page measurements and original parity audit are complete: direct
quality was substantially worse, and **25/28 parity cases failed**. Fresh-process
cold-start measurements and a real Qwen-driven browser demonstration are also
complete, with original failed attempts retained where applicable.

The comparison tables in this report describe the **historical implementation**:
primary Qwen source hashes match `a743972`; supplementary JSON-code and original
GLM hashes match `0f49372`. Cache-boundary revision `579daf3` was introduced after
the GLM failures. Its separate Qwen and GLM verification runs each pass all 56
cache comparisons while preserving prior semantic outcomes. Old comparison
tables must not be represented as measurements of that revision or mixed with
new direct timings to calculate speedups.

## Environment and provenance

| Item | Recorded configuration |
|---|---|
| Hardware | Apple M2 Max, `Mac14,6`, 12 CPU cores, 64 GiB unified memory |
| System / Python | Darwin 25.6.0, arm64 / Python 3.13.2 |
| Checkpoint | Qwen3.5-9B-OptiQ-4bit, local revision `76b3310ab7aa52a34303c66fc928b6d7239c860c` |
| Quantization | Affine, default 4-bit, group size 64; recorded per-layer entries: 157 at 4-bit and 93 at 8-bit |
| Model/cache architecture | `qwen3_5`; official `ArraysCache` and `KVCache` |
| Dependencies | MLX / MLX-Metal 0.31.2, MLX-LM 0.31.3, Transformers 5.9.0, Tokenizers 0.22.2, NumPy 2.5.3 |
| Runtime bounds | 256-token prefill chunks, 4,096-token prompt limit, 512 MiB / 16-entry prefix cache, serial inference |
| Sampling / margin | Greedy baselines; one-code limit 1 token, JSON limit 96; direct margin threshold 0.0 |

The exact weight-shard hashes and upstream revisions are in
[checkpoint provenance](../benchmarks/results/checkpoints.json). The
[primary metadata](../benchmarks/results/qwen9b-test-v1/metadata.json) records
configuration/tokenizer hashes and eight source-file hashes. Those eight hashes
were checked against commit `a743972` and all matched. The original metadata's
Git commit field is null and its dirty flag is true; the verified file hashes,
rather than an invented clean-checkout claim, identify that run's implementation.

The 16 development and 28 frozen test fixtures are fictional and separate. The
test fixture SHA-256 is
`e86e2278a872ab37b2143a12b2e39fb6dde7a0ffac96afa6cc80c139ddfafce3`.
There are **16 executable enum requests, 10 enum rejection requests, and 2
selected boolean answers** in the test split. The legacy mixed selected
denominator is 18; it is not a count of 18 application actions.
Each method ran every test case once in each of three cache conditions. Thus,
84 rows per method still represent **28 unique quality examples**, not 84
independent examples. Timing percentiles use 28 calls per method/condition.
The fixed shuffle seed was 20260919. This is one run without statistical
confidence intervals, an isolated-device claim, or a machine-boot measurement.

## Interpreting the historical mixed metrics

Original summaries are unchanged. Their `executable_request_coverage` counts
all expected `selected` choices, including boolean answers; `false_action` and
`raw_false_action` likewise apply to all kinds. Tables below label those retained
values **mixed choice coverage** and **wrong choices**. Boolean errors must not
be described as application misoperations.

A [read-only derivation](../benchmarks/results/legacy-kind-breakdown.json) joins
preserved trial IDs to the verified original fixture kinds. For the revised
cache runtime, every condition has:

| Model | Enum wrong actions / enum requests | Correct executable enum coverage | Boolean accuracy | Retained mixed coverage |
|---|---:|---:|---:|---:|
| Qwen | 0/26 | 15/16 (93.8%) | 2/2 | 17/18 (94.4%) |
| GLM | 2/26 (7.7%) | 8/16 (50.0%) | 2/2 | 10/18 (55.6%) |

These are model choices before execution, not counts of actions performed.
The derivation verifies source hashes and leaves all original evidence intact.

## Development and frozen-test boundary

| Development run | Method / condition | Correct | Wrong choices (all kinds) | Mixed choice coverage | Incorrect cases |
|---|---|---:|---:|---:|---|
| [Initial](../benchmarks/results/qwen9b-dev-initial/summary.json) | Direct, same page | 14/16 | 1/16 | 9/10 | `dev-first`: selected `play_moss` instead of `play_copper`; `dev-unknown-title`: abstain instead of no-match |
| [Refined](../benchmarks/results/qwen9b-dev-refined/summary.json) | Direct, same page | 15/16 | 0/16 | 10/10 | `dev-unspecified`: no-match instead of abstain |
| [Later format control](../benchmarks/results/qwen9b-jsoncode-dev/summary.json) | JSON code, same page | 16/16 | 0/16 | 10/10 | None |

The general prompt's ordering was refined using development evidence, placing
state before candidate choices. The semantic prompt and 0.0 threshold were then
frozen for the primary test. No phrase-specific matcher or executor correction
was introduced. Original development trials remain available alongside summaries.

After seeing the primary test's JSON code-versus-business-ID confusion, an
additional `json_code` output-format control was introduced. It first ran on dev,
then on the same unchanged test fixtures. **This is a test-informed supplementary
comparison, not an untouched held-out test or preregistered baseline.** Its
semantic policy/state/candidates and threshold stayed unchanged, but its output
instruction changed. The [supplementary metadata](../benchmarks/results/qwen9b-jsoncode-test/metadata.json)
records this history and its distinct source hashes. The original JSON result
has not been replaced.

## Historical primary quality results

Quality was identical across the three conditions for each primary method. The
table reports one 28-case cohort; denominators repeat across all three cohorts.
Accuracy requires the correct rejection status as well as the correct selected ID.
Host execution guards are not involved in assigning correctness.

| Method | Exact accuracy | Raw-choice accuracy | Wrong choices / all requests | Rejection rate | Abstention rate | Mixed choice coverage | Schema validity |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct, returned decision | 25/28 (89.3%) | 26/28 (92.9%) | 0/28 | 11/28 (39.3%) | 1/28 (3.6%) | 17/18 (94.4%) | 28/28 |
| One-code generation | 26/28 (92.9%) | 26/28 (92.9%) | 0/28 | 10/28 (35.7%) | 0/28 | 18/18 (100%) | 28/28 |
| Original JSON business ID | 6/28 (21.4%) | 6/28 (21.4%) | 0/28 | 6/28 (21.4%) | 0/28 | 0/18 | 6/28 (21.4%) |

Across the primary 252 measured attempts, there were no runtime exceptions or
preparation exceptions. The 66 invalid JSON outputs are still failures of the
requested output contract, even though generation itself completed. Among valid
selections (including boolean answers), the wrong-choice rate was 0/51 for direct
and 0/54 for one-code; it is undefined for original JSON because that method made no valid selections.
Zero observed false actions on this small set does not establish a zero-error
system.

The difference between direct returned accuracy and raw-choice accuracy is
`test-first-reordered`. The correct `play_lunar`, `sort_title`, and `__no_match__`
all had raw logit **22.25**. The stable raw tie-break selected `play_lunar`, while
the predeclared zero-margin rule returned abstention. Count the returned abstention
as a missed executable request; do not upgrade it because the raw tie-break
happened to match. [Derived raw metrics](../benchmarks/results/qwen9b-test-v1/raw-metrics.json)
are recomputed from preserved predictions without new inference or threshold
changes, and identify their source-trial hash.

## Historical latency under three cache conditions

Values are outer wall time in milliseconds, including completed and synchronized
MLX work plus request/result orchestration. They exclude model loading. Preparation
calls are recorded separately and excluded from the measured decision interval.
Each cell is **p50 / p95**, with 28 calls per cell.

| Method | Weights loaded, KV cold | Same page, fresh utterance | First decision after page update |
|---|---:|---:|---:|
| Direct | 2,447.5 / 3,751.7 | 196.3 / 202.7 | 1,196.3 / 1,678.9 |
| One-code generation | 2,794.7 / 3,243.2 | 445.4 / 693.9 | 1,490.0 / 2,248.8 |
| Original JSON business ID | 2,833.8 / 3,524.2 | 604.3 / 1,304.8 | 1,662.2 / 2,603.5 |
| Supplementary JSON code, test-informed | 2,666.6 / 4,271.9 | 529.4 / 953.6 | 1,615.9 / 2,834.7 |

Compared with one-code generation, direct p50 was about 1.14× faster with cold
KV, 2.27× with a reused page, and 1.25× after a page update. Direct cold-KV p95
was **slower**, and direct returned executable coverage was lower. These are
different quality/latency tradeoffs, not an unqualified dominance claim. No
fixed 100 ms performance target was met by these p50 values.

The one-code baseline uses official `stream_generate(max_tokens=1)`, whose
pipeline can schedule next-step lookahead work; synchronization includes it.
Direct scoring takes final-position logits without generating a continuation.
An optimized one-step argmax using the same official model can share that direct
computation. The measured difference therefore does not prove an exclusive
algorithm, new model architecture, advantage over every possible one-code
implementation, or reproduction of JEV's unpublished method.

Input scale was 2–6 application candidates plus two reserved outcomes, utterances
of 8–34 characters, and serialized state sizes of 65–336 characters. Direct/code
prompts were 478–623 tokens; original JSON used 495–640, and supplementary JSON
code used 500–645. Direct warm-page calls reused 465–607 tokens and recomputed
13–18 tokens. Page-update calls reused the 300-token stable system prefix and
recomputed 178–323 tokens. No completed answer was reused. The primary run retains
168 separate preparation records; the supplementary run retains 56.

## Every observed error family

Each error listed below occurred in all three cache conditions. All individual
attempts, including raw output, are in the
[primary trials](../benchmarks/results/qwen9b-test-v1/trials.jsonl) and
[supplementary trials](../benchmarks/results/qwen9b-jsoncode-test/trials.jsonl).

| Method | Case | Expected | Observed |
|---|---|---|---|
| Direct and one-code | `test-close-ambiguous` | Abstain: “Close it” with two open windows and no focus | No-match |
| Direct and one-code | `test-vague-course` | Abstain: “Play something” with several available courses | No-match |
| Direct only | `test-first-reordered` | Select `play_lunar` from current reversed visible order | Abstain because of the three-way logit tie described above |
| Supplementary JSON code | `test-close-ambiguous` | Abstain | No-match |
| Supplementary JSON code | `test-vague-course` | Abstain | Selected `play_glass`: a false action |

The original JSON baseline emitted valid JSON syntax containing internal option
codes where the requested `candidate_id` had to be a business ID. The parser
correctly kept these outputs invalid. All 22 affected unique cases and emitted
values are listed here; each occurred three times, yielding **66/84 invalid
attempts**:

| Case | Emitted `candidate_id` value | Case | Emitted `candidate_id` value |
|---|---|---|---|
| `test-pause-permuted` | `"3"` | `test-boolean-true` | `"0"` |
| `test-paused-resume` | `"0"` | `test-close-player` | `"2"` |
| `test-ready-pause` | `"0"` | `test-loading-close` | `"0"` |
| `test-close-settings` | `"1"` | `test-missing-course` | `"6"` |
| `test-close-question` | `"4"` | `test-science-filter` | `"3"` |
| `test-close-ambiguous` | `"2"` | `test-close-library` | `"5"` |
| `test-first-original` | `"0"` | `test-sort-title` | `"4"` |
| `test-first-reordered` | `"2"` | `test-open-feature` | `"0"` |
| `test-play-named` | `"1"` | `test-first-filtered` | `"1"` |
| `test-boolean-false` | `"1"` | `test-rewind` | `"1"` |
| `test-vague-course` | `"6"` | `test-return-library` | `"3"` |

This output-format confusion makes original JSON a weak quality comparator; it
does not show that structured generation is inherently unable to solve the task.
The supplementary `{"choice":"<code>"}` control restored 28/28 schema validity
and 26/28 accuracy per condition, with 18/18 mixed choice coverage. It nevertheless
made one wrong action: 1/28 among all kinds (3.6%), or 1/19 among all selected
choices including boolean answers (5.3%). It rejected 9/28 (32.1%) and never
abstained. Across its 84 attempts there were three false
actions, six incorrect results, and no runtime or preparation exceptions.

## Historical Qwen cache parity and memory

The primary [parity record](../benchmarks/results/qwen9b-test-v1/parity.jsonl)
contains 28 cases, each compared with full-fresh inference after same-page reuse
and after a page update: **56/56 comparisons passed**, without exceptions.
Maximum observed absolute raw-logit difference was **0.0**; maximum restricted
score difference was **0.0**; all raw winning IDs agreed. Declared acceptance
limits were absolute logit tolerance 0.5, relative tolerance 0.0, restricted-score
tolerance 0.1, and identical raw selection. Measured equality is specific to
these inputs and the recorded checkpoint/runtime; it is not proof for every
hybrid model, input length, or future framework version.

| Process measurement | Primary Qwen run, including parity | Supplementary JSON-code run |
|---|---:|---:|
| Engine construction/load wall time | 3,602.5 ms | 2,532.1 ms |
| MLX active memory immediately after load | 5.63 GiB | 5.63 GiB |
| MLX active memory at end | 6.08 GiB | 6.08 GiB |
| MLX lifetime peak memory | 6.74 GiB | 6.74 GiB |
| Recorded lifetime process peak RSS | 4.17 GiB | 6.24 GiB |
| MLX allocator cache at end | 3.90 GiB | 0.13 GiB |
| Largest prefix snapshot cache reported in measured trials | 0.473 GiB | 0.475 GiB |

These are distinct process runs and cumulative peaks, not per-method allocation
comparisons. MLX allocator cache is distinct from the bounded prefix-snapshot
cache. RSS and MLX figures overlap within unified memory and must not be summed
as independent pools. Load times above exclude fresh interpreter/process startup;
they are not the requested process-cold-start result. Full byte counts are in
each run's metadata and trial records.

## Second checkpoint: GLM-4.7-Flash-4bit

GLM loaded and produced real local outputs, but **successful loading did not
produce a usable general direct-choice model under this prompt**. Its direct
accuracy was 14/28 (50.0%) with two false actions, despite a warm-page p50 of
191.4 ms. Retaining this negative result is part of the model comparison.

The checkpoint revision is `1454cffb1a21737e162f508e5bc70be9def89276`, architecture
`glm4_moe_lite`, affine 4-bit quantization with group size 64, and official
`KVCache`. Hardware and dependency versions match the Qwen runs. Its
[metadata](../benchmarks/results/glm-test/metadata.json) records implementation
and checkpoint identities. No semantic prompt or threshold was tuned for GLM.
The JSON-code mode remains the previously disclosed, test-informed output-format
control, not an independently preregistered comparison.

The [GLM development run](../benchmarks/results/glm-dev/summary.json) completed
32/32 measurements: direct scored 7/16 (43.8%), with two false actions and 4/10
mixed choice coverage; JSON code scored 1/16 (6.3%), with 12 invalid outputs
and 1/10 coverage. Both had zero runtime exceptions. These poor development
results were retained, and the unchanged configuration was evaluated on test.

The original test run is **complete**, with 112/112 measured calls covering four
methods and all 28 fixtures **only in the same-page/fresh-utterance condition**,
plus all 28 parity cases. Every measured call reported a state-prefix hit.
Cold-KV and page-update latency cohorts were not part of this historical GLM
comparison. All measured trial records are available in
[GLM trials](../benchmarks/results/glm-test/trials.jsonl).

| Method | Exact accuracy | Raw-choice accuracy | Wrong choices / all requests | Rejection / abstention | Mixed choice coverage | Schema validity | Warm p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct returned decision | 14/28 (50.0%) | 15/28 (53.6%) | 2/28 (7.1%) | 16/28 / 12/28 | 10/18 (55.6%) | 28/28 | 191.4 / 652.5 |
| One-code generation | 5/28 (17.9%) | 5/28 (17.9%) | 0/28 | 8/28 / 7/28 | 3/18 (16.7%) | 11/28 (39.3%) | 335.9 / 810.7 |
| JSON business ID | 19/28 (67.9%) | 19/28 (67.9%) | 3/28 (10.7%) | 3/28 / 0/28 | 16/18 (88.9%) | 22/28 (78.6%) | 576.8 / 1,900.1 |
| Supplementary JSON code | 5/28 (17.9%) | 5/28 (17.9%) | 0/28 | 9/28 / 8/28 | 3/18 (16.7%) | 12/28 (42.9%) | 507.1 / 1,558.8 |

Direct raw choices contained **three** wrong action proposals (3/28 across all
kinds), while returned decisions contained two. On `test-content-not-executable`, the raw choice was
`open_library`, tied at logit 104.5 with `open_settings`; the zero-margin rule
returned abstention. That result was still incorrect because the expected status
was no-match. On `test-close-library`, the raw correct action tied with no-match
at logit 114.0 and was also rejected. The raw-versus-returned distinction neither
hides the model's incorrect action proposal nor credits the rejection as a
correct model answer.

All **69 incorrect measured outcomes** are retained: direct 14, code 23, JSON 9,
and JSON code 23. This includes **39 schema failures**: code 17, JSON 6, JSON code
16. There were no runtime or preparation exceptions. Direct's remaining errors
consisted of eight rejected executable requests and four incorrect rejection
labels, alongside its two false actions. The one-code method additionally had
six valid-but-incorrect outcomes; supplementary JSON code had seven. Original
JSON's three non-schema errors were all false actions.

| False-action method | Case | Observed action and error |
|---|---|---|
| Direct | `test-close-ambiguous` | `close_settings` although “Close it” has no focused target and should abstain |
| Direct | `test-loading-pause` | `back_to_library` although pause is unavailable during loading and should return no-match |
| JSON business ID | `test-close-ambiguous` | `close_library` instead of abstention |
| JSON business ID | `test-loading-pause` | `close_player` instead of no-match |
| JSON business ID | `test-first-reordered` | `play_glass` instead of the currently first visible `play_lunar` |

Among all selected choices, including boolean answers, wrong-choice rates were
2/12 (16.7%) for direct and 3/19 (15.8%) for JSON. Code and JSON-code methods each
selected only three choices; their zero wrong-choice count must be read with
their 16.7% mixed choice coverage. GLM often emitted business-ID text where an internal code was required:
the one-token baseline produced fragments such as `close`, `play`, and `__`,
while JSON code produced objects such as `{"choice":"close_settings"}`. These
remain invalid; no parser repaired them into apparently correct answers. Every
raw response is preserved in the trial artifacts.

GLM direct/code prompts were 449–594 tokens, JSON 466–611, and JSON code 471–616,
with the same 2–6 candidate and 8–34 utterance-character ranges as Qwen. Engine
construction/load took 5,938.1 ms. Immediately afterward MLX active memory was
15.70 GiB. Across the 112 measured calls, recorded maxima were 16.21 GiB active
MLX memory, 16.59 GiB lifetime MLX peak, 12.25 GiB lifetime process RSS, and
2.44 GiB MLX allocator cache. The maximum reported prefix-snapshot cache was
536,837,760 bytes, just below its 512 MiB limit. After the complete parity stage,
the lifetime MLX peak and RSS were unchanged; active MLX memory was 17,352,979,752
bytes and its allocator cache was 5,539,180,070 bytes. These are distinct memory
measurements, not isolated per-method allocations or fresh-process startup.

The original [GLM parity audit](../benchmarks/results/glm-test/parity.jsonl)
completed with **3/28 cases passing and 25/28 failing**. A case passes only when
both cache conditions meet every declared numerical and selection criterion.

| Original GLM cache condition | Raw-logit maximum absolute difference | Restricted-score maximum absolute difference | Raw winning ID agreement | Logit tolerance passed | Score tolerance passed |
|---|---:|---:|---:|---:|---:|
| Same page, full snapshot | 0.0 | 0.0 | 28/28 | 28/28 | 28/28 |
| Page update, nearest common prefix | 5.5 | 0.4214759775 | 27/28 | 5/28 | 19/28 |

The winning ID changed on `test-rewind`. The declared limits remained logit
absolute tolerance 0.5, relative tolerance 0.0, score tolerance 0.1, and identical
raw selection. No tolerance was relaxed to turn these failures into passes. The
[artifact integrity audit](../benchmarks/results/evidence-audit-glm-original.json)
passed its completeness/hash checks and retained **25 parity warnings**. An
integrity pass means the evidence is intact, not that numerical parity passed.

The identified trigger was reuse of an arbitrarily trimmed common token prefix
after a page update. Revision **`579daf3`** now requests explicit full page/system
snapshots in separate namespaces, rejects partial snapshot matches, and retains
official `LRUPromptCache` with a shared capacity budget. Semantic prompt, threshold,
and weights were unchanged. A framework bug or floating-point root cause has
not been established. A three-case development smoke passed its parity checks;
it does not replace complete verification on the frozen fixtures.

All original failures remain published. Separate direct-scoring reruns cover
all 28 cases, all three cache conditions, and full parity for both GLM and Qwen.
Both reruns are complete below. Historical tables identify the earlier runtime
and must not be relabeled as revised-runtime results.

## Cache-boundary revision: separate GLM verification

The [GLM revised-runtime run](../benchmarks/results/glm-cache-fixed/summary.json)
is complete: **84/84 direct decisions** across all three cache conditions, plus
28 parity cases comparing two reuse conditions each. Its eight recorded source
hashes match `579daf3`, as checked in the
[integrity audit](../benchmarks/results/glm-cache-fixed/integrity-audit.json).
[Metadata](../benchmarks/results/glm-cache-fixed/metadata.json) also retains the
dirty-worktree flag rather than claiming a clean checkout.
The semantic prompt, weights, fixture labels, threshold, and parity tolerances
were unchanged. This is post-failure engineering verification on the existing
frozen fixtures, not a newly unseen quality test.

| Revised GLM direct condition | Exact accuracy | Raw-choice accuracy | Returned / raw wrong choices (all kinds) | Mixed choice coverage | p50 / p95, ms | Observed prefix reuse |
|---|---:|---:|---:|---:|---:|---|
| Weights loaded, KV cold | 14/28 (50.0%) | 15/28 (53.6%) | 2/28 / 3/28 | 10/18 (55.6%) | 1,837.6 / 2,154.5 | 28/28 cold; 0 reused tokens |
| Same page, fresh utterance | 14/28 (50.0%) | 15/28 (53.6%) | 2/28 / 3/28 | 10/18 (55.6%) | 147.8 / 170.6 | 28/28 state hits; 443–585 reused tokens |
| First decision after page update | 14/28 (50.0%) | 15/28 (53.6%) | 2/28 / 3/28 | 10/18 (55.6%) | 927.4 / 1,246.5 | 28/28 prefix hits; 285 reused tokens |

All 84 candidate-logit dictionaries exactly match the corresponding original
GLM same-page direct reference. Consequently the same semantic errors remain:
each condition has 16 rejections, including 12 abstentions, two returned false
actions, and three raw false-action proposals. Schema validity is 28/28 in each
condition, with no runtime exceptions. Numerically repairing cache reuse did
not improve the model's understanding or justify executing its choices.

The [revised parity record](../benchmarks/results/glm-cache-fixed/parity.jsonl)
passes **28/28 cases, or 56/56 comparisons**. Same-page and page-update comparisons
both have maximum absolute logit difference **0.0**, maximum restricted-score
difference **0.0**, and 28/28 raw winner agreement. This addresses the observed
cache-boundary failure on these fixtures; it is not universal model validation.
GLM is **not recommended for direct action execution with the current semantic
prompt**, despite passing this numerical check.

These new direct timings must not be divided into historical one-code or JSON
timings to claim a speedup: the implementation and process run changed, and those
baselines were not rerun in this verification cohort. The historical comparison
remains the recorded full-split comparison among methods; later startup trials
cover only one fixture.

## Cache-boundary revision: separate Qwen verification

The [Qwen revised-runtime run](../benchmarks/results/qwen9b-cache-fixed/summary.json)
completed **84/84 direct decisions** and all 28 parity cases. Its metadata records
HEAD `f79c97f` and a dirty worktree, while the eight hashed runtime/benchmark source
files all match `579daf3`; the
[integrity audit](../benchmarks/results/qwen9b-cache-fixed/integrity-audit.json)
verifies those matches and public artifact copies. This distinguishes measured
code from an incidental documentation/publication commit.

| Revised Qwen direct condition | Exact accuracy | Raw-choice accuracy | Returned / raw wrong choices (all kinds) | Mixed choice coverage | p50 / p95, ms | Observed prefix reuse |
|---|---:|---:|---:|---:|---:|---|
| Weights loaded, KV cold | 25/28 (89.3%) | 26/28 (92.9%) | 0/28 / 0/28 | 17/18 (94.4%) | 2,159.9 / 2,406.6 | 28/28 cold; 0 reused tokens |
| Same page, fresh utterance | 25/28 (89.3%) | 26/28 (92.9%) | 0/28 / 0/28 | 17/18 (94.4%) | 171.7 / 176.4 | 28/28 state hits; 465–607 reused tokens |
| First decision after page update | 25/28 (89.3%) | 26/28 (92.9%) | 0/28 / 0/28 | 17/18 (94.4%) | 1,050.2 / 1,294.5 | 28/28 prefix hits; 300 reused tokens |

Every one of the 84 raw-score dictionaries exactly matches its original primary
Qwen case and cache condition. Each revised condition therefore retains the two
no-match/abstain confusions and the rejected three-way tie on
`test-first-reordered`. Each has 11 rejections, including one abstention, and
28/28 schema validity. All runtime calls completed without exceptions. The raw
correct tie-break is still not counted as a correct returned action.

The [Qwen revised parity record](../benchmarks/results/qwen9b-cache-fixed/parity.jsonl)
passes **28/28 cases, or 56/56 comparisons**: maximum logit and restricted-score
differences are both **0.0**, with 28/28 raw winner agreement in each reuse
condition. This is regression verification on existing frozen fixtures, not a
new independent semantic test. No prompt, threshold, or acceptance tolerance
was changed to obtain these outcomes.

No one-code or JSON baseline was rerun across the full test split in this revised
cohort. Its direct timings describe this run only; earlier full-split same-model
comparisons remain historical. The preserved baseline showed higher returned
coverage because direct abstained on an exact tie, so lower direct latency should
not be advertised as unconditional quality/performance dominance.

## Fresh-process cold-start measurements

Separate sequential subprocess runs completed for both checkpoints under the
revised runtime: [Qwen](../benchmarks/results/qwen9b-cold/summary.json) has 12
attempts, three per method; [GLM](../benchmarks/results/glm-cold/summary.json) has
eight, two per method. Their recorded runtime source hashes match `579daf3`.
Every attempt used a fresh Python process, loaded model weights, and evaluated
only the first test fixture, `test-close-player`. **The OS filesystem cache was
not flushed.** These are neither cold-disk nor machine-boot measurements, and
one repeated fixture does not measure general semantic accuracy.

The table separates median engine construction/load time (`load_wall_ms`), median
completed first-decision backend time, and parent-process wall time. Parent wall
includes interpreter startup, loading, the decision, process exit, and collection
overhead. Medians of separate components need not sum to the parent median.
All values are milliseconds. With **n=2 or n=3**, p95 is only an interpolated
description of these few attempts, not a stable tail-latency estimate.

| Checkpoint / method | Attempts | Engine-load p50 | First-decision p50 | Parent process p50 / p95 | Outcome on the one repeated fixture |
|---|---:|---:|---:|---:|---|
| Qwen direct | 3 | 2,473.3 | 2,213.3 | 4,897.3 / 4,928.1 | 3 correct selections |
| Qwen one code | 3 | 2,498.8 | 4,230.9 | 6,750.8 / 7,186.3 | 3 correct selections |
| Qwen JSON business ID | 3 | 2,467.5 | 3,157.5 | 5,803.0 / 7,464.4 | 3 invalid business IDs |
| Qwen JSON code | 3 | 2,508.4 | 3,247.1 | 5,948.1 / 7,396.2 | 3 correct selections |
| GLM direct | 2 | 5,369.1 | 3,014.9 | 8,726.6 / 8,848.2 | 2 incorrect abstentions |
| GLM one code | 2 | 5,575.8 | 3,256.1 | 9,162.7 / 9,391.8 | 2 invalid codes |
| GLM JSON business ID | 2 | 5,635.2 | 4,123.9 | 10,112.0 / 10,674.6 | 2 correct selections |
| GLM JSON code | 2 | 6,521.0 | 4,691.3 | 11,590.5 / 11,878.0 | 2 invalid codes |

All 20 subprocesses exited with code 0 and no runtime exception or timeout.
That is **not** 20 correct decisions. The seven format failures were Qwen JSON's
three `{"candidate_id":"2"}` outputs, GLM one-code's two `close` fragments, and
GLM JSON-code's two `{"choice":"close_player"}` outputs. GLM direct abstained
twice when `close_player` was requested. These outcomes remain incorrect, yielding
nine unsuccessful semantic/format outcomes overall. Raw output, component times,
per-process memory, return code, and stderr are retained in the
[Qwen cold trials](../benchmarks/results/qwen9b-cold/trials.jsonl) and
[GLM cold trials](../benchmarks/results/glm-cold/trials.jsonl).

These startup trials are reported separately from the 28-case quality tables.
They do not repair a poor full-split baseline, establish a new cross-method
speedup, or increase the number of independent semantic test examples.

## Real browser demonstration and execution evidence

The Qwen-backed Morrow Studio run completed in Chromium 153.0.8010.12 with
**16/16 accepted raw model choices, 16/16 correct execution outcomes, 10 actual
model-selected DOM click receipts, and zero recorded browser errors**. Read the
[complete transcript](assets/browser-demo/browser-transcript.json), watch the
[original WebM recording](assets/browser-demo/video/page@9986ccf6fcac324ee3a7302c87bf305e.webm),
or inspect the [initial desktop](assets/browser-demo/01-desktop.png),
[filtered library](assets/browser-demo/02-library.png),
[course player](assets/browser-demo/03-course-player.png),
[player control receipt](assets/browser-demo/03b-player-control.png), and
[stale-result screen](assets/browser-demo/04-stale-protection.png). The initial
desktop and player-control images were visually inspected. The content and player
are simulated; the model inference, browser buttons, state transitions, and
receipts are real.

The 16 browser cases are a separate integration demonstration, **not a replacement
for the frozen quality benchmark**. For decline scenarios, the browser acceptance
criteria allow either no-match or abstention. The strict benchmark distinguishes
them. In particular, the browser accepted no-match for “Do the thing”; this must
not erase the strict benchmark's ambiguity-label errors or turn browser 16/16
into a general accuracy claim. Raw model correctness is checked separately from
execution correctness; an executor blocking a wrong model choice cannot make
that choice correct.

| Browser scenario | Observed model choice and browser outcome |
|---|---|
| “Close it” with nothing open | No-match, no action |
| Open the course library feature | `open.library`; library opens without playing content |
| Filter to science courses | `filter.science`; visible list changes |
| “First one” after filtering and reversing visible order | `play.orbit`; Orbit Field Notes opens |
| Ready / paused player controls | `player.pause`, `player.resume`, and `player.rewind` each execute; rewind changes position from 60 to 50 seconds |
| “Did you just close it?” and “Don't close the player” | Both no-match; player stays open |
| “Close it” in player, library, and notes | Respectively `close.player`, `close.library`, and `close.notes` execute |
| Nonexistent Advanced Volcano Knitting course | No-match, no invented target or action |
| Open field notes | `open.notes`; the second object opens |
| Vague “Do the thing” | No-match, accepted by the browser's broad decline criterion |
| “Pause it” while loading | Only `close.player` is offered; raw no-match and no execution receipt |

The visible-order setup includes a manually clicked reverse-sort control; the
transcript records setup clicks separately from model decisions. The harness
does not credit that manual setup as a model-selected action. Every selected
operation targets an existing allowlisted `data-action` button and reaches its
actual click handler, followed by server ticket validation and a state receipt.
This is evidence for this local application's controls, not arbitrary-site
automation or screenshot-based visual understanding. The browser run used Qwen;
GLM browser operation was not evaluated.

A separate state-change check proves that the decision request overlapped a page
update: the old version-16 result had raw choice `open.library`, returned
`status="stale"`, and did not execute after the page changed to notes. The
transcript records `decision_request_overlap_proven=true` and
`old_result_not_executed=true`. It also records
`gpu_compute_overlap_measured=false`: request/response overlap was demonstrated,
but overlap with a specific GPU computation interval was not independently
instrumented. No stronger timing claim is made.

The first recording attempt failed in the capture harness. Reading `inner_text`
from a `pre` inside collapsed details yielded empty text; finalization then mixed
absolute and relative video paths and failed before writing the transcript.
Its [post-run diagnostic note](assets/browser-initial/harness-failure-note.json),
[original recording](assets/browser-initial/video/page@d304bc025a5ace797e8ae81934275ddb.webm),
and original screenshots remain in `docs/assets/browser-initial`. The note is
explicitly not a model transcript, and no semantic success or failure is inferred
from the missing transcript. The harness was corrected to use `text_content`,
resolve output paths, write the transcript before video finalization, and reject
nonempty output directories. The second full run passed as reported above;
neither the model prompt nor the decision threshold was changed for that rerun.

## Local automated and HTTP validation

The latest [core-suite record](../benchmarks/results/extended-release-checks/core-tests.json)
reports **161 passed, zero failures/errors/skips**, with three model tests
excluded, in one local run with loopback access. Pytest reported 3.76 seconds;
the JUnit suite duration is 3.752 seconds. Ruff also passed. No GPU model was
loaded by this suite; remote GitHub CI has not been executed.

Historical 0.1 validation recorded 145 core tests. The separate
[rename check](../benchmarks/results/rename-release-checks/verification.json)
first passed 138 with seven sandbox-blocked HTTP fixture setups, then passed
eight HTTP tests with loopback access (one overlap): 145 distinct tests across
those attempts. Those records are preserved, not relabeled as the latest run.
Historical opt-in model integration tests passed **2 for Qwen in 23.01 seconds**
and **2 for GLM in 25.11 seconds** on local Python 3.13.2.
Model integration checks validate their specified invariants and do not replace
the full semantic results above, particularly GLM's poor action-selection quality.

A real localhost `/v1/decide` request selected `player.pause`, returned state
version 3, raw margin 4.75, and Qwen model/cache identity. Its completed engine
decision time was 3,428.9 ms with a cold prefix. That endpoint returns a decision;
the separate browser receipt evidence above demonstrates actual execution.

## Distribution and installation validation

The records in this section describe historical artifacts. The current
extended release has separate [wheel installation and real Gemma evidence](../benchmarks/results/extended-release-checks/distribution.json).
Its source archive includes the new fixtures and reports; artifact-side content
checks and hashes are in `dist/extended-v1/verification.json` and `SHA256SUMS`.
Earlier verification remains attached to its original artifacts.

A historical wheel and source distribution were built successfully. The final rebuilt
wheel was installed offline into a separate validation environment; its import
location was checked to ensure Python loaded the installed package rather than
the source checkout. All three packaged browser assets were present. Invoked
from outside the checkout, that installed wheel's CLI ran a real Qwen decision
with `--no-cache`, selected `player.pause` at state version 3, and reported
2,001.64 ms completed decision time. All 14 packaged source/static files matched
the reviewed checkout byte-for-byte. The earlier candidate smoke (2,257.93 ms)
and the final smoke are both retained in the
[release verification records](../benchmarks/results/release-checks/verification.json),
which identify the tested final wheel by SHA-256. This is an installation/inference smoke,
not an additional independent quality sample or benchmark cohort.

Archive inspection found no virtual environment, local cache, private run
directory, or model weights. The source archive contains public fixtures,
evaluation artifacts, documentation, screenshots, the real browser recording,
and the retained harness-failure note. Use the checksums delivered with the final
distribution to identify exact artifacts; byte sizes are not used as artifact
identity in this report.

These historical checks used the former package name; they do not by themselves
verify that renamed distributions import or install correctly. The separate
rename verification linked above covers that packaging change.

These are local release-preparation checks. GitHub CI is configured but has not
run remotely, and no public GitHub push or package-registry upload has been
performed. Publication requires the explicitly chosen destination and account
described in [releasing](releasing.md).

## Reproduce and interpret

Use the exact checkpoint revision in [model compatibility](models.md), an isolated
environment, the pinned dependencies, and a fresh output directory. The primary
implementation is identified by its recorded source hashes (matching `a743972`);
the supplementary mode belongs to the later recorded implementation. Current
source uses the cache-boundary revision described above; retain new source hashes
with reruns and do not treat them as reproductions of the old runtime timings.

```sh
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct code json --repeats 1 --margin-threshold 0 \
  --parity --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/reproduction-primary
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes json_code --repeats 1 --margin-threshold 0 \
  --output results/reproduction-json-code

# Revised-runtime direct verification; repeat separately for each checkpoint.
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct --repeats 1 --margin-threshold 0 --parity \
  --output results/reproduction-cache-fixed

# First fixture only: Qwen used 3 repetitions; GLM used 2.
python -m benchmarks.cold_start --model "$JEV_MLX_MODEL" \
  --modes direct code json json_code --repeats 3 \
  --output results/reproduction-process-cold
```

Read the [evaluation protocol](evaluation.md) for all metric denominators and
preparation rules. These results establish an executable experimental path and
identify concrete failure cases. They do not establish production safety,
calibrated scores, arbitrary-model compatibility, stable cross-machine latency,
or quality generalization beyond the small fictional fixture set.
