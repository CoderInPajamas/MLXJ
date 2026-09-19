# Local HTTP API and browser demo

Start the real MLX backend with a separate local checkpoint:

```sh
jevkit serve --model /path/to/local/mlx-model --port 8765
```

Open `http://127.0.0.1:8765` in a browser. The server only binds to loopback and
does not download scripts, fonts, images, or model weights for the demo. It is a
single-user development service: all tabs share one fictional desktop and state
version. It is not a production multi-tenant server.

## What the demo actually does

Morrow Studio is an original fictional desktop with a course library, field notes,
and a simulated video player. Natural-language requests are always passed to the
configured local model. There is no regex intent router, canned language response,
or cached final answer.

The model scores current allowed action IDs. A selected ID becomes a constrained
browser operation such as:

```json
{
  "type": "click",
  "action_id": "player.pause",
  "selector": "[data-action=\"player.pause\"]",
  "ticket": "opaque-single-use-id",
  "state_version": 4
}
```

The browser locates that existing DOM button and invokes its actual click handler.
The same handler accepts manual clicks. A model click sends its issued ticket to
the executor; the executor verifies the original choice, current state version,
and single use before applying a transition. The receipt records the executed
action and before/after versions; the browser then renders the returned state.
The browser dispatches a `jevkit:receipt` event containing that receipt and the
observed view for integration tests.

This is a real browser interaction over a bounded, local application. It is not
arbitrary website navigation, generated JavaScript, a visual computer-use model,
or open-ended parameter generation. The player simulates playback state and
position; it does not download or play a real course video.

The inspector separates model choice from actual execution, reports measured
model time and browser round-trip time separately, and exposes candidate scores,
raw-logit margin, cache metadata, and the complete response. Restricted-softmax
scores are not calibrated probabilities of correctness.

## Interactive checks

These are reproduction steps, not claims that every model will pass every request.
Use the published evaluation report for measured accuracy.

1. On the desktop, ask **Open the course library**. Opening the feature should
   show the library without playing a course.
2. Ask **Only science courses**, then click **Z–A**. Ask **First one**. The first
   visible course is now **Orbit Field Notes**, not the first unfiltered course.
3. During the 1.6-second loading state, only **close.player** is executable. Pause,
   resume, and rewind become available when the player reports ready.
4. Ask **Pause it**, **Resume it**, **Go back ten seconds**, and **Close it**.
   Check the receipt and the resulting player state after each decision.
5. Ask **Close it** in the library, notes window, player, and empty desktop.
   The allowed close action changes with the focused object; none exists on the
   empty desktop.
6. Try **Did you just close it?**, **Don't close it**, an unclear request, and a
   nonexistent course. Inspect model errors as errors even if execution is blocked.
7. Submit a request, then immediately click a different page control while the
   model is working. The old result must not execute. Manual controls remain
   enabled during inference. With **Execute click** unchecked, a selected result
   can also be held and invalidated by a manual state change before execution.

Automatic loading changes the state version. A request that started while loading
may therefore become stale before inference finishes, which is intentional.

## Stateless API

`POST /v1/decide` accepts the same request fields as `DecisionRequest.from_dict`:

```sh
curl --fail-with-body http://127.0.0.1:8765/v1/decide \
  -H 'Content-Type: application/json' \
  --data-binary @examples/decision.json
```

It returns a `DecisionResult` object with `candidate_id`, `status`,
`raw_selected_id`, `raw_scores`, `scores`, `margin`, `state_version`, `model`,
`timing`, `cache`, `request_id`, and `selected_value`. Enum requests may contain an
empty candidate array so the model can return no-match or abstain. Boolean
requests require one true and one false candidate value.

The generic endpoint only computes a decision. Its supplied state version belongs
to the caller; the caller must validate execution against its own current state.
For application integration, use `DecisionSession` or an equivalent atomic
executor. A result from this stateless endpoint is not a demo execution ticket.

## Stateful demo API

| Method and route | Request | Behavior |
| --- | --- | --- |
| `GET /health` | — | Readiness and current demo state version |
| `GET /api/demo/state` | — | State, candidates, visible courses, model identity |
| `POST /api/demo/decide` | `{"utterance":"Close it"}` | Snapshot current state, infer, return result and optional browser operation; no execution |
| `POST /api/demo/execute` | `{"ticket":"issued-id","action_id":"close.notes"}` | Validate and consume the selected operation, then return actual execution receipt |
| `POST /api/demo/action` | `{"action_id":"open.notes","state_version":0}` | Apply a manual allowlisted operation against an exact version |
| `POST /api/demo/player-ready` | `{"state_version":2}` | Apply a simulated loading-complete event if its version is still current |

`409` means execution was rejected; the response includes current state.
`429` means another inference is active. `400` identifies malformed requests.
Request bodies are limited to 64 KiB. Demo utterances are limited to 4,096
characters. Unknown fields are rejected. Host, Origin, and Fetch Metadata checks
reject cross-origin browser access; no permissive CORS header is served. The
service should remain on loopback.

## CLI

```sh
jevkit decide --model /path/to/local/mlx-model --request examples/decision.json
cat examples/decision.json | jevkit decide --model /path/to/local/mlx-model
JEVKIT_MLX_MODEL=/path/to/local/mlx-model jevkit serve
```

`--no-cache` disables prefix reuse for the CLI request. A one-shot CLI command
loads a new model process; use a long-lived Python engine or HTTP service to
measure warm model behavior.

## Automated coverage

```sh
python -m pytest tests/test_demo.py tests/test_server.py -q
```

These controller and HTTP tests deliberately inject fake numeric scores to test
state transitions, single-use authorization, concurrency, input validation, and
the action mapping. They do **not** measure semantic model quality. Real-model
evaluation and browser evidence are reported separately.
