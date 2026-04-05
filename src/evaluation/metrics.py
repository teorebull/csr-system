from __future__ import annotations

from src.schemas.report import FinalReport


def compute_credibility_score(report: FinalReport) -> float:
    if report.total_claims == 0:
        return 0.0

    weighted_sum = (
        1.0 * report.supported
        + 0.5 * report.partially_supported
        + 0.0 * report.unsupported
        - 0.5 * report.contradicted
    )
    return weighted_sum / report.total_claims
