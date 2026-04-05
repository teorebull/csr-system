from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_evidence_analyzer(state: PipelineState) -> PipelineState:
    """Placeholder node for claim-evidence stance analysis."""
    state.logs.append(
        RunLogEntry(
            node_name="evidence_analyzer",
            status="pending_implementation",
            message="Evidence analysis logic is not implemented yet.",
        )
    )
    return state
