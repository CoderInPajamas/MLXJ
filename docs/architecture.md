# Architecture

[Back to home](../README.md)

JEV MLX 0.1 selects from a bounded set of application-supplied choices. Its
model path is semantic scoring; its execution path is explicit host code. Model
prediction, execution authorization, and execution receipt remain separate.

## Public contracts

`Candidate(id, description, value=None)` carries a stable business ID, semantic
description, and optional JSON value. `DecisionRequest` carries JSON state, the
utterance, candidates, a nonnegative `state_version`, a question, and `kind="enum"`
or `kind="boolean"`. Strict `from_dict` and `to_dict` conversions support external
clients. An empty application candidate list is valid: no-match and abstention
remain available.

Candidate IDs must be unique and cannot use `__no_match__` or `__abstain__`. JSON
requires string object keys and finite numbers. Inputs are copied at validation
and inference/session boundaries. Frozen fields do not make nested JSON objects
intrinsically immutable; callers should treat them as values. Sessions also
fingerprint issued results and reject modification before execution.

| Bound | Default |
|---|---|
| Application candidates | 64, plus two reserved outcomes |
| Candidate ID / description | 128 / 2,048 characters |
| Candidate JSON value | 16,384 UTF-8 bytes |
| State JSON | 131,072 UTF-8 bytes; at most 16 nesting levels |
| Utterance / question | 16,384 / 2,048 characters |
| Tokenized prompt | 4,096 tokens |
| Prefill chunk | 256 tokens |
| Prefix cache | 512 MiB, at most 16 entries |
| Outstanding session authorizations | Latest 256 selected results |

Backend prompt, prefill, and cache limits can be configured through
`MLXDecisionEngine(model, **backend_options)`. They are resource limits, not model
context-length guarantees. Token-code availability and chat-template validation
can reject a request below these bounds.

## Local model path

`MLXDecisionEngine` imports MLX lazily when constructing a real model engine.
Contracts, sessions, and injected-backend tests work without MLX. `MLXLMBackend`
requires a local directory with `config.json` and uses official `mlx_lm.load`
with `trust_remote_code=False`. It neither downloads nor edits weights.

`prompt.py` serializes state, question, candidate descriptions/values, and
utterance into the checkpoint's chat template. Its policy describes negation,
unavailable targets, visible order, status questions, and ambiguity. This is a
model instruction, not a phrase-specific rule engine. Boolean mode answers the
supplied factual question: `False` is a selected typed value; insufficient
evidence may cause abstention.

The compiler searches numerical and ASCII codes, verifies unique single-token
encodings and round trips, and checks one-token continuation of the complete
prompt. Codes are internal: reordering candidates can change codes while business
IDs remain stable. Visible order is explicit state for the model to interpret;
candidate order is not substituted for UI order.

After prefill, the backend calls the official model for the final input position
and indexes candidate logits from the unchanged output head, including its
quantized head when present. It does not replace that head with a sliced weight
matrix. No generated continuation is used for direct decisions. The method still
uses a causal language model's next-token distribution; it does not establish a
new non-autoregressive architecture or reproduce JEV training.

## Result semantics and timing

The engine verifies finite scores for exactly the current candidates and reserved
outcomes, computes stable restricted softmax scores, and reports the gap between
the largest two raw logits. These are not calibrated correctness probabilities.
The default `margin_threshold=0.0` rejects exact ties. A positive threshold can
reject a small margin; `raw_selected_id` retains the underlying winner.

| Status | Meaning | Executable ID |
|---|---|---|
| `selected` | One supplied application choice won | `candidate_id` |
| `no_match` | No requested action or answer applies | `None` |
| `abstain` | Ambiguity, insufficient evidence, or threshold rejection | `None` |
| `stale` | Session state changed during inference | `None` |

`selected_value` copies the chosen candidate's JSON value and is `None` for
nonselected results. A selected candidate may itself have value `None`; inspect
`status`. Metadata includes version, request ID, model/configuration/tokenizer
identities, dependencies, quantization, cache types, timings, and cache reuse.
It is not a complete weight-file fingerprint; retain checkpoint provenance too.

