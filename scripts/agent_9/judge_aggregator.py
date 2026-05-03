import csv
csv.field_size_limit(10**7)
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENTS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_8" / "claim_assessments.csv"
CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_2" / "claims.csv"
NORMALIZED_CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "normalized_claims.csv"
PRIORITIZED_CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "prioritized_claims.csv"
EXCLUDED_CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "excluded_claims.csv"
FUTURE_CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "future_claims.csv"
QUERIES_CSV = PROJECT_ROOT / "data" / "processed" / "agent_4" / "queries.csv"
SEARCH_RESULTS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_5" / "search_results.csv"
EVIDENCE_CANDIDATES_CSV = PROJECT_ROOT / "data" / "processed" / "agent_6" / "evidence_candidates.csv"
RANKED_EVIDENCE_CSV = PROJECT_ROOT / "data" / "processed" / "agent_7" / "ranked_evidence.csv"
AGENT_2_CACHE_JSON = PROJECT_ROOT / "data" / "processed" / "agent_2" / "claim_extraction_cache.json"
AGENT_8_CACHE_JSON = PROJECT_ROOT / "data" / "processed" / "agent_8" / "assessment_cache.json"
FINAL_REPORT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_9" / "final_report.csv"
FINAL_REPORT_JSON = PROJECT_ROOT / "data" / "processed" / "agent_9" / "final_report.json"
FINAL_SUMMARY_MD = PROJECT_ROOT / "data" / "processed" / "agent_9" / "final_summary.md"
COMPANY_NAME = "Microsoft"
LOCAL_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"
PIPELINE_MODE = os.environ.get("PIPELINE_MODE", "normal").strip().lower()
AGENT_2_MODEL = "qwen2.5:14b"
AGENT_4_MODEL = "mistral-nemo:latest"
AGENT_7_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
AGENT_8_MODEL = "qwen2.5:14b"
AGENT_8_TOP_K_EVIDENCE = 3
THEME_KEYWORDS = {
    "GHG emissions": ["ghg", "scope", "emissions", "carbon inventory", "warming potentials", "kyoto"],
    "Renewable electricity and Scope 2 accounting": ["renewable", "electricity", "recs", "eac", "ppa", "market-based", "location-based"],
    "Carbon neutrality and removals": ["carbon neutrality", "carbon neutral", "carbon negative", "carbon removal", "credits"],
    "Water and data centers": ["water", "withdrawal", "consumption", "discharge", "data center", "data centres"],
    "Land, ecosystems, and circularity": ["land", "ecosystem", "nature", "packaging", "waste", "circularity"],
    "Supply chain and methodology": ["supplier", "supply chain", "primary data", "estimates", "methodology", "spend"],
}


def load_csv_rows(csv_path: Path) -> list[dict]:
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


def load_json_file(json_path: Path):
    """Load a JSON file if it exists and is valid."""
    if not json_path.exists():
        return None

    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def count_rows(csv_path: Path) -> int:
    """Count rows in a CSV artifact if present."""
    return len(load_csv_rows(csv_path))


def unique_values(rows: list[dict], field_name: str) -> list[str]:
    """Return sorted non-empty unique values from rows."""
    values = set()

    for row in rows:
        value = row.get(field_name, "")

        if value:
            values.add(str(value))

    return sorted(values)


