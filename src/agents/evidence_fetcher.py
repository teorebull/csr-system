from __future__ import annotations

from src.schemas.state import PipelineState, RunLogEntry


def run_evidence_fetcher(state: PipelineState) -> PipelineState:
    """Placeholder node for downloading and cleaning evidence pages."""
    state.logs.append(
        RunLogEntry(
            node_name="evidence_fetcher",
            status="pending_implementation",
            message="Evidence fetching logic is not implemented yet.",
        )
    )
    return state
