from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_web_search(state: PipelineState) -> PipelineState:
    """Placeholder node for web search over external evidence sources."""
    state.logs.append(
        RunLogEntry(
            node_name="web_search",
            status="pending_implementation",
            message="Web search logic is not implemented yet.",
        )
    )
    return state
