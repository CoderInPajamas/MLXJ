<p align="center"><a href="README.md">简体中文</a> · <strong>English</strong></p>

<p align="center">
  <img src="docs/assets/mlxj-hero.en.svg" alt="MLXJ — JEV-inspired local decisions, powered by MLX" width="1280" />
</p>

<p align="center"><strong>Current state + a sentence → one allowed choice.</strong><br />JEV-inspired local decisions for Apple Silicon.</p>

<p align="center">
  <img src="docs/assets/badges/apple-silicon.svg" alt="Apple Silicon" />
  <img src="docs/assets/badges/python.svg" alt="Python 3.11+" />
  <a href="LICENSE"><img src="docs/assets/badges/license.svg" alt="MIT License" /></a>
  <a href="CHANGELOG.md"><img src="docs/assets/badges/release.svg" alt="0.1 experimental, not published" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#results">Measured results</a> ·
  <a href="docs/evaluation.md">Methodology</a> ·
  <a href="#replay">Static replay</a> ·
  <a href="#connect">Connect & support</a>
</p>

<p align="center">
  <a href="https://xhslink.com/m/18bjTTf180W"><img src="docs/assets/badges/follow-xiaohongshu.svg" alt="Follow 里奥YetAnotherLeo on Xiaohongshu, account ID 6236648830" /></a>
  <a href="https://x.com/YetAnotherLeo"><img src="docs/assets/badges/follow-x.svg" alt="Follow @YetAnotherLeo on X / Twitter" /></a>
</p>

---

## Connect language to your application

**MLXJ** uses the current application state, a user utterance, and dynamic allowed choices to select a stable business ID with a local model. No-match and abstention are explicit outcomes.

Embed it in an existing tool: open a feature, select a visible item, pause a player, or answer a boolean / enum question. Inference runs on your Mac with an existing checkpoint; no training is required.

> **Naming preview:** MLXJ is the candidate name used in this README preview. The working distribution and CLI remain `jev-mlx`, with Python imports from `jev_mlx`. Version 0.1 is experimental and has not been published to PyPI.

| Capability | What it means for your application |
| :--- | :--- |
| **Dynamic choices** | Update allowed actions with the page; keep your own stable business IDs. |
| **Explicit rejection** | Return `no_match` or `abstain` when an action is not appropriate. |
| **Version protection** | Reject stale decisions after state changes; consume execution authorization once. |
| **Prefix reuse** | Reuse stable context while evaluating every new utterance. Never cache final answers. |
| **Small integration surface** | Python API, CLI, and a localhost HTTP service. |

Models can make mistakes. Candidate scores rank choices and are **not calibrated probabilities of correctness**. State guards do not establish semantic correctness.

<a name="quick-start"></a>

## Quick start

Requires **Apple Silicon, native ARM Python 3.11+**, and a local MLX-LM checkpoint. Start with the verified Qwen checkpoint in the [model table](docs/models.md).

From this checkout:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mlx]'
export JEV_MLX_MODEL=/absolute/path/to/your/local/mlx-model
```

```python
import os
from jev_mlx import Candidate, DecisionRequest, MLXDecisionEngine

engine = MLXDecisionEngine(os.environ["JEV_MLX_MODEL"])
result = engine.decide(DecisionRequest(
    state={"focused_window": "notes"},
    utterance="Close it",
    candidates=(Candidate("close.notes", "Close the open notes window"),),
    state_version=1,
))