def build_run_metadata(
    claims: list[dict],
    normalized_claims: list[dict],
    prioritized_claims: list[dict],
    excluded_claims: list[dict],
    future_claims: list[dict],
    assessments: list[dict],
) -> dict:
    """Build reproducibility metadata for the final report."""
    agent_2_cache = load_json_file(AGENT_2_CACHE_JSON)
    agent_8_cache = load_json_file(AGENT_8_CACHE_JSON)
    document_ids = unique_values(claims, "document_id") or unique_values(normalized_claims, "document_id")
    document_names = unique_values(claims, "document_name") or unique_values(normalized_claims, "document_name")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_mode": PIPELINE_MODE,
        "company_name": COMPANY_NAME,
        "documents": {
            "document_count": len(document_ids) if document_ids else len(document_names),
            "document_ids": document_ids,
            "document_names": document_names,
        },
        "models": {
            "agent_2_claim_extractor": AGENT_2_MODEL,
            "agent_4_query_generator": AGENT_4_MODEL,
            "agent_7_embedding_model": AGENT_7_EMBEDDING_MODEL,
            "agent_8_evidence_analyzer": AGENT_8_MODEL,
            "agent_9_final_analysis": LOCAL_MODEL if PIPELINE_MODE != "fast" else "deterministic_fallback",
        },
        "settings": {
            "agent_8_top_k_evidence": AGENT_8_TOP_K_EVIDENCE,
            "agent_9_uses_llm_analysis": PIPELINE_MODE != "fast",
        },
        "artifact_counts": {
            "claims_extracted": len(claims),
            "claims_normalized": len(normalized_claims),
            "claims_prioritized_for_main_analysis": len(prioritized_claims),
            "claims_excluded_from_main_analysis": len(excluded_claims),
            "future_claims_excluded": len(future_claims),
            "queries_generated": count_rows(QUERIES_CSV),
            "search_results": count_rows(SEARCH_RESULTS_CSV),
            "evidence_candidates": count_rows(EVIDENCE_CANDIDATES_CSV),
            "ranked_evidence_rows": count_rows(RANKED_EVIDENCE_CSV),
            "claim_assessments": len(assessments),
        },
        "cache": {
            "agent_2_claim_extraction_cache_exists": AGENT_2_CACHE_JSON.exists(),
            "agent_2_cached_pages": len(agent_2_cache) if isinstance(agent_2_cache, dict) else 0,
            "agent_8_assessment_cache_exists": AGENT_8_CACHE_JSON.exists(),
            "agent_8_cached_assessments": len(agent_8_cache) if isinstance(agent_8_cache, dict) else 0,
        },
        "artifacts": {
            "claims_csv": str(CLAIMS_CSV.relative_to(PROJECT_ROOT)),
            "normalized_claims_csv": str(NORMALIZED_CLAIMS_CSV.relative_to(PROJECT_ROOT)),
            "prioritized_claims_csv": str(PRIORITIZED_CLAIMS_CSV.relative_to(PROJECT_ROOT)),
            "excluded_claims_csv": str(EXCLUDED_CLAIMS_CSV.relative_to(PROJECT_ROOT)),
            "future_claims_csv": str(FUTURE_CLAIMS_CSV.relative_to(PROJECT_ROOT)),
            "claim_assessments_csv": str(ASSESSMENTS_CSV.relative_to(PROJECT_ROOT)),
            "final_report_csv": str(FINAL_REPORT_CSV.relative_to(PROJECT_ROOT)),
            "final_report_json": str(FINAL_REPORT_JSON.relative_to(PROJECT_ROOT)),
            "final_summary_md": str(FINAL_SUMMARY_MD.relative_to(PROJECT_ROOT)),
        },
    }


def count_labels(assessments: list[dict]) -> dict:
    """Count final labels across all analyzed claims."""
    counts = {
        "SUPPORTED": 0,
        "PARTIALLY_SUPPORTED": 0,
        "UNVERIFIED": 0,
        "PARTIALLY_CONTRADICTED": 0,
        "CONTRADICTED": 0,
    }

    for row in assessments:
        label = row.get("final_label", "").strip().upper()

        if label in counts:
            counts[label] += 1

    return counts


def count_risk_levels(assessments: list[dict]) -> dict:
    """Count greenwashing risk levels across analyzed claims."""
    counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "UNCLEAR": 0,
    }

    for row in assessments:
        risk_level = row.get("greenwashing_risk_level", "").strip().upper()

        if risk_level in counts:
            counts[risk_level] += 1

    return counts


def count_evidence_relevance(assessments: list[dict]) -> dict:
    """Count evidence relevance levels across analyzed claims."""
    counts = {
        "DIRECT": 0,
        "INDIRECT": 0,
        "BACKGROUND": 0,
        "UNRELATED": 0,
    }

    for row in assessments:
        relevance = row.get("evidence_relevance", "").strip().upper()

        if relevance in counts:
            counts[relevance] += 1

    return counts


