from __future__ import annotations

import csv
import os
from pathlib import Path

from src.pipeline.query_generator import generate_queries_for_all_claims, load_claims
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_3" / "prioritized_claims.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_4" / "queries.csv"


def save_queries_csv(queries: list[dict], output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["normalized_claim_id", "query_type", "query_text"])
        writer.writeheader()

        for query in queries:
            writer.writerow(query)


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading normalized claims...")
    claims = load_claims(INPUT_CSV)

    print("Generating queries...")
    queries, _search_queries = generate_queries_for_all_claims(claims)

    save_queries_csv(queries, OUTPUT_CSV)

    print(f"Queries generated: {len(queries)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
