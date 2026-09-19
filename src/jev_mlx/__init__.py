"""JEV MLX: JEV-inspired local decisions for Apple Silicon."""

from .engine import DecisionBackend, MLXDecisionEngine
from .session import (
    DecisionExecutionError,
    DecisionSession,
    InvalidDecisionError,
    ReplayDecisionError,
    StaleDecisionError,
)
from .types import (
    ABSTAIN_ID,
    NO_MATCH_ID,
    BackendOutput,
    Candidate,
    DecisionRequest,
    DecisionResult,
    boolean_request,
)

__version__ = "0.1.0"

__all__ = [
    "ABSTAIN_ID",
    "NO_MATCH_ID",
    "BackendOutput",
    "Candidate",
    "DecisionBackend",
    "DecisionExecutionError",
    "DecisionRequest",
    "DecisionResult",
    "DecisionSession",
    "InvalidDecisionError",
    "MLXDecisionEngine",
    "ReplayDecisionError",
    "StaleDecisionError",
    "boolean_request",
]
