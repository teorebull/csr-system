from __future__ import annotations

import os
from pathlib import Path

from src.pipeline.evidence_fetcher import (
    extract_all_evidence,
    filter_low_quality_sources,
    load_search_results,
    save_evidence_csv,
    select_best_results,
)
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_5" / "search_results.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_6" / "evidence_candidates.csv"
PIPELINE_MODE = os.environ.get("PIPELINE_MODE", "normal").strip().lower()


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading search results...")
    results = load_search_results(INPUT_CSV)
    results = filter_low_quality_sources(results)
    results = select_best_results(results)

    print(f"Pipeline mode: {PIPELINE_MODE}")
    print("Extracting article and PDF text...")
    evidence_rows = extract_all_evidence(results)

    save_evidence_csv(evidence_rows, OUTPUT_CSV)

    print(f"Evidence rows created: {len(evidence_rows)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
