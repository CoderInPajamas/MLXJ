# Extended fictional suite v1

[Back to home](../../../README.md)

This suite adds **12 development cases and 36 frozen test cases** across six
fictional local applications. It supplements the original 16/28 course-player
suite; it does not replace or modify it. Every request remains English,
single-turn, single-step selection from dynamically supplied choices. There are
no external calendar changes, messages, file deletions, purchases, arbitrary
parameters, or application executions in these fixtures.

## Provenance and freeze boundary

The scenarios, names, states, utterances, labels, and explanations were written
from scratch for this extension. They contain no production exports, personal
records, external datasets, or model-generated evaluation answers. The six
applications and every document, draft, file, track, and product are fictional.

**The suite was authored after the project's historical development and model
evaluations were known.** It deliberately exercises similar failure categories
in new domains. It is a post-development extension, not the original untouched
benchmark, a random population sample, or evidence that its authors had no
knowledge of earlier model behavior. No inference on these new cases was used
to create or revise their labels. A separate read-only annotation review and
CPU-only schema validation preceded the recorded freeze.

[manifest.json](manifest.json) records the exact UTF-8 JSONL SHA-256 hashes,
counts, freeze time, authoring context, and validation-source hashes. Freeze
applies before any inference on this suite. Keep the frozen bytes unchanged;
future corrections or additions belong in a new version with an explanation.
Any prompt or threshold tuning must use development cases only and be recorded
before test evaluation. The comparison default is margin threshold `0.0`,
inherited from the existing protocol, not selected on this new test split.

## Coverage and denominators

| Domain | Fictional application | Dev | Test | Main checks |
|---|---|---:|---:|---|
| Documents | Fable Desk | 2 | 6 | Focused editor vs preview vs empty view; workspace vs a named document; negation |
| Calendar drafts | Petal Planner | 2 | 6 | Focused vs ambiguous draft; saving disables discard; past-action question; reminder boolean |
| File lists | Pebble Files | 2 | 6 | Filtered visible order, changed sorting, duplicate names, absent target, entry vs content, file-type boolean |
| Music queue | Velvet Queue | 2 | 6 | Playing vs paused vs loading, queue order, unresolved reference, playback boolean |
| Product comparison | Lantern Compare | 2 | 6 | Stated price/battery attributes, focused card, question vs action, missing product, unknown warranty |
| Local settings | Harbor Preferences | 2 | 6 | Enable/disable changes, exact preset availability, vague accessibility request, false/unknown boolean |

The development split has 8 `selected`, 3 `no_match`, and 1 `abstain` labels.
The test split has **19 `selected`, 11 `no_match`, and 6 `abstain` labels**.
Every domain contributes exactly six test cases, not six independent samples of
all possible use in that domain. Some paired cases intentionally reuse an
utterance with different state to test whether the selected action changes.
No complete request utterance is shared between development and test splits.

The 36 tests consist of:

- **30 enum requests:** 15 selected actions, 11 no-match, 4 abstentions.
- **6 boolean requests:** 2 true, 2 false, 2 abstentions for missing evidence.

The existing aggregate metric calls every expected `selected` decision
"executable," so its denominator is **19**, including four factual boolean
answers. That aggregate coverage is correct-choice coverage, not proof of 19
executed actions. Likewise an incorrect selected boolean answer can contribute
to the generic `false_action` metric; report enum and boolean results separately
when describing actual action mistakes. No executor can turn a wrong model
selection into a correct answer here.

Each request offers two or three business choices, plus the engine's reserved
no-match and abstain choices. Test utterances contain 13–54 English characters.
This suite expands semantic domains; it is not a large-candidate, long-context,
multilingual, multi-step, adversarial-security, or browser-automation benchmark.
Repeated cache conditions and repetitions provide more measurements of the
same **36 unique cases**, not additional independent quality examples.

## Annotation rules

- `selected`: the request uniquely identifies an allowed action, or available
  state establishes a true/false answer to the supplied boolean question.
- `no_match`: no allowed action matches; a specified target or exact parameter
  is unavailable; the enum utterance asks a factual/past-action question; or the
  only requested operation is negated. Opening an entry point is not a valid
  replacement for an unavailable content action.
- `abstain`: a plausible action has multiple unresolved targets or meanings, or
  a boolean proposition lacks evidence. Explicit `false` is a valid answer;
  `null` marked unknown or not loaded is not evidence of false.

Ordinals follow `visible_files` or `visible_tracks`, not candidate order.
For example, the same "Preview the first visible file." request selects Willow
under descending order and Reed under ascending order. "Dismiss that." selects
the focused document editor or preview, and has no match when neither is open.
"Pause this track." selects pause during playback and has no match while
loading. These pairs make context changes observable in expected decisions.

Each row follows the existing case schema: `id`, `family`, `request`, `expected`,
`warmup_utterance`, and `previous_request`. Additional `domain`, `tags`, and
`label_rationale` fields are audit metadata and must not be included in model
input. `previous_request` is a separate earlier state snapshot for cache-update
experiments, not conversational history. Its version is lower, its state differs,
and its utterance is the warmup utterance. No warmup answer is treated as a test
label. Boolean snapshots retain the same question and typed choices while prior
facts are unavailable; enum snapshots use another view or an earlier playback,
sorting, or setting state.

## Validation and reproduction

CPU validation constructs every current and previous request using the public
`DecisionRequest.from_dict` API; checks all 48 case IDs, expected status/ID
allowability, boolean types, version order, changed state, split counts, and
original-suite hashes; and verifies every frozen file against its manifest.
Independent semantic review found no label inconsistency before freezing. This
is input validation, not a model result. See the manifest for validation facts.

From the repository root, using an existing local model and a separate output
directory for each run:

```bash
python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split dev \
  --modes direct --conditions same_page_new_utterance \
  --output results/extended-local-dev

python -m benchmarks.run --model "$JEV_MLX_MODEL" \
  --fixtures-dir benchmarks/fixtures/extended-v1 --split test \
  --modes direct --conditions kv_cold same_page_new_utterance page_update \
  --margin-threshold 0 --repeats 1 --parity \
  --output results/extended-local-test
```

Run the same frozen inputs for every compared checkpoint. Preserve all failures,
raw choices, exact returned statuses, and cache information; record model,
quantization, runtime, source hashes, hardware, and input size. Do not tune test
labels or thresholds after inspecting a model's answers. At creation time this
suite has **no model results**; any later run must be reported separately from
the original benchmark and from the freeze/validation record.
