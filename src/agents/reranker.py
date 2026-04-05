from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_reranker(state: PipelineState) -> PipelineState:
    """Placeholder node for evidence reranking and source filtering."""
    state.logs.append(
        RunLogEntry(
            node_name="reranker",
            status="pending_implementation",
            message="Reranking logic is not implemented yet.",
        )
    )
    return state
