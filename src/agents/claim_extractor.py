from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_claim_extractor(state: PipelineState) -> PipelineState:
    """Placeholder node for structured CSR claim extraction."""
    state.logs.append(
        RunLogEntry(
            node_name="claim_extractor",
            status="pending_implementation",
            message="Claim extraction logic is not implemented yet.",
        )
    )
    return state
