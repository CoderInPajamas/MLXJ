"""Command-line entry point. Importing or asking for help does not load MLX."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="jevkit", description="JEV-inspired local decisions for Apple Silicon."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    decide = sub.add_parser(
        "decide", help="Score a JSON decision request from a file or standard input."
    )
    decide.add_argument(
        "--request", "-r", default="-", help="Request JSON path, or - for stdin (default)."
    )
    decide.add_argument(
        "--no-cache", action="store_true", help="Disable prefix-cache reuse for this request."
    )
    web = sub.add_parser("serve", help="Run the local browser demo and HTTP API.")
    web.add_argument("--host", choices=("127.0.0.1", "localhost"), default="127.0.0.1")
    web.add_argument("--port", type=int, default=8765)
    for command in (decide, web):
        command.add_argument(
            "--model",
            default=os.environ.get("JEVKIT_MLX_MODEL"),
            help="Local MLX-LM model directory, or JEVKIT_MLX_MODEL.",
        )
    args = parser.parse_args(argv)
    if not args.model:
        parser.error("provide --model or set JEVKIT_MLX_MODEL to a local model directory")
    try:
        from .engine import MLXDecisionEngine
        from .server import request_from_dict, serve

        if args.command == "decide":
            text = sys.stdin.read() if args.request == "-" else Path(args.request).read_text()
            request = request_from_dict(json.loads(text))
            engine = MLXDecisionEngine(args.model)
            result = engine.decide(request, use_cache=not args.no_cache)
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, allow_nan=False))
        else:
            engine = MLXDecisionEngine(args.model)
            serve(engine, host=args.host, port=args.port)
        return 0
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        print(f"jevkit: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
