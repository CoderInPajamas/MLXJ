# JEVKit MLX

**JEV-inspired local decisions for Apple Silicon.**

JEVKit MLX turns application state, a user utterance, and dynamic allowed choices
into one selected business ID, no match, or abstention. It runs an existing local
model through official MLX-LM APIs. Version 0.1 includes a Python SDK, CLI,
localhost HTTP service, and interactive browser demo.

This is an independent, experimental project inspired by
[TypeSafe AI's JEV](https://typesafe.ai/blog/introducing-system-one-models-and-jev).
It is not affiliated with or endorsed by TypeSafe AI, contains no JEV weights,
and does not claim to reproduce JEV's unpublished architecture or RLCD training.

## Install from this checkout

Inference requires Apple Silicon, native ARM Python 3.11 or newer, and an
existing local MLX-LM model directory. The package does not bundle or download
weights. See the [model support table](docs/models.md): successful loading alone
does not establish compatibility.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[mlx,dev]'
export JEVKIT_MLX_MODEL=/absolute/path/to/your/local/mlx-model
```

Use this project's own environment; shared environments and model weights need
no changes. For core development on Linux or without a GPU, install `'.[dev]'`
instead. Real inference is an optional dependency.

The project is not yet published to PyPI. Build and install a local wheel with:

```sh
python -m build
python -m pip install 'dist/jevkit_mlx-0.1.0-py3-none-any.whl[mlx]'
```

## Make a decision

```python
import os
from jevkit_mlx import Candidate, DecisionRequest, MLXDecisionEngine

engine = MLXDecisionEngine(os.environ["JEVKIT_MLX_MODEL"])
request = DecisionRequest(
    state={"view": "library", "visible_titles": ["Amber Maps", "Cloud Songs"]},
    utterance="Play the first one",
    candidates=(
        Candidate("play.amber", "Play the visible course Amber Maps"),
        Candidate("play.cloud", "Play the visible course Cloud Songs"),
        Candidate("close.library", "Close the course library"),
    ),
    state_version=3,
)
result = engine.decide(request)
print(result.to_dict())
```

Results report `candidate_id`, `status`, `raw_selected_id`, `raw_scores`,
`scores`, `margin`, `state_version`, `model`, `timing`, `cache`,
`request_id`, and `selected_value`. Only `status == "selected"` carries an
executable candidate ID. `no_match` means no applicable choice; `abstain`
means clarification or more evidence is needed. Sessions can also return `stale`.

`raw_scores` are candidate-token logits. `scores` are a softmax restricted to
the supplied candidates plus `__no_match__` and `__abstain__`; **they are not
calibrated probabilities of correctness**. `margin` is the raw top-minus-runner-up
logit gap. The default rejection threshold is 0.0, which rejects exact ties.
Select any other threshold using development data and report its limitations.

Boolean choices preserve typed values, including `False`:

```python
question = DecisionRequest.boolean(
    state={"player_status": "paused"},
    utterance="Is playback paused?",
    question="Is the player currently paused?",
)
answer = engine.decide(question)
if answer.status == "selected":
    print(answer.selected_value)  # A Python bool, not a string.
```

## Keep decisions aligned with application state

`DecisionSession` snapshots state before inference. Updates during inference
mark the result stale. Execution checks the current version again, verifies
that the result was issued intact by this session, and consumes it once.

```python
from jevkit_mlx import DecisionSession

session = DecisionSession(
    engine,
    state={"view": "notes"},
    candidates=(Candidate("close.notes", "Close the open notes window"),),
)
session.prewarm()  # Optional: computes prefix state, never a final answer.
decision = session.decide("Close it")

def apply_action(candidate):
    # Apply your application action here, then record its state atomically.
    version = session.update_state({"view": "desktop"}, candidates=())
    return {"executed": candidate.id, "state_version": version}

if decision.status == "selected":
    print(session.execute(decision, apply_action))
```

Call `update_state` for every relevant state or candidate change. Callbacks run
under the session's state lock and may update it reentrantly. Callback failure
consumes authorization too, preventing accidental replay of a partial effect.
These checks prevent stale and replayed execution; they do not establish whether
the model understood the user.

## CLI and real browser controls

```sh
jevkit decide --request examples/decision.json
jevkit serve --port 8765
```

`--model /path/to/model` can replace the environment variable.
`jevkit decide` also reads request JSON from stdin. `jevkit-mlx` is an alias.

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). **Morrow Studio** has a
fictional desktop, course library, filters and ordering, notes, and a simulated
player. Try opening the library, filtering courses, saying “First one,” and
pausing or closing the player. Compare “Close it” on different pages with “Did
you just close it?” and “Don't close anything.” Change the page during inference
to exercise stale-result rejection.

The model selects an allowed action. The browser maps the server-issued
operation to an existing `data-action` button and invokes its actual DOM click
handler. The server validates a single-use decision ticket before applying the
state transition. The interface shows current state, allowed actions, model
scores and timing, cache reuse, and a separate execution receipt.

The course content and player are simulated; inference and DOM controls are real.
This is not arbitrary-website automation, screenshot understanding, or generated
JavaScript execution. See the [HTTP API and demo](docs/http-and-demo.md).

## How scoring and caching work

The backend validates single-token option codes with the checkpoint's tokenizer,
calls the official model and unchanged output head, reads final-position candidate
logits, and maps the selected code back to a stable business ID. The direct path
does not generate JSON or an action-token continuation. The checkpoint remains
a causal language model: this is next-token scoring, not evidence of a new
non-autoregressive model architecture.

Official MLX-LM cache factories and `LRUPromptCache` store full stable-prefix
snapshots. Repeated page state can reuse its prefix while every new utterance is
computed. Page changes invalidate dependent later state; that suffix is recomputed
from a valid earlier snapshot. Hybrid attention/recurrent models are not treated
as plain trimmable KV caches. No final decision is cached.

Defaults are 64 application candidates, a 4,096-token prompt limit, and a
512 MiB / 16-entry prefix cache. Inference is serialized per backend. Checkpoints
may support fewer codes or different templates; incompatible inputs fail
explicitly. Read the [architecture](docs/architecture.md) and
[framework audit](docs/framework-audit.md).

## Tests and reproducible measurements

```sh
python -m pytest -m 'not model'
python -m ruff check src tests benchmarks scripts

# Actual model and cache tests on Apple Silicon, explicitly opted in.
JEVKIT_TEST_MODEL="$JEVKIT_MLX_MODEL" python -m pytest tests/test_model.py
python scripts/check_parity.py --model "$JEVKIT_MLX_MODEL" \
  --output results/local-parity.json

# Keep development and frozen test runs separate; use fresh output directories.
python -m benchmarks.run --model "$JEVKIT_MLX_MODEL" --split dev \
  --output results/local-dev
python -m benchmarks.run --model "$JEVKIT_MLX_MODEL" --split test --repeats 3 \
  --parity --output results/local-test
python -m benchmarks.cold_start --model "$JEVKIT_MLX_MODEL" --repeats 3 \
  --output results/local-process-cold
```

Fixtures are newly written fictional scenarios. Comparison includes direct scores,
the same model generating one option code, and the same model generating structured
JSON. It records process/model loading, loaded weights with cold KV, new utterances
on a cached page, and first decisions after page updates. Timing includes completed
MLX computation. Accuracy, false actions, rejection, executable-request coverage,
memory, invalid output, and failures are separate metrics. Executor rejections
never turn model mistakes into correct answers.

Read the [evaluation protocol](docs/evaluation.md), [model support](docs/models.md),
and [actual recorded results](docs/results.md). This README makes no fixed-latency,
universal compatibility, zero-error, or unmeasured speedup claim. Run different
models sequentially and report each checkpoint separately.

## Scope and contributing

The first release targets English, text-only, single-turn, single-step decisions
over known choices. STT, general chat, free-form tool arguments, multi-step
planning, training, and GPU batching are outside its scope. Small public tests
cannot establish production reliability. The host application remains responsible
for the meaning and consequences of its allowed actions.

See [contributing](CONTRIBUTING.md), [changes](CHANGELOG.md), and the
[release checklist](docs/releasing.md). GitHub publication and package upload
require an explicitly chosen owner, repository, and publishing credentials.

## License and references

Original code and documentation use the [MIT license](LICENSE). Dependencies,
model weights, and third-party material retain their own licenses; see
[NOTICE.md](NOTICE.md). Models remain external to release artifacts.

- [MLX-LM](https://github.com/ml-explore/mlx-lm): official loading, quantization, generation, and cache APIs.
- [TypeSafe documentation](https://docs.typesafe.ai/): inspiration for typed, state-aware decisions.
- [jevmlx](https://github.com/bnsd55/jevmlx), [kev](https://github.com/jaredpalmer/kev), and [JEV Ultrafast](https://github.com/browser-use/jev-ultrafast): related public approaches reviewed in the framework audit.
