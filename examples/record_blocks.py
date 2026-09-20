"""Record a fixed-seed, real-model Blocks run through its browser controls.

No retries, move solver or substituted responses. Every attempt is retained;
declines, errors and game-over stop the run. This is an illustrative development
run, not a held-out game benchmark or an accuracy measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from record_showcase import git_identity, package_versions, source_hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/blocks")
    parser.add_argument("--pieces", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-ms", type=int, default=120_000)
    args = parser.parse_args()
    if not 1 <= args.pieces <= 500 or not 0 <= args.seed <= 0xFFFFFFFF:
        parser.error("pieces must be 1..500 and seed must be an unsigned 32-bit integer")
    url = urlsplit(args.url)
    if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost"):
        parser.error("Use the local MLX service's loopback HTTP URL")
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Output must be empty; earlier attempts must not be overwritten")
    query = dict(parse_qsl(url.query))
    query["seed"] = str(args.seed)
    target = urlunsplit(url._replace(query=urlencode(query)))
    from playwright.sync_api import sync_playwright

    files = source_hashes()
    files["examples/record_blocks.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = {
        "schema_version": 1,
        "project": "MLXJ Blocks",
        "scope": "fixed-seed illustrative development run, not a held-out benchmark",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "planned_pieces": args.pieces,
        "seed": args.seed,
        "policy": "All legal vertical-drop placements; rule-computed facts; model chooses. "
        "No retries, hidden fallback, response substitution or answer cache.",
        "recording": {"playback_speed": 1, "inference_waits_removed": False},
        "source": git_identity(),
        "source_files": files,
        "environment": {
            "machine": platform.machine(), "system": platform.system(),
            "release": platform.release(), "python": platform.python_version(),
            "recorder_dependencies": package_versions(),
        },
        "attempts": [], "browser_errors": [], "recording_errors": [],
        "stop_reason": "not_started", "video_saved": False,
    }
    started = perf_counter()

    def save():
        # Synthetic game data only; remove local filesystem prefixes in errors.
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        payload = payload.replace(str(Path.home()), "<home>")
        (args.output / "transcript.json").write_text(payload + "\n")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            record_video_dir=str(args.output / "video"),
            record_video_size={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.set_default_timeout(args.timeout_ms)
        video = page.video
        page.on("pageerror", lambda error: report["browser_errors"].append(str(error)))
        page.on("console", lambda msg: report["browser_errors"].append(msg.text)
                if msg.type == "error" else None)
        try:
            page.goto(target, wait_until="networkidle")
            page.wait_for_function("() => typeof window.render_game_to_text === 'function'")
            report["initial_state"] = page.evaluate("JSON.parse(window.render_game_to_text())")
            page.screenshot(path=str(args.output / "initial.png"))
            report["stop_reason"] = "piece_limit"
            for index in range(args.pieces):
                before = page.evaluate("JSON.parse(window.render_game_to_text())")
                attempt = {"index": index + 1, "before": before,
                           "submitted_at_ms": round((perf_counter() - started) * 1000, 3)}
                report["attempts"].append(attempt)
                save()
                with page.expect_response(
                    lambda response: urlsplit(response.url).path == "/v1/decide"
                    and response.request.method == "POST"
                ) as pending:
                    page.get_by_role("button", name="One piece", exact=True).click()
                response = pending.value
                attempt["request"] = response.request.post_data_json
                attempt["http_status"] = response.status
                attempt["result"] = response.json()
                attempt["response_at_ms"] = round((perf_counter() - started) * 1000, 3)
                save()
                page.wait_for_function(
                    "() => {const s=JSON.parse(window.render_game_to_text());"
                    "return !s.inFlight && !s.animating;}"
                )
                page.wait_for_timeout(350)
                attempt["after"] = page.evaluate("JSON.parse(window.render_game_to_text())")
                report["game_transcript"] = page.evaluate("window.blocksTranscript")
                matching = [
                    item for item in report["game_transcript"]
                    if item.get("kind") == "decision"
                    and item.get("result", {}).get("request_id")
                    == attempt["result"].get("request_id")
                ]
                attempt["execution_receipt"] = matching[-1].get("receipt") if matching else None
                page.screenshot(path=str(args.output / f"piece-{index + 1:03d}.png"))
                save()
                print(json.dumps({"piece": index + 1, "status": attempt["result"].get("status"),
                                  "choice": attempt["result"].get("candidate_id"),
                                  "score": attempt["after"].get("score"),
                                  "lines": attempt["after"].get("lines")}), flush=True)
                if not response.ok or attempt["result"].get("status") != "selected":
                    report["stop_reason"] = "model_declined_or_error"
                    break
                receipt = attempt["execution_receipt"] or {}
                if (not receipt.get("executed")
                    or receipt.get("id") != attempt["result"].get("candidate_id")
                    or attempt["after"].get("pieces") != before.get("pieces", 0) + 1):
                    report["stop_reason"] = "execution_rejected"
                    break
                if attempt["after"].get("game_over"):
                    report["stop_reason"] = "game_over"
                    break
            report["final_state"] = page.evaluate("JSON.parse(window.render_game_to_text())")
            report["game_transcript"] = page.evaluate("window.blocksTranscript")
            page.screenshot(path=str(args.output / "final.png"))
            page.wait_for_timeout(1000)
        except Exception as error:
            report["recording_errors"].append(f"{type(error).__name__}: {error}")
            report["stop_reason"] = "recording_error"
            try:
                report["game_transcript"] = page.evaluate("window.blocksTranscript")
                report["final_state"] = page.evaluate("JSON.parse(window.render_game_to_text())")
            except Exception:
                pass
        finally:
            context.close()
            if video:
                try:
                    video.save_as(str(args.output / "original.webm"))
                    report["video_saved"] = True
                    report["video_sha256"] = hashlib.sha256(
                        (args.output / "original.webm").read_bytes()
                    ).hexdigest()
                except Exception as error:
                    report["recording_errors"].append(f"Video save: {error}")
            browser.close()
            report["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
            save()
    print(json.dumps({"stop_reason": report["stop_reason"],
                      "attempts": len(report["attempts"]),
                      "video_saved": report["video_saved"],
                      "browser_errors": report["browser_errors"],
                      "recording_errors": report["recording_errors"]}, indent=2))
    return int(bool(report["recording_errors"] or report["browser_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
