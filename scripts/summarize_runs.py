"""Render measured tables without excluding failures or incomplete run warnings."""

import argparse
import json
from pathlib import Path

from benchmarks.metrics import grouped_summary


def percent(value):
    return "—" if value is None else f"{value * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    args = parser.parse_args()
    for directory in args.runs:
        metadata = json.loads((directory / "metadata.json").read_text())
        summary = json.loads((directory / "summary.json").read_text())
        rows = [json.loads(line) for line in (directory / "trials.jsonl").read_text().splitlines()]
        groups = grouped_summary(rows)
        print(f"\n### {metadata['model_name']} / {directory.name}\n")
        print(
            f"Scope: {metadata.get('scope', 'unspecified')}; completed "
            f"{summary['completed']}/{summary['planned']}; complete={summary['complete']}.\n"
        )
        print(
            "| Method / condition | n | p50 ms | p95 ms | Accuracy | Wrong action | Rejection | Coverage | Schema |"
        )
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for name, group in groups.items():
            latency = group["latency_ms"]
            p50 = "—" if latency["p50"] is None else f"{latency['p50']:.1f}"
            p95 = "—" if latency["p95"] is None else f"{latency['p95']:.1f}"
            values = [
                percent(group.get(k))
                for k in (
                    "accuracy",
                    "false_action_rate",
                    "rejection_rate",
                    "executable_request_coverage",
                    "schema_validity",
                )
            ]
            print(f"| {name} | {group['attempts']} | {p50} | {p95} | " + " | ".join(values) + " |")
        peak = max(((r.get("memory") or {}).get("peak_memory_bytes", 0) for r in rows), default=0)
        rss = max(
            ((r.get("memory") or {}).get("process_peak_rss_bytes", 0) for r in rows), default=0
        )
        failures = sum(r.get("error") is not None for r in rows)
        print(
            f"\nRuntime errors: {failures}. Recorded peak MLX memory: {peak / 1024**3:.2f} GiB; "
            f"process peak RSS: {rss / 1024**3:.2f} GiB.\n"
        )
        print("| Method / condition | Raw choice accuracy | Raw wrong action rate |")
        print("|---|---:|---:|")
        for name, group in groups.items():
            print(
                f"| {name} | {percent(group['raw_choice_accuracy'])} | "
                f"{percent(group['raw_false_action_rate'])} |"
            )
        for condition in ("same_page_new_utterance", "page_update"):
            selected = [r for r in rows if r["condition"] == condition and r.get("prediction")]
            hits = [
                r for r in selected if r["prediction"].get("cache", {}).get("reused_tokens", 0) > 0
            ]
            print(
                f"{condition}: actual prefix reuse in {len(hits)}/{len(selected)} measured calls."
            )


if __name__ == "__main__":
    main()
