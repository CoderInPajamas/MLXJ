"""Generated-output format checks using a fake generator, without importing MLX."""

import sys
import threading
from types import SimpleNamespace

import pytest

from jev_mlx.backends.mlx_lm import MLXLMBackend
from jev_mlx.prompt import CompiledChoice


@pytest.fixture
def generated(monkeypatch):
    control = {"text": "", "kwargs": None}

    def stream_generate(*args, **kwargs):
        control["kwargs"] = kwargs
        yield SimpleNamespace(text=control["text"], generation_tokens=7, finish_reason="stop")

    monkeypatch.setitem(sys.modules, "mlx_lm", SimpleNamespace(stream_generate=stream_generate))
    monkeypatch.setitem(
        sys.modules, "mlx_lm.sample_utils", SimpleNamespace(make_sampler=lambda **kwargs: None)
    )
    backend = MLXLMBackend.__new__(MLXLMBackend)
    backend._lock = threading.RLock()
    backend.model = backend.tokenizer = None
    backend.prefill_step_size = 256
    backend.identity = {"name": "test-double"}
    backend.mx = SimpleNamespace(eval=lambda *args: None, synchronize=lambda: None)
    choices = (
        CompiledChoice("close.notes", "0", 10, "Close notes"),
        CompiledChoice("__no_match__", "1", 11, "No match"),
        CompiledChoice("__abstain__", "2", 12, "Abstain"),
    )
    backend._prepare = lambda *args: (SimpleNamespace(choices=choices), [], [7], {})
    backend._timing = lambda *args: {"total_ms": 1.0}
    return backend, control


@pytest.mark.parametrize(
    "text,status,candidate_id",
    [
        ('{"choice":"0"}', "selected", "close.notes"),
        ('{"choice":"1"}', "no_match", None),
        ('{"choice":"2"}', "abstain", None),
        ('{"choice":"9"}', "invalid", None),
        ('{"choice":0}', "invalid", None),
        ('{"choice":"close.notes"}', "invalid", None),
        ('{"candidate_id":"0"}', "invalid", None),
        ('{"choice":"0","explanation":"yes"}', "invalid", None),
        ('{"choice":"0"', "invalid", None),
        ('```json\n{"choice":"0"}\n```', "invalid", None),
    ],
)
def test_compact_json_maps_only_valid_option_codes(generated, text, status, candidate_id):
    backend, control = generated
    control["text"] = text
    result = backend.generate_baseline(None, mode="json_code")
    assert result["status"] == status
    assert result["candidate_id"] == candidate_id
    assert result["schema_valid"] is (status != "invalid")
    assert result["raw_text"] == text
    assert control["kwargs"]["max_tokens"] == 96
    assert "logits_processors" not in control["kwargs"]


@pytest.mark.parametrize(
    "mode,text,status,candidate_id",
    [
        ("json", '{"candidate_id":"close.notes"}', "selected", "close.notes"),
        ("json", '{"candidate_id":"0"}', "invalid", None),
        ("json", '{"choice":"0"}', "invalid", None),
        ("code", "0", "selected", "close.notes"),
        ("code", '{"choice":"0"}', "invalid", None),
    ],
)
def test_existing_generated_formats_keep_their_original_contract(
    generated, mode, text, status, candidate_id
):
    backend, control = generated
    control["text"] = text
    result = backend.generate_baseline(None, mode=mode)
    assert result["status"] == status
    assert result["candidate_id"] == candidate_id
    assert control["kwargs"]["max_tokens"] == (1 if mode == "code" else 96)
