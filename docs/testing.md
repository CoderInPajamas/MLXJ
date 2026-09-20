# Test methods and measured results

[Home](../README.md) · [Evaluation protocol](evaluation.md) · [Complete historical results](results.md) · [Six-domain extended results](extended-results.md) · [Additional evaluation protocol](extended-evaluation-protocol.md) · [Gemma original-suite measurements](gemma4-results.md) · [Supported models](models.md)

The latest core suite has **161 passing tests**. The three-model, four-method comparison on the six-domain extended suite has completed the same-page/fresh-utterance evaluation and passed its evidence audit. Only direct scoring is listed below; see the [extended results](extended-results.md) for all baselines, rejection rates, coverage, format failures, memory, and raw records.

| Model | Strictly correct / 36 | Wrong actions / 30 enum requests | Correct action coverage / 15 | Boolean correct / 6 | Same-page p50 / p95 |
|---|---:|---:|---:|---:|---:|
| Gemma 4 MoE | 31/36 (86.1%) | 1/30 | 12/15 | 5/6 | 168.9 / 556.5 ms |
| Qwen3.5-9B-OptiQ-4bit | 30/36 (83.3%) | 1/30 | 12/15 | 6/6 | 194.8 / 407.5 ms |
| GLM-4.7-Flash-4bit | 21/36 (58.3%) | 8/30 | 9/15 | 2/6 | 170.6 / 330.5 ms |

All three used the same frozen inputs, prompt, and threshold. These timings require loaded weights and an already prepared page prefix; each model's 144 test records still represent only 36 distinct scenarios. Gemma selected the wrong first queue item, Qwen selected the wrong product for longest battery life, and GLM made more action errors. Boolean answer errors are counted separately, not as wrong actions. **These results do not support general action execution without human confirmation.** Gemma also completed 108 direct decisions across three conditions and **72/72** cache comparisons; all three conditions had 31/36 correct decisions and 1/30 wrong enum actions. Cache consistency does not establish semantic correctness.

The new wheel was installed in an independent environment outside the repository. Its 14 runtime files matched the source and archive contents byte-for-byte; a real Gemma CLI call correctly selected `player.pause` for the example. [Installation verification](../benchmarks/results/extended-release-checks/distribution.json) is recorded separately and is not included in the model quality set.

The original 28 cases are retained separately: Gemma scored **26/28**, including one wrong selection of the first filtered item, meaning **1/26 enum requests returned a wrong action**. See the [Gemma original-suite report](gemma4-results.md). The two datasets must not be combined into one unseen-test score.

The sections below explain the historical Qwen and GLM measurements and the Qwen browser demonstration in detail. On the original 28-case suite, **Qwen3.5-9B-OptiQ-4bit achieved 25/28 final-decision accuracy (89.3%)**, with same-page/fresh-utterance p50 / p95 of **171.7 / 176.4 ms**. GLM-4.7-Flash-4bit scored **14/28 (50.0%)** and is not recommended for direct action execution with the current prompt.

These results apply to the specific machine, models, English scenarios, and implementation revisions measured. They do not establish arbitrary-model compatibility, a fixed 100 ms latency, zero semantic errors, or calibrated probabilities. Chinese documentation and interface text do not establish that Chinese or mixed-language instructions have passed model evaluation.

The original evaluations, screenshots, and recordings use the project's former name, JEVKit MLX. Evidence files retain their original name, source hashes, and recording times; they were not rewritten for the rename. Reproduction commands below use the current `jev-mlx` command, `jev_mlx` module, and `JEV_MLX_MODEL` environment variable. Rename verification reran the core suite and a real-model call from an independent wheel; **it did not rerun the full quality evaluation or browser model tests**. See the [rename verification record](../benchmarks/results/rename-release-checks/verification.json).

## What was tested

