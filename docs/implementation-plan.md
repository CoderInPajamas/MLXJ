# JEVKit MLX implementation plan

Status: 0.1 implemented. The package, versioned sessions, localhost service, real-model browser demo, synthetic fixtures, and measurement tools are present. Actual completed checks and limitations are recorded in [results](results.md); a source implementation or skipped test alone does not establish model compatibility.

## Product boundary

Ship a local decision SDK for Apple Silicon, with one verified model, a real local demo and reproducible measurements. The first version accepts English text and a versioned set of allowed single-step actions. It returns an allowed candidate ID or no-match/abstention, raw scores, candidate distribution, margins, model identity, state version and timing. A restricted softmax distribution is not a calibrated probability of correctness.

Keep general chat, STT/TTS, arbitrary generated arguments, multi-step planning, custom kernels and training outside the first release. Evaluate Chinese and mixed-language inputs as separate future cohorts rather than claiming support from English results.

## Runtime audit already performed

The local reference environment contains mlx 0.31.2 and mlx-lm 0.31.3. Official MLX-LM already provides model loading/quantization, cache factories, LRUPromptCache/PromptTrie, per-cache merge/extract operations and segmented prefill examples. Recheck the selected dependency version before implementing; reuse these capabilities rather than copying FounderOS's provider service or rebuilding framework internals.

The first local compatibility target is Qwen3.5-9B-OptiQ-4bit. The local checkpoint has both full-attention KV and linear-attention recurrent/convolution states. ArraysCache cannot be trimmed like a plain KV cache. Preserve a snapshot before mutable page content and rebuild its suffix when the page changes. A change to a middle prefix invalidates all later dependent state.

For a direct decision, call the official model with its official output head and select the final-position candidate logits. Do not replace a quantized head with a raw weight slice. Tokenizer-validated single-token codes map back to stable application candidate IDs. Do not describe generate(max_tokens=1) as zero-decoding: the installed generation pipeline may perform lookahead work.

## Repository layout

| Path | Responsibility |
|---|---|
| src/jevkit_mlx/ | Public decision contract and orchestration |
| src/jevkit_mlx/backends/ | Official MLX-LM integration and capability checks |
| src/jevkit_mlx/session.py | Versioned state and atomic execution; backend uses official cache primitives |
| examples/ | Python examples and local interactive desktop demo |
| benchmarks/ | Synthetic fixtures, baselines and measurement commands |
| tests/ | Contract, numerical parity and state lifecycle checks |
| docs/ | Architecture, supported models and measured results |

The implemented API uses `Candidate`, `DecisionRequest`, `MLXDecisionEngine`, and `DecisionSession`. See the [architecture](architecture.md) for the public contract and exact semantics.

## Delivery checkpoints

| Step | Deliverable | Verification | Status |
|---|---|---|---|
| 1 | Installable package, contracts, compile_choices and MLXDecisionEngine.decide | Core tests and actual local scoring | Implemented; see results |
| 2 | DecisionSession.update_state, prefix snapshots and prewarm | Numeric cache parity plus stale/replay/forgery tests | Implemented; see results |
| 3 | CLI, localhost service, desktop/library/player and DOM adapter | Separate model decision, actual click, receipt and observed state | Implemented; see browser evidence |
| 4 | Frozen public benchmark, compact-code and generated-JSON baselines | Every attempt retained, p50/p95 and quality per condition | Implemented; batching deferred |
| 5 | Wheel/sdist, English documentation, CI configuration and public assets | Clean wheel install; reviewed source and synthetic evidence | Prepared locally; publication needs a destination |

Multi-question batching follows single-question correctness. Prefer the framework's separate batch branches and cache merge operations. Do not impose a custom attention-only block mask on a hybrid recurrent model. A failed batching optimization must not block publishing a clearly scoped single-question experimental release.

## Public evaluation

Create data from scratch, using fictional names and simulated state; do not export or anonymize production databases, recordings, screenshots or conversation traces. Start with a development split and a separate frozen test split, grouped by scenario families.

Cover: close-it with different/no opened objects; opening a feature versus selecting its contents; first-item selection after filtering; library/loading/ready player states; status questions, negations and ambiguous requests; candidate-order permutations; a page change while inference is pending. Include deterministic scripts proving stale results cannot execute.

Report raw model accuracy, execution precision, executable-request coverage, abstention, schema validity and host-rejected proposals separately. Host validation catching a wrong answer does not make the model answer correct. Fit any rejection thresholds on development data and freeze them before testing.

Measure process/model cold start separately from inference with loaded weights. Report cold KV, warm stable state with fresh utterances, and first inference after a state update. Include model/quantization/runtime revisions, hardware, prompt sizes, candidate counts, p50/p95, memory and failed attempts. Synchronize MLX work for timing. Do not substitute a cached final answer for a fresh decision.

Fair baselines include the same model returning a single option code under the same context and cache conditions, plus a structured JSON/tool-generation baseline. Compare serial and batched questions separately. Do not imply speedups over the strongest baseline until measured, or advertise a fixed 100ms target as achieved.

## Publication

The planned first distribution is a public GitHub repository, an installable Python package, documentation and a local demo with authentic recordings. Public pages can show recorded results; actual MLX inference runs on an Apple Silicon machine. Package names and remote repository availability are not reserved by creating this local directory.

Keep model weights external. Verify each supported checkpoint's upstream and conversion licenses. Preserve attribution for any third-party code actually reused. This project is independently maintained, inspired by JEV, and does not claim TypeSafe affiliation, JEV weights, RLCD reproduction or calibrated accuracy without evidence.
