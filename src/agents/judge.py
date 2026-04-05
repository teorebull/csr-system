from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_judge(state: PipelineState) -> PipelineState:
    """Placeholder node for final aggregation and greenwashing assessment."""
    state.logs.append(
        RunLogEntry(
            node_name="judge",
            status="pending_implementation",
            message="Final judgment logic is not implemented yet.",
        )
    )
    return state
