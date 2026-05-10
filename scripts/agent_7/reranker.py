from __future__ import annotations

import os
from pathlib import Path

from src.pipeline.reranker import build_claim_lookup, filter_usable_evidence, load_csv_rows, rerank_evidence, save_ranked_evidence
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_3" / "prioritized_claims.csv"
EVIDENCE_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_6" / "evidence_candidates.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_7" / "ranked_evidence.csv"


def main() -> None:
    if not CLAIMS_CSV.exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not EVIDENCE_CSV.exists():
        print(f"Evidence CSV not found: {EVIDENCE_CSV}")
        return

    print("Loading normalized claims...")
    claims = load_csv_rows(CLAIMS_CSV)
    claim_lookup = build_claim_lookup(claims)

    print("Loading evidence candidates...")
    evidence_rows = load_csv_rows(EVIDENCE_CSV)
    evidence_rows = filter_usable_evidence(evidence_rows)

    print("Reranking evidence...")
    ranked_rows = rerank_evidence(claim_lookup, evidence_rows)

    save_ranked_evidence(ranked_rows, OUTPUT_CSV)

    print(f"Usable evidence rows: {len(evidence_rows)}")
    print(f"Ranked evidence rows: {len(ranked_rows)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
