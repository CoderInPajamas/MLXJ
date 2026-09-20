"""Record eight fixed live-model requests through the fictional desktop's DOM.

Start the local service separately. This recorder neither changes model prompts
nor calls action/decision APIs itself. Manual setup clicks are labeled, all
model attempts are retained, and the continuous original video is not edited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VIEWPORT = {"width": 1280, "height": 800}
PAUSE_MS = 1200
RESULT_PAUSE_MS = 1500
TYPE_DELAY_MS = 40
DECLINES = ("__no_match__", "__abstain__")

# Expectations are recording assertions, never model input or response repairs.
PLAN = (
    {
        "name": "close-empty-desktop-before",
        "setup": "desktop",
        "caption": "Nothing is open. Ask the local model: Close it.",
        "utterance": "Close it",
        "expected_ids": DECLINES,
        "expected_view": "desktop",
    },
    {
        "name": "close-notes",
        "setup": "notes",
        "caption": "Field Notes is open. The same words: Close it.",
        "utterance": "Close it",
        "expected_ids": ("close.notes",),
        "expected_view": "desktop",
    },
    {
        "name": "first-filtered-reversed",
        "setup": "science_reversed",
        "caption": "Science courses, Z–A. Ask for the first visible item.",
        "utterance": "First one",
        "expected_ids": ("play.orbit",),
        "expected_view": "player",
        "expected_course": "Orbit Field Notes",
    },
    {
        "name": "pause-ready-player",
        "setup": "playing",
        "caption": "The player is ready. Ask the local model to pause it.",
        "utterance": "Pause it",
        "expected_ids": ("player.pause",),
        "expected_view": "player",
        "expected_player": "paused",
    },
    {
        "name": "question-is-not-an-action",
        "setup": "paused",
        "caption": "A question about an action, while the player stays open.",
        "utterance": "Did you just close it?",
        "expected_ids": DECLINES,
        "expected_view": "player",
        "expected_player": "paused",
    },
    {
        "name": "close-player",
        "setup": "ready_player",
        "caption": "The player is open. Ask again: Close it.",
        "utterance": "Close it",
        "expected_ids": ("close.player",),
        "expected_view": "library",
    },
    {
        "name": "close-library",
        "setup": "library",
        "caption": "Now the library is open. The same words: Close it.",
        "utterance": "Close it",
        "expected_ids": ("close.library",),
        "expected_view": "desktop",
    },
    {
        "name": "close-empty-desktop-after",
        "setup": "desktop",
        "caption": "Back to an empty desktop. One last: Close it.",
        "utterance": "Close it",
        "expected_ids": DECLINES,
        "expected_view": "desktop",
    },
)


def source_hashes() -> dict[str, str]:
    paths = [ROOT / "examples/record_showcase.py", ROOT / "pyproject.toml"]
    paths.extend((ROOT / "src/jev_mlx").rglob("*.py"))
    paths.extend(path for path in (ROOT / "src/jev_mlx/static").iterdir() if path.is_file())
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(set(paths))
    }


def package_versions() -> dict[str, str | None]:
    values = {}
    for name in ("playwright", "jev-mlx", "mlx", "mlx-lm", "transformers", "tokenizers"):
        try:
            values[name] = version(name)
        except PackageNotFoundError:
            values[name] = None
    return values


def git_identity() -> dict[str, str | bool | None]:
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            ).strip()
        )
        return {"revision": revision, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "dirty": None}


class Recorder:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.page: Any = None
        self.origin = perf_counter()
        self.active_case: int | None = None
        self.request_times: dict[Any, dict[str, Any]] = {}
        self.report: dict[str, Any] = {
            "schema_version": 1,
            "project": "MLXJ",
            "scope": "illustrative live-model recording, not benchmark",
            "capture_started_utc": datetime.now(timezone.utc).isoformat(),
            "video": "original.webm",
            "video_saved": False,
            "viewport": VIEWPORT,
            "timing": {
                "unit": "milliseconds",
                "origin": "perf_counter immediately before creating the recorded browser page",
                "alignment": "Approximate video alignment; Playwright exposes no first-frame clock.",
                "continuous_original_video": True,
                "playback_speed": 1,
                "inference_waits_removed": False,
                "typing_delay_ms_per_character": TYPE_DELAY_MS,
                "before_and_after_typing_pause_ms": PAUSE_MS,
                "after_result_pause_ms": RESULT_PAUSE_MS,
                "backend_latency": "Original result.timing; typing and presentation pauses excluded.",
            },
            "plan": list(PLAN),
            "evaluation_note": (
                "Fixed illustrative sequence, not held-out quality evaluation. Decline scenes "
                "accept either no_match or abstain; strict label accuracy is not claimed. "
                "Assertions never alter a request, output, or execution. No inference retries."
            ),
            "setup_note": (
                "All setup is via labeled manual DOM clicks, including recovery after a failed "
                "earlier choice. Setup success is not credited to the model. Player readiness "
                "uses the application's normal simulated loading event."
            ),
            "recorder_environment": {
                "python": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "dependencies": package_versions(),
                "note": "Recorder environment; backend dependency identity is in each result.model.",
            },
            "source": git_identity(),
            "source_files": source_hashes(),
            "cases": [],
            "setup_clicks": [],
            "network_events": [],
            "browser_errors": [],
            "recording_errors": [],
            "timeline": [],
            "screenshots": [],
        }

    def elapsed(self) -> float:
        return round((perf_counter() - self.origin) * 1000, 3)

    def event(self, event: str, **details: Any) -> None:
        self.report["timeline"].append(
            {"at_ms": self.elapsed(), "event": event, "case_index": self.active_case, **details}
        )

    def public_copy(self, value: Any, counts: dict[str, int]) -> Any:
        if isinstance(value, dict):
            return {key: self.public_copy(item, counts) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.public_copy(item, counts) for item in value]
        if not isinstance(value, str):
            return value
        for path, label in sorted(
            (
                (str(self.args.output), "<capture-output>"),
                (str(ROOT), "<project>"),
                (str(Path.home()), "<home>"),
            ),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            occurrences = value.count(path)
            if occurrences:
                counts[label] = counts.get(label, 0) + occurrences
                value = value.replace(path, label)
        value, found = re.subn(r"/(?:Users|home)/[^\s\"'<>]+", "<local-user-path>", value)
        if found:
            counts["other_local_user_paths"] = counts.get("other_local_user_paths", 0) + found
        if self.args.executable_path:
            count = value.count(self.args.executable_path)
            if count:
                counts["browser_executable"] = counts.get("browser_executable", 0) + count
                value = value.replace(self.args.executable_path, "<browser-executable>")
        return value

    def save(self) -> None:
        cases = self.report["cases"]
        self.report["summary"] = {
            "planned": len(PLAN),
            "recorded": len(cases),
            "submitted": sum(bool(case.get("submitted")) for case in cases),
            "responses": sum(case.get("result") is not None for case in cases),
            "model_correct": sum(bool(case.get("model_correct")) for case in cases),
            "execution_correct": sum(bool(case.get("execution_correct")) for case in cases),
            "passed": sum(bool(case.get("passed")) for case in cases),
            "browser_errors": len(self.report["browser_errors"]),
            "recording_errors": len(self.report["recording_errors"]),
        }
        redactions: dict[str, int] = {}
        public = self.public_copy(self.report, redactions)
        public["path_redactions"] = redactions
        public["redaction_note"] = "Only local paths are redacted; model choices and timings remain."
        temporary = self.args.output / "transcript.pending.json"
        temporary.write_text(
            json.dumps(public, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.args.output / "transcript.json")

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": json.loads(self.page.locator("#state-json").text_content() or ""),
            "state_version": int(
                self.page.locator("#state-version").inner_text().split()[-1]
            ),
            "candidates": self.page.locator("#candidate-list .candidate").evaluate_all(
                "elements => elements.map(e => ({id:e.textContent, description:e.title}))"
            ),
        }

    def caption(self, text: str, *, setup: bool = False) -> None:
        step = f"{(self.active_case or 0) + 1:02d} / {len(PLAN):02d}"
        label = f"MANUAL SETUP · {step}" if setup else f"LIVE REQUEST · {step}"
        if self.active_case is None:
            label = "CAPTURE COMPLETE"
        self.page.locator("#showcase-step").evaluate(
            "(element, text) => {element.textContent = text;}",
            label,
        )
        self.page.locator("#showcase-caption").evaluate(
            "(element, text) => {element.textContent = text;}", text
        )
        self.event("caption", text=text, manual_setup=setup)

    def on_request(self, request: Any) -> None:
        if request.method == "POST" and urlsplit(request.url).path.startswith("/api/demo/"):
            self.request_times[request] = {
                "request_started_ms": self.elapsed(),
                "case_index": self.active_case,
            }

    def on_response(self, response: Any) -> None:
        request = response.request
        if request not in self.request_times:
            return
        entry = {
            **self.request_times.pop(request),
            "response_received_ms": self.elapsed(),
            "path": urlsplit(response.url).path,
            "method": request.method,
            "http_status": response.status,
        }
        self.report["network_events"].append(entry)
        try:
            entry["request"] = request.post_data_json
            entry["response"] = response.json()
        except Exception as error:
            entry["capture_error"] = str(error)
            try:
                entry["response_text"] = response.text()
            except Exception as body_error:
                entry["body_error"] = str(body_error)

    def on_request_failed(self, request: Any) -> None:
        if request in self.request_times:
            self.report["network_events"].append(
                {
                    **self.request_times.pop(request),
                    "request_failed_ms": self.elapsed(),
                    "path": urlsplit(request.url).path,
                    "failure": request.failure,
                }
            )

    def click(self, action_id: str) -> None:
        self.caption(f"Manual setup: click {action_id}.", setup=True)
        self.page.wait_for_timeout(PAUSE_MS)
        before = self.snapshot()
        row = {
            "case_index": self.active_case,
            "action_id": action_id,
            "before": before,
            "started_ms": self.elapsed(),
        }
        self.report["setup_clicks"].append(row)
        try:
            self.page.locator(f'[data-action="{action_id}"]').click()
            self.page.wait_for_function(
                "version => Number(document.getElementById('state-version').textContent"
                ".split(' ').at(-1)) > version",
                arg=before["state_version"],
            )
            self.page.wait_for_timeout(PAUSE_MS)
            row["after"] = self.snapshot()
        except Exception as error:
            row["error"] = str(error)
            raise
        finally:
            row["finished_ms"] = self.elapsed()
            self.save()

    def desktop(self) -> None:
        for _ in range(3):
            view = self.snapshot()["state"]["view"]
            if view == "desktop":
                return
            self.click(f"close.{view}")
        raise RuntimeError("Manual controls did not reach the desktop.")

    def library(self) -> None:
        if self.snapshot()["state"]["view"] != "library":
            self.desktop()
            self.click("open.library")

    def notes(self) -> None:
        if self.snapshot()["state"]["view"] != "notes":
            self.desktop()
            self.click("open.notes")

    def science_reversed(self) -> None:
        self.library()
        if self.snapshot()["state"]["library"]["filter"] != "Science":
            self.click("filter.science")
        if self.snapshot()["state"]["library"]["sort"] != "za":
            self.click("sort.za")

    def ready_player(self) -> None:
        state = self.snapshot()["state"]
        if state["view"] != "player" or state["player"]["course"] != "Orbit Field Notes":
            self.science_reversed()
            self.click("play.orbit")
        self.caption("Scene setup: wait for the player's normal ready event.", setup=True)
        self.page.wait_for_function(
            "() => {const s=JSON.parse(document.getElementById('state-json').textContent);"
            "return s.view === 'player' && s.player.status !== 'loading';}"
        )

    def playing(self) -> None:
        self.ready_player()
        if self.snapshot()["state"]["player"]["status"] == "paused":
            self.click("player.resume")

    def paused(self) -> None:
        self.ready_player()
        if self.snapshot()["state"]["player"]["status"] == "playing":
            self.click("player.pause")

    def receipts(self, decision_id: str) -> list[dict[str, Any]]:
        return self.page.evaluate(
            "id => window.__showcaseReceipts.filter(r => r.receipt.decision_id === id)",
            decision_id,
        )

    def case(self, index: int, planned: dict[str, Any]) -> None:
        self.active_case = index
        row: dict[str, Any] = {
            **planned,
            "index": index,
            "started_ms": self.elapsed(),
            "submitted": False,
            "result": None,
            "execution_receipt": None,
            "model_correct": False,
            "execution_correct": False,
            "passed": False,
            "errors": [],
        }
        self.report["cases"].append(row)
        self.event("case_started", name=planned["name"])
        self.save()
        try:
            getattr(self, planned["setup"])()
            self.caption(planned["caption"])
            self.page.locator("#auto-execute").check()
            self.page.wait_for_function(
                "() => !document.getElementById('decide-button').disabled"
            )
            self.page.wait_for_timeout(PAUSE_MS)
            row["before"] = self.snapshot()
            row["before_state"] = row["before"]["state"]
            self.page.locator("#utterance").fill("")
            row["typing_started_ms"] = self.elapsed()
            self.page.locator("#utterance").press_sequentially(
                planned["utterance"], delay=TYPE_DELAY_MS
            )
            row["typing_finished_ms"] = self.elapsed()
            self.page.wait_for_timeout(PAUSE_MS)
            # This click is the only model submission. The script never retries it.
            with self.page.expect_response(
                lambda response: urlsplit(response.url).path == "/api/demo/decide"
                and response.request.method == "POST",
                timeout=self.args.timeout_ms,
            ) as pending:
                row["submitted_ms"] = self.elapsed()
                self.page.locator("#decide-button").click()
                row["submitted"] = True
                self.event("model_request_submitted", utterance=planned["utterance"])
            response = pending.value
            row["response_received_ms"] = self.elapsed()
            row["response_status"] = response.status
            try:
                payload = response.json()
            except Exception:
                row["response_text"] = response.text()
                raise
            row["response"] = payload
            row["result"] = payload.get("result")
            row["browser_operation"] = payload.get("browser_operation")
            self.save()
            if not response.ok or not isinstance(row["result"], dict):
                raise RuntimeError(f"Decision response was HTTP {response.status} without success.")
            result = row["result"]
            self.page.wait_for_function(
                "id => {try {return JSON.parse(document.getElementById('result-json')"
                ".textContent).request_id === id;} catch {return false;}}",
                arg=result["request_id"],
            )
            if payload.get("browser_operation"):
                try:
                    self.page.wait_for_function(
                        "id => window.__showcaseReceipts.some(r => r.receipt.decision_id === id)",
                        arg=result["request_id"],
                        timeout=10_000,
                    )
                except Exception as error:
                    row["errors"].append(f"Execution receipt wait: {error}")
            # Leave the real result and any error visible without altering them.
            self.page.wait_for_timeout(RESULT_PAUSE_MS)
            receipts = self.receipts(result["request_id"])
            row["receipt_events"] = receipts
            row["execution_receipt"] = receipts[-1]["receipt"] if receipts else None
            row["after"] = self.snapshot()
            row["observed_state"] = row["after"]["state"]
            row["observed_version"] = row["after"]["state_version"]
            row["receipt_display"] = self.page.locator("#receipt").inner_text()
            row["notice_display"] = self.page.locator("#notice").inner_text()
            expected = planned["expected_ids"]
            is_decline = all(candidate in DECLINES for candidate in expected)
            row["raw_choice_correct"] = result.get("raw_selected_id") in expected
            row["model_correct"] = row["raw_choice_correct"] and (
                result.get("status") in ("no_match", "abstain")
                if is_decline
                else result.get("status") == "selected" and result.get("candidate_id") in expected
            )
            receipt = row["execution_receipt"]
            if is_decline:
                row["execution_correct"] = not receipts and row["after"] == row["before"]
            else:
                row["execution_correct"] = bool(
                    len(receipts) == 1
                    and receipt["executed"]
                    and receipt["source"] == "model"
                    and receipt["action_id"] in expected
                )
            observed = row["observed_state"]
            row["execution_correct"] &= observed["view"] == planned["expected_view"]
            player = observed.get("player") or {}
            if "expected_player" in planned:
                row["execution_correct"] &= player.get("status") == planned["expected_player"]
            if "expected_course" in planned:
                row["execution_correct"] &= player.get("course") == planned["expected_course"]
            row["passed"] = (
                row["model_correct"] and row["execution_correct"] and not row["errors"]
            )
        except Exception as error:
            row["errors"].append(str(error))
            try:
                row["state_at_failure"] = self.snapshot()
                self.caption("This attempt failed; its response and errors remain in the transcript.")
                self.page.wait_for_timeout(RESULT_PAUSE_MS)
            except Exception as capture_error:
                row["errors"].append(f"Failure-state capture: {capture_error}")
        finally:
            row["finished_ms"] = self.elapsed()
            self.event("case_finished", name=planned["name"], passed=row["passed"])
            self.save()
            result = row.get("result") or {}
            print(
                f"{'PASS' if row['passed'] else 'FAIL'} {index + 1}/{len(PLAN)} "
                f"{planned['name']}: {result.get('raw_selected_id', 'no recorded result')}",
                flush=True,
            )

    def screenshot(self, name: str) -> None:
        self.page.screenshot(path=str(self.args.output / name), full_page=False)
        self.report["screenshots"].append({"path": name, "at_ms": self.elapsed()})

    def run(self) -> int:
        from playwright.sync_api import sync_playwright

        browser = context = video = None
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(
                    headless=not self.args.headed, executable_path=self.args.executable_path
                )
                context = browser.new_context(
                    viewport=VIEWPORT,
                    record_video_dir=str(self.args.output / "raw-video"),
                    record_video_size=VIEWPORT,
                    device_scale_factor=1,
                )
                context.add_init_script(
                    "window.__showcaseReceipts=[];document.addEventListener('jev-mlx:receipt',"
                    "event=>window.__showcaseReceipts.push({browser_performance_ms:"
                    "performance.now(),receipt:event.detail}));"
                )
                self.origin = perf_counter()
                self.report["capture_started_utc"] = datetime.now(timezone.utc).isoformat()
                self.page = context.new_page()
                video = self.page.video
                self.page.set_default_timeout(self.args.timeout_ms)
                self.page.on(
                    "pageerror",
                    lambda error: self.report["browser_errors"].append(
                        {"at_ms": self.elapsed(), "error": str(error)}
                    ),
                )
                self.page.on("request", self.on_request)
                self.page.on("response", self.on_response)
                self.page.on("requestfailed", self.on_request_failed)
                self.report["browser"] = {"name": "Chromium", "version": browser.version}
                self.event("recorded_page_created")
                self.page.goto(self.args.url)
                self.page.wait_for_function(
                    "() => document.getElementById('state-json').textContent.length > 0"
                )
                self.page.locator("#showcase-caption").wait_for(state="visible")
                self.report["page_visible_ms"] = self.elapsed()
                self.report["initial_snapshot"] = self.snapshot()
                self.report["initial_model_display"] = self.page.locator("#model-name").inner_text()
                self.screenshot("initial.png")
                self.save()
                for index, planned in enumerate(PLAN):
                    self.case(index, planned)
                self.active_case = None
                self.caption("Eight fixed requests complete. Every response is preserved.")
                self.page.wait_for_timeout(RESULT_PAUSE_MS)
                self.screenshot("final.png")
                self.report["final_snapshot"] = self.snapshot()
                self.report["all_receipt_events"] = self.page.evaluate(
                    "window.__showcaseReceipts"
                )
            except Exception as error:
                self.report["recording_errors"].append(str(error))
            finally:
                self.report["capture_finished_ms"] = self.elapsed()
                self.report["source_files_after"] = source_hashes()
                self.report["source_unchanged_during_capture"] = (
                    self.report["source_files"] == self.report["source_files_after"]
                )
                if not self.report["source_unchanged_during_capture"]:
                    self.report["recording_errors"].append("Source files changed during capture.")
                self.save()
                for label, resource in (("context", context), ("browser", browser)):
                    if resource is not None:
                        try:
                            resource.close()
                        except Exception as error:
                            self.report["recording_errors"].append(f"Close {label}: {error}")
                if video is not None:
                    try:
                        video.save_as(str(self.args.output / "original.webm"))
                        self.report["video_saved"] = True
                        self.report["video_sha256"] = hashlib.sha256(
                            (self.args.output / "original.webm").read_bytes()
                        ).hexdigest()
                        # save_as copies identical bytes; retain only the named raw artifact.
                        video.delete()
                        (self.args.output / "raw-video").rmdir()
                    except Exception as error:
                        self.report["recording_errors"].append(f"Video finalization: {error}")
                self.save()
        print(json.dumps(self.report["summary"]), flush=True)
        return int(
            self.report["summary"]["passed"] != len(PLAN)
            or bool(self.report["browser_errors"])
            or bool(self.report["recording_errors"])
            or not self.report["video_saved"]
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/?showcase=1")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-ms", type=int, default=120_000)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--executable-path", help="Optional Chromium binary; no user profile is used.")
    args = parser.parse_args(argv)
    parsed = urlsplit(args.url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
    ):
        parser.error("Use the fictional demo's localhost HTTP root URL without credentials.")
    if args.timeout_ms < 1:
        parser.error("--timeout-ms must be positive.")
    args.output = args.output.expanduser().resolve()
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("Output must be a new or empty directory; previous attempts are preserved.")
    args.output.mkdir(parents=True, exist_ok=True)
    recorder = Recorder(args)
    recorder.save()
    return recorder.run()


if __name__ == "__main__":
    raise SystemExit(main())