def clean_generated_text(text: str) -> str:
    """Remove runtime contamination and obvious markup from generated fields."""
    text = str(text).strip()

    if not text:
        return ""

    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_generated_markdown(text: str) -> str:
    """Remove runtime contamination while preserving Markdown structure."""
    text = str(text).strip()

    if not text:
        return ""

    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def build_conclusion(
    label_counts: dict,
    risk_counts: dict,
    total_claims: int,
    future_claims_count: int,
) -> str:
    """Create a simple rule-based conclusion for the MVP."""
    supported = label_counts["SUPPORTED"]
    partial = label_counts["PARTIALLY_SUPPORTED"]
    unverified = label_counts["UNVERIFIED"]
    partially_contradicted = label_counts["PARTIALLY_CONTRADICTED"]
    contradicted = label_counts["CONTRADICTED"]
    high_risk = risk_counts.get("HIGH", 0)

    if total_claims == 0:
        return "No claims were analyzed, so no overall conclusion can be drawn."

    if contradicted > 0:
        return (
            f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, "
            f"but at least {contradicted} claim(s) are contradicted by external evidence, which may indicate "
            f"potential greenwashing risk or inconsistency in the company's sustainability communication."
        )

    if partially_contradicted > 0:
        return (
            f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, "
            f"but {partially_contradicted} claim(s) are partially contradicted by external evidence, which indicates "
            f"potential selective framing or incomplete sustainability communication."
        )

    if high_risk > 0:
        return (
            f"The analyzed discourse shows material greenwashing risk. No claim is directly contradicted by the provided evidence, "
            f"but {high_risk} claim(s) have high greenwashing-risk signals, mainly due to external evidence about emissions growth, "
            f"data-center energy demand, or accounting caveats. This suggests the narrative may be factually incomplete or selectively framed."
        )

    if supported + partial == total_claims:
        return (
            f"The analyzed discourse appears broadly credible. Most evaluated claims are supported or partially supported "
            f"by external evidence, although some claims may still require stronger third-party validation."
        )

    if unverified >= total_claims / 2:
        return (
            f"The analyzed discourse is weakly verified by external evidence. A large share of prioritized claims remain unverified, "
            f"which suggests limited external confirmation rather than direct falsification."
        )

    conclusion = (
        f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, while others remain unverified. "
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
                "greenwashing_risk_level": row.get("greenwashing_risk_level", ""),
                "evidence_relevance": row.get("evidence_relevance", ""),
                "justification": clean_generated_text(row.get("justification", "")),
                "risk_reasoning": clean_generated_text(row.get("risk_reasoning", "")),
                "top_evidence_url": row.get("top_evidence_url", ""),
                "top_evidence_title": row.get("top_evidence_title", ""),
            }
        )

    return report_rows


