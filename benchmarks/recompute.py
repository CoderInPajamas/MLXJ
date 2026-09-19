"""Recompute metrics from recorded evidence without modifying any original run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .metrics import grouped_summary


def recompute(directory: Path) -> dict:
    data = (directory / "trials.jsonl").read_bytes()
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    original = json.loads((directory / "summary.json").read_text())
    return {
        "schema_version": 1,
        "source_trials_sha256": hashlib.sha256(data).hexdigest(),
        "derived_metrics_source_sha256": hashlib.sha256(
            Path(__file__).with_name("metrics.py").read_bytes()
        ).hexdigest(),
        "recorded_attempts": len(rows),
        "original_run_status": {
            key: original.get(key)
            for key in ("completed", "planned", "complete", "measurements_complete", "parity")
        },
        "notes": "Derived metrics only. Original trial and summary files are unchanged. Raw-choice metrics use raw_selected_id before score-margin abstention; invalid/missing choices and errors remain incorrect.",
        "groups": grouped_summary(rows),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path, help="New derived JSON file; defaults to stdout")
    args = parser.parse_args(argv)
    result = json.dumps(recompute(args.run_directory), indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(result, end="")
    else:
        try:
            with args.output.open("x") as stream:
                stream.write(result)
        except FileExistsError:
            parser.error(
                "Output already exists; original evidence and earlier reports cannot be overwritten"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
