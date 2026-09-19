"""Fixture integrity and public metadata helpers; no model imports at import time."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.metadata
import json
import platform
import resource
import subprocess
import sys
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixtures(split: str = "test") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if split not in {"dev", "test"}:
        raise ValueError("split must be dev or test")
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    path = FIXTURES / f"{split}.jsonl"
    expected = manifest["files"][path.name]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected["sha256"]:
        raise ValueError(f"Frozen fixture hash mismatch: {path.name}")
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(cases) != expected["rows"] or len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Fixture count or identity mismatch")
    return cases, manifest


def request_from_dict(value: dict[str, Any]):
    from jevkit_mlx import Candidate, DecisionRequest

    return DecisionRequest(
        **{**value, "candidates": tuple(Candidate(**item) for item in value["candidates"])}
    )


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(f"Unsupported result type: {type(value).__name__}")


def sanitize(value: Any, model_path: str | None = None) -> Any:
    """Public artifacts include model names/hashes, never local usernames or paths."""
    if isinstance(value, dict):
        return {key: sanitize(item, model_path) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item, model_path) for item in value]
    if isinstance(value, str):
        if model_path:
            value = value.replace(
                str(Path(model_path).expanduser().resolve()), Path(model_path).name
            )
        return value.replace(str(Path.home()), "<HOME>")
    return value


def memory_snapshot() -> dict[str, Any]:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {"process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024)}
    # MLX import can initialize Metal; only query it after the backend loaded it.
    mx = sys.modules.get("mlx.core")
    if mx is not None:
        for name in ("get_active_memory", "get_peak_memory", "get_cache_memory"):
            method = getattr(mx, name, None)
            if method is not None:
                try:
                    result[name.removeprefix("get_") + "_bytes"] = int(method())
                except Exception as exc:
                    result[name + "_error"] = type(exc).__name__
    return result


def environment_metadata() -> dict[str, Any]:
    deps = {}
    for package in (
        "jevkit-mlx",
        "mlx",
        "mlx-lm",
        "mlx-metal",
        "transformers",
        "tokenizers",
        "numpy",
    ):
        try:
            deps[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            deps[package] = None
    hardware = {
        "architecture": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
    }
    if sys.platform == "darwin":
        for key in ("hw.model", "machdep.cpu.brand_string", "hw.memsize", "hw.ncpu"):
            result = subprocess.run(
                ["sysctl", "-n", key], capture_output=True, text=True, check=False
            )
            hardware[key] = result.stdout.strip() if result.returncode == 0 else None
    git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    )
    root = Path(__file__).resolve().parents[1]
    sources = [
        root / "src" / "jevkit_mlx" / name
        for name in ("prompt.py", "types.py", "engine.py", "backends/mlx_lm.py")
    ]
    sources.extend(
        Path(__file__).parent / name
        for name in ("common.py", "run.py", "metrics.py", "cold_start.py")
    )
    return {
        "python": platform.python_version(),
        "dependencies": deps,
        "hardware": hardware,
        "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "git_worktree_dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
        "source_sha256": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sources
            if path.exists()
        },
    }
