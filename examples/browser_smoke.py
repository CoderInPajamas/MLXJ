"""Record real-model decisions driving real DOM controls in an isolated browser.

Start ``jevkit serve --model PATH`` separately. This script never substitutes a
fake model, fixes model output, or invokes the action API instead of the UI.
Failures remain in its JSON transcript and produce a nonzero exit status.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    """Persist the transcript independently of video/browser cleanup success."""
    report["summary"] = {
        "cases": len(report["cases"]),
        "model_correct": sum(bool(case.get("model_correct")) for case in report["cases"]),
        "execution_correct": sum(bool(case.get("execution_correct")) for case in report["cases"]),
        "passed": sum(bool(case.get("passed")) for case in report["cases"]),
        "browser_errors": len(report["browser_errors"]),
    }
    output = output_dir / "browser-transcript.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--output", type=Path, default=Path("output/playwright"))
    parser.add_argument("--timeout-ms", type=int, default=120_000)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument(
        "--executable-path",
        help="Optional Chromium executable; no existing browser profile is used.",
    )
    args = parser.parse_args(argv)
    from playwright.sync_api import sync_playwright

    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Output directory must be empty so earlier browser evidence is preserved")
    report: dict[str, Any] = {
        "project": "JEVKit MLX",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "url": args.url,
        "scope": "Real local backend; allowlisted decisions -> actual DOM button click -> execution receipt -> observed DOM state.",
        "cases": [],
        "setup_clicks": [],
        "browser_errors": [],
        "screenshots": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=not args.headed, executable_path=args.executable_path
        )
        context_options: dict[str, Any] = {"viewport": {"width": 1440, "height": 1100}}
        if not args.no_video:
            context_options.update(
                record_video_dir=str(args.output / "video"),
                record_video_size={"width": 1440, "height": 1100},
            )
        context = browser.new_context(**context_options)
        page = context.new_page()
        page.set_default_timeout(args.timeout_ms)
        page.on("pageerror", lambda error: report["browser_errors"].append(str(error)))
        page.add_init_script(
            "window.__jevkitReceipts = []; document.addEventListener('jevkit:receipt', event => window.__jevkitReceipts.push(event.detail));"
        )

        def state() -> dict[str, Any]:
            # The inspector <pre> lives inside a collapsed <details>. Read its
            # DOM text even when it does not contribute visible innerText.
            return json.loads(page.locator("#state-json").text_content() or "")

        def version() -> int:
            return int(page.locator("#state-version").inner_text().split()[-1])

        def click(action_id: str) -> None:
            before = version()
            page.locator(f'[data-action="{action_id}"]').click()
            page.wait_for_function(
                "before => Number(document.getElementById('state-version').textContent.split(' ').at(-1)) > before",
                arg=before,
            )
            report["setup_clicks"].append(
                {
                    "action_id": action_id,
                    "from_version": before,
                    "to_version": version(),
                    "state": state(),
                }
            )

        def desktop() -> None:
            for _ in range(3):
                view = state()["view"]
                if view == "desktop":
                    return
                click(f"close.{view}")
            raise RuntimeError("Could not return to the desktop through its controls.")

        def library() -> None:
            if state()["view"] != "library":
                desktop()
                click("open.library")

        def player_ready(course_id: str = "orbit") -> None:
            if state()["view"] != "player" or state()["player"]["course"] != "Orbit Field Notes":
                library()
                if not page.locator(f'[data-action="play.{course_id}"]').count():
                    click("filter.all")
                click(f"play.{course_id}")
            page.wait_for_function(
                "() => {const s = JSON.parse(document.getElementById('state-json').textContent); return s.view === 'player' && s.player.status !== 'loading';}"
            )

        def screenshot(name: str) -> None:
            path = args.output / f"{name}.png"
            page.screenshot(path=str(path), full_page=True)
            report["screenshots"].append(path.name)

        def decide(
            name: str,
            utterance: str,
            expected_ids: list[str],
            expected_view: str,
            expected_player: str | None = None,
        ) -> dict[str, Any]:
            before_state, before_version = state(), version()
            started = perf_counter()
            page.locator("#utterance").fill(utterance)
            with page.expect_response(
                lambda response: (
                    response.url.endswith("/api/demo/decide") and response.request.method == "POST"
                ),
                timeout=args.timeout_ms,
            ) as pending:
                page.locator("#decide-button").click()
            response = pending.value
            payload = response.json()
            if not response.ok:
                raise RuntimeError(f"Decision HTTP {response.status}: {payload}")
            result = payload["result"]
            page.wait_for_function(
                "id => {try {return JSON.parse(document.getElementById('result-json').textContent).request_id === id;} catch {return false;}}",
                arg=result["request_id"],
            )
            receipt = None
            execution_error = None
            if result["status"] == "selected":
                try:
                    page.wait_for_function(
                        "id => window.__jevkitReceipts.some(receipt => receipt.decision_id === id)",
                        arg=result["request_id"],
                        timeout=10_000,
                    )
                    receipt = page.evaluate(
                        "id => window.__jevkitReceipts.find(receipt => receipt.decision_id === id)",
                        result["request_id"],
                    )
                except Exception as error:
                    execution_error = str(error)
            observed = state()
            # The model score is judged before any executor intervention.
            model_correct = (
                result["raw_selected_id"] in expected_ids and result["status"] != "stale"
            )
            if expected_ids and all(choice.startswith("__") for choice in expected_ids):
                execution_correct = (
                    receipt is None and version() == before_version and observed == before_state
                )
            else:
                execution_correct = bool(
                    receipt
                    and receipt["executed"]
                    and receipt["source"] == "model"
                    and receipt["action_id"] in expected_ids
                )
            execution_correct = execution_correct and observed["view"] == expected_view
            if expected_player:
                execution_correct = (
                    execution_correct
                    and observed.get("player", {}).get("status") == expected_player
                )
            record = {
                "name": name,
                "utterance": utterance,
                "expected_ids": expected_ids,
                "before_state": before_state,
                "result": result,
                "browser_operation": payload.get("browser_operation"),
                "execution_receipt": receipt,
                "execution_error": execution_error,
                "observed_state": observed,
                "observed_version": version(),
                "model_correct": model_correct,
                "execution_correct": execution_correct,
                "passed": model_correct and execution_correct,
                "browser_round_trip_ms": (perf_counter() - started) * 1000,
            }
            report["cases"].append(record)
            print(
                f"{'PASS' if record['passed'] else 'FAIL'} {name}: {result['raw_selected_id']} -> {observed['view']}",
                flush=True,
            )
            return record

        def case(
            name: str,
            setup,
            utterance: str,
            expected_ids: list[str],
            expected_view: str,
            expected_player: str | None = None,
        ):
            try:
                setup()
                return decide(name, utterance, expected_ids, expected_view, expected_player)
            except Exception as error:
                report["cases"].append(
                    {
                        "name": name,
                        "utterance": utterance,
                        "passed": False,
                        "model_correct": False,
                        "execution_correct": False,
                        "error": str(error),
                    }
                )
                print(f"FAIL {name}: {error}", flush=True)
                return None

        try:
            page.goto(args.url)
            page.wait_for_function(
                "() => document.getElementById('state-json').textContent.length > 0"
            )
            report["browser"] = {"name": "Chromium", "version": browser.version}
            screenshot("01-desktop")
            declined = ["__no_match__", "__abstain__"]
            case("close-with-no-open-object", desktop, "Close it", declined, "desktop")
            case(
                "open-feature-without-playing-content",
                desktop,
                "Open the course library",
                ["open.library"],
                "library",
            )
            screenshot("02-library")

            def unfiltered_library():
                library()
                if state()["library"]["filter"] != "All":
                    click("filter.all")

            case(
                "filter-by-category",
                unfiltered_library,
                "Show only science courses",
                ["filter.science"],
                "library",
            )

            def reordered_science():
                library()
                if state()["library"]["filter"] != "Science":
                    click("filter.science")
                if state()["library"]["sort"] != "za":
                    click("sort.za")

            case(
                "first-follows-filtered-reversed-visible-order",
                reordered_science,
                "First one",
                ["play.orbit"],
                "player",
            )
            screenshot("03-course-player")

            def playing():
                player_ready()
                if state()["player"]["status"] == "paused":
                    click("player.resume")

            def paused():
                player_ready()
                if state()["player"]["status"] == "playing":
                    click("player.pause")

            case(
                "pause-ready-player",
                playing,
                "Pause this for a moment",
                ["player.pause"],
                "player",
                "paused",
            )
            screenshot("03b-player-control")
            case(
                "resume-paused-player",
                paused,
                "Continue playing",
                ["player.resume"],
                "player",
                "playing",
            )
            rewind = case(
                "rewind-ten-seconds",
                playing,
                "Go back ten seconds",
                ["player.rewind"],
                "player",
                "playing",
            )
            if rewind and rewind.get("observed_state"):
                rewind["execution_correct"] = rewind["execution_correct"] and rewind[
                    "observed_state"
                ]["player"]["position_seconds"] == max(
                    0, rewind["before_state"]["player"]["position_seconds"] - 10
                )
                rewind["passed"] = rewind["model_correct"] and rewind["execution_correct"]
            case(
                "question-is-not-a-close-command",
                playing,
                "Did you just close it?",
                declined,
                "player",
                "playing",
            )
            case(
                "negation-is-not-an-action",
                playing,
                "Don't close the player",
                declined,
                "player",
                "playing",
            )
            case("close-current-player", playing, "Close it", ["close.player"], "library")
            case(
                "nonexistent-course",
                library,
                "Play the Advanced Volcano Knitting course",
                declined,
                "library",
            )
            case("close-current-library", library, "Close it", ["close.library"], "desktop")
            case("open-second-object", desktop, "Open my field notes", ["open.notes"], "notes")

            def notes():
                if state()["view"] != "notes":
                    desktop()
                    click("open.notes")

            case("close-current-notes", notes, "Close it", ["close.notes"], "desktop")
            case("ambiguous-request", desktop, "Do the thing", declined, "desktop")

            # Capture the loading-only action set before the automatic ready
            # event. Even if inference outlasts loading, inspect the raw choice
            # separately from the correctly rejected stale execution.
            library()
            if not page.locator('[data-action="play.orbit"]').count():
                click("filter.all")
            click("play.orbit")
            loading_state = state()
            loading_candidates = page.locator("#candidate-list .candidate").all_text_contents()
            page.locator("#utterance").fill("Pause it")
            with page.expect_response(
                lambda response: (
                    response.url.endswith("/api/demo/decide") and response.request.method == "POST"
                ),
                timeout=args.timeout_ms,
            ) as pending:
                page.locator("#decide-button").click()
            payload = pending.value.json()
            result = payload["result"]
            page.wait_for_function(
                "id => {try {return JSON.parse(document.getElementById('result-json').textContent).request_id === id;} catch {return false;}}",
                arg=result["request_id"],
            )
            loading_receipts = page.evaluate(
                "id => window.__jevkitReceipts.filter(receipt => receipt.decision_id === id)",
                result["request_id"],
            )
            loading_model_correct = result["raw_selected_id"] in declined
            loading_safe = (
                loading_candidates == ["close.player"]
                and not loading_receipts
                and result["status"] != "selected"
            )
            report["cases"].append(
                {
                    "name": "loading-player-has-no-pause-action",
                    "utterance": "Pause it",
                    "before_state": loading_state,
                    "loading_candidates": loading_candidates,
                    "result": result,
                    "observed_state": state(),
                    "execution_receipt": loading_receipts,
                    "model_correct": loading_model_correct,
                    "execution_correct": loading_safe,
                    "passed": loading_model_correct and loading_safe,
                    "note": "Automatic readiness may invalidate the request during inference; raw model choice and stale execution status are recorded separately.",
                }
            )

            # Keep execution paused so even an exceptionally fast model cannot
            # change the page before the deliberate manual state update.
            desktop()
            page.locator("#auto-execute").uncheck()
            page.locator("#utterance").fill("Open the course library")
            before = version()
            with page.expect_response(
                lambda response: (
                    response.url.endswith("/api/demo/decide") and response.request.method == "POST"
                ),
                timeout=args.timeout_ms,
            ) as pending:
                with page.expect_request(lambda request: request.url.endswith("/api/demo/decide")):
                    page.locator("#decide-button").click()
                click("open.notes")
            payload = pending.value.json()
            result = payload["result"]
            page.wait_for_function(
                "id => {try {return JSON.parse(document.getElementById('result-json').textContent).request_id === id;} catch {return false;}}",
                arg=result["request_id"],
            )
            overlap = result["status"] == "stale"
            if page.locator("#execute-pending").is_visible():
                page.locator("#execute-pending").click()
            safe = state()["view"] == "notes" and version() == before + 1
            report["state_change_check"] = {
                "result": result,
                "decision_request_overlap_proven": overlap,
                "gpu_compute_overlap_measured": False,
                "old_result_not_executed": safe,
                "observed_state": state(),
                "note": "State changed before the decision response was finalized; GPU-compute overlap is not separately measured."
                if overlap
                else "Model completed before a concurrent overlap was proven; the held old result was still rejected after the page changed.",
            }
            if not safe:
                report["browser_errors"].append(
                    "An old decision changed the page after its version became stale."
                )
            screenshot("04-stale-protection")
        except Exception as error:
            report["browser_errors"].append(str(error))
        finally:
            # Save before teardown as well: a video or browser cleanup failure
            # must never discard completed model/DOM observations.
            write_report(report, args.output)
            video = None
            try:
                video = page.video
            except Exception as error:
                report["browser_errors"].append(f"Video handle: {error}")
            for label, close in (
                ("Context cleanup", context.close),
                ("Browser cleanup", browser.close),
            ):
                try:
                    close()
                except Exception as error:
                    report["browser_errors"].append(f"{label}: {error}")
            if video is not None:
                try:
                    report["video"] = str(Path(video.path()).resolve().relative_to(args.output))
                except Exception as error:
                    report["browser_errors"].append(f"Video artifact: {error}")
            write_report(report, args.output)

    output = write_report(report, args.output)
    print(f"Transcript: {output}")
    print(json.dumps(report["summary"]))
    return int(
        bool(report["browser_errors"]) or report["summary"]["passed"] != report["summary"]["cases"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
