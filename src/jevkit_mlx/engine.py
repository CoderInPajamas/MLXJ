"""Backend-independent decision scoring and explicit rejection semantics."""

from __future__ import annotations

import copy
import math
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from .types import (
    ABSTAIN_ID,
    NO_MATCH_ID,
    RESERVED_IDS,
    BackendOutput,
    DecisionRequest,
    DecisionResult,
)


class DecisionBackend(Protocol):
    def score(
        self,
        request: DecisionRequest,
        *,
        cache_key: str | None = None,
        use_cache: bool = True,
    ) -> BackendOutput: ...


class MLXDecisionEngine:
    """Select one supplied choice using model logits, without text generation.

    ``margin_threshold`` is an optional raw-logit rejection threshold, not a
    calibrated confidence level. Tune it on development data only. A zero
    default rejects exact ties but makes no additional confidence claim.
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        backend: DecisionBackend | None = None,
        margin_threshold: float = 0.0,
        **backend_options: object,
    ) -> None:
        if isinstance(margin_threshold, bool) or not isinstance(margin_threshold, (int, float)):
            raise ValueError("margin_threshold must be a finite nonnegative number")  # noqa: TRY004
        if not math.isfinite(margin_threshold) or margin_threshold < 0:
            raise ValueError("margin_threshold must be a finite nonnegative number")
        if backend is not None and (model is not None or backend_options):
            raise ValueError("supply either a model and backend options or an injected backend")
        if backend is None:
            if not model:
                raise ValueError("a model path or an injected backend is required")
            from .backends.mlx_lm import MLXLMBackend

            backend = MLXLMBackend(model, **backend_options)
        self.backend = backend
        self.margin_threshold = float(margin_threshold)

    @property
    def model_identity(self) -> dict:
        """Return the backend's recorded model and runtime identity."""
        return copy.deepcopy(getattr(self.backend, "identity", {}))

    def decide(
        self,
        request: DecisionRequest,
        *,
        use_cache: bool = True,
        cache_key: str | None = None,
    ) -> DecisionResult:
        if not isinstance(request, DecisionRequest):
            raise TypeError("request must be a DecisionRequest")
        # Revalidate and isolate mutable JSON from a caller while inference runs.
        request = DecisionRequest.from_dict(request.to_dict())
        started = perf_counter()
        output = self.backend.score(request, cache_key=cache_key, use_cache=use_cache)
        if not isinstance(output, BackendOutput):
            raise TypeError("backend.score must return BackendOutput")
        ids = [candidate.id for candidate in request.candidates] + list(RESERVED_IDS)
        if not isinstance(output.raw_scores, dict) or set(output.raw_scores) != set(ids):
            raise ValueError(
                "backend scores must cover exactly the candidates and reserved choices"
            )
        raw_scores = {}
        for candidate_id in ids:
            score = output.raw_scores[candidate_id]
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                raise ValueError("backend scores must be finite real numbers")
            raw_scores[candidate_id] = float(score)
        ranked = sorted(ids, key=lambda candidate_id: raw_scores[candidate_id], reverse=True)
        winner = ranked[0]
        margin = raw_scores[winner] - raw_scores[ranked[1]]
        if not math.isfinite(margin):
            raise ValueError("backend logit range is too large")
        exponentials = {
            candidate_id: math.exp(score - raw_scores[winner])
            for candidate_id, score in raw_scores.items()
        }
        denominator = sum(exponentials.values())
        scores = {candidate_id: score / denominator for candidate_id, score in exponentials.items()}
        status = (
            "no_match"
            if winner == NO_MATCH_ID
            else "abstain"
            if winner == ABSTAIN_ID
            else "selected"
        )
        if status == "selected" and margin <= self.margin_threshold:
            status = "abstain"
        timing = copy.deepcopy(output.timing)
        timing["decision_ms"] = (perf_counter() - started) * 1000
        return DecisionResult(
            candidate_id=winner if status == "selected" else None,
            status=status,
            raw_selected_id=winner,
            raw_scores=raw_scores,
            scores=scores,
            margin=margin,
            state_version=request.state_version,
            model=copy.deepcopy(output.model),
            timing=timing,
            cache=copy.deepcopy(output.cache),
            request_id=uuid4().hex,
            selected_value=copy.deepcopy(
                next(
                    (candidate.value for candidate in request.candidates if candidate.id == winner),
                    None,
                )
            )
            if status == "selected"
            else None,
        )