| Layer | Samples or checks | What it establishes |
|---|---|---|
| Core automated tests | Latest single run: 161 passed, 0 failures, 0 errors; no GPU model loaded | Software behavior including data contracts, score handling, state versions, concurrent stale-result protection, result identity and replay protection, HTTP, and cache boundaries |
| Development set | 16 newly written fictional English scenarios | Prompt development; not an unseen-test score |
| Frozen test set | 28 distinct English scenarios: 16 executable enum requests, 10 enum rejection requests, and 2 boolean answers | Model semantic quality with a fixed prompt and threshold |
| Six-domain extended set | Separate 12-case development and 36-case frozen test splits; test contains 30 enum requests and 6 boolean judgments | New-scenario performance of three models on documents, calendar drafts, files, music, product comparisons, and settings; not an additional independent sample from the original set |
| Qwen/GLM cache comparisons | Two models, each with 28 scenarios × 2 reuse conditions | Whether cache reuse changes candidate scores or choices relative to fully fresh computation |
| Gemma extended cache comparisons | 36 scenarios × 3 conditions = 108 direct decisions; 36 parity records contain 72 comparisons, all passing | Numerical consistency of same-page reuse and page updates against fresh computation on the extended set; not new independent semantic samples |
| Real browser | 16 Qwen-driven scenarios, plus one page-change check | Whether model choices, actual DOM clicks, server execution receipts, and visible state connect correctly |

The [latest core verification](../benchmarks/results/extended-release-checks/core-tests.json) records a single run with **161 passed**. Pytest reported 3.76 seconds (the JUnit suite recorded 3.752 seconds), with 0 failures, 0 errors, and 0 skips; 3 real-model tests were deselected, and lint passed. HTTP tests ran with loopback-port access. Remote GitHub CI has not been executed.

The historical **145-test** rename verification is retained: 138 tests passed initially, while 7 HTTP fixtures could not be set up because the sandbox blocked port binding. Rerunning HTTP produced 8 passing tests, including 1 overlap, for 145 distinct tests in total. This historical sequence does not mean the same errors occurred in the latest 161-test run.

Both development and test sets are public fictional data, not exports from production conversations, recordings, screenshots, or logs. Files and frozen hashes are in the [data manifest](../benchmarks/fixtures/manifest.json); full inputs are in the [development set](../benchmarks/fixtures/dev.jsonl) and [test set](../benchmarks/fixtures/test.jsonl). Coverage includes:

- How “Close it” changes meaning with different open objects or no open object.
- Opening the video-library feature versus playing a particular course.
- Selecting “First one” according to the current visible order after filtering and sorting.
- Allowed actions changing between the video library, a loading player, and a ready player.
- Treating “Did you just close it?” as a question; declining negation, vague expressions, and nonexistent targets.
- Candidate-order changes, boolean judgments, and stale-result protection during execution.

During development, Qwen improved from 14/16 to 15/16 on the development set. The general semantic prompt and `margin_threshold=0.0` were then frozen before the primary test. No phrase-specific regex rules were added, and the threshold was not tuned on the frozen test set.

## Reading the quality metrics

**Final-decision accuracy** requires both the selected ID and status to be correct. For example, if the label requires `abstain` but the model returns `no_match`, strict evaluation still counts it as wrong, even though neither outcome executes an action.

**Raw-choice accuracy** uses `raw_selected_id`, preserving the model's choice before threshold handling. A zero-margin tie can be converted to `abstain` by the engine, so raw and final accuracy may differ. If the executor blocks a wrong choice, that demonstrates a working guard; it does not turn the model error into a correct answer.

**Wrong-action rate** counts only enum requests: the denominator is 26 in the original set and 30 in the extended set. **Action coverage** divides correct action selections by executable enum requests: 16 in the original set and 15 in the extended set. The model evaluation itself does not execute these actions. Boolean questions have separate answer accuracy; factual answers must not be described as executed actions.

