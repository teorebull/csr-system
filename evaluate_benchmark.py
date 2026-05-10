from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BENCHMARK_CSV = PROJECT_ROOT / "BENCHMARK_DATASET.csv"
FINAL_REPORT_JSON = PROJECT_ROOT / "data" / "processed" / "langgraph" / "agent_9" / "final_report.json"


def load_benchmark_rows(csv_path: Path) -> list[dict]:
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def load_final_report_claims(json_path: Path) -> list[dict]:
    if not json_path.exists():
        raise FileNotFoundError(f"Final report not found: {json_path}")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return data.get("claims", [])


def build_claim_lookup(rows: list[dict]) -> dict[str, dict]:
    return {row.get("normalized_claim_id", ""): row for row in rows if row.get("normalized_claim_id")}


def score_row(benchmark_row: dict, pipeline_row: dict | None) -> tuple[int, dict[str, str]]:
    details = {
        "included": "0",
        "support": "0",
        "relevance": "0",
        "risk": "0",
    }

    benchmark_include = benchmark_row.get("benchmark_include", "").strip().lower()
    expected_support = benchmark_row.get("benchmark_support", "").strip().upper()
    expected_relevance = benchmark_row.get("benchmark_relevance", "").strip().upper()
    expected_risk = benchmark_row.get("benchmark_risk", "").strip().upper()

    actual_included = pipeline_row is not None
    expected_included = benchmark_include == "yes"

    score = 0

    if actual_included == expected_included:
        score += 1
        details["included"] = "1"

    if pipeline_row is None:
        return score, details

    actual_support = pipeline_row.get("final_label", "").strip().upper()
    actual_relevance = pipeline_row.get("evidence_relevance", "").strip().upper()
    actual_risk = pipeline_row.get("greenwashing_risk_level", "").strip().upper()

    if actual_support == expected_support:
        score += 1
        details["support"] = "1"

    if actual_relevance == expected_relevance:
        score += 1
        details["relevance"] = "1"

    if actual_risk == expected_risk:
        score += 1
        details["risk"] = "1"

    return score, details


def main() -> None:
    benchmark_rows = [
        row for row in load_benchmark_rows(BENCHMARK_CSV)
        if row.get("review_status", "").strip().lower() == "reviewed"
    ]
    pipeline_claims = load_final_report_claims(FINAL_REPORT_JSON)
    pipeline_lookup = build_claim_lookup(pipeline_claims)

    total_possible = len(benchmark_rows) * 4
    total_score = 0

    print("Benchmark evaluation against current LangGraph final report")
    print(f"Benchmark rows: {len(benchmark_rows)}")
    print(f"Final report claims: {len(pipeline_claims)}")
    print()

    for row in benchmark_rows:
        claim_id = row["normalized_claim_id"]
        pipeline_row = pipeline_lookup.get(claim_id)
        row_score, details = score_row(row, pipeline_row)
        total_score += row_score

        print(f"{row['benchmark_id']} | {claim_id} | score {row_score}/4")
        print(f"  Include:   {details['included']}")
        print(f"  Support:   {details['support']}")
        print(f"  Relevance: {details['relevance']}")
        print(f"  Risk:      {details['risk']}")
        if pipeline_row is None:
            print("  Pipeline row: missing")
        else:
            print(
                "  Pipeline row: "
                f"{pipeline_row.get('final_label', '')} / "
                f"{pipeline_row.get('evidence_relevance', '')} / "
                f"{pipeline_row.get('greenwashing_risk_level', '')}"
            )
        print()

    print(f"Total score: {total_score}/{total_possible}")
    if total_possible:
        print(f"Accuracy proxy: {100 * total_score / total_possible:.1f}%")


if __name__ == "__main__":
    main()
