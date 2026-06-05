from __future__ import annotations

import os
from pathlib import Path

from src.pipeline.judge_aggregator import build_final_report, load_csv_rows, save_final_report_artifacts
from src.utils.company import artifact_root_for_company


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
ARTIFACT_ROOT = artifact_root_for_company(COMPANY_NAME)
ASSESSMENTS_CSV = ARTIFACT_ROOT / "agent_8" / "claim_assessments.csv"


def main() -> None:
    assessments = load_csv_rows(ASSESSMENTS_CSV)

    if not assessments:
        print(f"Assessments CSV not found or empty: {ASSESSMENTS_CSV}")
        return

    final_report = build_final_report(ARTIFACT_ROOT, assessments)
    save_final_report_artifacts(ARTIFACT_ROOT, final_report)

    print(f"Final report saved to: {ARTIFACT_ROOT / 'agent_9' / 'final_report.csv'}")
    print(f"Final CSR CSV saved to: {ARTIFACT_ROOT / 'agent_9' / 'final_csr_assessment.csv'}")
    print(f"Final environmental CSV saved to: {ARTIFACT_ROOT / 'agent_9' / 'final_environmental_subassessment.csv'}")
    print(f"Final JSON saved to: {ARTIFACT_ROOT / 'agent_9' / 'final_report.json'}")
    print(f"Final summary saved to: {ARTIFACT_ROOT / 'agent_9' / 'final_summary.md'}")


if __name__ == "__main__":
    main()
