"""Benchmark command validation and cold-process evidence without MLX or workers."""

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks import cold_start, run
from benchmarks.audit import audit_run
from benchmarks.common import load_fixtures


@pytest.mark.parametrize(
    "module,option,values,message",
    [
        (run, "--modes", ["direct", "direct"], "modes must be unique"),
        (run, "--conditions", ["kv_cold", "kv_cold"], "conditions must be unique"),
        (run, "--cohorts", ["page_update", "page_update"], "conditions must be unique"),
        (cold_start, "--modes", ["json", "json"], "modes must be unique"),
    ],
)
def test_duplicate_schedule_arguments_fail_before_loading(
    module, option, values, message, tmp_path, monkeypatch, capsys
):
    def unexpected_load(*args, **kwargs):
        pytest.fail("Invalid CLI arguments reached fixture or model loading")

    monkeypatch.setattr(module, "load_fixtures", unexpected_load)
    output = tmp_path / "run"
    with pytest.raises(SystemExit) as exc:
        module.main(["--model", "unused-model", "--output", str(output), option, *values])
    assert exc.value.code == 2
    assert message in capsys.readouterr().err
    assert not output.exists()


@pytest.fixture
def boolean_suite(tmp_path):
    case = next(case for case in load_fixtures("test")[0] if case["request"]["kind"] == "boolean")
    case["id"] = "cold-start-boolean-fixture"
    suite = tmp_path / "suite"
    suite.mkdir()
    data = (json.dumps(case) + "\n").encode()
    (suite / "test.jsonl").write_bytes(data)
    manifest = {"files": {"test.jsonl": {"sha256": hashlib.sha256(data).hexdigest(), "rows": 1}}}
    (suite / "manifest.json").write_text(json.dumps(manifest))
    return suite, case


def test_cold_worker_preserves_boolean_kind_without_a_real_model(
    boolean_suite, tmp_path, monkeypatch
):
    import jev_mlx

    suite, case = boolean_suite

    class FakeEngine:
        def __init__(self, **kwargs):
            pass

        def decide(self, request, *, cache_key, use_cache):
            assert request.kind == "boolean"
            assert not use_cache
            return dict(case["expected"])

    monkeypatch.setattr(jev_mlx, "MLXDecisionEngine", FakeEngine)
    monkeypatch.setattr(cold_start, "memory_snapshot", lambda: {})
    record = tmp_path / "worker.json"
    args = SimpleNamespace(
        split="test", fixtures_dir=suite, model="unused-model", mode="direct", worker_record=record
    )
    assert cold_start.worker(args) == 0
    row = json.loads(record.read_text())
    assert row["kind"] == "boolean"
    assert row["case_id"] == case["id"]
    assert row["prediction"]["status"] == case["expected"]["status"]


@pytest.mark.parametrize("worker_failed", [False, True])
def test_cold_schedule_metadata_audits_successes_and_missing_worker_records(
    boolean_suite, tmp_path, monkeypatch, worker_failed
):
    suite, case = boolean_suite
    output = tmp_path / "run"
    monkeypatch.setattr(cold_start, "environment_metadata", lambda: {})
    calls = []

    def fake_worker(command, **kwargs):
        assert command[command.index("--fixtures-dir") + 1] == str(suite)
        assert kwargs["timeout"] == 17
        mode = command[command.index("--mode") + 1]
        calls.append(mode)
        if not worker_failed:
            record = Path(command[command.index("--worker-record") + 1])
            # Kind remains present even if a worker returns a partial record.
            record.write_text(
                json.dumps({"prediction": {**case["expected"], "schema_valid": True}})
            )
        return subprocess.CompletedProcess(command, int(worker_failed), stdout="", stderr="")

    monkeypatch.setattr(cold_start.subprocess, "run", fake_worker)
    result = cold_start.main(
        [
            "--model",
            "unused-model",
            "--output",
            str(output),
            "--fixtures-dir",
            str(suite),
            "--modes",
            "direct",
            "code",
            "json",
            "json_code",
            "--repeats",
            "3",
            "--timeout",
            "17",
        ]
    )
    assert result == int(worker_failed)
    assert sorted(calls) == sorted(["direct", "code", "json", "json_code"] * 3)
    metadata_path = output / "metadata.json"
    metadata = json.loads(metadata_path.read_text())
    assert metadata["modes"] == ["direct", "code", "json", "json_code"]
    assert metadata["conditions"] == ["process_cold_start"]
    assert metadata["case_count"] == 1
    assert metadata["seed"] == 20260919
    assert metadata["timeout_seconds"] == 17
    rows = [json.loads(line) for line in (output / "trials.jsonl").read_text().splitlines()]
    assert len(rows) == 12
    assert {row["case_id"] for row in rows} == {case["id"]}
    assert (
        len({(row["case_id"], row["mode"], row["condition"], row["repeat"]) for row in rows}) == 12
    )
    assert all(row["kind"] == "boolean" for row in rows)
    assert all(bool(row["error"]) == worker_failed for row in rows)
    summary = json.loads((output / "summary.json").read_text())
    assert set(summary["groups_by_kind"]) == {
        f"{mode}/process_cold_start/boolean" for mode in metadata["modes"]
    }
    assert all(group["attempts"] == 3 for group in summary["groups_by_kind"].values())
    assert audit_run(output, fixtures_dir=suite)["passed"]

    # The declared schedule must now expose a missing repetition to the audit.
    metadata["repeats"] = 4
    metadata_path.write_text(json.dumps(metadata))
    report = audit_run(output, fixtures_dir=suite)
    assert not report["passed"]
    assert any("declared schedule" in error for error in report["errors"])
