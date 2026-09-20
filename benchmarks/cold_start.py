"""Measure fresh Python process + model load + first decision, sequentially."""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

from .common import (
    environment_metadata,
    load_fixtures,
    memory_snapshot,
    request_from_dict,
    sanitize,
)
from .metrics import grouped_summary


def worker(args) -> int:
    from .run import call

    cases, _ = load_fixtures(args.split, args.fixtures_dir)
    case = cases[0]
    row = {
        "case_id": case["id"],
        "family": case["family"],
        "mode": args.mode,
        "condition": "process_cold_start",
        "expected": case["expected"],
        "error": None,
        "prediction": None,
    }
    start = time.perf_counter()
    try:
        from jev_mlx import MLXDecisionEngine

        engine = MLXDecisionEngine(model=args.model, margin_threshold=0.0)
        row["load_wall_ms"] = (time.perf_counter() - start) * 1000
        row["prediction"] = call(
            engine,
            request_from_dict(case["request"]),
            args.mode,
            cache_key="cold_start",
            use_cache=False,
        )
    except Exception as exc:
        row["error"] = {"type": type(exc).__name__, "message": str(exc)}
    row["worker_wall_ms"] = (time.perf_counter() - start) * 1000
    row["memory"] = memory_snapshot()
    args.worker_record.write_text(json.dumps(sanitize(row, args.model), allow_nan=False) + "\n")
    return 1 if row["error"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--split", choices=("dev", "test"), default="test")
    parser.add_argument("--fixtures-dir", type=Path, help="Separate frozen suite directory")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=("direct", "code", "json", "json_code"),
        default=["direct", "code", "json"],
    )
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--worker-record", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--mode", choices=("direct", "code", "json", "json_code"), help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    if args.worker_record:
        return worker(args)
    if not args.output or args.repeats < 1 or args.timeout <= 0:
        parser.error("output is required; repeats and timeout must be positive")
    cases, manifest = load_fixtures(args.split, args.fixtures_dir)
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Output directory must be empty so earlier attempts cannot be overwritten")
    metadata = {
        "environment": environment_metadata(),
        "fixtures": manifest,
        "split": args.split,
        "model_name": Path(args.model).name,
        "repeats": args.repeats,
        "scope": "first_fixture_only",
        "os_filesystem_cache_flushed": False,
        "notes": "Fresh Python process and model weights per attempt; OS disk cache is intentionally not flushed. Parent wall time includes interpreter startup, load, first decision, and shutdown. One repetition cannot establish stable percentiles.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    jobs = [(mode, repeat) for repeat in range(args.repeats) for mode in args.modes]
    random.Random(20260919).shuffle(jobs)
    rows = []
    with (args.output / "trials.jsonl").open("w") as log:
        for index, (mode, repeat) in enumerate(jobs, 1):
            record = args.output / f"worker-{index}.json"
            command = [
                sys.executable,
                "-m",
                "benchmarks.cold_start",
                "--model",
                args.model,
                "--split",
                args.split,
                "--mode",
                mode,
                "--worker-record",
                str(record),
            ]
            if args.fixtures_dir is not None:
                command.extend(["--fixtures-dir", str(args.fixtures_dir)])
            start = time.perf_counter()
            row = {
                "case_id": cases[0]["id"],
                "expected": cases[0]["expected"],
                "mode": mode,
                "condition": "process_cold_start",
                "error": None,
                "prediction": None,
            }
            try:
                process = subprocess.run(
                    command, text=True, capture_output=True, check=False, timeout=args.timeout
                )
                if record.exists():
                    row.update(json.loads(record.read_text()))
                else:
                    row["error"] = {
                        "type": "WorkerFailed",
                        "message": "Worker did not produce a result",
                    }
                row["returncode"] = process.returncode
                row["worker_stdout"] = process.stdout
                row["worker_stderr"] = process.stderr
                if process.returncode != 0 and row["error"] is None:
                    row["error"] = {
                        "type": "WorkerExit",
                        "message": f"Worker exit {process.returncode}",
                    }
            except subprocess.TimeoutExpired as exc:
                row["error"] = {
                    "type": "TimeoutExpired",
                    "message": f"Exceeded {args.timeout} seconds",
                }
                row["worker_stdout"] = (
                    (exc.stdout or b"").decode(errors="replace")
                    if isinstance(exc.stdout, bytes)
                    else exc.stdout
                )
                row["worker_stderr"] = (
                    (exc.stderr or b"").decode(errors="replace")
                    if isinstance(exc.stderr, bytes)
                    else exc.stderr
                )
            row.update(
                wall_ms=(time.perf_counter() - start) * 1000, repeat=repeat, trial_index=index
            )
            row = sanitize(row, args.model)
            rows.append(row)
            log.write(json.dumps(row, allow_nan=False) + "\n")
            log.flush()
            if record.exists():
                record.unlink()
            (args.output / "summary.json").write_text(
                json.dumps(
                    {
                        "completed": index,
                        "planned": len(jobs),
                        "complete": index == len(jobs),
                        "groups": grouped_summary(rows),
                    },
                    indent=2,
                )
                + "\n"
            )
            print(
                f"{index}/{len(jobs)} {mode}: {'ERROR' if row['error'] else 'ok'} {row['wall_ms']:.1f} ms",
                flush=True,
            )
    return 1 if any(row["error"] for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
