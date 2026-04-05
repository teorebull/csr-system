from src.schemas.claim import ClaimGroup


def test_claim_group_tracks_members() -> None:
    group = ClaimGroup(
        canonical_claim_id="c1",
        member_claim_ids=["c1", "c2"],
        merge_reason="Semantic similarity above threshold.",
    )

    assert group.member_claim_ids == ["c1", "c2"]
