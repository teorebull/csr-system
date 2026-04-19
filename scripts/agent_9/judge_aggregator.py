import csv
import json
from pathlib import Path


ASSESSMENTS_CSV = "data/processed/agent_8/claim_assessments.csv"
FUTURE_CLAIMS_CSV = "data/processed/agent_3/future_claims.csv"
FINAL_REPORT_CSV = "data/processed/agent_9/final_report.csv"
FINAL_REPORT_JSON = "data/processed/agent_9/final_report.json"
FINAL_SUMMARY_MD = "data/processed/agent_9/final_summary.md"
COMPANY_NAME = "Microsoft"


def load_csv_rows(csv_path: str) -> list[dict]:
    """Load rows from CSV if the file exists."""
    path = Path(csv_path)

    if not path.exists():
        return []

    rows = []

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def count_labels(assessments: list[dict]) -> dict:
    """Count final labels across all analyzed claims."""
    counts = {
        "SUPPORTED": 0,
        "PARTIALLY_SUPPORTED": 0,
        "UNSUPPORTED": 0,
        "CONTRADICTED": 0,
    }

    for row in assessments:
        label = row.get("final_label", "").strip().upper()

        if label in counts:
            counts[label] += 1

    return counts


def build_conclusion(label_counts: dict, total_claims: int, future_claims_count: int) -> str:
    """Create a simple rule-based conclusion for the MVP."""
    supported = label_counts["SUPPORTED"]
    partial = label_counts["PARTIALLY_SUPPORTED"]
    unsupported = label_counts["UNSUPPORTED"]
    contradicted = label_counts["CONTRADICTED"]

    if total_claims == 0:
        return "No claims were analyzed, so no overall conclusion can be drawn."

    if contradicted > 0:
        return (
            f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, "
            f"but at least {contradicted} claim(s) are contradicted by external evidence, which may indicate "
            f"potential greenwashing risk or inconsistency in the company's sustainability communication."
        )

    if supported + partial == total_claims:
        return (
            f"The analyzed discourse appears broadly credible. Most evaluated claims are supported or partially supported "
            f"by external evidence, although some claims may still require stronger third-party validation."
        )

    if unsupported >= total_claims / 2:
        return (
            f"The analyzed discourse is weakly substantiated by external evidence. A large share of claims remain unsupported, "
            f"which suggests limited external confirmation of the company's sustainability narrative."
        )

    conclusion = (
        f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, while others remain unsupported. "
        f"This suggests that the company's sustainability discourse is only partially substantiated by external evidence."
    )

    if future_claims_count > 0:
        conclusion += f" In addition, {future_claims_count} future-looking claim(s) were identified and excluded from the main evaluation."

    return conclusion


def build_report_rows(assessments: list[dict]) -> list[dict]:
    """Create a simple final report table from claim assessments."""
    report_rows = []

    for row in assessments:
        report_rows.append(
            {
                "normalized_claim_id": row.get("normalized_claim_id", ""),
                "claim_text": row.get("claim_text", ""),
                "final_label": row.get("final_label", ""),
                "justification": row.get("justification", ""),
                "top_evidence_url": row.get("top_evidence_url", ""),
                "top_evidence_title": row.get("top_evidence_title", ""),
            }
        )

    return report_rows


def save_report_csv(rows: list[dict], output_path: str) -> None:
    """Save final report rows to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "claim_text",
                "final_label",
                "justification",
                "top_evidence_url",
                "top_evidence_title",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def save_report_json(report: dict, output_path: str) -> None:
    """Save the aggregated final report as JSON."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def build_summary_markdown(report: dict) -> str:
    """Build a readable markdown summary for the MVP."""
    label_counts = report["label_counts"]

    lines = [
        f"# Final Summary - {report['company_name']}",
        "",
        "## Overview",
        f"- Total claims analyzed: {report['total_claims_analyzed']}",
        f"- Future claims excluded: {report['future_claims_excluded']}",
        "",
        "## Label Counts",
        f"- SUPPORTED: {label_counts['SUPPORTED']}",
        f"- PARTIALLY_SUPPORTED: {label_counts['PARTIALLY_SUPPORTED']}",
        f"- UNSUPPORTED: {label_counts['UNSUPPORTED']}",
        f"- CONTRADICTED: {label_counts['CONTRADICTED']}",
        "",
        "## Final Conclusion",
        report["final_conclusion"],
        "",
        "## Claim Summary",
    ]

    for row in report["claims"]:
        lines.append(f"- [{row['final_label']}] {row['claim_text']}")
        lines.append(f"  Evidence: {row['top_evidence_url']}")

    return "\n".join(lines)


def save_summary_markdown(text: str, output_path: str) -> None:
    """Save the markdown summary."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8")


def main() -> None:
    assessments = load_csv_rows(ASSESSMENTS_CSV)
    future_claims = load_csv_rows(FUTURE_CLAIMS_CSV)

    if not assessments:
        print(f"Assessments CSV not found or empty: {ASSESSMENTS_CSV}")
        return

    label_counts = count_labels(assessments)
    total_claims = len(assessments)
    future_claims_count = len(future_claims)
    final_conclusion = build_conclusion(label_counts, total_claims, future_claims_count)
    report_rows = build_report_rows(assessments)

    final_report = {
        "company_name": COMPANY_NAME,
        "total_claims_analyzed": total_claims,
        "future_claims_excluded": future_claims_count,
        "label_counts": label_counts,
        "final_conclusion": final_conclusion,
        "claims": report_rows,
    }

    save_report_csv(report_rows, FINAL_REPORT_CSV)
    save_report_json(final_report, FINAL_REPORT_JSON)
    save_summary_markdown(build_summary_markdown(final_report), FINAL_SUMMARY_MD)

    print(f"Final report saved to: {FINAL_REPORT_CSV}")
    print(f"Final JSON saved to: {FINAL_REPORT_JSON}")
    print(f"Final summary saved to: {FINAL_SUMMARY_MD}")


if __name__ == "__main__":
    main()
