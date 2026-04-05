from src.schemas.claim import Claim, ClaimCandidate, ClaimPriority, ClaimTopic, ClaimType
from src.schemas.state import PipelineState


def test_claim_candidate_can_be_created() -> None:
    claim = ClaimCandidate(
        claim_id="c1",
        company="Example Corp",
        claim_text="We reduced emissions by 20% in 2024.",
        source_document="report.pdf",
        source_page=12,
        source_excerpt="We reduced emissions by 20% in 2024.",
        claim_type=ClaimType.PERFORMANCE,
        topic=ClaimTopic.EMISSIONS,
        priority=ClaimPriority.HIGH,
    )

    assert claim.claim_id == "c1"
    assert claim.topic == ClaimTopic.EMISSIONS


def test_pipeline_state_can_hold_normalized_claims() -> None:
    normalized_claim = Claim(
        claim_id="c1",
        company="Example Corp",
        claim_text="We reduced emissions by 20% in 2024.",
        canonical_text="Example Corp reduced emissions by 20% in 2024.",
        source_document="report.pdf",
        source_page=12,
        source_excerpt="We reduced emissions by 20% in 2024.",
        claim_type=ClaimType.PERFORMANCE,
        topic=ClaimTopic.EMISSIONS,
        priority=ClaimPriority.HIGH,
        normalized_from_ids=["c1"],
    )

    state = PipelineState(
        user_query="Analyze Example Corp's sustainability claims.",
        company_name="Example Corp",
        normalized_claims=[normalized_claim],
    )

    assert len(state.normalized_claims) == 1