The old records' `false_action` and `executable_request_coverage` use mixed definitions: the 28 cases include two boolean answers, so the 18 expected `selected` outcomes are 16 actions plus 2 answers. Old numbers are retained and explicitly labeled “mixed choices.” The breakdown by kind comes from a [read-only derived report](../benchmarks/results/legacy-kind-breakdown.json), without rewriting raw records. **Rejection rate** still counts `no_match` and `abstain` across all requests; **abstention rate** counts only `abstain`.

Of the extended set's 6 boolean questions, 4 should select a true/false answer and 2 should abstain because information is insufficient. Its historical mixed-choice denominator is 19: 15 actions plus 4 answers, not 19 executable actions. Extended results use the breakdown by kind.

`scores` are softmax scores restricted to the candidate set; `margin` is the gap between the highest and second-highest raw logits. Neither is a “probability of being correct,” and logit values from different models should not be compared directly.

## Qwen/GLM cache-revision results (historical runs)

The following numbers come from the [final Qwen summary](../benchmarks/results/qwen9b-cache-fixed/summary.json) and [final GLM summary](../benchmarks/results/glm-cache-fixed/summary.json). Each model ran 28 calls under each of three cache conditions. Quality was identical across conditions, so only one cohort's denominator is shown here.

| Metric | Qwen3.5-9B-OptiQ-4bit | GLM-4.7-Flash-4bit |
|---|---:|---:|
| Final-decision accuracy | **25/28 (89.3%)** | **14/28 (50.0%)** |
| Raw-choice accuracy | 26/28 (92.9%) | 15/28 (53.6%) |
| Final wrong-action rate (enum) | 0/26 (0%) | 2/26 (7.7%) |
| Raw wrong-action rate (enum) | 0/26 (0%) | 3/26 (11.5%) |
| Rejection rate | 11/28 (39.3%) | 16/28 (57.1%) |
| Abstention rate | 1/28 (3.6%) | 12/28 (42.9%) |
| Executable enum action coverage | 15/16 (93.8%) | 8/16 (50.0%) |
| Boolean answer accuracy | 2/2 | 2/2 |
| Historical mixed-choice coverage | 17/18 (94.4%) | 10/18 (55.6%) |
| Valid output structure | 28/28 | 28/28 |
| Runtime exceptions | 0/28 | 0/28 |

GLM returned 10 actions and 2 boolean answers; two of those actions were wrong. The old 2/12 (16.7%) value is the mixed error rate among returned choices; among returned actions alone, it is 2/10 (20%). Qwen made no wrong actions in the 26 enum scenarios, but that does not establish that real applications will never misoperate.

Each model's 84 records are **the same 28 scenarios × 3 cache conditions**. They are not 84 independent semantic samples, and both models share the same 28 scenarios. Increasing `--repeats` produces more timing observations, not new test cases.

Times are in milliseconds. Each cell is **p50 / p95** from 28 calls; MLX computation was synchronously evaluated before timing ended.

| Cache condition | Qwen | GLM |
|---|---:|---:|
| Weights loaded, KV cold: `kv_cold` | 2159.9 / 2406.6 | 1837.6 / 2154.5 |
| Same page, fresh utterance: `same_page_new_utterance` | **171.7 / 176.4** | **147.8 / 170.6** |
| First decision after page change: `page_update` | 1050.2 / 1294.5 | 927.4 / 1246.5 |

Same-page calls reuse the full page prefix. After a page change, only the stable system prefix before the change is reused, and the page and utterance suffixes are recomputed. Completed answers are not cached to imitate model acceleration. Page updates and cold-KV calls still take roughly one to several seconds; these measurements do not support “fixed 100 ms” performance.

The measured machine was an Apple M2 Max with 64 GiB unified memory, running Python 3.13.2, MLX 0.31.2, and MLX-LM 0.31.3. Qwen uses mixed 4/8-bit quantization with group size 64; GLM uses 4-bit quantization with group size 64. Each test input has 2–6 business candidates plus two rejection candidates, with utterances of 8–34 English characters. The current implementation runs serial inference, allowing at most 64 business candidates and 4096 prompt tokens, with a prefix-cache bound of 512 MiB / 16 entries. Full model hashes, memory definitions, and hardware details are in the [complete report](results.md) and [model provenance](../benchmarks/results/checkpoints.json).