def save_report_csv(rows: list[dict], output_path: Path) -> None:
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
                "greenwashing_risk_level",
                "evidence_relevance",
                "justification",
                "risk_reasoning",
                "top_evidence_url",
                "top_evidence_title",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def save_report_json(report: dict, output_path: Path) -> None:
    """Save the aggregated final report as JSON."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def build_fallback_deep_analysis(report: dict) -> str:
    """Build a deterministic analytical section if the LLM is unavailable."""
    label_counts = report["label_counts"]
    risk_counts = report["greenwashing_risk_counts"]
    relevance_counts = report["evidence_relevance_counts"]
    claims = report["claims"]
    total_claims = report["total_claims_analyzed"]
    theme_summaries = build_theme_summaries(claims)

    unverified_or_partial = label_counts["UNVERIFIED"] + label_counts["PARTIALLY_SUPPORTED"]
    high_or_medium_risk = risk_counts["HIGH"] + risk_counts["MEDIUM"]

    lines = [
        "## Analytical Assessment",
        f"The main analysis covers {total_claims} prioritized claims. Most claims are not fully confirmed: {unverified_or_partial} are either partially supported or unverified.",
        f"Greenwashing risk is concentrated in {high_or_medium_risk} claims marked as medium or high risk.",
        f"Evidence relevance is direct or indirect for {relevance_counts['DIRECT'] + relevance_counts['INDIRECT']} claim(s), while {relevance_counts['BACKGROUND'] + relevance_counts['UNRELATED']} claim(s) rely on background or unrelated evidence.",
        "The strongest concern is not direct contradiction, but incomplete substantiation and contextual risk: several claims are factually plausible while the evidence raises concerns about emissions growth, accounting choices, renewable electricity matching, offsets, supplier emissions, or water impacts.",
        "",
        "## Main Risk Patterns",
    ]

    for theme in theme_summaries:
        risks = theme["risks"]
        labels = theme["labels"]
        lines.append(
            f"- {theme['theme']}: {theme['count']} claim(s), labels {labels}, risks {risks}."
        )

        for example in theme["examples"][:2]:
            lines.append(f"  Example: [{example['final_label']} | Risk: {example['risk']}] {example['claim_text']}")
            lines.append(f"  Reason: {example['risk_reasoning']}")

    lines.extend(["", "## Evidence Limitations"])

    unclear_claims = [claim for claim in claims if claim.get("greenwashing_risk_level") == "UNCLEAR"]
    no_evidence_claims = [claim for claim in claims if not claim.get("top_evidence_url")]
    weak_relevance_claims = [claim for claim in claims if claim.get("evidence_relevance") in {"BACKGROUND", "UNRELATED"}]
    lines.append(f"- {len(no_evidence_claims)} claim(s) did not have a selected evidence URL in the final assessment.")
    lines.append(f"- {len(unclear_claims)} claim(s) had unclear greenwashing risk, usually because the evidence was missing, weak, or not specific enough.")
    lines.append(f"- {len(weak_relevance_claims)} claim(s) were assessed with background or unrelated evidence, so their risk interpretation should be treated cautiously.")
    lines.append("- The report should be read as an evidence-driven screening, not a definitive audit. Claims with weak evidence need targeted retrieval before drawing strong conclusions.")

    lines.extend(["", "## Overall Interpretation"])
    lines.append(report["final_conclusion"])

    return "\n".join(lines)


def infer_theme(claim: dict) -> str:
    """Assign a broad theme to a claim for final narrative grouping."""
    text = f"{claim.get('claim_text', '')} {claim.get('risk_reasoning', '')}".lower()

    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return theme

    return "Other environmental claims"


def build_theme_summaries(claims: list[dict]) -> list[dict]:
    """Group claim-level results into compact theme summaries."""
    grouped = {}

    for claim in claims:
        theme = infer_theme(claim)

        if theme not in grouped:
            grouped[theme] = {
                "theme": theme,
                "count": 0,
                "labels": {},
                "risks": {},
                "examples": [],
            }

        summary = grouped[theme]
        label = claim.get("final_label", "")
        risk = claim.get("greenwashing_risk_level", "")
        relevance = claim.get("evidence_relevance", "")
        summary["count"] += 1
        summary["labels"][label] = summary["labels"].get(label, 0) + 1
        summary["risks"][risk] = summary["risks"].get(risk, 0) + 1

        if len(summary["examples"]) < 3 and risk in {"HIGH", "MEDIUM"}:
            summary["examples"].append(
                {
                    "claim_text": claim.get("claim_text", ""),
                    "final_label": label,
                    "risk": risk,
                    "evidence_relevance": relevance,
                    "risk_reasoning": claim.get("risk_reasoning", ""),
                    "evidence_url": claim.get("top_evidence_url", ""),
                }
            )

    return list(grouped.values())


def select_claim_examples(claims: list[dict]) -> dict:
    """Select compact examples for final LLM synthesis."""
    high_risk = [claim for claim in claims if claim.get("greenwashing_risk_level") == "HIGH"][:8]
    unverified = [claim for claim in claims if claim.get("final_label") == "UNVERIFIED"][:8]
    supported = [claim for claim in claims if claim.get("final_label") == "SUPPORTED"][:6]

    return {
        "high_risk_examples": high_risk,
        "unverified_examples": unverified,
        "supported_examples": supported,
    }


def build_llm_analysis_prompt(report: dict) -> str:
    """Create a compact prompt for a deeper final narrative."""
    claims = report["claims"]
    theme_summaries = build_theme_summaries(claims)
    selected_examples = select_claim_examples(claims)

    return f"""
You are writing the final analytical section for a greenwashing-risk assessment.

Use only the structured results below. Do not add outside facts.

Write a deeper analysis, not just a summary. Explain:
- what the overall evidence pattern suggests
- which types of claims are better substantiated
- where greenwashing risk comes from
- how evidence relevance affects confidence in the risk interpretation
- whether the risk is direct contradiction, weak substantiation, selective framing, accounting caveats, offsets/credits, renewable electricity matching, supplier emissions, water, or other issues
- what the main limitations of this automated assessment are

