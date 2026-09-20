# Recorded browser decisions

[Back to home](../../README.en.md)

Open `index.html` directly in a browser, including through `file://`. This is an
offline, bilingual **recorded replay**, not a live model demonstration. It needs
no Python runtime, model, HTTP server, CDN, or network connection at viewing time.

The page exposes all 16 cases and the separate state-change check from the
existing public [browser transcript](../assets/browser-demo/browser-transcript.json).
It preserves the original English utterances, candidate IDs, logits, scores,
measured timings, cache information, and execution receipts. The interface follows
the language selected on the homepage (`?lang=en` or `?lang=zh-CN`); opening the
file without a language defaults to Chinese. Recorded inputs and results are
unchanged in either language. Missing fields remain missing.

The original artifacts retain the project's previous name. They have not been
rewritten or retouched. The replay uses the current MLXJ display name for its interface. Python and CLI identifiers remain `jev_mlx` and `jev-mlx`.
This single browser smoke run is separate from the held-out model benchmark;
see [measured results and limitations](../results.md).

## Exact screenshot associations

| Recorded case | Original screenshot |
| --- | --- |
| `open-feature-without-playing-content` | `02-library.png` |
| `first-follows-filtered-reversed-visible-order` | `03-course-player.png` |
| `pause-ready-player` | `03b-player-control.png` |
| Separate `state_change_check` | `04-stale-protection.png` |

`01-desktop.png` shows the initial desktop **before any decision** and is linked
separately. Every other case explicitly says that no per-case screenshot was
captured. A screenshot is never substituted from a neighboring case. The complete
original WebM recording is linked without invented per-case timestamps.

The concurrency check did not store its original utterance, pre-change state, or
an execution receipt. The page shows those gaps instead of reconstructing them.
Its recorded `old_result_not_executed` check is displayed separately from the
raw model choice. Candidate scores are not calibrated correctness probabilities.

## Rebuild the offline data bundle

```sh
python docs/demo/build_data.py
```

The standard-library script reads only the public transcript and artifact
provenance. It verifies every original artifact SHA-256, omits the unnecessary
capture loopback URL, rejects unexpected local-user paths or credential markers,
and writes `data.js`. It does not alter source evidence. No `fetch` is used, so
the same files work when double-clicked locally or served by static hosting.
The page's CSP disallows network connections (`connect-src 'none'`).