## Known errors: guards do not erase model errors

Qwen's three final errors occurred under all three cache conditions:

| Scenario | Expected | Observed |
|---|---|---|
| Two open windows, no focus: “Close it” | `abstain`, clarification needed | `no_match` |
| Several courses available: “Play something” | `abstain`, clarification needed | `no_match` |
| Reordered list: “First one” | `play_lunar` | The raw tie-break chose correctly, but margin was 0, so the final result was `abstain` |

For the third case, `play_lunar`, `sort_title`, and `__no_match__` all had a logit of 22.25. The engine abstains on exact ties, so raw accuracy of 26/28 must not be reported as final accuracy.

GLM's two final wrong actions were selecting `close_settings` under multi-window ambiguity and selecting `back_to_library` when asked to pause a loading player. Another raw wrong choice, `open_library`, was converted to abstention by a zero margin; it is excluded from final wrong actions but retained as a raw model error. Successful loading, valid candidate outputs, and consistent cache numerics do not establish sufficient semantic quality for action execution.

All case inputs, outputs, raw scores, and errors are retained in the [Qwen trial records](../benchmarks/results/qwen9b-cache-fixed/trials.jsonl) and [GLM trial records](../benchmarks/results/glm-cache-fixed/trials.jsonl).

## Why the Qwen/GLM cache check reports 112 passing comparisons

For each model and each of 28 scenarios, the check compares both “same-page reuse versus fresh computation” and “page-update reuse versus fresh computation”: **2 models × 28 scenarios × 2 comparisons = 112/112 passing comparisons**. The largest observed candidate-logit difference and softmax-score difference were both 0 across these comparisons, and raw winning candidates agreed. The records retain the predeclared tolerances: logit absolute error 0.5, relative error 0, and score absolute error 0.1.

These are not 112 distinct semantic questions, nor a guarantee of bitwise equality on all future inputs. See the [Qwen comparisons](../benchmarks/results/qwen9b-cache-fixed/parity.jsonl) and [GLM comparisons](../benchmarks/results/glm-cache-fixed/parity.jsonl).

The old implementation had **25 failing comparisons among GLM's 28 cache scenarios**: same-page reuse agreed, but partial reuse of an arbitrary common prefix after page changes diverged, with a maximum logit difference of 5.5 and a changed winning candidate in 1 case. Revision `579daf3` accepts reuse only at complete system or page snapshot boundaries, after which the full checks above were rerun. The semantic prompt and threshold did not change. [Original failure records](../benchmarks/results/glm-test/parity.jsonl) remain available; the differences have not been attributed to a framework bug without evidence.

## Comparison with generating one code or JSON

The primary comparison used the same Qwen model on the old implementation `a743972`: direct candidate logits, one code from the official generation API, and JSON containing a business ID. The table below shows same-page/fresh-utterance results from **that same historical run**. Do not combine these timings with revised-runtime timings above to calculate a speedup.

| Historical method | Final accuracy | Wrong choices (mixed) | Choice coverage (mixed) | Same-page p50 / p95 (ms) |
|---|---:|---:|---:|---:|
| Direct candidate scoring | 25/28 | 0/28 | 17/18 | 196.3 / 202.7 |
| Generate one code | 26/28 | 0/28 | 18/18 | 445.4 / 693.9 |
| Generate business-ID JSON | 6/28 | 0/28 | 0/18 | 604.3 / 1304.8 |

The original JSON baseline produced 66/84 invalid structures across three conditions, mainly placing internal codes in a field that required a business ID. Producing no valid action outputs must not be read as safety or accuracy. All raw text is retained. The [primary comparison record](../benchmarks/results/qwen9b-test-v1/summary.json) also shows direct scoring's cold-KV p95 of 3751.7 ms was slower than the code baseline's 3243.2 ms; favorable warm-cache results must not be shown alone.

