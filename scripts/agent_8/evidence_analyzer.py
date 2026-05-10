from __future__ import annotations

import csv
import os
csv.field_size_limit(10**7)
from pathlib import Path

from src.pipeline.evidence_analyzer import (
    analyze_all_claims,
    build_claim_lookup,
    group_top_evidence,
    is_ollama_available,
    load_assessment_cache,
    load_csv_rows,
    save_assessment_cache,
    save_assessments_csv,
)
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_3" / "prioritized_claims.csv"
RANKED_EVIDENCE_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_7" / "ranked_evidence.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_8" / "claim_assessments.csv"
CACHE_JSON = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_8" / "assessment_cache.json"


def main() -> None:
    if not CLAIMS_CSV.exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not RANKED_EVIDENCE_CSV.exists():
        print(f"Ranked evidence CSV not found: {RANKED_EVIDENCE_CSV}")
        return

    if not is_ollama_available():
        print("Ollama is not reachable. Start it with `ollama serve` before running Agent 8.")
        print("Existing claim assessments were left unchanged.")
        return

    print("Loading normalized claims...")
    claims = load_csv_rows(CLAIMS_CSV)
    claim_lookup = build_claim_lookup(claims)

    print("Loading ranked evidence...")
    ranked_evidence = load_csv_rows(RANKED_EVIDENCE_CSV)
    grouped_evidence = group_top_evidence(ranked_evidence, 3)

    print("Analyzing claims against evidence...")
    cache = load_assessment_cache(CACHE_JSON)
    assessments = analyze_all_claims(claim_lookup, grouped_evidence, cache)
    save_assessment_cache(cache, CACHE_JSON)

    save_assessments_csv(assessments, OUTPUT_CSV)

    print(f"Claim assessments created: {len(assessments)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