MLX schedules work lazily. The backend evaluates logits and all cache states and
synchronizes before measuring completed inference. Backend timing separates
queue wait, inference, and load. Engine `decision_ms` measures its scoring and
orchestration interval; HTTP round-trip time includes transport and browser work.
Memory peaks are process-lifetime values, not per-decision allocations.

## Stable-prefix snapshots

The implementation reuses official `make_prompt_cache` and `LRUPromptCache`;
see the [framework audit](framework-audit.md). Cache namespaces separate sessions
and output modes, with separate system/page snapshot namespaces under one shared
LRU capacity limit. Actual token sequences identify reusable content. State version
is host metadata rather than an answer-cache key.

Two full snapshot boundaries matter:

1. Before mutable page content.
2. After stable state and candidates, before the current utterance.

A tokenizer can merge across nominal text boundaries. The builder retains only
an exact token prefix common to the complete encoded prompt, rather than assuming
text offsets are safe cache boundaries.

The same page with a new utterance can reuse the second snapshot and must compute
the new suffix. A state, candidate, or question change invalidates its dependent
suffix; only the complete saved system snapshot can then be reused. The SDK
discards nearest-cache matches trimmed at intermediate positions, including for
attention-only models. This keeps prefill boundaries aligned with fresh calls;
the earlier GLM numerical failure and subsequent validation are recorded in
[results](results.md). Hybrid models such as
Qwen3.5 include recurrent/convolution state as well as attention KV. Full earlier
snapshots preserve both. The implementation does not roll recurrent state back
like KV, replace a middle prefix while retaining later state, or invent an
attention mask for independent questions.

`session.prewarm()` computes stable-prefix state only and reports its captured
version, current version, and `ready` or `stale`. It issues no decision or execution
authorization. Cache eviction can cause a later miss. Final answers are never
cached. Real numerical and selected-action parity require actual model runs;
see [evaluation](evaluation.md) and [results](results.md) for tolerances and outcomes.

## State and execution lifecycle

`DecisionSession.decide` snapshots state/candidates under a lock, releases it
during inference, and rechecks the captured version afterward. `update_state`
atomically replaces state and optional candidates, increments the version, and
invalidates outstanding action authorizations. Applications must call it for
every change relevant to validity, including manual clicks and loading/ready
transitions.

`execute(result, callback)` requires an intact object issued by this session, a
selected candidate, the current version, and an unconsumed request ID. It consumes
authorization before application code and holds the state lock through the
callback. A callback failure cannot automatically replay a partial effect.
Callbacks may update state reentrantly. If the host has another state lock,
consistently acquire the host lock before the session lock.

`StaleDecisionError`, `ReplayDecisionError`, and `InvalidDecisionError` derive
from `DecisionExecutionError`. The callback returns the application receipt.
Passing these checks means the action was current and issued by this session,
not semantically correct. HTTP clients receive opaque tickets to server-held
results; deserializing result JSON cannot recreate execution authorization.

## Browser and service boundary

The localhost service serves packaged Morrow Studio assets and the HTTP API.
Its desktop and courses are fictional. The demo derives allowed actions from
the current view, filter, sort, and player readiness. A selected ID becomes an
allowlisted click operation for an existing `data-action` control. Browser code
invokes that control's actual click handler with a server-issued ticket. The
server validates and consumes the ticket before applying a state transition.
Manual controls use the same state machine and invalidate pending decisions.

The UI reports model decision, browser event, and server execution receipt
separately. Its simulated player does not decode actual video. The model does
not receive screenshots, locate arbitrary DOM targets, generate JavaScript, or
operate unrelated websites. See [HTTP and demo documentation](http-and-demo.md)
for request formats and local-service constraints.

## Deferred work

The backend serializes calls and uses existing checkpoints. GPU batching,
multi-step planning, general chat, STT, arbitrary tool arguments, new training,
and universal checkpoint compatibility are outside 0.1. Future parallel inference
should reuse official batch/cache capabilities and verify hybrid-state and
numerical parity before claiming support.