After observing the original JSON test failures, an additional `json_code` format control requesting `{"choice":"0"}` was introduced. On the same frozen set it scored 26/28, with 1/28 mixed wrong choices (1/26 wrong enum actions), 28/28 schema validity, and same-page p50 / p95 of 529.4 / 953.6 ms. Its wrong action converted “Play something” into playing a particular course. **This supplementary format experiment was added after seeing test results; it is not an independent blind evaluation untouched by the test set.** See the [supplementary record](../benchmarks/results/qwen9b-jsoncode-test/summary.json).

Direct scoring retains the official model's quantized output head and reads final-position candidate logits without generating subsequent text. The underlying computation is still a causal language model's next-token prediction. The official `max_tokens=1` generation path may also prefetch the next step; timings include completed computation. These comparisons describe the current interface paths. They do not establish a unique non-autoregressive architecture or guaranteed speed superiority over an equally optimized single-step argmax.

## Process cold start is a separate metric

Loaded weights with a cold KV cache are different from cold-starting a fresh process. Separate new-process runs used 3 attempts per method for Qwen and 2 for GLM, totaling 20 attempts across four methods. Outer timing includes process startup, loading, the first decision, and exit. Only the first test case was used, and the operating-system file cache was not flushed.

For direct scoring, outer p50 / p95 was 4897.3 / 4928.1 ms for Qwen and 8726.6 / 8848.2 ms for GLM. With only 2–3 samples per group, these are not stable p95 estimates. None of the 20 processes had a runtime exception, but that does not mean all 20 model answers were correct. Format and semantic failures are preserved in the [Qwen cold-start records](../benchmarks/results/qwen9b-cold/summary.json), [GLM cold-start records](../benchmarks/results/glm-cold/summary.json), and [full explanation](results.md).

## How the real browser was tested

The test used the real local Qwen backend and Chromium. An utterance is entered into the fictional Morrow Studio application; the model selects from currently allowed actions; the matching DOM button is clicked; the server returns a one-time execution receipt; and the page state is checked. The model, browser click, and execution are real. The desktop, courses, and player form a public simulated application; this is neither arbitrary-website operation nor screenshot-based visual recognition.

The 16 scenarios cover declining to close an empty desktop, opening the course library, filtering courses, playing in visible order, pause, resume, rewind, close, not acting on questions or negation, nonexistent targets, vague requests, the notes window, and declining to pause during loading. Setup actions such as sorting are recorded separately and are not counted as model-choice results.

The result was **16/16 passing scenarios, 10 model actions with DOM execution receipts, 6 rejections, and 0 browser errors**. The browser demonstration accepts either `no_match` or `abstain` for rejection, which is broader than the frozen benchmark's strict status matching. Its 16/16 must not replace the earlier 25/28 or become a claim of 100% general model accuracy. GLM and Gemma have not completed the same real-browser test; the six-domain evaluation selects candidates without operating real applications.

A separate concurrency check showed that the page changed to the notes window while the decision request was still pending. The old `open.library` choice was ultimately marked `stale` and was not executed. The record proves overlap between the request and page update; overlap with the actual GPU computation interval was not measured separately. During loading, the only allowed candidate was closing the player; “Pause it” returned `no_match` and did not execute.

See the [full browser record](assets/browser-demo/browser-transcript.json), [actual recording](assets/browser-demo/video/page@9986ccf6fcac324ee3a7302c87bf305e.webm), and [player screenshot](assets/browser-demo/03b-player-control.png). The first capture attempt failed because of hidden-element text extraction and video-path handling; the original media and [failure note](assets/browser-initial/harness-failure-note.json) are retained. The capture script was fixed without changing the model prompt or threshold, and the capture failure was not presented as a model result.

## Reproduce on your own machine

