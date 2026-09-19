"""HTTP behavior with fake scores; real-model and real-browser checks are separate."""

import json
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from threading import Event, Thread

import pytest

from jevkit_mlx.engine import MLXDecisionEngine
from jevkit_mlx.server import MAX_BODY_BYTES, create_server, request_from_dict
from jevkit_mlx.types import ABSTAIN_ID, NO_MATCH_ID, BackendOutput


class StubBackend:
    def __init__(self):
        self.identity = {"name": "test-only fake backend"}
        self.started = None
        self.release = None

    def score(self, request, **kwargs):
        if self.started:
            self.started.set()
            assert self.release.wait(4)
        ids = [c.id for c in request.candidates] + [NO_MATCH_ID, ABSTAIN_ID]
        return BackendOutput(
            {key: 6.0 if key == ids[0] else 0.0 for key in ids}, model=self.identity
        )


@pytest.fixture
def running_server():
    backend = StubBackend()
    server = create_server(MLXDecisionEngine(backend=backend), port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, backend
    server.shutdown()
    server.server_close()
    thread.join(2)


def request(server, path, data=None, headers=None, body=None):
    conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    method = "GET" if data is None and body is None else "POST"
    if data is not None:
        body = json.dumps(data)
    sent_headers = {"Content-Type": "application/json"} if method == "POST" else {}
    sent_headers.update(headers or {})
    conn.request(method, path, body=body, headers=sent_headers)
    response = conn.getresponse()
    content = response.read()
    response_headers = dict(response.getheaders())
    status = response.status
    conn.close()
    return (
        status,
        json.loads(content)
        if "application/json" in response_headers.get("Content-Type", "")
        else content.decode(),
        response_headers,
    )


def test_health_static_demo_and_no_external_dependencies(running_server):
    server, _ = running_server
    assert request(server, "/health")[1]["status"] == "ready"
    status, html, headers = request(server, "/")
    assert status == 200
    assert "JEVKit MLX" in html
    assert "http://" not in html and "https://" not in html
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers
    assert request(server, "/app.js")[0] == 200
    assert request(server, "/style.css")[0] == 200
    assert request(server, "/../../LICENSE")[0] == 404


def test_public_decide_accepts_dynamic_choices(running_server):
    server, _ = running_server
    status, result, _ = request(
        server,
        "/v1/decide",
        {
            "state": {"page": "fictional"},
            "utterance": "An arbitrary request",
            "state_version": 7,
            "candidates": [{"id": "custom.action", "description": "A custom choice"}],
        },
    )
    assert status == 200
    assert result["candidate_id"] == "custom.action"
    assert result["state_version"] == 7
    assert result["model"]["name"] == "test-only fake backend"


def test_empty_candidates_can_decline(running_server):
    server, _ = running_server
    data = {"state": {}, "utterance": "There is nothing to do", "candidates": []}
    assert request_from_dict(data).candidates == ()
    status, result, _ = request(server, "/v1/decide", data)
    assert status == 200
    assert result["status"] == "no_match"
    assert result["candidate_id"] is None


def test_http_decide_and_execute_are_separate_and_replay_protected(running_server):
    server, _ = running_server
    status, decision, _ = request(server, "/api/demo/decide", {"utterance": "An arbitrary request"})
    assert status == 200
    assert request(server, "/api/demo/state")[1]["state"]["view"] == "desktop"
    op = decision["browser_operation"]
    payload = {"ticket": op["ticket"], "action_id": op["action_id"]}
    status, executed, _ = request(server, "/api/demo/execute", payload)
    assert status == 200 and executed["receipt"]["executed"]
    assert executed["state"]["view"] == "library"
    assert request(server, "/api/demo/execute", payload)[0] == 409


def test_host_origin_and_fetch_metadata_checks(running_server):
    server, _ = running_server
    assert request(server, "/health", headers={"Host": "attacker.example"})[0] == 403
    assert request(server, "/health", headers={"Origin": "https://attacker.example"})[0] == 403
    assert request(server, "/health", headers={"Sec-Fetch-Site": "cross-site"})[0] == 403
    assert (
        request(server, "/health", headers={"Origin": f"http://127.0.0.1:{server.server_port}"})[0]
        == 200
    )


def test_rejects_bad_shape_content_type_large_body_and_nan(running_server):
    server, _ = running_server
    assert request(server, "/api/demo/decide", {"utterance": "ok", "unexpected": True})[0] == 400
    assert request(server, "/api/demo/decide", {"utterance": " "})[0] == 400
    assert request(server, "/api/demo/decide", {"utterance": "x" * 4097})[0] == 400
    assert request(server, "/api/demo/decide", body="bad JSON")[0] == 400
    assert (
        request(server, "/api/demo/decide", body="{}", headers={"Content-Type": "text/plain"})[0]
        == 415
    )
    assert request(server, "/api/demo/decide", body="x" * (MAX_BODY_BYTES + 1))[0] == 413
    assert (
        request(
            server,
            "/v1/decide",
            {"state": {"bad": float("nan")}, "utterance": "test", "candidates": []},
        )[0]
        == 400
    )
    assert (
        request(server, "/api/demo/action", {"action_id": "open.library", "state_version": True})[0]
        == 400
    )


def test_slow_inference_does_not_block_state_change_and_busy_returns_429(running_server):
    server, backend = running_server
    backend.started, backend.release = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(request, server, "/api/demo/decide", {"utterance": "Test request"})
        assert backend.started.wait(2)
        assert request(server, "/api/demo/decide", {"utterance": "Second request"})[0] == 429
        status, changed, _ = request(
            server, "/api/demo/action", {"action_id": "open.notes", "state_version": 0}
        )
        assert status == 200 and changed["state"]["view"] == "notes"
        backend.release.set()
        status, response, _ = pending.result(timeout=3)
    assert status == 200
    assert response["result"]["status"] == "stale"
    assert response["browser_operation"] is None


def test_loopback_only():
    with pytest.raises(ValueError, match="binds only"):
        create_server(MLXDecisionEngine(backend=StubBackend()), host="0.0.0.0")
