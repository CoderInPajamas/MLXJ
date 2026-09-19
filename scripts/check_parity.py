"""Write public, synthetic numerical cache evidence for one local checkpoint."""

import argparse
import json
from pathlib import Path

from jev_mlx import Candidate, DecisionRequest, MLXDecisionEngine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    engine = MLXDecisionEngine(args.model)
    choices = (
        Candidate("play_amber", "Play the visible course Amber Maps"),
        Candidate("play_cloud", "Play the visible course Cloud Songs"),
        Candidate("close_library", "Close the course library"),
    )
    rows = []
    for order in (["Amber Maps", "Cloud Songs"], ["Cloud Songs", "Amber Maps"]):
        for utterance in ("Play the first one", "Close it", "Don't close anything"):
            request = DecisionRequest(
                {"view": "library", "visible_order": order}, utterance, choices
            )
            cold_or_updated = engine.decide(request, cache_key="parity")
            warm = engine.decide(request, cache_key="parity")
            fresh = engine.decide(request, use_cache=False)
            for label, result in (("cold_or_updated", cold_or_updated), ("warm", warm)):
                delta = max(
                    abs(result.raw_scores[k] - fresh.raw_scores[k]) for k in result.raw_scores
                )
                score_delta = max(abs(result.scores[k] - fresh.scores[k]) for k in result.scores)
                rows.append(
                    {
                        "order": order,
                        "utterance": utterance,
                        "condition": label,
                        "max_absolute_logit_difference": delta,
                        "max_absolute_score_difference": score_delta,
                        "same_raw_selection": result.raw_selected_id == fresh.raw_selected_id,
                        "cache": result.cache,
                        "raw_scores": result.raw_scores,
                        "fresh_raw_scores": fresh.raw_scores,
                    }
                )
    passed = all(
        r["max_absolute_logit_difference"] <= 0.5
        and r["max_absolute_score_difference"] <= 0.1
        and r["same_raw_selection"]
        for r in rows
    )
    report = {
        "model": engine.backend.identity,
        "logit_tolerance": 0.5,
        "restricted_score_tolerance": 0.1,
        "passed": passed,
        "comparisons": rows,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "comparisons": len(rows),
                "max_logit_difference": max(r["max_absolute_logit_difference"] for r in rows),
            }
        )
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