print(result.status, result.candidate_id)
print(result.margin, result.timing)
```

The CLI uses the same request contract:

```sh
jev-mlx decide --request examples/decision.json
```

Results include the candidate ID, raw logits, candidate scores, margin, state version, model identity, actual timing, and cache details. See the [Python API](docs/python-api.md) for booleans, state updates, and versioned execution.

<a name="results"></a>

## Measurements, with their limits

**Apple M2 Max · 64 GiB · 28 fictional English test cases · revised cache runtime.**

| Local checkpoint | Exact decisions | Wrong action choices / all requests | Same-page p50 / p95 |
| :--- | ---: | ---: | ---: |
| Qwen3.5-9B-OptiQ-4bit | **25 / 28 (89.3%)** | **0 / 28** | **171.7 / 176.4 ms** |
| GLM-4.7-Flash-4bit | 14 / 28 (50.0%) | 2 / 28 | 147.8 / 170.6 ms |

These timings require **loaded weights and a reusable page prefix**. Qwen's KV-cold p50 was **2,159.9 ms**; its first decision after a page update was **1,050.2 ms**. About 170 ms is not a per-request guarantee.

- **145 core tests passed:** contracts, state updates, stale decisions, single-use authorization, HTTP, and related behavior. These do not measure model semantics.
- **112 / 112 cache comparisons passed:** two models × 28 cases × two reuse conditions, each compared with fresh computation.
- **16 recorded browser scenarios checked:** actual DOM clicks and execution receipts. Decline cases accept either rejection outcome, unlike the strict quality set above.

Qwen's three misses include rejection-status distinctions and a tied choice after reordering. GLM produced incorrect actions and is **not recommended for automatic execution with the current prompt**. A 28-case sample cannot establish zero errors or broad reliability.

<details>
<summary><strong>How was this tested?</strong></summary>

1. Write **16 development cases and 28 frozen test cases** from scratch, with no production exports. Version 0.1 validates English inputs only.
2. Refine the general prompt on development data, then freeze the semantic prompt and rejection threshold. Do not tune the threshold on test data.
3. Compare the same model using direct candidate scoring, one-code generation, and structured JSON generation. Retain failed outputs.
4. Measure process startup, loaded weights with cold KV, a new utterance on the same page, and the first decision after a page update. Synchronize MLX work before stopping the timer.
5. Score model choice separately from execution. A guard blocking a bad action does not make the model correct.

Repeating 28 cases under several cache conditions does not create more independent samples. The historical one-code baseline reached 26/28, slightly better than the direct returned decision. Direct scoring did not dominate every quality and latency metric. A supplementary JSON-format experiment was informed by earlier test results and is explicitly labeled as such.

The [full report](docs/results.md) includes p50/p95, rejection, executable coverage, memory, versions, input sizes, reproduction commands, and original cache failures. Do not combine timings from different code revisions to calculate a speedup. A [Chinese testing guide](docs/testing.zh-CN.md) is also available.

</details>

<a name="replay"></a>

## Explore a real recording without installing a model

The **fully static recorded replay** lets you choose a scenario and inspect its original utterance, candidates, model choice, timing, and execution receipt. It uses saved test evidence and needs no server, model, or external network.

**[Open the static replay file](docs/demo/index.html)** · [Original browser transcript](docs/assets/browser-demo/browser-transcript.json)

GitHub displays HTML files as source. Clone or download the repository, then open `docs/demo/index.html` in a browser. It can also be hosted on a static site once a public destination is chosen.

<details>
<summary><strong>See the original screenshot and the live-inference boundary</strong></summary>

![Real local browser test, captured under the former project name](docs/assets/browser-demo/03b-player-control.png)

The screenshot and recording retain their original branding. The static replay does not infer new free-text requests or operate the desktop again. Live decisions require `jev-mlx serve` on Apple Silicon; see the [local HTTP and browser guide](docs/http-and-demo.md).

The browser integration operates allowlisted DOM controls in a fictional application. It is not arbitrary website navigation or visual computer use.

</details>

## How a choice is made

```text
Application state + utterance + allowed choices
                       │
               Official MLX-LM model
                       │
           Final-position candidate logits
                       │
          selected(id) / no_match / abstain
                       │
       Application version check → execution → receipt
```

Choices map to tokenizer-verified single-token codes, then back to business IDs. Direct scoring reads a causal model's next-token logits without generating a JSON continuation. It retains the official quantized output head. Hybrid caches reuse only complete, valid prefix boundaries.

See the [architecture](docs/architecture.md) and [framework audit](docs/framework-audit.md). Version 0.1 focuses on **English, single-turn, single-step choices**. General chat, multi-step planning, arbitrary arguments, vision, training, and GPU batching are outside its scope. **Chinese documentation does not mean Chinese model behavior has been validated.**

## Documentation

| Guide | Contents |
| :--- | :--- |
| [Python API](docs/python-api.md) | Enum / boolean, result fields, and versioned execution |
| [Model compatibility](docs/models.md) | Checkpoints, quantization, dependencies, licenses, and limits |
| [Evaluation](docs/evaluation.md) · [Results](docs/results.md) | All baselines, raw evidence, versions, and failures |
| [Chinese testing guide](docs/testing.zh-CN.md) | Methodology, results, and reproduction in Chinese |
| [Local HTTP](docs/http-and-demo.md) | CLI, service, and actual browser operations |
| [Contributing](CONTRIBUTING.md) · [Releasing](docs/releasing.md) | Development, builds, and publication |

<details>
<summary><strong>Run development checks</strong></summary>

```sh
python -m pip install -e '.[dev]'
python -m pytest -m 'not model'
python -m ruff check src tests benchmarks scripts examples
```

Real-model tests require explicitly selected local weights. Run model workloads sequentially. GitHub CI is configured; no remote CI pass is claimed.

</details>

<a name="connect"></a>

## Connect & support

Share use cases, reproduction results, and suggestions. Issues, documentation fixes, and new public test cases also support the project.

<p align="center"><strong>里奥YetAnotherLeo</strong><br />Xiaohongshu ID: <code>6236648830</code></p>

<p align="center"><a href="https://xhslink.com/m/18bjTTf180W">Xiaohongshu · 里奥YetAnotherLeo ↗</a> · <a href="https://x.com/YetAnotherLeo">X / Twitter · @YetAnotherLeo ↗</a></p>

<details>
<summary><strong>Scan the Xiaohongshu profile card</strong></summary>

<p align="center"><img src="docs/assets/social/xiaohongshu-profile.jpg" alt="Xiaohongshu profile card for 里奥YetAnotherLeo, ID 6236648830" width="320" /></p>

Original public profile card supplied by the owner. The QR code has not been redrawn or modified.

</details>

<p align="center"><sub>A sponsorship destination is still awaiting an owner-provided public link. No payment link or donation QR code is enabled.</sub></p>

## License & inspiration

[MIT](LICENSE). Independently maintained, inspired by [TypeSafe AI's JEV](https://docs.typesafe.ai/), and built on official [MLX-LM](https://github.com/ml-explore/mlx-lm). No affiliation or endorsement, no JEV weights, and no claim to reproduce unpublished RLCD.

Models and dependencies retain their own licenses; see [NOTICE](NOTICE.md). Recorded evidence retains former project names, source paths, and hashes as explained in [results](docs/results.md). See the [naming research](docs/naming.md) for the candidate name.

<p align="center"><sub>Local decisions. Visible evidence. Open source.</sub></p>
