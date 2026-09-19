"""One local, versioned action decision. No application outside this example is changed."""

import argparse
import json

from jev_mlx import Candidate, DecisionSession, MLXDecisionEngine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--utterance", default="Close it")
    args = parser.parse_args()
    session = DecisionSession(
        MLXDecisionEngine(args.model),
        state={"focused_window": "notes", "title": "Field Notes"},
        candidates=[Candidate("close_notes", "Close the currently open Field Notes window")],
    )
    result = session.decide(args.utterance)
    print(json.dumps(result.to_dict(), indent=2))

    def apply(candidate):
        version = session.update_state({"focused_window": None}, candidates=[])
        return {
            "executed": True,
            "action_id": candidate.id,
            "state_version": version,
            "scope": "fictional in-memory example",
        }

    if result.status == "selected":
        print(json.dumps(session.execute(result, apply)))


if __name__ == "__main__":
    main()
