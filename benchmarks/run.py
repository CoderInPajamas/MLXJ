"""Run honest same-model comparisons: python -m benchmarks.run --help."""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import random
import time
from pathlib import Path
from typing import Any

from .common import (
    as_dict,
    environment_metadata,
    load_fixtures,
    memory_snapshot,
    request_from_dict,
    sanitize,
)
from .metrics import grouped_summary

MODES = ("direct", "code", "json")
CONDITIONS = ("kv_cold", "same_page_new_utterance", "page_update")


def call(engine, request, mode: str, *, cache_key: str, use_cache: bool) -> dict[str, Any]:
    if mode == "direct":
        result = as_dict(engine.decide(request, cache_key=cache_key, use_cache=use_cache))
        result["schema_valid"] = result.get("status") in {"selected", "no_match", "abstain"}
        return result
    return as_dict(
        engine.backend.generate_baseline(
            request, mode=mode, cache_key=cache_key, use_cache=use_cache
        )
    )


def attempt(engine, case: dict[str, Any], mode: str, condition: str, repeat: int) -> dict[str, Any]:
    request = request_from_dict(case["request"])
    key = f"benchmark:{case['id']}:{mode}:{condition}:{repeat}"
    row = {
        "case_id": case["id"],
        "family": case["family"],
        "mode": mode,
        "condition": condition,
        "repeat": repeat,
        "expected": case["expected"],
        "candidate_count": len(request.candidates),
        "utterance_chars": len(request.utterance),
        "state_chars": len(json.dumps(request.state, sort_keys=True)),
        "state_version": request.state_version,
        "prediction": None,
        "error": None,
        "preparation": None,
    }
    start = time.perf_counter()
    try:
        if condition != "kv_cold":
            warmup = (
                dataclasses.replace(request, utterance=case["warmup_utterance"])
                if condition == "same_page_new_utterance"
                else request_from_dict(case["previous_request"])
            )
            start = time.perf_counter()
            prepared = call(engine, warmup, mode, cache_key=key, use_cache=True)
            row["preparation"] = {
                "wall_ms": (time.perf_counter() - start) * 1000,
                "prediction": prepared,
            }
    except Exception as exc:
        failed_preparation_ms = (time.perf_counter() - start) * 1000
        row["preparation"] = {
            "wall_ms": failed_preparation_ms,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
        row["error"] = {"phase": "preparation", "type": type(exc).__name__, "message": str(exc)}
        row["wall_ms"] = failed_preparation_ms
        row["memory"] = memory_snapshot()
        return row
    start = time.perf_counter()
    try:
        row["prediction"] = call(
            engine, request, mode, cache_key=key, use_cache=condition != "kv_cold"
        )
    except Exception as exc:
        row["error"] = {"phase": "decision", "type": type(exc).__name__, "message": str(exc)}
    row["wall_ms"] = (time.perf_counter() - start) * 1000
    row["memory"] = memory_snapshot()
    return row


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    if not scores or any(not math.isfinite(value) for value in scores.values()):
        raise ValueError("Parity requires nonempty, finite raw scores")
    peak = max(scores.values())
    values = {key: math.exp(value - peak) for key, value in scores.items()}
    total = sum(values.values())
    return {key: value / total for key, value in values.items()}


def parity_attempt(
    engine, case: dict[str, Any], *, atol: float, rtol: float, score_atol: float = 0.1
) -> dict[str, Any]:
    """Independent forward passes compare fresh/cached and updated/fresh logits."""
    request = request_from_dict(case["request"])
    row: dict[str, Any] = {
        "case_id": case["id"],
        "atol": atol,
        "rtol": rtol,
        "score_atol": score_atol,
        "passed": False,
        "error": None,
    }
    try:
        backend = engine.backend
        fresh = as_dict(backend.score(request, use_cache=False))
        key = f"parity:warm:{case['id']}"
        backend.score(
            dataclasses.replace(request, utterance=case["warmup_utterance"]),
            cache_key=key,
            use_cache=True,
        )
        warm = as_dict(backend.score(request, cache_key=key, use_cache=True))
        update_key = f"parity:update:{case['id']}"
        backend.score(
            request_from_dict(case["previous_request"]), cache_key=update_key, use_cache=True
        )
        updated = as_dict(backend.score(request, cache_key=update_key, use_cache=True))
        for label, result in (("same_page", warm), ("page_update", updated)):
            a, b = fresh["raw_scores"], result["raw_scores"]
            a_scores, b_scores = _softmax(a), _softmax(b)
            same_keys = a.keys() == b.keys()
            differences = {k: abs(a[k] - b[k]) for k in a if k in b}
            score_difference = max(
                (abs(a_scores[k] - b_scores[k]) for k in a if k in b), default=None
            )
            close = same_keys and all(
                math.isclose(a[k], b[k], rel_tol=rtol, abs_tol=atol) for k in a
            )
            row[label] = {
                "allclose": close,
                "max_abs_difference": max(differences.values(), default=None),
                "same_top_choice": max(a, key=a.get) == max(b, key=b.get),
                "max_score_difference": score_difference,
                "scores_close": same_keys
                and score_difference is not None
                and score_difference <= score_atol,
                "cache": result.get("cache"),
                "raw_scores": b,
            }
        row["fresh_raw_scores"] = fresh["raw_scores"]
        row["model"] = fresh.get("model")
        row["passed"] = all(
            row[label]["allclose"] and row[label]["same_top_choice"] and row[label]["scores_close"]
            for label in ("same_page", "page_update")
        )
    except Exception as exc:
        row["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return row


def run_summary(rows, planned, parity_rows, parity_planned):
    """A requested parity phase is part of run completion and success."""
    failed_parity = sum(not row["passed"] for row in parity_rows)
    return {
        "completed": len(rows),
        "planned": planned,
        "measurements_complete": len(rows) == planned,
        "complete": len(rows) == planned and len(parity_rows) == parity_planned,
        "groups": grouped_summary(rows),
        "parity": {
            "completed": len(parity_rows),
            "planned": parity_planned,
            "passed": len(parity_rows) - failed_parity,
            "failed": failed_parity,
        },
    }


def exit_code(rows, parity_rows):
    return (
        1
        if any(row["error"] for row in rows) or any(not row["passed"] for row in parity_rows)
        else 0
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", required=True, help="Local MLX model directory; weights are never modified"
    )
    parser.add_argument("--split", choices=("dev", "test"), default="test")
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES))
    parser.add_argument(
        "--conditions", "--cohorts", nargs="+", choices=CONDITIONS, default=list(CONDITIONS)
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--limit", type=int, help="Smoke subset only; never label this a full test result"
    )
    parser.add_argument(
        "--seed", type=int, default=20260919, help="Fixed shuffle interleaves modes and conditions"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--parity",
        action="store_true",
        help="Also compare cached/update logits against fresh passes",
    )
    parser.add_argument("--parity-atol", type=float, default=0.5)
    parser.add_argument("--parity-rtol", type=float, default=0.0)
    parser.add_argument("--parity-score-atol", type=float, default=0.1)
    parser.add_argument("--margin-threshold", type=float, default=0.0)
    args = parser.parse_args(argv)
    if args.repeats < 1 or (args.limit is not None and args.limit < 1):
        parser.error("repeats and limit must be positive")
    if any(
        not math.isfinite(value) or value < 0
        for value in (args.parity_atol, args.parity_rtol, args.parity_score_atol)
    ):
        parser.error("parity tolerances must be finite and nonnegative")
    if args.split == "test" and args.margin_threshold != 0.0:
        parser.error(
            "Frozen test policy uses margin threshold 0.0; tune on dev and freeze a new protocol before a new test split"
        )
    cases, manifest = load_fixtures(args.split)
    total_cases = len(cases)
    if args.limit:
        cases = cases[: args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    if any(
        (args.output / name).exists()
        for name in ("metadata.json", "trials.jsonl", "summary.json", "parity.jsonl")
    ):
        parser.error("Output already contains a run; use a new directory to retain all attempts")
    metadata = {
        "schema_version": 1,
        "model_name": Path(args.model).name,
        "environment": environment_metadata(),
        "fixtures": manifest,
        "split": args.split,
        "scope": "full" if len(cases) == total_cases else "smoke_subset",
        "case_count": len(cases),
        "full_split_case_count": total_cases,
        "modes": args.modes,
        "conditions": args.conditions,
        "repeats": args.repeats,
        "seed": args.seed,
        "margin_threshold": args.margin_threshold,
        "generation": {"sampling": "greedy", "code_max_tokens": 1, "json_max_tokens": 96},
        "parity": {
            "enabled": args.parity,
            "atol": args.parity_atol,
            "rtol": args.parity_rtol,
            "score_atol": args.parity_score_atol,
            "same_top_choice_required": True,
        },
        "notes": [
            "Model decisions scored before any execution gate.",
            "Preparation calls are recorded and excluded from measured decision latency.",
            "Wall times include backend synchronization; failed attempts are retained.",
            "OS filesystem caches are not flushed; loaded-model inference is separate from process cold start.",
        ],
    }

    def write_json(name, value):
        (args.output / name).write_text(
            json.dumps(sanitize(value, args.model), indent=2, allow_nan=False) + "\n"
        )

    write_json("metadata.json", metadata)
    load_start = time.perf_counter()
    try:
        from jevkit_mlx import MLXDecisionEngine

        engine = MLXDecisionEngine(model=args.model, margin_threshold=args.margin_threshold)
    except Exception as exc:
        metadata["load_error"] = {"type": type(exc).__name__, "message": str(exc)}
        metadata["engine_load_wall_ms"] = (time.perf_counter() - load_start) * 1000
        write_json("metadata.json", metadata)
        return 2
    metadata["engine_load_wall_ms"] = (time.perf_counter() - load_start) * 1000
    metadata["memory_after_load"] = memory_snapshot()
    write_json("metadata.json", metadata)
    schedule = [
        (case, mode, condition, repeat)
        for repeat in range(args.repeats)
        for case in cases
        for mode in args.modes
        for condition in args.conditions
    ]
    random.Random(args.seed).shuffle(schedule)
    rows = []
    parity_rows = []
    parity_planned = len(cases) if args.parity else 0
    with (args.output / "trials.jsonl").open("w") as log:
        for index, (case, mode, condition, repeat) in enumerate(schedule, 1):
            row = sanitize(attempt(engine, case, mode, condition, repeat), args.model)
            row["trial_index"] = index
            rows.append(row)
            log.write(json.dumps(row, allow_nan=False) + "\n")
            log.flush()
            write_json(
                "summary.json", run_summary(rows, len(schedule), parity_rows, parity_planned)
            )
            print(
                f"{index}/{len(schedule)} {case['id']} {mode}/{condition}: {'ERROR' if row['error'] else row['prediction'].get('status')} {row['wall_ms']:.1f} ms",
                flush=True,
            )
    if args.parity:
        with (args.output / "parity.jsonl").open("w") as log:
            for index, case in enumerate(cases, 1):
                row = sanitize(
                    parity_attempt(
                        engine,
                        case,
                        atol=args.parity_atol,
                        rtol=args.parity_rtol,
                        score_atol=args.parity_score_atol,
                    ),
                    args.model,
                )
                parity_rows.append(row)
                log.write(json.dumps(row, allow_nan=False) + "\n")
                log.flush()
                write_json(
                    "summary.json", run_summary(rows, len(schedule), parity_rows, parity_planned)
                )
                print(
                    f"parity {index}/{len(cases)} {case['id']}: {'ERROR' if row['error'] else row['passed']}",
                    flush=True,
                )
    metadata["memory_at_end"] = memory_snapshot()
    write_json("metadata.json", metadata)
    return exit_code(rows, parity_rows)


if __name__ == "__main__":
    raise SystemExit(main())
