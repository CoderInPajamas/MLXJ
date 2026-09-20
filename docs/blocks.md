# MLXJ Blocks

[Back to home](../README.md)

MLXJ Blocks is a falling-block game in which a local model chooses where to place
the next piece. The board makes each choice visible: pieces stack, completed rows
disappear, and a bad sequence can end the game. It is an original, simplified rule
implementation, not an official Tetris product or an implementation of competitive
Tetris rules. No third-party game code is copied into this demo.

## Run locally

Install MLXJ in its own environment following the [quick start](../README.md#quick-start),
then start the server with an existing compatible local checkpoint:

```sh
jev-mlx serve --model /absolute/path/to/local/checkpoint --port 8765
```

Open [MLXJ Blocks](http://127.0.0.1:8765/blocks). You can start continuous local-model
play, request a single placement, pause, reset, or play manually. These modes share
the same board rules. Manual play does not require inference; new model decisions
require the local MLX server. No cloud API or API key is involved.

The HTML, JavaScript, and manual game can be served as static files. Publishing
those files or a recording does **not** run a model on GitHub Pages or in the
viewer’s browser. The model runs in the Python process on the Mac hosting the
loopback service.

## What the model chooses

For each turn, the browser supplies the structured 10 × 20 board, current piece,
and every currently legal placement reachable by rotating the piece above the
board and dropping it vertically. Placements requiring a lateral slide under an
overhang are outside this simplified action space.

Each candidate includes factual consequences computed by the game rules, such as
rows cleared, resulting maximum stack height, and holes. This is useful structured
input, not visual perception: the model does not receive a screenshot. The rules
code does not rank placements or choose a best move. It provides the candidates;
MLXJ scores their single-token codes using the configured local model.

The selected candidate identifies both rotation and landing column. The game code
performs the rotation, drop, collision checks, row clearing, scoring, and drawing.
It does not ask the model to control every animation frame. This is **one model
decision per piece**, with the board waiting for that decision. The animation does
not establish a real-time reaction rate.

No-match, abstention, and the configured margin threshold still apply. A rejected
or failed decision does not trigger a hidden rule-based move or an automatic retry
to obtain a better answer. Candidate scores are not calibrated probabilities of
correct play.

## See what happened

The page shows score, cleared rows, the chosen placement, and measured decision
time. Its detailed trace separates the complete model response from the actual
execution receipt, including state version, scores, margin, model identity,
timing, and cache information. Download the transcript to inspect the sequence.

A reset, manual move, or other relevant state change while inference is pending
invalidates the old decision. The browser checks the current state version and
candidate before applying a result. An execution guard rejecting a model output
is not evidence that the model chose correctly.

Prefix caching reuses eligible model state, not final actions. The board changes
after each placement, so previously computed board-dependent cache content cannot
be reused as though the page were unchanged. The reported cache metadata describes
what was actually reused.

## Reproduce and inspect

The deterministic game-engine checks run without a model:

```sh
node --test tests/blocks-engine.test.mjs
```

For an actual local-model recording, install the optional browser dependency and
Chromium in the project environment, then leave the MLX server running:

```sh
python -m pip install -e '.[mlx,browser]'
PLAYWRIGHT_BROWSERS_PATH=.cache/playwright python -m playwright install chromium --only-shell
```

In another terminal, record a fixed-seed run in an isolated browser context:

```sh
PLAYWRIGHT_BROWSERS_PATH=.cache/playwright .venv/bin/python examples/record_blocks.py \
  --url http://127.0.0.1:8765/blocks \
  --pieces 20 --seed 42 \
  --output output/playwright-blocks/run-42
```

Use a fresh output directory for each attempt. Keep failed runs, refusals, and
execution errors alongside successful runs. A fixed seed reproduces the piece
sequence; it does not guarantee identical model scores across hardware or
dependency versions.

## Current scope

Game-playing quality is experimental and has not yet been measured in a frozen
game benchmark. A recording demonstrates that a particular run happened, not
strong play, a speed advantage, or general planning ability. The existing
[evaluation results](results.md) concern semantic action selection and must not
be presented as falling-block performance.

The demo exposes legal placements and their immediate consequences to the model.
It does not establish screenshot understanding, multi-step search, frame-by-frame
control, or arbitrary browser automation. This small game is intended to make
local action selection easy to observe and test.