Run these commands from the repository root. Use an isolated virtual environment, leaving shared Python environments and model files unchanged. Replace the model path with your own existing local MLX weights. Run only one model job at a time to avoid including other GPU workloads in timing measurements.

Start with core tests that do not require a model:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -m 'not model' -q
python -m ruff check src tests benchmarks scripts examples
```

On Apple Silicon, install real-inference dependencies, run a decision, and optionally run model integration tests:

```bash
python -m pip install -e '.[mlx,dev,browser]'
export JEV_MLX_MODEL=/absolute/path/to/Qwen3.5-9B-OptiQ-4bit
jev-mlx decide --request examples/decision.json
JEV_TEST_MODEL="$JEV_MLX_MODEL" python -m pytest tests/test_model.py -q
```

Run the development set first. Use only that set if changing prompts or thresholds. Then run the full frozen set and cache comparisons with a fixed configuration:

```bash
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split dev \
  --modes direct --repeats 1 --output results/local-qwen-dev

python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct --conditions kv_cold same_page_new_utterance page_update \
  --repeats 1 --margin-threshold 0 --parity \
  --parity-atol 0.5 --parity-rtol 0 --parity-score-atol 0.1 \
  --output results/local-qwen-direct-test
```

Run the three-method comparison on the same model, and the separate fresh-process cold-start check:

```bash
python -m benchmarks.run --model "$JEV_MLX_MODEL" --split test \
  --modes direct code json --repeats 1 \
  --output results/local-qwen-comparison

python -m benchmarks.cold_start --model "$JEV_MLX_MODEL" \
  --modes direct code json json_code --repeats 3 \
  --output results/local-qwen-process-cold
```

These commands use current source and cannot guarantee the same timings as historical revisions. When switching to GLM, set a new `JEV_MLX_MODEL` and use a new output directory; the original GLM cold-start record used only 2 repetitions per method. Inspect `metadata.json`, `trials.jsonl`, `summary.json`, and `parity.jsonl`; retain failures and full inputs, and compare model identities, source hashes, and cache-hit conditions before comparing speed.

To reproduce the six-domain extension, explicitly pass `--fixtures-dir benchmarks/fixtures/extended-v1`. Run its separate development split before the frozen test split. This three-model, four-method comparison used only `--conditions same_page_new_utterance`. Full commands and the separately declared Gemma cache phase are in the [fixed protocol](extended-evaluation-protocol.md); actual completed scope is in the [extended report](extended-results.md). Do not modify frozen files or tune thresholds using these published test results and still call the result unseen evaluation.

For browser testing, start the service in terminal one:

```bash
source .venv/bin/activate
export JEV_MLX_MODEL=/absolute/path/to/Qwen3.5-9B-OptiQ-4bit
jev-mlx serve --port 8765
```

In terminal two, install the test Chromium and run capture:

```bash
source .venv/bin/activate
export PLAYWRIGHT_BROWSERS_PATH=.cache/playwright
python -m playwright install chromium --only-shell
python examples/browser_smoke.py --url http://127.0.0.1:8765 \
  --output output/browser-local
```

The browser output directory must be empty. Use a new directory for every run; the original evidence in `docs/assets` is not overwritten. This script checks the known demonstration flow. Entering other utterances in the interface is exploration and is not automatically included in the frozen test score.

## What remains to validate Chinese and mixed-language support

The existing frozen model evaluations cover English, single-turn, single-step actions. You can try Chinese instructions, but no accuracy, wrong-action, or latency conclusions are currently available for Chinese or mixed-language instructions. Documentation translation, button translation, and model understanding are different validation targets.

To extend coverage to Chinese, write separate public fictional Chinese development and frozen test sets covering references, negation, questions, order, ambiguity, and mixed Chinese/English course names. After development-only tuning, freeze prompts, thresholds, and data hashes, then report Chinese, English, and mixed-language results separately. Do not modify the existing frozen files or treat handpicked successful demonstrations as a complete evaluation.
