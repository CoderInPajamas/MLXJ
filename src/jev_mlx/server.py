"""Small loopback-only HTTP interface; no browser or web framework dependency."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from threading import BoundedSemaphore
from typing import Any
from urllib.parse import urlsplit

from .demo import DemoController, DemoError
from .session import DecisionExecutionError
from .types import DecisionRequest

MAX_BODY_BYTES = 65_536
LOGGER = logging.getLogger(__name__)
STATIC_ROUTES = {
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "application/javascript"),
    "/style.css": ("style.css", "text/css"),
    "/blocks": ("blocks.html", "text/html"),
    "/blocks.html": ("blocks.html", "text/html"),
    "/blocks.js": ("blocks.js", "application/javascript"),
    "/blocks-engine.js": ("blocks-engine.js", "application/javascript"),
    "/blocks.css": ("blocks.css", "text/css"),
}


def request_from_dict(data: dict[str, Any]) -> DecisionRequest:
    """Parse the same explicit request shape used by the Python API and CLI."""
    return DecisionRequest.from_dict(data)


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], engine: Any):
        self.engine = engine
        self.controller = DemoController(engine)
        self.inference_slots = BoundedSemaphore(1)
        super().__init__(address, RequestHandler)


class RequestHandler(BaseHTTPRequestHandler):
    server: LocalServer
    server_version = "JEVMLX/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.info("%s %s", self.client_address[0], format % args)

    def _local_request(self) -> bool:
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if port == 80:
            allowed_hosts.update(("127.0.0.1", "localhost"))
        host = self.headers.get("Host", "").lower()
        if host not in allowed_hosts:
            self._json(
                403,
                {"error": "invalid_host", "message": "Use this service through its localhost URL."},
            )
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            self._json(
                403,
                {"error": "invalid_origin", "message": "Cross-origin requests are not allowed."},
            )
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._json(
                403, {"error": "cross_site", "message": "Cross-site requests are not allowed."}
            )
            return False
        return True

    def _send(self, status: int, payload: bytes, mime: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict[str, Any]) -> None:
        self._send(
            status,
            json.dumps(data, ensure_ascii=False, allow_nan=False).encode(),
            "application/json; charset=utf-8",
        )

    def do_GET(self) -> None:
        if not self._local_request():
            return
        path = urlsplit(self.path).path
        if path in ("/health", "/api/health"):
            self._json(
                200,
                {
                    "status": "ready",
                    "project": "JEV MLX",
                    "backend": "local",
                    "state_version": self.server.controller.snapshot()["state_version"],
                },
            )
        elif path == "/api/demo/state":
            self._json(200, self.server.controller.snapshot())
        elif path in STATIC_ROUTES:
            name, mime = STATIC_ROUTES[path]
            self._send(
                200,
                files("jev_mlx").joinpath("static", name).read_bytes(),
                f"{mime}; charset=utf-8",
            )
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if not self._local_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            self._json(
                413 if length > MAX_BODY_BYTES else 411,
                {
                    "error": "invalid_length",
                    "message": f"Provide Content-Length up to {MAX_BODY_BYTES} bytes.",
                },
            )
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            self._json(415, {"error": "content_type", "message": "Use application/json."})
            return
        try:
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise TypeError("Body must be a JSON object.")
            self._dispatch(urlsplit(self.path).path, data)
        except (DemoError, DecisionExecutionError) as exc:
            self._json(
                409,
                {
                    "error": "execution_rejected",
                    "message": str(exc),
                    **self.server.controller.snapshot(),
                },
            )
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
            self._json(400, {"error": "invalid_request", "message": str(exc)})
        except Exception as exc:
            LOGGER.exception("Local request failed")
            self._json(500, {"error": "backend_failure", "message": str(exc)})

    @staticmethod
    def _fields(data: dict[str, Any], required: set[str]) -> None:
        if set(data) != required:
            raise ValueError(f"Expected fields: {', '.join(sorted(required))}")

    @staticmethod
    def _version(data: dict[str, Any]) -> int:
        value = data["state_version"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("state_version must be a nonnegative integer.")
        return value

    def _dispatch(self, path: str, data: dict[str, Any]) -> None:
        controller = self.server.controller
        if path in ("/v1/decide", "/api/demo/decide"):
            if not self.server.inference_slots.acquire(blocking=False):
                self._json(
                    429,
                    {
                        "error": "busy",
                        "message": "A local decision is already running. Retry after it finishes.",
                    },
                )
                return
            try:
                if path == "/v1/decide":
                    result = self.server.engine.decide(request_from_dict(data))
                    response = result.to_dict()
                else:
                    self._fields(data, {"utterance"})
                    if (
                        not isinstance(data["utterance"], str)
                        or not 1 <= len(data["utterance"].strip()) <= 4096
                    ):
                        raise ValueError(
                            "utterance must be nonempty text with at most 4096 characters."
                        )
                    response = controller.decide(data["utterance"])
                self._json(200, response)
            finally:
                self.server.inference_slots.release()
        elif path == "/api/demo/action":
            self._fields(data, {"action_id", "state_version"})
            self._json(200, controller.action(data["action_id"], self._version(data)))
        elif path == "/api/demo/player-ready":
            self._fields(data, {"state_version"})
            self._json(200, controller.player_ready(self._version(data)))
        elif path == "/api/demo/execute":
            self._fields(data, {"ticket", "action_id"})
            if not isinstance(data["ticket"], str) or not isinstance(data["action_id"], str):
                raise ValueError("ticket and action_id must be strings.")
            self._json(200, controller.execute(data["ticket"], data["action_id"]))
        else:
            self._json(404, {"error": "not_found"})


def create_server(engine: Any, *, host: str = "127.0.0.1", port: int = 8765) -> LocalServer:
    """Create (but do not start) a loopback HTTP server around an existing engine."""
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("The 0.1 service binds only to 127.0.0.1 or localhost.")
    return LocalServer((host, port), engine)


def serve(engine: Any, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    with create_server(engine, host=host, port=port) as server:
        print(f"JEV MLX demo: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
