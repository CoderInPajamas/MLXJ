# Contributing to JEV MLX

[Back to home](README.md)

Use a dedicated environment and a local model directory. Do not install into a
shared inference environment, modify model weights, or stop other applications
to improve benchmark numbers. Python 3.11 or newer is required.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python scripts/check_docs.py
python -m pytest -m 'not model'
python -m ruff check src tests benchmarks scripts
python -m build
```

On Apple Silicon, install `'.[mlx,dev]'` for real inference. Run one checkpoint
at a time and explicitly set `JEV_TEST_MODEL` for `tests/test_model.py`. Core
tests use injected backends; they do not prove model quality, Metal execution,
or real-checkpoint cache correctness.

## Implementation principles

- Inspect official MLX/MLX-LM capabilities first. Reuse loading, quantization,
  generation, and caching before implementing alternatives.
- Keep semantics in the model. Do not add phrase-specific regular expressions
  or hidden expected answers to improve examples or tests.
- Keep state, dynamic candidates, no-match, and abstention explicit. Stable
  business IDs must not depend on internal token codes.
- Separate model predictions, host execution validation, and receipts. A
  blocked wrong action remains a model mistake in evaluation.
- Preserve full valid cache snapshots for hybrid models. Changed middle content
  invalidates all downstream dependent state.
- Keep public imports usable without MLX. Add meaningful regression coverage
  for correctness changes and run checks relevant to the affected behavior.
- Preserve licenses and attribution for third-party material.

The first release targets English single-step choices using existing checkpoints.
Discuss broader features before expanding the public contract. Documentation
should describe observed behavior and explicit limits, not future performance.

## Documentation languages

Keep a complete English and Chinese version of each document, registered in
`docs/locales.json`. Only the two homepages link across languages; inner document
links stay in the same language and return to that language's homepage. Do not
add language selectors to inner pages. Preserve original prompts, commands, and
raw evidence when translating. Run `python scripts/check_docs.py` to check pairs,
local links, and language routes; CI runs the same check.

## Evaluation changes

Read [the evaluation protocol](docs/evaluation.md) before modifying fixtures,
prompts, thresholds, metrics, baselines, or cache tests. Development and frozen
test data are separate and manifest hashes are checked. Do not tune on frozen
test data and continue calling it held out. A newly tuned method needs new
held-out data and provenance.

All examples and assets must be fictional and newly authored for public use.
Do not export production data, conversations, recordings, screenshots, or logs,
including allegedly anonymized versions. Retain every attempt and failure in
benchmark artifacts and use fresh output directories. Do not select only
successful examples.

Performance claims need model, quantization, dependency, hardware, input-size,
memory, and cache details. Compare the one-code and JSON baselines under the same
state/cache conditions. Synchronize MLX for timing. Repeated examples increase
timing observations, not independent quality samples. Raw scores and restricted
softmax require separate calibration evidence before being described as
correctness probabilities.

## Pull requests and reports

Describe the problem, resulting behavior, validation, and relevant limits.
Provide reproduction commands and label unrun checks. For model-specific issues,
include public checkpoint identity, dependency versions, a small fictional
request, and its complete result or exception. Remove usernames, private paths,
secrets, and unrelated logs before sharing artifacts. Do not attach weights.

Original contributions use MIT. Dependencies and model weights retain their own
licenses. Publication procedures are in [docs/releasing.md](docs/releasing.md).
