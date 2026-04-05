from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_claim_normalizer(state: PipelineState) -> PipelineState:
    """Placeholder node for claim canonicalization and deduplication."""
    state.logs.append(
        RunLogEntry(
            node_name="claim_normalizer",
            status="pending_implementation",
            message="Claim normalization logic is not implemented yet.",
        )
    )
    return state
