from __future__ import annotations

import csv
import os
from pathlib import Path

from src.pipeline.web_search import load_queries, search_all_queries
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_4" / "queries.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_5" / "search_results.csv"


def save_results_csv(results: list[dict], output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "query_type",
                "query_text",
                "result_rank",
                "title",
                "url",
                "snippet",
                "source",
                "source_quality_score",
                "source_quality_label",
            ],
        )
        writer.writeheader()

        for result in results:
            writer.writerow(result)


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading queries...")
    queries = load_queries(INPUT_CSV)

    print(f"Company filter: {COMPANY_NAME}")
    print("Running web search...")
    results, _result_models = search_all_queries(queries, COMPANY_NAME)

    save_results_csv(results, OUTPUT_CSV)

    print(f"Search results collected: {len(results)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