Keep factual support and greenwashing risk separate. A claim can be unverified but still useful for risk analysis.
Do not focus on only the last one or two claims. Synthesize across themes and use examples only to support broader patterns.
Do not change any label or risk level. Do not list a claim as HIGH risk unless the selected examples mark it as HIGH. If evidence is missing, treat that as an evidence limitation, not as a high-risk signal by itself.

Return Markdown only with these sections:
## Analytical Assessment
## Main Risk Patterns
## Evidence Limitations
## Overall Interpretation

Company: {report['company_name']}
Total claims analyzed: {report['total_claims_analyzed']}
Future claims excluded: {report['future_claims_excluded']}
Claims excluded from main analysis: {report['claims_excluded_from_main_analysis']}
Label counts: {json.dumps(report['label_counts'], ensure_ascii=False)}
Risk counts: {json.dumps(report['greenwashing_risk_counts'], ensure_ascii=False)}
Evidence relevance counts: {json.dumps(report['evidence_relevance_counts'], ensure_ascii=False)}
Rule-based conclusion: {report['final_conclusion']}

Theme summaries:
{json.dumps(theme_summaries, indent=2, ensure_ascii=False)}

Selected examples:
{json.dumps(selected_examples, indent=2, ensure_ascii=False)}
""".strip()


def call_ollama(prompt: str) -> str:
    """Call local Ollama for the final analytical narrative."""
    payload = {
        "model": LOCAL_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    with request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    return clean_generated_markdown(result.get("response", ""))


def build_deep_analysis(report: dict) -> str:
    """Generate a deeper final analysis using the local LLM with fallback."""
    if PIPELINE_MODE == "fast":
        return build_fallback_deep_analysis(report)

    try:
        analysis = call_ollama(build_llm_analysis_prompt(report))
    except Exception as error:
        print(f"LLM final analysis failed, using fallback: {error}")
        return build_fallback_deep_analysis(report)

    if not analysis:
        return build_fallback_deep_analysis(report)

    return analysis


def build_summary_markdown(report: dict) -> str:
    """Build a readable markdown summary for the MVP."""
    label_counts = report["label_counts"]
    risk_counts = report["greenwashing_risk_counts"]
    relevance_counts = report["evidence_relevance_counts"]
    metadata = report["run_metadata"]
    artifact_counts = metadata["artifact_counts"]
    cache_metadata = metadata["cache"]

    lines = [
        f"# Final Summary - {report['company_name']}",
        "",
        "## Overview",
        f"- Total claims analyzed: {report['total_claims_analyzed']}",
        f"- Claims excluded from main analysis: {report['claims_excluded_from_main_analysis']}",
        f"- Future claims excluded: {report['future_claims_excluded']}",
        "",
        "## Run Metadata",
        f"- Generated at UTC: {metadata['generated_at_utc']}",
        f"- Pipeline mode: {metadata['pipeline_mode']}",
        f"- Documents processed: {metadata['documents']['document_count']}",
        f"- Document IDs: {', '.join(metadata['documents']['document_ids']) if metadata['documents']['document_ids'] else 'unknown'}",
        f"- Document names: {', '.join(metadata['documents']['document_names']) if metadata['documents']['document_names'] else 'unknown'}",
        f"- Agent 2 model: {metadata['models']['agent_2_claim_extractor']}",
        f"- Agent 4 model: {metadata['models']['agent_4_query_generator']}",
        f"- Agent 7 embedding model: {metadata['models']['agent_7_embedding_model']}",
        f"- Agent 8 model: {metadata['models']['agent_8_evidence_analyzer']}",
        f"- Agent 9 analysis mode: {metadata['models']['agent_9_final_analysis']}",
        f"- Queries generated: {artifact_counts['queries_generated']}",
        f"- Evidence candidates: {artifact_counts['evidence_candidates']}",
        f"- Ranked evidence rows: {artifact_counts['ranked_evidence_rows']}",
        f"- Agent 2 cached pages: {cache_metadata['agent_2_cached_pages']}",
        f"- Agent 8 cached assessments: {cache_metadata['agent_8_cached_assessments']}",
        "",
        "## Label Counts",
        f"- SUPPORTED: {label_counts['SUPPORTED']}",
        f"- PARTIALLY_SUPPORTED: {label_counts['PARTIALLY_SUPPORTED']}",
        f"- UNVERIFIED: {label_counts['UNVERIFIED']}",
        f"- PARTIALLY_CONTRADICTED: {label_counts['PARTIALLY_CONTRADICTED']}",
        f"- CONTRADICTED: {label_counts['CONTRADICTED']}",
        "",
        "## Greenwashing Risk Counts",
        f"- LOW: {risk_counts['LOW']}",
        f"- MEDIUM: {risk_counts['MEDIUM']}",
        f"- HIGH: {risk_counts['HIGH']}",
        f"- UNCLEAR: {risk_counts['UNCLEAR']}",
        "",
        "## Evidence Relevance Counts",
        f"- DIRECT: {relevance_counts['DIRECT']}",
        f"- INDIRECT: {relevance_counts['INDIRECT']}",
        f"- BACKGROUND: {relevance_counts['BACKGROUND']}",
        f"- UNRELATED: {relevance_counts['UNRELATED']}",
        "",
        "## Final Conclusion",
        report["final_conclusion"],
        "",
        report["deep_analysis"],
        "",
        "## Claim Summary",
    ]

    for row in report["claims"]:
        lines.append(f"- [{row['final_label']} | Risk: {row['greenwashing_risk_level']} | Evidence: {row['evidence_relevance']}] {row['claim_text']}")
        lines.append(f"  Evidence: {row['top_evidence_url']}")
        lines.append(f"  Risk reasoning: {row['risk_reasoning']}")

    if report["excluded_claims"]:
        lines.extend(["", "## Claims Excluded From Main Analysis"])

        for row in report["excluded_claims"]:
            lines.append(f"- [{row.get('evaluation_priority', '')} | {row.get('exclusion_reason', '')}] {row.get('claim_text', '')}")

    return "\n".join(lines)


def save_summary_markdown(text: str, output_path: Path) -> None:
    """Save the markdown summary."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8")


