from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_query_generator(state: PipelineState) -> PipelineState:
    """Placeholder node for search query generation."""
    state.logs.append(
        RunLogEntry(
            node_name="query_generator",
            status="pending_implementation",
            message="Query generation logic is not implemented yet.",
        )
    )
    return state
