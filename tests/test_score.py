from src.evaluation.metrics import compute_credibility_score
from src.schemas.report import FinalReport, GreenwashingRiskLevel


def test_compute_credibility_score() -> None:
    report = FinalReport(
        company="Example Corp",
        total_claims=4,
        supported=2,
        partially_supported=1,
        unsupported=1,
        contradicted=0,
        credibility_score=0.0,
        greenwashing_risk_level=GreenwashingRiskLevel.MODERATE,
        final_conclusion="Test report.",
    )

    assert compute_credibility_score(report) == 0.625