def main() -> None:
    claims = load_csv_rows(CLAIMS_CSV)
    normalized_claims = load_csv_rows(NORMALIZED_CLAIMS_CSV)
    prioritized_claims = load_csv_rows(PRIORITIZED_CLAIMS_CSV)
    assessments = load_csv_rows(ASSESSMENTS_CSV)
    excluded_claims = load_csv_rows(EXCLUDED_CLAIMS_CSV)
    future_claims = load_csv_rows(FUTURE_CLAIMS_CSV)

    if not assessments:
        print(f"Assessments CSV not found or empty: {ASSESSMENTS_CSV}")
        return

    label_counts = count_labels(assessments)
    risk_counts = count_risk_levels(assessments)
    relevance_counts = count_evidence_relevance(assessments)
    total_claims = len(assessments)
    future_claims_count = len(future_claims)
    final_conclusion = build_conclusion(label_counts, risk_counts, total_claims, future_claims_count)
    report_rows = build_report_rows(assessments)
    run_metadata = build_run_metadata(
        claims,
        normalized_claims,
        prioritized_claims,
        excluded_claims,
        future_claims,
        assessments,
    )

    final_report = {
        "company_name": COMPANY_NAME,
        "run_metadata": run_metadata,
        "total_claims_analyzed": total_claims,
        "claims_excluded_from_main_analysis": len(excluded_claims),
        "future_claims_excluded": future_claims_count,
        "label_counts": label_counts,
        "greenwashing_risk_counts": risk_counts,
        "evidence_relevance_counts": relevance_counts,
        "final_conclusion": final_conclusion,
        "claims": report_rows,
        "excluded_claims": excluded_claims,
    }
    final_report["deep_analysis"] = build_deep_analysis(final_report)

    save_report_csv(report_rows, FINAL_REPORT_CSV)
    save_report_json(final_report, FINAL_REPORT_JSON)
    save_summary_markdown(build_summary_markdown(final_report), FINAL_SUMMARY_MD)

    print(f"Final report saved to: {FINAL_REPORT_CSV}")
    print(f"Final JSON saved to: {FINAL_REPORT_JSON}")
    print(f"Final summary saved to: {FINAL_SUMMARY_MD}")


if __name__ == "__main__":
    main()
