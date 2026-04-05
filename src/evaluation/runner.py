from __future__ import annotations

from src.schemas.state import PipelineState


def run_evaluation(state: PipelineState) -> dict:
    """Placeholder evaluation runner for manual or batch experiments."""
    return {
        "company": state.company_name,
        "claims_candidates": len(state.claims_candidates),
        "normalized_claims": len(state.normalized_claims),
        "assessments": len(state.claim_assessments),
    }
