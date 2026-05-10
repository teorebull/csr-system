from __future__ import annotations

import os
from pathlib import Path

from src.pipeline.judge_aggregator import build_final_report, load_csv_rows, save_final_report_artifacts
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
ASSESSMENTS_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_8" / "claim_assessments.csv"


def main() -> None:
    assessments = load_csv_rows(ASSESSMENTS_CSV)

    if not assessments:
        print(f"Assessments CSV not found or empty: {ASSESSMENTS_CSV}")
        return

    final_report = build_final_report(PROJECT_ROOT, assessments)
    save_final_report_artifacts(PROJECT_ROOT, final_report)

    print(f"Final report saved to: {PROJECT_ROOT / 'data' / 'processed' / 'agent_9' / 'final_report.csv'}")
    print(f"Final JSON saved to: {PROJECT_ROOT / 'data' / 'processed' / 'agent_9' / 'final_report.json'}")
    print(f"Final summary saved to: {PROJECT_ROOT / 'data' / 'processed' / 'agent_9' / 'final_summary.md'}")


if __name__ == "__main__":
    main()
