# Changelog

## 0.1.0 — prepared release

Initial experimental JEVKit MLX implementation. Public repository/registry
publication is tracked separately from preparing this source release.

- Installable Python package with dynamic enum and typed boolean requests,
  no-match and abstention, logits, restricted scores, raw margin, model identity,
  completed-work timing, and cache metadata.
- Official MLX-LM loading and final-position scoring through the original head,
  tokenizer-validated single-token codes, and local weights.
- Official prefix-cache snapshots, resource bounds, prewarm, state updates, and
  serialized inference.
- Versioned sessions with stale-result protection and single-use authorization,
  including forged/modified/replayed-result rejection.
- CLI and localhost HTTP service with Morrow Studio's fictional desktop,
  filterable/sortable library, simulated player, and real model-selected DOM
  button clicks with separate execution receipts.
- Core tests, opt-in real-model tests, fictional development/frozen fixtures,
  parity tools, one-code/JSON baselines, process cold-start measurements, and
  complete failure records.
- Architecture, framework audit, model support, evaluation protocol, recorded
  results, contribution guidance, and release instructions.

See [results](docs/results.md) for actual runs and [model support](docs/models.md)
for checkpoint-specific validation. This release does not assert universal model
support, calibrated confidence, fixed latency, zero errors, or reproduction of
JEV weights/training. GPU batching, arbitrary-site automation, training, general
chat, and multi-step planning remain outside its scope.
