"""Check Blocks controls with explicitly mocked responses, never model quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/blocks?seed=42")
    parser.add_argument("--output", type=Path, default=Path("output/playwright-blocks/controls"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    errors, checks, pending = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/v1/decide", lambda route: pending.append(route))

        def state():
            return page.evaluate("JSON.parse(window.render_game_to_text())")

        def settled():
            page.wait_for_function(
                "() => {const s=JSON.parse(window.render_game_to_text());"
                "return !s.inFlight && !s.animating;}"
            )

        def begin():
            page.locator("#step-ai").click()
            page.wait_for_timeout(50)
            assert len(pending) == 1
            return pending.pop()

        def finish(route, *, status="selected", candidate=None, version_offset=0):
            data = route.request.post_data_json
            candidate = candidate or data["candidates"][0]["id"]
            route.fulfill(json={
                "status": status, "candidate_id": candidate if status == "selected" else None,
                "raw_selected_id": candidate,
                "state_version": data["state_version"] + version_offset,
                "request_id": "explicit-browser-test-fixture", "margin": 1.0,
                "scores": {candidate: 1.0}, "raw_scores": {candidate: 5.0},
                "model": {"name": "EXPLICIT TEST DOUBLE — not real MLX"},
                "timing": {"decision_ms": 0}, "cache": {},
            })
            settled()

        page.goto(args.url, wait_until="networkidle")
        page.locator("#manual-mode").click()
        page.keyboard.press("ArrowLeft")
        page.keyboard.press("ArrowUp")
        page.keyboard.press("Space")
        settled()
        assert state()["pieces"] == 1
        checks.append("manual move, rotate, hard-drop")
        page.locator("#reset").click()
        assert state()["pieces"] == 0
        finish(begin())
        assert state()["pieces"] == 1
        checks.append("single selected choice executes once")
        page.locator("#reset").click()
        route = begin()
        page.locator("#reset").click()
        finish(route)
        assert state()["pieces"] == 0
        checks.append("reset rejects pending result")
        route = begin()
        page.locator("#pause").click()
        finish(route)
        assert state()["pieces"] == 0
        checks.append("pause rejects pending result")
        page.locator("#start-ai").click()
        page.wait_for_timeout(50)
        finish(pending.pop(), version_offset=1)
        page.wait_for_timeout(700)
        assert not pending and not state()["auto"] and state()["pieces"] == 0
        checks.append("wrong response version stops autoplay without retry")
        route = begin()
        page.locator("#manual-mode").click()
        page.keyboard.press("ArrowLeft")
        finish(route)
        assert state()["pieces"] == 0
        checks.append("manual state change rejects pending result")
        finish(begin(), candidate="not-a-legal-placement")
        assert state()["pieces"] == 0
        checks.append("invalid placement rejected")
        finish(begin(), status="abstain")
        assert state()["pieces"] == 0
        checks.append("abstention makes no move")
        route = begin()
        route.fulfill(status=500, json={"error": "explicit test backend failure"})
        settled()
        assert state()["pieces"] == 0
        checks.append("backend failure makes no move")
        board = [".........." for _ in range(19)] + ["XXXXXX...."]
        page.evaluate("rows => window.blocksDebug.setBoard(rows, 'I')", board)
        finish(begin(), candidate="drop.I.r0.x6")
        assert state()["lines"] == 1 and state()["score"] == 100
        checks.append("line clearing updates score and board")
        page.screenshot(path=str(args.output / "line-clear.png"))
        page.evaluate("rows => window.blocksDebug.setBoard(rows, 'O')", ["XXXXXXXXXX"] * 20)
        assert state()["game_over"]
        checks.append("blocked board enters game-over")
        page.screenshot(path=str(args.output / "game-over.png"))
        page.locator("#reset").click()
        assert not state()["game_over"]
        page.keyboard.press("f")
        page.wait_for_function("() => Boolean(document.fullscreenElement)")
        page.keyboard.press("Escape")
        page.wait_for_function("() => !document.fullscreenElement")
        checks.append("fullscreen and exit")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
        checks.append("mobile width has no horizontal overflow")
        assert not errors, errors
        report = {"scope": "mocked browser controls, not model quality", "checks": checks,
                  "errors": errors, "transcript": page.evaluate("window.blocksTranscript")}
        (args.output / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
        browser.close()
    print(json.dumps({"passed": len(checks), "checks": checks, "errors": errors}, indent=2))


if __name__ == "__main__":
    main()
