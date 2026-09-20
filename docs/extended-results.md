<p align="center"><a href="extended-results.zh-CN.md">简体中文</a> · <strong>English</strong></p>

# Six-domain extended evaluation

**The three-model warm comparison and Gemma's separate extended cache
verification are complete and audited:** 684 measured calls and 72 numerical
cache comparisons. These are repeated evaluations of 12 development and 36
test cases, not 684 independent quality examples.

All models made action errors on the new 36-case extension. These are direct
scoring results from the same frozen examples and same-page/new-utterance
condition; full four-method comparisons and failures follow.

| Model | Exact accuracy / 36 | Wrong enum actions / 30 | Correct action coverage / 15 | Boolean correct / 6 | Warm p50 / p95, ms |
|---|---:|---:|---:|---:|---:|
| Gemma | **31/36 (86.1%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **5/6 (83.3%)** | **168.9 / 556.5** |
| Qwen | **30/36 (83.3%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **6/6** | **194.8 / 407.5** |
| GLM | **21/36 (58.3%)** | **8/30 (26.7%)** | **9/15 (60.0%)** | **2/6 (33.3%)** | **170.6 / 330.5** |

Gemma's single-code baseline has one fewer exact match, three invalid outputs,
and no valid wrong action. Qwen direct and code agree on every test outcome,
including a wrong product selection. GLM's substantial semantic and format
failures make this configuration unsuitable for unattended action execution.
These small samples support neither a universal model ranking nor a fixed
100 ms latency claim.

This report concerns the [six-domain fixtures](../benchmarks/fixtures/extended-v1/README.md)
under the [fixed additional-run protocol](extended-evaluation-protocol.md).
The [original 28-case Gemma report](gemma4-results.md) and historical
[Qwen/GLM report](results.md) are different datasets/runs, not additional samples
to pool into these percentages.
The [complete additional-campaign audit](../benchmarks/results/extended-campaign.json)
covers all ten formal runs: **1096/1096 measured calls**, no runtime or
preparation errors, and **128/128 numerical cache comparisons**. Those totals
combine this extension with Gemma's original-suite and process-start runs;
they are workload totals, not an accuracy denominator or independent questions.

## Scope, provenance, and completion

The extension contains 12 development and 36 frozen test cases: documents,
local calendar drafts, file lists, music queues, product comparison, and local
settings. Each domain contributes six test cases. All are fictional English,
single-turn, single-step choices; no production data or external actions are
involved. The suite was written after historical project results were known,
then frozen before inference on its own cases. It is a post-development
extension, not a randomly sampled population study or the original unseen test.

The [manifest](../benchmarks/fixtures/extended-v1/manifest.json) records the freeze
at `2026-09-20T06:09:44.415784+00:00` and test SHA-256
`ad804e681bb6906c81dc5da316b61a805dd1dbfc8df20940c7b1cc22776aa25e`.
No prompt, threshold, label, or format parser was changed after seeing these
development or test outcomes. Poor baseline development results were retained
and evaluated with the same fixed configuration.

| Phase | Gemma | Qwen | GLM |
|---|---|---|---|
| Extended dev, 12 cases × 4 modes | Complete, 48/48 | Complete, 48/48 | Complete, 48/48 |
| Extended test, 36 cases × 4 modes | Complete, 144/144 | Complete, 144/144 | Complete, 144/144 |
| Extended direct, 3 cache conditions + parity | Complete, 108/108 + 72/72 comparisons | Outside this campaign | Outside this campaign |

The four-method comparison uses **same-page/new-utterance only**, one measured
repeat, seed `20260919`, and margin threshold `0.0`. Preparation requests are
recorded separately. A model's 144 test rows still represent **36 unique quality
examples**, not 144 independent questions. Different models and output modes do
not create new independent examples either.

The tested Gemma checkpoint is `gemma-4-26b-a4b-it-4bit`, verified conversion
revision `8bcfa0de037c2b1bfa323a1e8d1f0132243b9e87`: default affine 4-bit, group 64,
with 8-bit overrides. Full weight/tokenizer hashes are in
[checkpoint provenance](../benchmarks/results/gemma4-checkpoint.json).
Qwen uses `Qwen3.5-9B-OptiQ-4bit`, verified local conversion revision
`76b3310ab7aa52a34303c66fc928b6d7239c860c`, with mixed 4/8-bit quantization and
group size 64; see [checkpoint evidence](../benchmarks/results/checkpoints.json).
The same evidence records `GLM-4.7-Flash-4bit`, default 4-bit, group size 64.

The campaign uses **`ba98b71` as its canonical source revision**. All eight
recorded runtime/benchmark source hashes in each of the seven completed runs
match that revision. Recorded HEAD remains `7174e56` for Gemma dev/test and
`efed866` for Qwen, GLM, and Gemma cache, with dirty-worktree flags; these
documentation-era HEADs do not
replace the verified source identities or imply different inference code.

The host was Apple M2 Max (`Mac14,6`), 12 CPU cores, 64 GiB unified memory, Darwin
25.6.0 arm64, Python 3.13.2, MLX/MLX-Metal 0.31.2, MLX-LM 0.31.3, Transformers
5.9.0, Tokenizers 0.22.2, and NumPy 2.5.3. Model jobs run sequentially; the records
do not establish an otherwise isolated machine. Evidence and read-only derived
metrics are retained for [development](../benchmarks/results/extended-v1-gemma4-dev/derived-report.json)
and [test](../benchmarks/results/extended-v1-gemma4-test/derived-report.json).
Gemma audits passed, with no runtime or preparation exceptions. Qwen evidence
is retained separately for [development](../benchmarks/results/extended-v1-qwen9b-dev/derived-report.json)
and [test](../benchmarks/results/extended-v1-qwen9b-test/derived-report.json); both
runs also passed their integrity audits without runtime or preparation errors.
GLM [development](../benchmarks/results/extended-v1-glm-dev/derived-report.json)
and [test](../benchmarks/results/extended-v1-glm-test/derived-report.json) also
passed both audits with no runtime or preparation errors. All 576 measured
dev/test attempts across the three models are retained, including failures.

## Denominators and meaning

Test has 30 enum requests: 15 requiring an action and 15 requiring a decline.
Its six boolean questions expect two true answers, two false answers, and two
abstentions for missing evidence. Therefore 19 expected selected choices mean
**15 actions plus four factual answers**. Dev contains seven executable enum
requests, four enum declines, and one selected boolean answer.

Accuracy requires the correct status and selected ID, including the distinction
between `no_match` and `abstain`. Action errors below use enum requests only;
boolean mistakes are classification errors. The generic historical metric field
`false_action` can include either kind, so it is not used as an action-only
denominator here. Correct executable coverage counts correct enum action choices
before any executor. Restricting or rejecting execution cannot make a wrong
model answer correct.

These fixtures do **not** drive a browser or execute application effects.
An action ID is not an execution receipt. The historical Qwen browser recording
does not establish Gemma or GLM browser operation, and English fixture results
do not establish Chinese or mixed-language quality. Scores and margins remain
uncalibrated model outputs rather than correctness probabilities.

## Gemma development: all four methods retained

Each method ran all 12 development cases in the same-page condition. Raw-choice
and returned accuracy agree for these runs. The one-token code failure is
`ext1-dev-music-unspecified-track`: raw text `AB` instead of a valid abstain code.
JSON produced 12 invalid responses; JSON-code produced eight. All 21 incorrect
development outcomes were format failures, not runtime exceptions.

| Method | Exact accuracy | Wrong enum actions / 11 | Action coverage / 7 | Boolean correct / 1 | Valid format / 12 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 12/12 (100%) | 0/11 | 7/7 | 1/1 | 12/12 | 161.9 / 573.0 |
| One code | 11/12 (91.7%) | 0/11 | 7/7 | 1/1 | 11/12 | 433.4 / 850.8 |
| JSON business ID | 0/12 | 0/11 | 0/7 | 0/1 | 0/12 | 782.5 / 2049.6 |
| JSON code | 4/12 (33.3%) | 0/11 | 0/7 | 0/1 | 4/12 | 653.8 / 1836.1 |

Direct rejected 4/12 (33.3%), including 1/12 abstention (8.3%); code rejected
3/12 (25.0%), with no abstention; JSON had no valid declines; JSON-code rejected
4/12, including one abstention. Invalid output is not a successful rejection.
The complete [development trials](../benchmarks/results/extended-v1-gemma4-dev/trials.jsonl)
preserve the raw text for every failure.

## Gemma frozen test: one shared warm cohort

Each row below contains 36 measured test calls in the same process/run. Returned
and raw-choice accuracy agree; no zero-margin policy conversion changed the
direct outcomes. The small sample and one run provide descriptive percentiles,
not stable tail-latency or generalization estimates.

| Method | Exact accuracy / 36 | Wrong enum actions / 30 | Correct action coverage / 15 | Boolean correct / 6 | Valid format / 36 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | **31/36 (86.1%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **5/6 (83.3%)** | 36/36 | **168.9 / 556.5** |
| One code | 30/36 (83.3%) | 0/30 | 12/15 (80.0%) | 5/6 (83.3%) | 33/36 (91.7%) | 429.4 / 795.9 |
| JSON business ID | 0/36 | 0/30 | 0/15 | 0/6 | 0/36 | 641.4 / 2292.4 |
| JSON code | 14/36 (38.9%) | 0/30 | 1/15 (6.7%) | 2/6 (33.3%) | 17/36 (47.2%) | 579.4 / 2383.7 |

| Method | Rejected / 36 | Abstained / 36 | Invalid format / 36 | Runtime errors | Wrong selected boolean answers |
|---|---:|---:|---:|---:|---:|
| Direct | 18/36 (50.0%) | 5/36 (13.9%) | 0/36 | 0 | 1 |
| One code | 16/36 (44.4%) | 3/36 (8.3%) | 3/36 | 0 | 1 |
| JSON business ID | 0/36 | 0/36 | 36/36 | 0 | 0 |
| JSON code | 14/36 (38.9%) | 5/36 (13.9%) | 19/36 | 0 | 1 |

All 144 attempts are retained: 75 correct, **69 incorrect**, including 58 format
failures and 11 valid-but-wrong semantic outcomes. The four wrong selected
choices comprise one enum action in direct mode and the same wrong boolean
answer in three modes. They are not four distinct action mistakes. JSON's zero
action-error count accompanies zero valid responses; it is not evidence of safe
or useful decision making.

Direct is faster than the official single-code generation path in this measured
warm cohort, with one additional exact match. It also returns an incorrect
action where the code path produces invalid output. The paths therefore do not
have identical quality or failure behavior. Official generation can schedule
lookahead work even with `max_tokens=1`; synchronized timing includes it. This
comparison does not prove superiority over an equally optimized single-step
argmax implementation or establish a universal non-autoregressive advantage.

## Every Gemma direct test failure

Case names below omit the common prefix `ext1-test-`. Full states, allowed
choices, scores, expected labels, and outputs are in the
[test trials](../benchmarks/results/extended-v1-gemma4-test/trials.jsonl).

| Case | Expected | Raw winner and returned decision | Raw margin |
|---|---|---|---:|
| `documents-dismiss-editor` | Select `document.cinder.close` | `__no_match__` → no-match | 9.0625 |
| `music-queue-first` | Select `track.velour.play` | `track.marble.play` → selected wrong track | 6.0009 |
| `comparison-remove-focused` | Select `compare.mistral.remove` | `__abstain__` → abstain | 4.5156 |
| `comparison-unknown-warranty` | Abstain: warranty information unavailable | `false` → selected boolean answer | 16.1250 |
| `settings-vague-accessibility` | Abstain: several unspecified possible changes | `__no_match__` → no-match | 12.6758 |

The queue's visible first track is Velour Tide after filtering and sorting;
Marble Rain appears first among candidate codes but not in the visible queue.
This is an actual wrong action choice, without an executor correction. The
unknown-warranty response invents a negative factual answer from missing data;
its large margin does not make it reliable. The focused document and product
removal errors decline executable requests. The vague accessibility result is
a strict rejection-label error even though neither decline executes anything.

Direct accuracy by domain was documents 5/6, calendar drafts 6/6, files 6/6,
music 5/6, product comparison 4/6, and settings 5/6. These six-case slices are
descriptive; none is a certification of a whole application domain.

## Baseline semantic and format failures

The one-code path has three valid semantic errors: `documents-dismiss-editor`
returns no-match, `comparison-unknown-warranty` returns false, and
`settings-vague-accessibility` returns no-match. Its other three failures are
invalid one-token outputs:

| Case | Raw output | Required outcome |
|---|---|---|
| `music-queue-first` | `{"` | `track.velour.play` |
| `comparison-remove-focused` | `AB` | `compare.mistral.remove` |
| `music-unspecified-track` | `AB` | Abstain |

Business-ID JSON fails its exact contract on **all 36 cases**: 19 bare JSON
objects place an internal numeric code in `candidate_id`; 17 responses are
wrapped in Markdown fences. Among those fenced responses, 11 also use numeric
codes and six contain business IDs. Examples such as `{"candidate_id":"2"}`
or a fenced object with `"candidate_id":"playback.resume"` are retained as
invalid; the evaluator does not strip fences or reinterpret IDs after the fact.
The fenced business-ID response for `music-queue-first` also names the wrong
track, so removing formatting alone would not make every response correct.

JSON-code has 19 format failures: 18 fenced objects and one 96-token,
length-limited response on `music-queue-first`. That response starts with a
fenced `{"choice":"code:0"}` then continues with explanatory text. The other
three errors are valid responses: abstain for `comparison-remove-focused`, false
for `comparison-unknown-warranty`, and no-match for `settings-vague-accessibility`.
Only one of its 15 executable enum requests receives the correct action choice.

These strict failures measure the current fixed output instructions and parser.
They do not show that JSON generation is inherently unable to solve the task.
The JSON-code format was already a disclosed historical, test-informed control;
all four formats were fixed before this extension's inference. No repair parser
or newly tuned prompt replaces these failed baseline attempts.

## Qwen development: the unchanged configuration

Qwen completed 48/48 development calls. Its direct and code paths made the same
two errors: `ext1-dev-files-last-visible` selected `file.fern.open` instead of
`file.quartz.open`, and `ext1-dev-music-unspecified-track` returned no-match
instead of abstain. Direct margins were 1.5 and 2.375 respectively. JSON-code
made the same wrong file selection and emitted invalid `{"choice":"NO_MATCH"}`
for the ambiguous track. Business-ID JSON had six format failures, all numeric
codes in `candidate_id`; every valid JSON outcome was correct.

| Method | Exact accuracy / 12 | Wrong enum actions / 11 | Action coverage / 7 | Boolean correct / 1 | Valid format / 12 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 12/12 | 188.9 / 369.3 |
| One code | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 12/12 | 414.4 / 557.3 |
| JSON business ID | 6/12 (50.0%) | 0/11 | 1/7 | 1/1 | 6/12 | 545.6 / 1047.0 |
| JSON code | 10/12 (83.3%) | 1/11 | 6/7 | 1/1 | 11/12 | 579.1 / 880.6 |

Direct and code each rejected 4/12 without abstaining; JSON rejected 4/12,
including one abstention; JSON-code rejected 3/12 without abstaining. Across
methods there were 12 incorrect outcomes: seven format failures and five valid
semantic errors. The same wrong file choice in three modes is not three distinct
failure cases. All [development outputs](../benchmarks/results/extended-v1-qwen9b-dev/trials.jsonl)
were retained before the unchanged test run.

## Qwen frozen test: all four methods

Qwen completed 144/144 calls with no exceptions. Direct and code agree on every
returned status/ID across all 36 cases, including their six errors. Raw and
returned quality match; no measured direct result has a zero margin or a
threshold-induced status change. Zero margins in some preparation calls are
not test decisions and are not counted in these quality metrics.

| Method | Exact accuracy / 36 | Wrong enum actions / 30 | Correct action coverage / 15 | Boolean correct / 6 | Valid format / 36 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | **30/36 (83.3%)** | **1/30 (3.3%)** | **12/15 (80.0%)** | **6/6** | 36/36 | **194.8 / 407.5** |
| One code | 30/36 (83.3%) | 1/30 (3.3%) | 12/15 (80.0%) | 6/6 | 36/36 | 453.4 / 721.4 |
| JSON business ID | 17/36 (47.2%) | 0/30 | 1/15 (6.7%) | 5/6 (83.3%) | 20/36 (55.6%) | 645.7 / 1280.0 |
| JSON code | 30/36 (83.3%) | 1/30 (3.3%) | 13/15 (86.7%) | 5/6 (83.3%) | 36/36 | 586.7 / 1133.7 |

| Method | Rejected / 36 | Abstained / 36 | Invalid format / 36 | Runtime errors | Wrong selected boolean answers |
|---|---:|---:|---:|---:|---:|
| Direct | 19/36 (52.8%) | 3/36 (8.3%) | 0/36 | 0 | 0 |
| One code | 19/36 (52.8%) | 3/36 (8.3%) | 0/36 | 0 | 0 |
| JSON business ID | 14/36 (38.9%) | 4/36 (11.1%) | 16/36 | 0 | 1 |
| JSON code | 17/36 (47.2%) | 7/36 (19.4%) | 0/36 | 0 | 1 |

There are **37 incorrect outcomes**: 16 format failures and 21 valid semantic
errors, leaving 107/144 correct across methods. Five wrong selected choices
comprise three enum mistakes on the same battery-life case and two boolean
mistakes on the same unknown-warranty case. They are not five independent
misoperations. Direct has lower warm median and p95 than code while matching
all of its outcomes in this measured cohort; the model's wrong action remains
wrong in both paths. JSON-code improves action coverage by one request but loses
one boolean answer, so equal overall accuracy does not imply equal behavior.

## Every Qwen direct/code test failure

Case names omit `ext1-test-`. Direct and code share each returned outcome;
margins below belong to direct only. Every one is a valid output, so none is
rescored as correct because an application could reject execution.

| Case | Expected | Shared raw winner and returned decision | Direct margin |
|---|---|---|---:|
| `documents-dismiss-editor` | `document.cinder.close` | `__no_match__` → no-match | 1.125 |
| `calendar_drafts-discard-ambiguous` | Abstain | `__no_match__` → no-match | 3.625 |
| `files-duplicate-name` | Abstain | `__no_match__` → no-match | 1.625 |
| `music-unspecified-track` | Abstain | `__no_match__` → no-match | 1.750 |
| `comparison-remove-focused` | `compare.mistral.remove` | `__no_match__` → no-match | 0.500 |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.kestrel.inspect` → selected wrong product | 2.375 |

The battery-life state explicitly lists Nimbus at 18 hours and Kestrel at 12
hours; the choice is wrong despite valid format. Two executable requests are
incorrectly declined and three ambiguity cases return the wrong decline type.
Direct domain accuracy is documents 5/6, calendar drafts 5/6, files 5/6, music
5/6, product comparison 4/6, and settings 6/6. The original 28-case Qwen run's
zero observed action errors must not be carried over to this extension.

Qwen JSON's 16 invalid responses are all bare objects whose `candidate_id`
contains a numeric code rather than a legal business/rejection ID. Its three
valid errors are `calendar_drafts-discard-ambiguous` → no-match instead of
abstain, `settings-unsupported-size` → abstain instead of no-match, and
`comparison-unknown-warranty` → false instead of abstain.

All six JSON-code errors have valid format:

| Case | Expected | Returned choice/status |
|---|---|---|
| `calendar_drafts-discard-ambiguous` | Abstain | No-match (`__no_match__`) |
| `comparison-remove-focused` | `compare.mistral.remove` | Abstain (`__abstain__`) |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.mistral.inspect`, a different wrong product from direct/code |
| `comparison-unknown-warranty` | Abstain | Selected boolean `false` |
| `settings-unsupported-size` | No-match | Abstain (`__abstain__`) |
| `comparison-price-question` | No-match | Abstain (`__abstain__`) |

The Mistral battery is listed as nine hours. No prompt, threshold, or parser was
adjusted to repair these mistakes. All scores, raw JSON and generated codes are
in the [Qwen test trials](../benchmarks/results/extended-v1-qwen9b-test/trials.jsonl).

## GLM development: policy effects and format failures

GLM completed all 48 development calls without runtime exceptions. Direct
returned 9/12 correct, while its raw winners were correct on 10/12. Zero-margin
abstention turned correct raw actions into incorrect declines on
`ext1-dev-music-open-queue` and `ext1-dev-calendar_drafts-preset-time`. On
`ext1-dev-music-unspecified-track`, the raw winner incorrectly selected
`track.copper.play`; the policy returned the expected abstention. This last
returned success is a policy protection, not a correct raw model answer. The
other direct error selected `file.fern.open` instead of `file.quartz.open` on
`ext1-dev-files-last-visible` (margin 1.0).

| Method | Exact accuracy / 12 | Wrong enum actions / 11 | Action coverage / 7 | Boolean correct / 1 | Valid format / 12 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | 9/12 (75.0%) | 1/11 | 4/7 (57.1%) | 1/1 | 12/12 | 209.1 / 479.3 |
| One code | 0/12 | 0/11 | 0/7 | 0/1 | 0/12 | 350.6 / 386.9 |
| JSON business ID | 8/12 (66.7%) | 3/11 | 7/7 | 0/1 | 12/12 | 635.1 / 2251.2 |
| JSON code | 2/12 (16.7%) | 0/11 | 2/7 (28.6%) | 0/1 | 2/12 | 604.7 / 2462.8 |

Direct rejected 6/12, including three abstentions; JSON rejected 1/12 with no
abstention. Neither generated-code format had a valid decline. Across methods,
29 outcomes were incorrect: 22 format failures and seven valid semantic errors.
Raw direct enum errors were 2/11 versus 1/11 after the policy.

All four JSON development errors were valid selections: a past-save question
selected `document.save`, a negated removal selected `compare.sprout.remove`,
an unspecified track selected `track.copper.play`, and a false reminder fact
was answered true. One-code output was invalid on all 12 cases. JSON-code's two
valid responses were `{"choice":"0"}` for dark theme and the preset draft time;
the other ten placed business or rejection IDs in the code field. The
[development trials](../benchmarks/results/extended-v1-glm-dev/trials.jsonl)
retain all outputs and policy changes.

## GLM frozen test: all four methods

All 144 measured calls completed. Direct raw accuracy was **24/36 (66.7%)**,
versus **21/36 (58.3%) returned accuracy**. The fixed zero-margin policy
suppressed four raw selections: three were correct and one was wrong. That
wrong selection remained an incorrect answer after abstention. Returned enum
action errors were **8/30**; raw enum action errors were **9/30**. The model
does not receive credit for the policy blocking its wrong choice.

| Method | Exact accuracy / 36 | Wrong enum actions / 30 | Correct action coverage / 15 | Boolean correct / 6 | Valid format / 36 | p50 / p95, ms |
|---|---:|---:|---:|---:|---:|---:|
| Direct | **21/36 (58.3%)** | **8/30 (26.7%)** | **9/15 (60.0%)** | **2/6 (33.3%)** | 36/36 | **170.6 / 330.5** |
| One code | 0/36 | 0/30 | 0/15 | 0/6 | 0/36 | 320.0 / 427.1 |
| JSON business ID | 20/36 (55.6%) | 13/30 (43.3%) | 14/15 (93.3%) | 3/6 (50.0%) | 36/36 | 533.1 / 1292.1 |
| JSON code | 1/36 (2.8%) | 0/30 | 1/15 (6.7%) | 0/6 | 1/36 (2.8%) | 480.5 / 913.7 |

| Method | Rejected / 36 | Abstained / 36 | Invalid format / 36 | Runtime errors | Wrong selected boolean answers |
|---|---:|---:|---:|---:|---:|
| Direct | 14/36 (38.9%) | 5/36 (13.9%) | 0/36 | 0 | 3 |
| One code | 0/36 | 0/36 | 36/36 | 0 | 0 |
| JSON business ID | 3/36 (8.3%) | 0/36 | 0/36 | 0 | 3 |
| JSON code | 0/36 | 0/36 | 35/36 | 0 | 0 |

There are **102 incorrect outcomes**: 71 format failures and 31 valid semantic
errors, leaving 42/144 correct across methods. The 27 wrong selected choices
comprise 21 enum errors and six boolean errors across modes, not 27 independent
action mistakes. JSON's high action coverage accompanies 13 wrong actions;
the code formats' zero wrong selections accompanies almost no usable output.

## Every GLM direct test failure

Case names omit `ext1-test-`. All 15 outputs satisfy the direct format contract.
The four zero-margin rows explicitly distinguish raw choices from returned
abstention. The other eleven are wrong selected choices.

| Case | Expected | Raw winner → returned decision | Margin |
|---|---|---|---:|
| `documents-dismiss-editor` | `document.cinder.close` | Correct `document.cinder.close` → abstain | 0 |
| `calendar_drafts-discard-ambiguous` | Abstain | `draft.stencil.discard` → selected | 1.0 |
| `calendar_drafts-reminder-present` (boolean) | `true` | Correct `true` → abstain | 0 |
| `files-first-filtered` | `file.willow.open` | Wrong `file.reed.open` → abstain | 0 |
| `files-first-reordered` | `file.reed.open` | Correct `file.reed.open` → abstain | 0 |
| `files-duplicate-name` | Abstain | `file.outline_work.open` → selected | 1.5 |
| `files-entry-not-content` | No-match | `activity.open` → selected | 1.0 |
| `music-queue-first` | `track.velour.play` | `filter.all` → selected | 0.5 |
| `music-unspecified-track` | Abstain | `track.velour.play` → selected | 0.5 |
| `music-pause-loading` | No-match | `player.close` → selected | 0.5 |
| `music-is-paused` (boolean) | `true` | `false` → selected | 0.5 |
| `comparison-longest-battery` | `product.nimbus.inspect` | `product.mistral.inspect` → selected | 1.5 |
| `comparison-lowest-price` | `product.kestrel.inspect` | `product.mistral.inspect` → selected | 2.0 |
| `comparison-unknown-warranty` (boolean) | Abstain | `false` → selected | 2.0 |
| `settings-notifications-unknown` (boolean) | Abstain | `false` → selected | 2.5 |

Direct accuracy by domain is documents 5/6, calendar drafts 4/6, files 2/6,
music 2/6, comparison 3/6, and settings 5/6. Loading this checkpoint successfully
and reusing its cache do not establish adequate semantic quality.

## GLM baseline failures: valid JSON does not ensure the right choice

The business-ID JSON baseline has no format errors. Its 16 failures are all
valid but wrong selected choices:

| Case | Expected | Returned business ID |
|---|---|---|
| `documents-dismiss-empty` | No-match | `documents.open` |
| `documents-negated-close` | No-match | `document.cinder.close` |
| `calendar_drafts-discard-ambiguous` | Abstain | `draft.lantern.discard` |
| `calendar_drafts-discard-question` | No-match | `draft.discard` |
| `calendar_drafts-negated-move` | No-match | `draft.discard` |
| `files-first-filtered` | `file.willow.open` | `file.reed.open` |
| `files-missing-file` | No-match | `file.reed.open` |
| `files-duplicate-name` | Abstain | `file.outline_work.open` |
| `music-unspecified-track` | Abstain | `track.velour.play` |
| `comparison-price-question` | No-match | `product.nimbus.inspect` |
| `comparison-absent-product` | No-match | `compare.kestrel.add` |
| `settings-unsupported-size` | No-match | `text.small` |
| `settings-vague-accessibility` | Abstain | `text.large` |
| `comparison-unknown-warranty` (boolean) | Abstain | `true` |
| `settings-contrast-disabled` (boolean) | `false` | `true` |
| `settings-notifications-unknown` (boolean) | Abstain | `false` |

One-code output fails on all 36 requests. Each raw output is one generated
token: `__` (12), `code` (5), `true` (4), `false`, `sounds`, `product`, `play`,
`file`, and `draft` (two each), or `document`, `documents`, and `compare` (one
each). None is a legal numeric option code. `finish_reason=length` follows the
predefined one-token limit; these are neither empty outputs nor Markdown
fences. We do not infer what a longer continuation would have said.

JSON-code has one valid response, `{"choice":"1"}` for
`documents-open-feature`, and **35 invalid responses**:

- 30 bare JSON objects put a business ID, rejection ID, `true`, or `false` in
  `choice` instead of a numeric option code.
- `comparison-remove-focused` and `music-unspecified-track` use `NO_MATCH`.
- `settings-unsupported-size` and `comparison-price-question` use `5`, outside
  their allowed `0`–`4` codes.
- `calendar_drafts-discard-ambiguous` emits a fenced object whose `choice` is
  the business ID `draft.lantern.discard`.

All 36 JSON-code responses finish normally without reaching the 96-token cap.
The evaluator preserves these contract failures rather than guessing intended
choices. Full raw text, candidates, scores, and expected labels are in the
[GLM test trials](../benchmarks/results/extended-v1-glm-test/trials.jsonl).

## Input size, cache observations, and memory

Each completed Gemma, Qwen, and GLM run reported verified state-prefix hits:
**48/48 dev and 144/144 test per model**. This verifies actual prefix reuse,
not numerical parity by itself. The separate Gemma cache phase below verifies
numerical parity. No cold-KV, page-update, or process-start latency should be
inferred from the four-method warm tables.

All three models receive the same test state and utterance text: 2–3 business
candidates plus two rejection candidates,
13–54 English utterance characters, and 135–436 serialized state characters.
Gemma direct/code prompts span 499–624 tokens, business-ID JSON 518–643, and JSON-code
522–647. Measured state-prefix reuse spans 486–627 tokens across modes, with
13–21 prompt-suffix tokens to prefill per call; generation modes additionally
compute their output tokens. Gemma dev prompts span 503–600 tokens across modes,
with 17–44 utterance and 147–293 serialized state characters. Qwen test
prompts span 490–617 tokens for direct/code, 507–634 for JSON, and 512–639 for
JSON-code; reuse spans 477–619 tokens, with 13–21 prompt-suffix tokens. Qwen dev
prompts span 493–587 tokens across modes, with 14–24 suffix tokens.
GLM test prompts span 461–583 tokens for direct/code, 478–600 for JSON, and
483–605 for JSON-code; reuse spans 455–592 tokens, with 6–14 prompt-suffix tokens.
GLM dev prompts span 464–546 tokens across modes, with 7–15 suffix tokens.

| Measurement | Gemma dev | Gemma test | Qwen dev | Qwen test |
|---|---:|---:|---:|---:|
| Engine construction/loading | 5193.4 ms | 5433.8 ms | 3795.5 ms | 2954.8 ms |
| Lifetime process peak RSS | 10.966 GiB | 10.609 GiB | 6.271 GiB | 6.230 GiB |
| Lifetime MLX peak | 14.375 GiB | 14.362 GiB | 6.696 GiB | 6.719 GiB |
| Maximum recorded active MLX memory | 13.926 GiB | 13.976 GiB | 6.080 GiB | 6.103 GiB |
| Maximum recorded MLX allocator cache | 1.884 GiB | 2.819 GiB | 1.910 GiB | 2.020 GiB |
| Maximum saved-prefix snapshot cache | 0.448 GiB | 0.499 GiB | 0.451 GiB | 0.474 GiB |

| Measurement | GLM dev | GLM test |
|---|---:|---:|
| Engine construction/loading | 6790.0 ms | 6287.0 ms |
| Lifetime process peak RSS | 10.653 GiB | 11.357 GiB |
| Lifetime MLX peak | 16.494 GiB | 16.531 GiB |
| Maximum recorded active MLX memory | 16.129 GiB | 16.167 GiB |
| Maximum recorded MLX allocator cache | 1.274 GiB | 1.664 GiB |
| Maximum saved-prefix snapshot cache | 0.423 GiB | 0.462 GiB |

These maxima cover the whole process and all its methods, not isolated
per-method allocations. RSS and MLX memory overlap in unified memory and must
not be summed. Loading and recorded warmup costs are excluded from the reported
decision percentiles. The 512 MiB / 16-entry snapshot bound remains in force.
Metadata retains exact byte counts for [Gemma dev](../benchmarks/results/extended-v1-gemma4-dev/metadata.json),
[Gemma test](../benchmarks/results/extended-v1-gemma4-test/metadata.json),
[Qwen dev](../benchmarks/results/extended-v1-qwen9b-dev/metadata.json),
[Qwen test](../benchmarks/results/extended-v1-qwen9b-test/metadata.json),
[GLM dev](../benchmarks/results/extended-v1-glm-dev/metadata.json), and
[GLM test](../benchmarks/results/extended-v1-glm-test/metadata.json).

## Gemma extended cache verification: complete, separate run

The prospectively selected cache phase completed **108/108 direct calls**:
the same 36 cases under three cache conditions. It used the same frozen
fixtures, source hashes, prompt, threshold, and hardware. All 108 raw score
dictionaries and returned status/ID pairs exactly match the corresponding
direct cases in the earlier warm comparison. Each condition therefore retains
31/36 accuracy, one wrong enum action among 30, 12/15 correct action coverage,
5/6 boolean accuracy, 18/36 rejections, and 5/36 abstentions. Cache consistency
also preserves the model's mistakes.

| Direct condition | Measurements | Observed cache behavior | p50 / p95, ms |
|---|---:|---|---:|
| Weights loaded, KV cold | 36/36 | No hit; 0 reused tokens | **1949.9 / 3709.8** |
| First decision after page update | 36/36 | System-prefix hit; 300 reused tokens | **831.1 / 1495.3** |
| Same page, new utterance | 36/36 | State-prefix hit; 486–604 reused tokens | **166.1 / 520.7** |

The numerical check has **36 case rows containing 72 comparisons**: fresh
scores versus a reused state snapshot, and fresh scores versus a system-prefix
snapshot after the previous page changed. **All 72 passed**, with identical
top choices and maximum absolute logit and candidate-softmax-score differences
of **0.0**. These maxima were independently recomputed from each recorded raw
score dictionary. The predefined tolerances were logit `atol=0.5`, `rtol=0`,
and score `atol=0.1`; observed differences were zero, not merely below them.
All cache hit/scope checks passed. No runtime or schema errors occurred.

Engine construction/loading took 7060.6 ms in this separate process. Its
lifetime peak RSS was 10.702 GiB and MLX peak 14.357 GiB; maximum recorded active
MLX memory was 13.964 GiB, allocator cache 11.087 GiB, and saved-prefix snapshot
cache 0.487 GiB. The MLX allocator cache is separate from the application's
512 MiB prefix-cache bound; these overlapping memory measures must not be
summed. Prompt lengths were 499–624 tokens. Decision percentiles exclude loading
and recorded preparation, and KV cold is not a fresh-process startup measure.

The [derived report](../benchmarks/results/extended-v1-gemma4-cache/derived-report.json),
[raw trials](../benchmarks/results/extended-v1-gemma4-cache/trials.jsonl),
[parity dictionaries](../benchmarks/results/extended-v1-gemma4-cache/parity.jsonl),
and [integrity audit](../benchmarks/results/extended-v1-gemma4-cache/evidence-audit.json)
retain the complete separate run. Its 166.1/520.7 ms warm percentiles do not
replace the earlier 168.9/556.5 ms values in the four-method comparison; no
generation baseline was rerun in this cache process. Extended Qwen/GLM cache
matrices were outside this campaign, so their historical 28-case parity results
must not be described as extension measurements.

## Comparison limits

The completed warm comparison finds action errors for every tested model and
marked differences in format compliance. Neither an allowlisted candidate nor
a valid JSON object guarantees a correct choice.

Direct has a lower warm median than the tested generation paths for all three
models. This is a measured property of these implementations and input sizes,
not a comparison with an independently optimized single-token argmax baseline.
Quality and failures differ between modes, especially for GLM. These extension
figures must not be ranked against a different model's older 28-case figures,
and none demonstrates actual application or browser execution.

## Reproduce the completed warm runs

Use the verified local checkpoint and a fresh output directory per run. The
commands below load a real model; documentation checks alone do not run them.

```bash
export JEV_MLX_MODEL=/absolute/path/to/gemma-4-26b-a4b-it-4bit
python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split dev \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/reproduce-extended-gemma-dev

python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
  --modes direct code json json_code --conditions same_page_new_utterance \
  --margin-threshold 0 --repeats 1 --seed 20260919 \
  --output results/reproduce-extended-gemma-test
```

For Qwen or GLM, use the verified `Qwen3.5-9B-OptiQ-4bit` or
`GLM-4.7-Flash-4bit` path with the same arguments and new output directories;
the full three-model command loop is in the protocol.

Retain every trial and raw output, metadata, summary, and integrity audit. Keep
new runs distinct from these published attempts; repeated inputs remain the
same 36 quality examples. Full campaign and optional-cache commands are in the
[protocol](extended-evaluation-protocol.md).
