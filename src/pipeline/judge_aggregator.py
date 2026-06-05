from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

from src.utils.env import load_local_env


load_local_env()

LOCAL_MODEL = os.environ.get("AGENT_9_MODEL", "qwen2.5:14b")
AGENT_9_PROVIDER = os.environ.get("AGENT_9_PROVIDER", "ollama").strip().lower()
OLLAMA_URL = "http://localhost:11434/api/generate"
PIPELINE_MODE = os.environ.get("PIPELINE_MODE", "normal").strip().lower()
AGENT_2_MODEL = "qwen2.5:14b"
AGENT_4_MODEL = "mistral-nemo:latest"
AGENT_7_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
AGENT_8_MODEL = "qwen2.5:14b"
AGENT_8_TOP_K_EVIDENCE = 3
GEMINI_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

csv.field_size_limit(10**7)


THEME_KEYWORDS = {
    "GHG emissions": ["ghg", "scope", "emissions", "carbon inventory", "warming potentials", "kyoto"],
    "Renewable electricity and Scope 2 accounting": ["renewable", "electricity", "recs", "eac", "ppa", "market-based", "location-based"],
    "Carbon neutrality and removals": ["carbon neutrality", "carbon neutral", "carbon negative", "carbon removal", "credits"],
    "Water and data centers": ["water", "withdrawal", "consumption", "discharge", "data center", "data centres"],
    "Land, ecosystems, and circularity": ["land", "ecosystem", "nature", "packaging", "waste", "circularity"],
    "Supply chain and methodology": ["supplier", "supply chain", "primary data", "estimates", "methodology", "spend"],
}

CORE_MATERIALITY_KEYWORDS = {
    "GHG emissions": ["ghg", "scope 1", "scope 2", "scope 3", "emissions", "carbon inventory", "warming potential"],
    "Renewable electricity and Scope 2 accounting": ["renewable", "electricity", "recs", "eac", "ppa", "market-based", "location-based"],
    "Carbon neutrality and removals": ["carbon neutrality", "carbon neutral", "carbon negative", "carbon removal", "removals", "credits"],
    "Water and data centers": ["water", "withdrawal", "consumption", "discharge", "data center", "data centres"],
    "Land, ecosystems, and circularity": ["land", "ecosystem", "nature", "packaging", "waste", "circularity"],
    "Supply chain and methodology": ["supplier", "supply chain", "primary data", "estimates", "methodology", "spend"],
}

LABEL_SCORE = {
    "SUPPORTED": 2.2,
    "PARTIALLY_SUPPORTED": 1.1,
    "UNVERIFIED": 0.0,
    "PARTIALLY_CONTRADICTED": -1.7,
    "CONTRADICTED": -3.2,
}

RISK_SCORE = {
    "LOW": 0.0,
    "MEDIUM": 0.8,
    "HIGH": 1.8,
    "UNCLEAR": 0.2,
}

RELEVANCE_SCORE = {
    "DIRECT": 0.9,
    "INDIRECT": 0.25,
    "BACKGROUND": -0.4,
    "UNRELATED": -1.0,
}


def load_csv_rows(csv_path: Path) -> list[dict]:
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
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def count_rows(csv_path: Path) -> int:
    return len(load_csv_rows(csv_path))


def unique_values(rows: list[dict], field_name: str) -> list[str]:
    values = set()
    for row in rows:
        value = row.get(field_name, "")
        if value:
            values.add(str(value))
    return sorted(values)


def filter_claims_by_family(rows: list[dict], claim_family: str) -> list[dict]:
    return [row for row in rows if str(row.get("claim_family", "")).strip().lower() == claim_family]


NON_ENVIRONMENTAL_OVERRIDE_MARKERS = {
    "seeing ai",
    "haleon",
    "accessibility",
    "blind",
    "visually impaired",
    "partially sighted",
    "responsible ai",
    "ai for good",
}


def normalize_report_claim_family(row: dict) -> dict:
    normalized = dict(row)
    text_parts = [
        str(row.get("claim_text", "")),
        str(row.get("justification", "")),
        str(row.get("risk_reasoning", "")),
        str(row.get("document_name", "")),
    ]
    text_blob = " ".join(text_parts).lower()
    claim_family = str(row.get("claim_family", "other")).strip().lower() or "other"

    if any(marker in text_blob for marker in NON_ENVIRONMENTAL_OVERRIDE_MARKERS):
        claim_family = "governance_ai"

    normalized["claim_family"] = claim_family
    return normalized


def build_run_metadata(company_name: str, claims: list[dict], normalized_claims: list[dict], prioritized_claims: list[dict], excluded_claims: list[dict], future_claims: list[dict], assessments: list[dict], project_root: Path) -> dict:
    agent_2_cache = load_json_file(project_root / "agent_2" / "claim_extraction_cache.json")
    agent_8_cache = load_json_file(project_root / "agent_8" / "assessment_cache.json")
    document_ids = unique_values(claims, "document_id") or unique_values(normalized_claims, "document_id")
    document_names = unique_values(claims, "document_name") or unique_values(normalized_claims, "document_name")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_mode": PIPELINE_MODE,
        "company_name": company_name,
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
            "agent_9_final_analysis": LOCAL_MODEL if AGENT_9_PROVIDER != "gemini" else os.environ.get("AGENT_9_GEMINI_MODEL", "gemini-2.0-flash"),
            "agent_9_provider": AGENT_9_PROVIDER,
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
            "queries_generated": count_rows(project_root / "agent_4" / "queries.csv"),
            "search_results": count_rows(project_root / "agent_5" / "search_results.csv"),
            "evidence_candidates": count_rows(project_root / "agent_6" / "evidence_candidates.csv"),
            "ranked_evidence_rows": count_rows(project_root / "agent_7" / "ranked_evidence.csv"),
            "claim_assessments": len(assessments),
        },
        "cache": {
            "agent_2_claim_extraction_cache_exists": (project_root / "agent_2" / "claim_extraction_cache.json").exists(),
            "agent_2_cached_pages": len(agent_2_cache) if isinstance(agent_2_cache, dict) else 0,
            "agent_8_assessment_cache_exists": (project_root / "agent_8" / "assessment_cache.json").exists(),
            "agent_8_cached_assessments": len(agent_8_cache) if isinstance(agent_8_cache, dict) else 0,
        },
        "artifacts": {},
    }


def count_labels(assessments: list[dict]) -> dict:
    counts = {"SUPPORTED": 0, "PARTIALLY_SUPPORTED": 0, "UNVERIFIED": 0, "PARTIALLY_CONTRADICTED": 0, "CONTRADICTED": 0}
    for row in assessments:
        label = row.get("final_label", "").strip().upper()
        if label in counts:
            counts[label] += 1
    return counts


def count_risk_levels(assessments: list[dict]) -> dict:
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "UNCLEAR": 0}
    for row in assessments:
        risk_level = row.get("greenwashing_risk_level", "").strip().upper()
        if risk_level in counts:
            counts[risk_level] += 1
    return counts


def count_credibility_signal_levels(assessments: list[dict]) -> dict:
    return count_risk_levels(assessments)


def count_evidence_relevance(assessments: list[dict]) -> dict:
    counts = {"DIRECT": 0, "INDIRECT": 0, "BACKGROUND": 0, "UNRELATED": 0}
    for row in assessments:
        relevance = row.get("evidence_relevance", "").strip().upper()
        if relevance in counts:
            counts[relevance] += 1
    return counts


def clean_generated_text(text: str) -> str:
    text = str(text).strip()
    if not text:
        return ""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_generated_markdown(text: str) -> str:
    text = str(text).strip()
    if not text:
        return ""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def claim_text_blob(claim: dict) -> str:
    parts = [
        str(claim.get("claim_text", "")),
        str(claim.get("risk_reasoning", "")),
        str(claim.get("justification", "")),
        str(claim.get("claim_family", "")),
    ]
    return " ".join(parts).lower()


def materiality_score(claim: dict) -> float:
    text = claim_text_blob(claim)
    score = 0.0
    for theme_keywords in CORE_MATERIALITY_KEYWORDS.values():
        if any(keyword in text for keyword in theme_keywords):
            score += 0.45
    if str(claim.get("claim_family", "")).strip().lower() == "environmental":
        score += 0.35
    return min(score, 1.5)


def score_claim_for_judgment(claim: dict) -> dict:
    label = str(claim.get("final_label", "")).strip().upper()
    risk = str(claim.get("greenwashing_risk_level", "")).strip().upper()
    relevance = str(claim.get("evidence_relevance", "")).strip().upper()

    label_score = LABEL_SCORE.get(label, 0.0)
    risk_score = RISK_SCORE.get(risk, 0.0)
    relevance_score = RELEVANCE_SCORE.get(relevance, 0.0)
    materiality = materiality_score(claim)
    total = label_score + relevance_score + materiality - risk_score

    if label in {"SUPPORTED", "PARTIALLY_SUPPORTED"}:
        stance = "support"
    elif label in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"}:
        stance = "concern"
    elif risk == "HIGH":
        stance = "concern"
    else:
        stance = "uncertain"

    return {
        "normalized_claim_id": claim.get("normalized_claim_id", ""),
        "claim_text": claim.get("claim_text", ""),
        "claim_family": claim.get("claim_family", "other"),
        "document_name": claim.get("document_name", ""),
        "document_id": claim.get("document_id", ""),
        "page_numbers": claim.get("page_numbers", ""),
        "source_locations": claim.get("source_locations", ""),
        "source_excerpts": claim.get("source_excerpts", ""),
        "final_label": label,
        "greenwashing_risk_level": risk,
        "evidence_relevance": relevance,
        "top_evidence_url": claim.get("top_evidence_url", ""),
        "top_evidence_title": claim.get("top_evidence_title", ""),
        "justification": clean_generated_text(claim.get("justification", "")),
        "risk_reasoning": clean_generated_text(claim.get("risk_reasoning", "")),
        "materiality_score": round(materiality, 3),
        "judgment_score": round(total, 3),
        "stance": stance,
    }


def build_conclusion(label_counts: dict, risk_counts: dict, total_claims: int, future_claims_count: int) -> str:
    supported = label_counts["SUPPORTED"]
    partial = label_counts["PARTIALLY_SUPPORTED"]
    unverified = label_counts["UNVERIFIED"]
    partially_contradicted = label_counts["PARTIALLY_CONTRADICTED"]
    contradicted = label_counts["CONTRADICTED"]
    high_risk = risk_counts.get("HIGH", 0)

    if total_claims == 0:
        return "No claims were analyzed, so no overall conclusion can be drawn."
    if contradicted > 0:
        return f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, but at least {contradicted} claim(s) are contradicted by external evidence, which may indicate potential greenwashing risk or inconsistency in the company's sustainability communication."
    if partially_contradicted > 0:
        return f"The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, but {partially_contradicted} claim(s) are partially contradicted by external evidence, which indicates potential selective framing or incomplete sustainability communication."
    if high_risk > 0:
        return f"The analyzed discourse shows material greenwashing risk. No claim is directly contradicted by the provided evidence, but {high_risk} claim(s) have high greenwashing-risk signals, mainly due to external evidence about emissions growth, data-center energy demand, or accounting caveats. This suggests the narrative may be factually incomplete or selectively framed."
    if supported + partial == total_claims:
        return "The analyzed discourse appears broadly credible. Most evaluated claims are supported or partially supported by external evidence, although some claims may still require stronger third-party validation."
    if unverified >= total_claims / 2:
        return "The analyzed discourse is weakly verified by external evidence. A large share of prioritized claims remain unverified, which suggests limited external confirmation rather than direct falsification."

    conclusion = "The analyzed discourse shows mixed credibility. Some claims are supported or partially supported, while others remain unverified. This suggests that the company's sustainability discourse is only partially substantiated by external evidence."
    if future_claims_count > 0:
        conclusion += f" In addition, {future_claims_count} future-looking claim(s) were identified and excluded from the main evaluation."
    return conclusion


def build_report_rows(assessments: list[dict]) -> list[dict]:
    rows = []
    for row in assessments:
        rows.append(score_claim_for_judgment(row))
    return rows


def build_normalized_claim_lookup(normalized_claims: list[dict]) -> dict[str, dict]:
    lookup = {}
    for row in normalized_claims:
        normalized_claim_id = str(row.get("normalized_claim_id", "")).strip()
        if normalized_claim_id:
            lookup[normalized_claim_id] = row
    return lookup


def enrich_report_rows(report_rows: list[dict], normalized_claim_lookup: dict[str, dict]) -> list[dict]:
    enriched_rows = []
    for row in report_rows:
        normalized_claim_id = str(row.get("normalized_claim_id", "")).strip()
        source_row = normalized_claim_lookup.get(normalized_claim_id, {})
        enriched_rows.append(
            {
                **row,
                "document_name": row.get("document_name") or source_row.get("document_name", ""),
                "document_id": row.get("document_id") or source_row.get("document_id", ""),
                "page_numbers": row.get("page_numbers") or source_row.get("page_numbers", ""),
                "source_locations": row.get("source_locations") or source_row.get("source_locations", ""),
                "source_excerpts": row.get("source_excerpts") or source_row.get("source_excerpts", ""),
            }
        )
    return enriched_rows


def save_report_csv(rows: list[dict], output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "claim_text",
                "claim_family",
                "document_id",
                "document_name",
                "page_numbers",
                "source_locations",
                "source_excerpts",
                "final_label",
                "greenwashing_risk_level",
                "evidence_relevance",
                "justification",
                "risk_reasoning",
                "top_evidence_url",
                "top_evidence_title",
                "materiality_score",
                "judgment_score",
                "stance",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def save_report_json(report: dict, output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def infer_theme(claim: dict) -> str:
    text = f"{claim.get('claim_text', '')} {claim.get('risk_reasoning', '')}".lower()
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return theme
    return "Other environmental claims"


def build_theme_summaries(claims: list[dict]) -> list[dict]:
    grouped = {}
    for claim in claims:
        theme = infer_theme(claim)
        grouped.setdefault(theme, {"theme": theme, "count": 0, "labels": {}, "risks": {}, "examples": []})
        summary = grouped[theme]
        label = claim.get("final_label", "")
        risk = claim.get("greenwashing_risk_level", "")
        relevance = claim.get("evidence_relevance", "")
        summary["count"] += 1
        summary["labels"][label] = summary["labels"].get(label, 0) + 1
        summary["risks"][risk] = summary["risks"].get(risk, 0) + 1
        if len(summary["examples"]) < 3 and risk in {"HIGH", "MEDIUM"}:
            summary["examples"].append({"claim_text": claim.get("claim_text", ""), "final_label": label, "risk": risk, "evidence_relevance": relevance, "risk_reasoning": claim.get("risk_reasoning", ""), "evidence_url": claim.get("top_evidence_url", "")})
    return list(grouped.values())


def summarize_source(row: dict) -> str:
    document_name = str(row.get("document_name", "")).strip()
    page_numbers = str(row.get("page_numbers", "")).strip()
    source_locations = str(row.get("source_locations", "")).strip()
    parts = []
    if document_name:
        parts.append(document_name)
    if page_numbers:
        parts.append(f"p. {page_numbers}")
    if source_locations:
        parts.append(source_locations)
    if row.get("top_evidence_url"):
        parts.append(row["top_evidence_url"])
    return " | ".join(parts) if parts else "source unavailable"


def build_report_context_paragraph(report: dict) -> str:
    company = report["company_name"]
    doc_count = report["run_metadata"]["documents"]["document_count"]
    document_names = report.get("run_metadata", {}).get("documents", {}).get("document_names", [])
    if document_names:
        disclosure_scope = f"The selected disclosure set spans {', '.join(document_names[:3])}"
        if len(document_names) > 3:
            disclosure_scope += f", and {len(document_names) - 3} additional document(s)"
        disclosure_scope += "."
    else:
        disclosure_scope = "The selected disclosure set spans the processed company reports and statements."
    return (
        f"{company}'s CSR narrative in this run is derived only from the selected company disclosure set. {disclosure_scope} "
        f"That matters because the report is evaluating how the company's own selected claims hold up against outside evidence, not attempting a sector-wide benchmark or a complete ESG audit. "
        f"In this run, {doc_count} document(s) were processed, so the final judgment should be read as a structured reading of the selected disclosure set rather than a complete external audit of everything the company has ever said."
    )


def build_stronger_thesis_paragraph(report: dict) -> str:
    verdict_label = report.get("verdict_label", "Mixed Evidence")
    company = report["company_name"]
    if verdict_label == "Broadly Supported":
        return (
            f"The clearest reading of this evidence set is that {company}'s CSR disclosure is substantively credible. "
            "The strongest claims are directly corroborated, and the remaining unresolved items do not overturn the overall picture."
        )
    if verdict_label == "Mostly Credible":
        return (
            f"The clearest reading of this evidence set is that {company}'s CSR disclosure is mostly credible. "
            "The report shows real support for the company’s main claims, with a smaller set of unresolved items that look more like gaps in external coverage than signs of a misleading story."
        )
    if verdict_label == "Questionable":
        return (
            f"The clearest reading of this evidence set is that {company}'s CSR disclosure is questionable. "
            "The evidence introduces enough tension around material claims that the company’s preferred narrative should not be taken at face value."
        )
    if verdict_label == "High Greenwashing Risk":
        return (
            f"The clearest reading of this evidence set is that {company}'s CSR disclosure carries material credibility concerns, including elevated greenwashing-related risk in the environmental subset. "
            "The evidence does not merely leave gaps; it points to material contradictions that weaken confidence in the company’s CSR framing."
        )
    return (
        f"The clearest reading of this evidence set is that {company}'s CSR disclosure is mixed but leaning supportive. "
        "The report has enough direct support to be taken seriously, and the unresolved pieces should be treated as coverage gaps unless they materially change the balance of evidence."
    )


def build_greenwashing_definition_paragraph() -> str:
    return (
        "In this project, CSR claim assessment is broader than environmental greenwashing alone. Environmental claims are reviewed for greenwashing-related risk, while non-environmental claims such as responsible AI, accessibility, human rights, diversity, and governance are assessed as broader CSR credibility issues. "
        "That is why the report distinguishes between supported claims, partially supported claims, unverified claims, and claims that raise contradiction or concern signals."
    )


def build_source_of_truth_paragraph(report: dict) -> str:
    provider = report.get("run_metadata", {}).get("models", {}).get("agent_9_provider", "ollama")
    model = report.get("run_metadata", {}).get("models", {}).get("agent_9_final_analysis", "unknown")
    if provider == "gemini":
        return (
            f"This final narrative was generated with the Gemini provider using model {model}. That matters because the last stage is where the system is expected to do the most synthesis, not just classification."
        )
    return (
        f"This final narrative was generated with the local Ollama provider using model {model}. That matters because the last stage is where the system is expected to do the most synthesis, not just classification."
    )


def build_claim_paragraphs(report: dict) -> list[str]:
    return build_theme_narratives(report)


def build_theme_bundles(claims: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for claim in claims:
        theme = infer_theme(claim)
        bucket = grouped.setdefault(
            theme,
            {
                "theme": theme,
                "count": 0,
                "supported": 0,
                "partial": 0,
                "unverified": 0,
                "concern": 0,
                "claims": [],
            },
        )
        bucket["count"] += 1
        label = str(claim.get("final_label", "")).upper()
        if label == "SUPPORTED":
            bucket["supported"] += 1
        elif label == "PARTIALLY_SUPPORTED":
            bucket["partial"] += 1
        elif label == "UNVERIFIED":
            bucket["unverified"] += 1
        elif label in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"} or claim.get("greenwashing_risk_level") == "HIGH":
            bucket["concern"] += 1

        bucket["claims"].append(
            {
                "id": claim.get("normalized_claim_id", ""),
                "claim_text": claim.get("claim_text", ""),
                "final_label": claim.get("final_label", ""),
                "risk": claim.get("greenwashing_risk_level", ""),
                "relevance": claim.get("evidence_relevance", ""),
                "source": summarize_source(claim),
                "note": clean_generated_text(claim.get("risk_reasoning", "")) or clean_generated_text(claim.get("justification", "")),
            }
        )

    ordered_themes = sorted(
        grouped.values(),
        key=lambda item: (item["concern"], item["supported"] + item["partial"], item["count"]),
        reverse=True,
    )

    for theme in ordered_themes:
        theme["claims"] = sorted(
            theme["claims"],
            key=lambda row: (row["final_label"] == "SUPPORTED", row["final_label"] == "PARTIALLY_SUPPORTED", row["relevance"] == "DIRECT"),
            reverse=True,
        )[:4]

    return ordered_themes[:5]


def build_narrative_packet(report: dict) -> dict:
    claims = report["claims"]
    return {
        "company_context": build_report_context_paragraph(report),
        "greenwashing_definition": build_greenwashing_definition_paragraph(),
        "metrics": {
            "total_claims_analyzed": report.get("total_claims_analyzed", 0),
            "label_counts": report.get("csr_label_counts", report.get("label_counts", {})),
            "risk_counts": report.get("csr_credibility_signal_counts", report.get("greenwashing_risk_counts", {})),
            "relevance_counts": report.get("csr_evidence_relevance_counts", report.get("evidence_relevance_counts", {})),
            "verdict_label": report.get("verdict_label", "Mixed Evidence"),
            "verdict_reason": report.get("verdict_reason", ""),
        },
        "theme_bundles": build_theme_bundles(claims),
    }


def build_verdict_paragraph(report: dict) -> str:
    verdict_label = report.get("verdict_label", "Mixed Evidence")
    verdict_reason = report.get("verdict_reason", "")
    if verdict_label == "Broadly Supported":
        opening = "Overall, the report reads as broadly supported and materially credible."
    elif verdict_label == "Mostly Credible":
        opening = "Overall, the report reads as mostly credible and directionally supportive."
    elif verdict_label == "Questionable":
        opening = "Overall, the report is genuinely questionable."
    elif verdict_label == "High Greenwashing Risk":
        opening = "Overall, the report suggests high greenwashing risk."
    else:
        opening = "Overall, the report shows mixed evidence, but still points in a clear direction."

    return (
        f"{opening} {verdict_reason} "
        "In practical terms, that means the report is making a judgment call from the balance of the evidence, not hiding behind a neutral summary. "
        "The supported claims carry the most weight, the unresolved claims are treated as gaps, and the concern signals matter only when they affect the company’s central sustainability story."
    )


def build_report_summary_bullets(report: dict) -> list[str]:
    claims = report["claims"]
    supported = [claim for claim in claims if claim.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}]
    unresolved = [claim for claim in claims if claim.get("final_label") == "UNVERIFIED"]
    concerns = [claim for claim in claims if claim.get("final_label") in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"} or claim.get("greenwashing_risk_level") == "HIGH"]

    bullets = []
    if supported:
        bullets.append(f"Supported signals: {len(supported)} claim(s), led by {supported[0].get('normalized_claim_id', 'n/a')}.")
    if unresolved:
        bullets.append(f"Unresolved coverage gaps: {len(unresolved)} claim(s), mainly where external coverage was too weak or too indirect.")
    if concerns:
        bullets.append(f"Concern signals: {len(concerns)} claim(s), where the external material adds tension or caution rather than full confirmation.")
    return bullets


def human_label(label: str, risk: str) -> str:
    label = str(label).strip().upper()
    risk = str(risk).strip().upper()
    if label == "SUPPORTED":
        return "supported"
    if label == "PARTIALLY_SUPPORTED":
        return "mostly supported"
    if label == "UNVERIFIED" and risk == "UNCLEAR":
        return "not fully verified"
    if label == "UNVERIFIED":
        return "not fully verified"
    if label in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"} or risk == "HIGH":
        return "raises concern"
    return "mixed"


def build_public_claim_briefs(report: dict, max_claims: int = 5) -> list[dict]:
    claims = list(report.get("claims", []))
    ordered = sorted(claims, key=lambda claim: claim.get("judgment_score", 0.0), reverse=True)
    selected: list[dict] = []

    def add_claim(claim: dict) -> None:
        if claim not in selected and len(selected) < max_claims:
            selected.append(claim)

    for claim in ordered:
        if claim.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"} and len([c for c in selected if c.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}]) < 2:
            add_claim(claim)

    for claim in ordered:
        if claim.get("final_label") == "UNVERIFIED" and len([c for c in selected if c.get("final_label") == "UNVERIFIED" or c.get("evidence_relevance") in {"BACKGROUND", "UNRELATED"}]) < 2:
            add_claim(claim)

    for claim in reversed(ordered):
        if claim.get("final_label") in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"} or claim.get("greenwashing_risk_level") == "HIGH":
            add_claim(claim)

    for claim in ordered:
        add_claim(claim)

    briefs = []
    for index, claim in enumerate(selected[:max_claims], start=1):
        briefs.append(
            {
                "number": index,
                "claim": claim.get("claim_text", ""),
                "status": human_label(claim.get("final_label", ""), claim.get("greenwashing_risk_level", "")),
                "evidence_relevance": claim.get("evidence_relevance", ""),
                "source": summarize_source(claim),
                "source_title": claim.get("top_evidence_title", ""),
                "note": clean_generated_text(claim.get("risk_reasoning", "")) or clean_generated_text(claim.get("justification", "")),
            }
        )
    return briefs


def build_public_report_prompt(report: dict) -> str:
    claim_briefs = build_public_claim_briefs(report)
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    return f"""
You are writing a plain-language report for a non-expert reader who wants a CSR claim assessment with a separate environmental greenwashing-risk sub-assessment.

Write a clear, human report in simple language. Do not mention internal IDs, theme labels, model names, or technical audit language.

Required sections:
## Title
## Short Context
## What CSR Claim Assessment Means
## What the Company Claims Across CSR Topics
## Environmental Greenwashing-Risk Sub-Assessment
## What External Sources Say
## Overall Assessment
## Why This Matters
## Limitations
## Conclusion

Rules:
- Use short paragraphs.
- Explain the company, the claims, and the outside evidence in a way a non-expert can follow.
- Be direct about whether the broader CSR evidence is supportive, mixed, or concerning.
- Explain that greenwashing-risk language applies only to the environmental subset.
- Use the verdict target as guidance, but write naturally.
- Mention only a few representative claims.
- Do not expose internal IDs or theme names.
- Do not mention excluded claims.
- Keep the conclusion clear and bold.

Company: {report['company_name']}
Verdict target: {verdict_label}
Verdict rationale: {verdict_reason}
Public claim briefs:
{json.dumps(claim_briefs, indent=2, ensure_ascii=False)}

Environmental subassessment counts:
{json.dumps({
    'total_environmental_claims_assessed': report.get('total_environmental_claims_assessed', 0),
    'environmental_label_counts': report.get('environmental_label_counts', {}),
    'environmental_greenwashing_risk_counts': report.get('environmental_greenwashing_risk_counts', {}),
    'environmental_evidence_relevance_counts': report.get('environmental_evidence_relevance_counts', {}),
}, indent=2, ensure_ascii=False)}

Context:
{build_report_context_paragraph(report)}

CSR assessment framing:
{build_greenwashing_definition_paragraph()}

Important:
- If a claim is supported, say it plainly.
- If a claim is unverified, say the outside evidence did not fully confirm it.
- If a claim raises concern, say that the outside evidence weakens confidence in the company’s framing.
- Do not describe responsible-AI, accessibility, diversity, governance, or human-rights claims as greenwashing.
- Connect the claims to the final verdict in a way that feels like a short report, not a checklist.

Write the full report as Markdown only.
""".strip()


def select_claim_examples(claims: list[dict]) -> dict:
    ordered = sorted(claims, key=lambda claim: claim.get("judgment_score", 0.0), reverse=True)
    concern_ordered = sorted(claims, key=lambda claim: claim.get("judgment_score", 0.0))
    return {
        "high_risk_examples": [claim for claim in concern_ordered if claim.get("greenwashing_risk_level") == "HIGH"][:6],
        "unverified_examples": [claim for claim in concern_ordered if claim.get("final_label") == "UNVERIFIED"][:6],
        "supported_examples": [claim for claim in ordered if claim.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}][:6],
        "top_positive_examples": [claim for claim in ordered if claim.get("judgment_score", 0.0) > 0][:4],
        "top_negative_examples": [claim for claim in concern_ordered if claim.get("judgment_score", 0.0) < 0][:4],
    }


def format_claim_reference(claim: dict) -> str:
    claim_id = claim.get("normalized_claim_id", "unknown_claim")
    claim_text = truncate_markdown_text(claim.get("claim_text", ""), 120) or "claim text unavailable"
    return f"**{claim_id}** ({claim_text})"


def format_claim_references(claims: list[dict], limit: int = 3) -> str:
    selected = [format_claim_reference(claim) for claim in claims[:limit]]
    if not selected:
        return "no specific claim examples"
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return f"{selected[0]} and {selected[1]}"
    return f"{', '.join(selected[:-1])}, and {selected[-1]}"


def determine_confidence_label(report: dict) -> str:
    total_claims = max(int(report.get("total_claims_analyzed", 0)), 1)
    relevance_counts = report.get("evidence_relevance_counts", {})
    direct_share = relevance_counts.get("DIRECT", 0) / total_claims
    weak_share = (relevance_counts.get("BACKGROUND", 0) + relevance_counts.get("UNRELATED", 0)) / total_claims
    if direct_share >= 0.5:
        return "moderate-to-high"
    if direct_share >= 0.25 and weak_share <= 0.5:
        return "moderate"
    return "low-to-moderate"


def build_dynamic_verdict_reason(report: dict) -> str:
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    counts = report.get("label_counts", {})
    supported = counts.get("SUPPORTED", 0)
    partial = counts.get("PARTIALLY_SUPPORTED", 0)
    unverified = counts.get("UNVERIFIED", 0)
    partial_contradicted = counts.get("PARTIALLY_CONTRADICTED", 0)
    contradicted = counts.get("CONTRADICTED", 0)
    total = max(int(report.get("total_claims_analyzed", 0)), 1)
    relevance_counts = report.get("evidence_relevance_counts", {})
    direct = relevance_counts.get("DIRECT", 0)
    weak = relevance_counts.get("BACKGROUND", 0) + relevance_counts.get("UNRELATED", 0)
    return (
        f"The verdict is {verdict_label} because {supported + partial} of {total} prioritized claim(s) are supported or partially supported, "
        f"{unverified} remain unverified, and {partial_contradicted + contradicted} show contradiction-level concern. "
        f"The evidence base includes {direct} direct-evidence claim(s), while {weak} claim(s) depend on weak or unrelated external support. "
        f"{verdict_reason}"
    )


def build_dynamic_final_conclusion(report: dict) -> str:
    company = report.get("company_name", "The company")
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    counts = report.get("label_counts", {})
    supported = counts.get("SUPPORTED", 0)
    partial = counts.get("PARTIALLY_SUPPORTED", 0)
    unverified = counts.get("UNVERIFIED", 0)
    partial_contradicted = counts.get("PARTIALLY_CONTRADICTED", 0)
    contradicted = counts.get("CONTRADICTED", 0)
    return (
        f"The system cannot make a company-wide audit judgment, but it can assess the selected claims for {company}. "
        f"Across the prioritized set, {supported} claim(s) are supported, {partial} are partially supported, {unverified} remain unverified, "
        f"and {partial_contradicted + contradicted} raise contradiction-level concern. "
        f"The overall verdict is {verdict_label}. {verdict_reason}"
    )


def build_dynamic_verdict_rationale(report: dict) -> str:
    company = report.get("company_name", "The company")
    counts = report.get("label_counts", {})
    relevance_counts = report.get("evidence_relevance_counts", {})
    examples = select_claim_examples(report.get("claims", []))
    top_support = examples.get("top_positive_examples", [])
    top_concern = examples.get("top_negative_examples", []) or examples.get("high_risk_examples", [])
    confidence = determine_confidence_label(report)
    verdict_label, verdict_reason = infer_balanced_verdict(report)

    support_text = format_claim_references(top_support, limit=3)
    concern_text = format_claim_references(top_concern, limit=2)

    return "\n\n".join(
        [
            (
                "### Evidence Pattern\n"
                f"Observed evidence shows a mixed claim-level pattern across {report.get('total_claims_analyzed', 0)} prioritized CSR claim(s). "
                f"{counts.get('SUPPORTED', 0)} claim(s) are supported, {counts.get('PARTIALLY_SUPPORTED', 0)} are partially supported, "
                f"{counts.get('UNVERIFIED', 0)} remain unverified, {counts.get('PARTIALLY_CONTRADICTED', 0)} are partially contradicted, "
                f"and {counts.get('CONTRADICTED', 0)} are contradicted."
            ),
            (
                "### Interpretive Weight\n"
                f"The claims do not carry equal interpretive weight. The strongest supportive examples in this run are {support_text}. "
                f"The strongest concern-side examples are {concern_text}. This means the final reading should emphasize claim materiality and evidence strength rather than raw counts alone."
            ),
            (
                "### Claim-Type Pattern\n"
                f"Support tends to be strongest where external evidence can directly confirm a published policy, report, metric, or formal process. "
                f"Unverified claims are better read as coverage gaps unless stronger contradiction appears, especially where the available sources are indirect, background-only, or unrelated to the exact statement."
            ),
            (
                "### Scoped Conclusion\n"
                f"System inference should therefore be scoped. The evidence does not justify a blanket statement about {company}'s overall CSR performance, but it does support the verdict {verdict_label} for the selected claim set. "
                f"Confidence is {confidence} because the report combines {relevance_counts.get('DIRECT', 0)} direct-evidence claim(s), {relevance_counts.get('INDIRECT', 0)} indirect-evidence claim(s), "
                f"and {relevance_counts.get('BACKGROUND', 0) + relevance_counts.get('UNRELATED', 0)} weak-evidence claim(s). {verdict_reason}"
            ),
        ]
    )


def infer_balanced_verdict(report: dict) -> tuple[str, str]:
    label_counts = report["label_counts"]
    risk_counts = report["greenwashing_risk_counts"]
    relevance_counts = report["evidence_relevance_counts"]
    claims = report["claims"]
    total = max(int(report.get("total_claims_analyzed", 0)), 1)

    direct = relevance_counts.get("DIRECT", 0)
    indirect = relevance_counts.get("INDIRECT", 0)
    background = relevance_counts.get("BACKGROUND", 0)
    unrelated = relevance_counts.get("UNRELATED", 0)
    supported = label_counts.get("SUPPORTED", 0)
    partial = label_counts.get("PARTIALLY_SUPPORTED", 0)
    unverified = label_counts.get("UNVERIFIED", 0)
    contradicted = label_counts.get("CONTRADICTED", 0)
    partial_contradicted = label_counts.get("PARTIALLY_CONTRADICTED", 0)
    high_risk = risk_counts.get("HIGH", 0)
    medium_risk = risk_counts.get("MEDIUM", 0)

    supportive_share = (supported + partial) / total
    concern_share = (high_risk + medium_risk + contradicted + partial_contradicted) / total
    direct_share = direct / total
    weak_evidence_share = (background + unrelated) / total
    weighted_net = sum(claim.get("judgment_score", 0.0) for claim in claims) / total
    materiality_pressure = sum(claim.get("materiality_score", 0.0) for claim in claims if claim.get("judgment_score", 0.0) < 0)
    direct_support = sum(
        1
        for claim in claims
        if claim.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"} and claim.get("evidence_relevance") == "DIRECT"
    )
    material_support = sum(
        1
        for claim in claims
        if claim.get("final_label") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
        and claim.get("evidence_relevance") in {"DIRECT", "INDIRECT"}
        and claim.get("materiality_score", 0.0) >= 0.8
    )
    material_concern = sum(
        1
        for claim in claims
        if claim.get("final_label") in {"PARTIALLY_CONTRADICTED", "CONTRADICTED"}
        or (claim.get("greenwashing_risk_level") == "HIGH" and claim.get("evidence_relevance") == "DIRECT")
    )
    coverage_gap = unverified + background + unrelated

    if contradicted > 0 and (high_risk > 0 or weighted_net < -0.75 or materiality_pressure >= 1.0):
        return "High Greenwashing Risk", "At least one claim is directly contradicted, and the negative evidence is material enough to suggest more than isolated weakness."
    if contradicted > 0 or partial_contradicted >= 2 or (high_risk >= 2 and concern_share >= 0.35):
        return "Questionable", "The evidence includes direct contradiction or repeated high-concern signals that weaken confidence in the sustainability narrative."
    if material_support >= 2 and material_concern == 0 and direct_share >= 0.5:
        if direct_support >= 3 and coverage_gap <= 1:
            return "Broadly Supported", "The strongest claims are directly supported, and the remaining gaps are limited enough to look like ordinary coverage gaps rather than substantive concern signals."
        return "Mostly Credible", "The evidence leans clearly toward support on the most material claims, while unresolved items remain as coverage gaps rather than decisive negatives."
    if supportive_share >= 0.5 and concern_share <= 0.35 and weighted_net >= 0.5:
        return "Mostly Credible", "Supportive evidence outweighs the unresolved claims, and the remaining gaps do not materially overturn the overall picture."
    if support_share := supportive_share >= 0.35 and coverage_gap >= 2:
        pass
    if coverage_gap >= 2 and direct_share < 0.5 and material_concern == 0:
        return "Mixed Evidence", "The report has some support, but too much of the evidence remains unverified or only indirectly related to support a stronger conclusion."
    if weak_evidence_share >= 0.5 or direct_share < 0.2:
        return "Mixed Evidence", "Too many claims depend on weak, contextual, or unrelated evidence to justify a stronger verdict."

    return "Mixed Evidence", "The evidence contains both support and unresolved signals, so the safest reading is a mixed overall picture."


def build_balanced_conclusion(report: dict) -> str:
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    future_claims_count = report.get("future_claims_excluded", 0)

    if verdict_label == "High Greenwashing Risk":
        conclusion = "The analyzed discourse shows material CSR credibility concerns. The available evidence contains direct contradiction or repeatedly material concern signals strong enough to suggest that parts of the company's CSR narrative may be incomplete or selectively framed."
    elif verdict_label == "Questionable":
        conclusion = "The analyzed discourse is questionable as a CSR claim set. The evidence contains repeated concern signals or direct contradiction that materially weaken confidence in the company's CSR narrative."
    elif verdict_label == "Broadly Supported":
        conclusion = "The analyzed discourse is broadly supported as a CSR claim set. The strongest claims are directly corroborated, and the remaining unverified items look more like coverage gaps than evidence of misleading disclosure."
    elif verdict_label == "Credible":
        conclusion = "The analyzed discourse appears credible as a CSR claim set. The strongest claims are directly supported by the available evidence, and the unresolved gaps are limited enough not to overturn the overall picture."
    elif verdict_label == "Mostly Credible":
        conclusion = "The analyzed discourse appears mostly credible as a CSR claim set. The strongest claims are supported by the available evidence, although some material statements remain only partially verified or unresolved."
    else:
        conclusion = "The analyzed discourse shows mixed CSR evidence. Some claims are supported or partially supported, while others remain unresolved because external coverage is incomplete. This suggests caution rather than a definitive credibility finding."

    if verdict_reason:
        conclusion += f" {verdict_reason}"
    if future_claims_count > 0:
        conclusion += f" In addition, {future_claims_count} future-looking claim(s) were identified and excluded from the main evaluation."
    return conclusion


def build_llm_analysis_prompt(report: dict) -> str:
    narrative_packet = build_narrative_packet(report)
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    return f"""
You are writing the Verdict Rationale section of a formal CSR claim-assessment report with a separate environmental greenwashing-risk sub-assessment.

Use only the structured results below. Do not add outside facts.

Write a concise but detailed rationale that explains:
- the overall evidence pattern
- why the verdict is {verdict_label}
- which claims are most material
- why some unresolved claims do or do not change the verdict
- how direct versus indirect evidence affects confidence
- the main limitation of the automated judgment
- distinguish broader CSR credibility concerns from environmental greenwashing-related risk
- connect the claims into a smooth narrative instead of repeating the same template for each claim
- compare themes to one another when useful
- use transitions such as "that same pattern", "by contrast", "taken together", and "in the more cautious cases"

Use a formal report style.
Return Markdown only as 4 short subsections with these headings:
### Company Context
### Greenwashing Framing
### Theme-Based Analysis
### Verdict and Confidence

Rules:
- Cite claim IDs and source URLs where they materially support a statement.
- Do not invent facts.
- Do not overstate weak indirect evidence.
- Keep the language clear and specific, not promotional.
- Do not describe non-environmental claims as greenwashing.
- Prefer paragraphs over bullet lists.
- Avoid repeating the sentence pattern "A strong example of direct support is...".
- Use one paragraph per theme bundle, then a short synthesis paragraph.

Company: {report['company_name']}
Total claims analyzed: {report['total_claims_analyzed']}
Future claims excluded: {report['future_claims_excluded']}
Claims excluded from main analysis: {report['claims_excluded_from_main_analysis']}
CSR label counts: {json.dumps(report['csr_label_counts'], ensure_ascii=False)}
CSR credibility signal counts: {json.dumps(report['csr_credibility_signal_counts'], ensure_ascii=False)}
CSR evidence relevance counts: {json.dumps(report['csr_evidence_relevance_counts'], ensure_ascii=False)}
Environmental label counts: {json.dumps(report['environmental_label_counts'], ensure_ascii=False)}
Environmental greenwashing-risk counts: {json.dumps(report['environmental_greenwashing_risk_counts'], ensure_ascii=False)}
Environmental evidence relevance counts: {json.dumps(report['environmental_evidence_relevance_counts'], ensure_ascii=False)}
Rule-based conclusion: {report['final_conclusion']}
Balanced verdict target: {verdict_label}
Balanced verdict rationale: {verdict_reason}
Narrative packet: {json.dumps(narrative_packet, indent=2, ensure_ascii=False)}
Summary bullets: {json.dumps(build_report_summary_bullets(report), ensure_ascii=False)}

Decision guidance:
- Prefer the strongest supported claims and the most material unresolved claims.
- If the evidence is mostly supportive with only a few unresolved material points, say that clearly.
- If the evidence is mixed, explain why the unresolved pieces matter.
- If no contradictions exist, do not imply a stronger risk than the evidence supports.
- Treat theme bundles as the organizing unit, not isolated claims.

    """.strip()


def build_gemini_prompt(report: dict) -> str:
    narrative_packet = build_narrative_packet(report)
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    return f"""
You are writing the final narrative verdict for a CSR claim-assessment report with a separate environmental greenwashing-risk sub-assessment.

Write a human, connected, paragraph-based analysis. Do not write one paragraph per claim in a repetitive template. Group related claims together, compare them, and connect them with transitions.

Use only the structured packet below. Do not add outside facts.

Required tone:
- formal but readable
- analytical, not robotic
- concise but detailed
- source-backed
- not promotional
- not repetitive
- careful not to label non-environmental claims as greenwashing

Required structure:
### Company Context
### Greenwashing Framing
### Theme-Based Analysis
### Verdict and Confidence

Rules:
- Prefer paragraphs over bullets.
- Treat theme bundles as the organizing unit.
- Compare themes to each other when useful.
- Use transitions like "that same pattern appears in...", "by contrast...", "taken together...", and "in the more cautious cases...".
- Cite claim IDs, document names, pages, and URLs when they materially support a statement.
- If a claim is supported, explain why it matters.
- If a claim is unverified, frame it as a coverage gap unless it is a real concern signal.
- Do not overstate indirect or background evidence.
- Do not repeat the same opening sentence pattern for each claim.
- Do not mention excluded claims in the public narrative.

Input packet:
- company context
- greenwashing definition
- verdict metrics
- theme bundles
- summary bullets
- rule-based verdict target

Company: {report['company_name']}
Balanced verdict target: {verdict_label}
Balanced verdict rationale: {verdict_reason}
Narrative packet: {json.dumps(narrative_packet, indent=2, ensure_ascii=False)}
Summary bullets: {json.dumps(build_report_summary_bullets(report), ensure_ascii=False)}

Write the final answer as Markdown only.
""".strip()


def call_ollama(prompt: str) -> str:
    payload = {"model": LOCAL_MODEL, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    return clean_generated_markdown(result.get("response", ""))


def call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is not set.")

    model = os.environ.get("AGENT_9_GEMINI_MODEL", "gemini-2.0-flash")
    endpoint = GEMINI_ENDPOINT_TEMPLATE.format(model=model, api_key=api_key)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "topP": 0.95,
            "maxOutputTokens": 4096,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    return clean_generated_markdown(text)


def call_report_llm(prompt: str) -> str:
    if AGENT_9_PROVIDER == "gemini":
        return call_gemini(prompt)
    return call_ollama(prompt)


def build_theme_narrative_prompt(report: dict, theme_bundle: dict) -> str:
    return f"""
You are writing one paragraph for the Theme-Based Analysis section of a CSR / greenwashing report.

Write a smooth, human paragraph about the theme below. Do not use a fixed template. Do not repeat the same sentence openings across themes.

Rules:
- Write exactly one paragraph.
- 120 to 170 words preferred.
- Connect the claims with transitions and comparisons where useful.
- Use the claim IDs and sources naturally in the sentence, not as a list.
- Explain why the theme matters to the overall verdict.
- If the theme is mainly supportive, say so clearly.
- If the theme has gaps, frame them as gaps unless they materially change the picture.
- If the theme has tension signals, explain the tension without overstating it.
- Do not mention excluded claims.

Company: {report['company_name']}
Verdict target: {report.get('verdict_label', 'Mixed Evidence')}
Verdict rationale: {report.get('verdict_reason', '')}

Theme bundle:
{json.dumps(theme_bundle, indent=2, ensure_ascii=False)}

Context:
- company context: {build_report_context_paragraph(report)}
- greenwashing definition: {build_greenwashing_definition_paragraph()}
- summary bullets: {json.dumps(build_report_summary_bullets(report), ensure_ascii=False)}

Write only the paragraph text.
""".strip()


def build_theme_narratives(report: dict) -> list[str]:
    theme_bundles = build_theme_bundles(report["claims"])
    paragraphs: list[str] = []

    for bundle in theme_bundles:
        try:
            paragraph = call_report_llm(build_theme_narrative_prompt(report, bundle))
        except Exception:
            claim_bits = []
            for claim in bundle.get("claims", [])[:2]:
                claim_bits.append(f"[{claim['id']}] {claim['claim_text']} ({claim['source']})")
            if bundle.get("supported", 0) > bundle.get("unverified", 0) and bundle.get("concern", 0) == 0:
                paragraph = (
                    f"The {bundle['theme']} theme is mostly supportive: {bundle.get('supported', 0)} supported or partially supported claim(s) outweigh the unresolved ones. "
                    f"{'; '.join(claim_bits)}"
                )
            elif bundle.get("concern", 0) > 0:
                paragraph = (
                    f"The {bundle['theme']} theme contains some cautionary tension because the external evidence does not fully align with the company’s framing. "
                    f"{'; '.join(claim_bits)}"
                )
            else:
                paragraph = (
                    f"The {bundle['theme']} theme remains partly unresolved because the outside evidence is not specific enough to close the gap. "
                    f"{'; '.join(claim_bits)}"
                )

        paragraph = clean_generated_markdown(paragraph)
        if paragraph:
            paragraphs.append(f"**{bundle['theme']}**\n\n{paragraph}")

    return paragraphs


def build_fallback_deep_analysis(report: dict) -> str:
    label_counts = report["label_counts"]
    risk_counts = report["greenwashing_risk_counts"]
    relevance_counts = report["evidence_relevance_counts"]
    claims = report["claims"]
    total_claims = report["total_claims_analyzed"]
    theme_summaries = build_theme_summaries(claims)
    verdict_label, verdict_reason = infer_balanced_verdict(report)

    support_claims = [claim for claim in claims if claim.get("judgment_score", 0.0) > 0]
    concern_claims = [claim for claim in claims if claim.get("judgment_score", 0.0) < 0]
    direct_confidence = "moderate"
    if relevance_counts["DIRECT"] >= 4:
        direct_confidence = "moderate-to-high"
    elif relevance_counts["UNRELATED"] + relevance_counts["BACKGROUND"] >= max(total_claims // 2, 1):
        direct_confidence = "low-to-moderate"

    lines = [
        "### Evidence Pattern",
        f"The main analysis covers {total_claims} prioritized claims. {len(support_claims)} claim(s) lean supportive overall, while {len(concern_claims)} claim(s) remain unresolved or concerning after weighting label, relevance, and materiality.",
        f"Direct evidence accounts for {relevance_counts['DIRECT']} claim(s), which gives the report a usable factual base. Indirect or weaker evidence ({relevance_counts['INDIRECT'] + relevance_counts['BACKGROUND'] + relevance_counts['UNRELATED']} claim(s)) is treated as context rather than decisive proof.",
        "",
        "### Verdict Rationale",
        f"The verdict is {verdict_label} because the strongest claims are directly supported and the remaining gaps are not large enough to overturn the overall picture.",
        f"This is reinforced by the weighted score pattern, which favors the supported claims and treats indirect criticism as lower-confidence context unless it concerns a material claim with strong corroboration.",
        f"{verdict_reason}",
    ]

    if support_claims:
        best_support = sorted(support_claims, key=lambda claim: claim.get("judgment_score", 0.0), reverse=True)[:2]
        for claim in best_support:
            source = claim.get("top_evidence_url", "") or "No selected source"
            lines.append(f"- Support example [{claim['normalized_claim_id']}]: {claim['claim_text']} Source: {source}")
    if concern_claims:
        worst_concern = sorted(concern_claims, key=lambda claim: claim.get("judgment_score", 0.0))[:2]
        for claim in worst_concern:
            source = claim.get("top_evidence_url", "") or "No selected source"
            lines.append(f"- Concern example [{claim['normalized_claim_id']}]: {claim['claim_text']} Source: {source}")

    lines.extend([
        "",
        "### Confidence and Limits",
        f"Confidence is {direct_confidence}. The verdict is strongest where evidence is direct and weakest where the report relies on background commentary or indirect criticism.",
        f"{len([claim for claim in claims if not claim.get('top_evidence_url')])} claim(s) still do not have a strong selected source, so they should be treated cautiously in the final narrative.",
        f"{len([claim for claim in claims if claim.get('greenwashing_risk_level') == 'UNCLEAR'])} claim(s) remain unclear because the available evidence does not fully resolve the statement.",
    ])

    return "\n".join(lines)


def build_deep_analysis(report: dict) -> str:
    if PIPELINE_MODE == "fast":
        return build_fallback_deep_analysis(report)
    try:
        if AGENT_9_PROVIDER == "gemini":
            return call_gemini(build_gemini_prompt(report))
        return call_ollama(build_llm_analysis_prompt(report))
    except Exception:
        return build_fallback_deep_analysis(report)


def build_public_report(report: dict) -> str:
    try:
        return call_report_llm(build_public_report_prompt(report))
    except Exception:
        return build_fallback_public_report(report)


def build_fallback_public_report(report: dict) -> str:
    claim_briefs = build_public_claim_briefs(report)
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    context = build_report_context_paragraph(report)
    greenwashing = build_greenwashing_definition_paragraph()
    selected_text = []
    for brief in claim_briefs:
        selected_text.append(f"{brief['number']}. {brief['claim']} ({brief['status']}) - {brief['source']}")

    return "\n\n".join(
        [
            f"# {report['company_name']} CSR Claim Assessment",
            "## Short Context",
            context,
            "## What CSR Claim Assessment Means",
            greenwashing,
            "## What the Company Claims Across CSR Topics",
            "The report looks across the assessed CSR claims, including environmental, governance, responsible-AI, accessibility, human-rights, diversity, and social-impact statements. These include claims that are clearly supported, claims that are only partly supported, and claims that are not fully confirmed by the external evidence.",
            "\n".join(selected_text[:3]),
            "## Environmental Greenwashing-Risk Sub-Assessment",
            f"The environmental subset contains {report.get('total_environmental_claims_assessed', 0)} claim(s). Those claims are separately assessed for greenwashing-related risk, while non-environmental claims are treated as broader CSR credibility questions.",
            "## What External Sources Say",
            "The external evidence supports some of the company’s claims directly, while other claims are only partially confirmed or remain unresolved. In a few places, the outside sources raise concern because they weaken confidence in the company’s framing rather than simply repeating it.",
            "## Overall Assessment",
            f"The evidence points to {verdict_label.lower()}. {verdict_reason}",
            "## Why This Matters",
            "This matters because a company’s CSR story should be judged by how well its strongest claims hold up when checked against outside information. Environmental claims can raise greenwashing-related risk, while governance, responsible-AI, accessibility, diversity, and human-rights claims raise broader credibility questions if the evidence is weak or contradictory.",
            "## Limitations",
            "The report is based on the available external evidence, so some claims may remain unresolved if outside sources are limited or not specific enough.",
            "## Conclusion",
            f"**Conclusion:** {verdict_label}. {report['final_conclusion']}",
        ]
    )


def build_summary_markdown(report: dict) -> str:
    return build_analytical_summary_markdown(report)


def bold_claim_ids_in_text(text: str) -> str:
    return re.sub(r"\b(normalized_claim_\d+)\b", r"**\1**", str(text or ""))


def truncate_markdown_text(text: str, max_length: int) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def truncate_source_title(text: str, max_length: int = 60) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return "No selected source"
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def build_summary_source_link(title: str, url: str) -> str:
    clean_url = str(url or "").strip()
    if not clean_url:
        return "No selected source"
    return f"[{markdown_escape_cell(truncate_source_title(title))}]({clean_url})"


def build_claim_level_summary_rows(claims: list[dict], environmental: bool = False) -> list[str]:
    rows: list[str] = []
    for claim in claims:
        claim_id = markdown_escape_cell(claim.get("normalized_claim_id", ""))
        preview = markdown_escape_cell(truncate_markdown_text(claim.get("claim_text", ""), 90) or "N/A")
        label = markdown_escape_cell(claim.get("final_label", ""))
        signal = markdown_escape_cell(claim.get("greenwashing_risk_level", ""))
        evidence = markdown_escape_cell(claim.get("evidence_relevance", ""))
        source = build_summary_source_link(claim.get("top_evidence_title", ""), claim.get("top_evidence_url", ""))
        if environmental:
            rows.append(f"| {claim_id} | {preview} | {label} | {signal} | {evidence} | {source} |")
        else:
            domain = markdown_escape_cell(claim.get("claim_family", ""))
            rows.append(f"| {claim_id} | {preview} | {domain} | {label} | {signal} | {evidence} | {source} |")
    return rows


def build_required_verdict_reason(report: dict) -> str:
    return build_dynamic_verdict_reason(report)


def build_required_final_conclusion(report: dict) -> str:
    return build_dynamic_final_conclusion(report)


def build_required_verdict_rationale(report: dict) -> str:
    return build_dynamic_verdict_rationale(report)


def build_analytical_summary_markdown(report: dict) -> str:
    claims = list(report.get("claims", []))
    environmental_claims = list(report.get("environmental_claims", []))
    company = report.get("company_name", "Company")
    counts = report.get("label_counts", {})
    relevance_counts = report.get("evidence_relevance_counts", {})
    environmental_counts = report.get("environmental_label_counts", {})
    verdict_label, verdict_reason = infer_balanced_verdict(report)
    confidence = determine_confidence_label(report)
    examples = select_claim_examples(claims)
    top_support = examples.get("top_positive_examples", [])
    top_concern = examples.get("top_negative_examples", []) or examples.get("high_risk_examples", [])
    top_unverified = examples.get("unverified_examples", [])

    support_refs = format_claim_references(top_support, limit=3)
    concern_refs = format_claim_references(top_concern, limit=2)
    unverified_refs = format_claim_references(top_unverified, limit=3)

    supported_total = counts.get("SUPPORTED", 0) + counts.get("PARTIALLY_SUPPORTED", 0)
    weak_total = relevance_counts.get("BACKGROUND", 0) + relevance_counts.get("UNRELATED", 0)
    environmental_total = report.get("total_environmental_claims_assessed", 0)
    environmental_supported = environmental_counts.get("SUPPORTED", 0) + environmental_counts.get("PARTIALLY_SUPPORTED", 0)
    environmental_concern = environmental_counts.get("PARTIALLY_CONTRADICTED", 0) + environmental_counts.get("CONTRADICTED", 0)

    claim_table = [
        "| Claim ID | Claim preview | Domain | Label | Signal | Evidence | Source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *build_claim_level_summary_rows(claims, environmental=False),
    ]
    environmental_table = [
        "| Claim ID | Claim preview | Label | Greenwashing-risk | Evidence | Source |",
        "| --- | --- | --- | --- | --- | --- |",
        *build_claim_level_summary_rows(environmental_claims, environmental=True),
    ]

    summary = "\n".join(
        [
            f"# {company} CSR Claim Assessment",
            "",
            "## Executive Interpretation",
            "",
            f"Observed evidence across the {report.get('total_claims_analyzed', 0)} prioritized CSR claim(s) shows a {verdict_label.lower()} pattern rather than a simple pattern of broad falsification or blanket support. {counts.get('SUPPORTED', 0)} claim(s) are supported and {counts.get('PARTIALLY_SUPPORTED', 0)} are partially supported, which means the system found real external support for {supported_total} claim(s) in the selected set.",
            "",
            f"System inference is therefore scoped and claim-level. At claim level, the selected {company} CSR discourse is best read as {verdict_label.lower()}. {counts.get('UNVERIFIED', 0)} claim(s) remain unverified because the selected external evidence is not specific enough to confirm the exact statement, while {counts.get('PARTIALLY_CONTRADICTED', 0) + counts.get('CONTRADICTED', 0)} claim(s) raise contradiction-level concern. The system inference is not a blanket statement about whether {company}'s CSR discourse is broadly true or false; it is a weighted interpretation of the selected claims and selected outside evidence.",
            "",
            f"Confidence is {confidence} at claim level because the evidence pattern includes {relevance_counts.get('DIRECT', 0)} DIRECT case(s), {relevance_counts.get('INDIRECT', 0)} INDIRECT case(s), {relevance_counts.get('BACKGROUND', 0)} BACKGROUND case(s), and {relevance_counts.get('UNRELATED', 0)} UNRELATED case(s). That is enough to support interpretation, comparison, and prioritization, but not enough to collapse all claims into a single simple verdict where weak-evidence coverage remains high.",
            "",
            f"The limits of the conclusion are important but not disabling. The system cannot determine {company}'s overall CSR performance as a company, cannot produce a full audit verdict, and cannot prove intent or deception. It can, however, interpret the selected claims, identify which claim types are better supported, identify where evidence remains weak, and highlight the claims that most shape the final CSR credibility interpretation.",
            "",
            "## Evidence Balance",
            "",
            "| Category | Count | Interpretation |",
            "|---|---:|---|",
            f"| CSR claims assessed | {report.get('total_claims_analyzed', 0)} | Selected prioritized claims evaluated with external evidence |",
            f"| Supported | {counts.get('SUPPORTED', 0)} | Claims with external evidence supporting the statement |",
            f"| Partially supported | {counts.get('PARTIALLY_SUPPORTED', 0)} | Claim(s) with some support but important qualifications |",
            f"| Unverified | {counts.get('UNVERIFIED', 0)} | Evidence insufficiently specific; not evidence of falsehood |",
            f"| Partially contradicted | {counts.get('PARTIALLY_CONTRADICTED', 0)} | Stronger concern signal requiring scrutiny |",
            f"| Contradicted | {counts.get('CONTRADICTED', 0)} | Claim(s) fully contradicted by selected evidence |",
            "",
            f"The counts matter because {supported_total} supported or partially supported claim(s) show where the system found real external support, while {counts.get('UNVERIFIED', 0)} unverified claim(s) and {counts.get('PARTIALLY_CONTRADICTED', 0) + counts.get('CONTRADICTED', 0)} contradiction-level claim(s) show where the narrative is weaker or more exposed to challenge.",
            "",
            f"The {counts.get('UNVERIFIED', 0)} unverified claim(s) should not be read automatically as falsehoods. They indicate that the selected external evidence was not specific enough to verify the exact metric, operational detail, or year-specific claim. This is especially important where the available sources are only indirect or where claim language is broader than the evidence base.",
            "",
            f"The contradiction-side claims matter disproportionately when they are paired with direct evidence and high materiality. At the same time, the report should avoid claiming broad falsification unless contradiction is repeated and well-supported across the set.",
            "",
            "## Claim-Level Summary Table",
            "",
            *claim_table,
            "",
            "## Environmental Sub-Assessment Table",
            "",
            *environmental_table,
            "",
            "## Claim Influence and Interpretive Weight",
            "",
            "Not all claims have equal interpretive weight. Claim influence depends on materiality, whether the claim is impact-related or mainly procedural, the relevance of the selected evidence, the final label, and whether the claim materially changes the final CSR credibility interpretation.",
            "",
            f"Higher-influence support-side examples in this run include {support_refs}. These claims matter because they provide the strongest available support for the company's selected CSR framing, especially where the evidence is direct or tied to formal documentation.",
            "",
            f"Higher-influence concern-side examples include {concern_refs}. These claims matter because they carry the most pressure against the company's narrative in this run, especially when the evidence is direct, the claim is environmental or operationally material, or the claim language is broader than the available corroboration.",
            "",
            f"A separate set of lower-confidence claims remains unresolved, including {unverified_refs}. These entries should generally be read as verification gaps unless stronger contradiction appears, because the selected evidence does not tightly confirm the exact wording or metric.",
            "",
            f"Taken together, this means the final interpretation should weight evidence quality and claim materiality more heavily than the presence of generic supporting language or weak contextual sources. {verdict_reason}",
            "",
            "## Supported Claim Patterns",
            "",
            f"Supported claims are usually the ones that the external evidence can confirm most directly. In this run, that pattern appears most clearly in {support_refs}. These claims tend to concern published policies, documented commitments, disclosed metrics, or visible governance artifacts rather than broad outcome claims that would require deeper audit evidence.",
            "",
            "Observed support should still be interpreted carefully. A supported disclosure claim does not automatically prove strong real-world outcomes; in many cases it confirms that a document, process, or statement exists and is externally recognizable.",
            "",
            "## Unverified Claim Patterns",
            "",
            f"Unverified claims are clustered where the selected evidence is too general, too weak, or too distant from the exact statement to confirm it confidently. In this run, that includes {unverified_refs}. Those gaps should not be treated as proof of falsehood, but they do limit how strongly the system can endorse the broader narrative.",
            "",
            f"This is also where the {weak_total} weak-evidence claim(s) matter most: when a claim is paired mainly with background or unrelated material, the report should remain cautious even if the claim sounds plausible on its face.",
            "",
            "## Main Environmental Concern",
            "",
            f"The environmental subset contains {environmental_total} claim(s), of which {environmental_supported} are supported or partially supported and {environmental_concern} raise contradiction-level concern. Environmental concern is most important when a material operational or impact-related claim is weakened by direct outside evidence rather than by mere lack of coverage.",
            "",
            f"Where environmental claims remain only weakly supported, the sub-assessment should be read as targeted greenwashing-related risk analysis rather than a blanket greenwashing accusation. The system is assessing whether the selected claim framing is stronger than the corroboration behind it.",
            "",
            "## Environmental Greenwashing-Risk Sub-Assessment",
            "",
            f"The environmental subset is mixed. It contains {environmental_total} claim(s): {environmental_counts.get('SUPPORTED', 0)} supported, {environmental_counts.get('PARTIALLY_SUPPORTED', 0)} partially supported, {environmental_counts.get('UNVERIFIED', 0)} unverified, {environmental_counts.get('PARTIALLY_CONTRADICTED', 0)} partially contradicted, and {environmental_counts.get('CONTRADICTED', 0)} contradicted. This means the environmental subset should be read claim by claim rather than collapsed into a single undifferentiated signal.",
            "",
            f"System inference is therefore specific: the environmental sub-assessment suggests targeted greenwashing-related risk only where evidence quality, materiality, and contradiction justify it. Otherwise, weaker environmental claims remain verification gaps rather than firm adverse findings.",
            "",
            "## Non-Environmental CSR Credibility Assessment",
            "",
            "Non-environmental claims in this report should not be interpreted as greenwashing by default. They are better read as governance, responsible-AI, diversity, labor, inclusion, human-rights, or social-impact credibility claims depending on the claim family involved.",
            "",
            f"Observed evidence is usually stronger for non-environmental claims when the claim concerns the existence of a policy, process, or documented artifact, and weaker when the claim implies broader cultural impact or operational outcomes that the selected sources do not directly verify.",
            "",
            "## Final Interpretation",
            "",
            f"Based on the selected prioritized claims, {company}'s CSR discourse is best read as {verdict_label.lower()}. The strongest supported areas are the claims with the best direct corroboration, while the weakest areas are the claims that remain unverified or carry contradiction-level concern. {verdict_reason}",
            "",
            f"The system cannot make a company-wide audit judgment, but it can conclude that the selected CSR discourse for {company} is unevenly supported and should be interpreted with attention to evidence strength, claim materiality, and the difference between documented process claims and outcome claims.",
            "",
            "## Scope Note",
            "",
            "This report provides a claim-level interpretation of the selected CSR disclosure set. It should not be read as a complete CSR audit, a company-wide ESG rating, or evidence of intentional deception.",
        ]
    )
    return bold_claim_ids_in_text(summary)


def claim_preview(text: str, max_length: int = 120) -> str:
    value = str(text or "").strip()
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def markdown_link(label: str, url: str) -> str:
    clean_label = str(label or "").strip()
    clean_url = str(url or "").strip()
    if not clean_url:
        return "No selected external source"
    if not clean_label:
        clean_label = clean_url
    return f"[{clean_label}]({clean_url})"


def markdown_escape_cell(value: str) -> str:
    text = str(value or "").replace("\n", " ").replace("\r", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text.replace("|", "\\|")


def format_counts_inline(counts: dict) -> str:
    return ", ".join(f"{key}: {value}" for key, value in counts.items())


def build_traceability_table_rows(claims: list[dict], environmental: bool = False) -> list[str]:
    rows = []
    for claim in claims:
        page_numbers = str(claim.get("page_numbers", "")).strip() or "N/A"
        evidence_title = str(claim.get("top_evidence_title", "")).strip()
        evidence_url = str(claim.get("top_evidence_url", "")).strip()
        source_name = str(claim.get("document_name", "")).strip() or "N/A"
        preview = claim_preview(claim.get("claim_text", "")) or "N/A"
        if environmental:
            rows.append(
                "| "
                + " | ".join(
                    [
                        markdown_escape_cell(claim.get("normalized_claim_id", "")),
                        markdown_escape_cell(preview),
                        markdown_escape_cell(claim.get("final_label", "")),
                        markdown_escape_cell(claim.get("greenwashing_risk_level", "")),
                        markdown_escape_cell(source_name),
                        markdown_escape_cell(page_numbers),
                        markdown_escape_cell(evidence_title or "No selected external source"),
                        markdown_escape_cell(evidence_url or "No selected external source"),
                        markdown_escape_cell(claim.get("evidence_relevance", "")),
                    ]
                )
                + " |"
            )
        else:
            rows.append(
                "| "
                + " | ".join(
                    [
                        markdown_escape_cell(claim.get("normalized_claim_id", "")),
                        markdown_escape_cell(preview),
                        markdown_escape_cell(claim.get("claim_family", "")),
                        markdown_escape_cell(claim.get("final_label", "")),
                        markdown_escape_cell(claim.get("greenwashing_risk_level", "")),
                        markdown_escape_cell(source_name),
                        markdown_escape_cell(page_numbers),
                        markdown_escape_cell(evidence_title or "No selected external source"),
                        markdown_escape_cell(evidence_url or "No selected external source"),
                        markdown_escape_cell(claim.get("evidence_relevance", "")),
                    ]
                )
                + " |"
            )
    return rows


def build_detailed_claim_notes(claims: list[dict]) -> list[str]:
    sections = []
    for claim in claims:
        claim_id = str(claim.get("normalized_claim_id", "")).strip() or "N/A"
        claim_text = str(claim.get("claim_text", "")).strip() or "N/A"
        domain = str(claim.get("claim_family", "")).strip() or "N/A"
        document_name = str(claim.get("document_name", "")).strip() or "N/A"
        page_numbers = str(claim.get("page_numbers", "")).strip() or "N/A"
        source_excerpt = str(claim.get("source_excerpts", "")).strip() or "N/A"
        evidence_title = str(claim.get("top_evidence_title", "")).strip()
        evidence_url = str(claim.get("top_evidence_url", "")).strip()
        final_label = str(claim.get("final_label", "")).strip() or "N/A"
        relevance = str(claim.get("evidence_relevance", "")).strip() or "N/A"
        signal = str(claim.get("greenwashing_risk_level", "")).strip() or "N/A"
        justification = clean_generated_text(claim.get("justification", "")) or "N/A"

        sections.append(
            "\n".join(
                [
                    f"### {claim_id}",
                    f"- Claim ID: `{claim_id}`",
                    f"- Full claim text: {claim_text}",
                    f"- Domain: `{domain}`",
                    f"- Corporate source and page: {document_name} | p. {page_numbers}",
                    f"- Corporate excerpt: {source_excerpt}",
                    f"- External source title and URL: {markdown_link(evidence_title or 'External source', evidence_url)}",
                    f"- Final label: `{final_label}`",
                    f"- Evidence relevance: `{relevance}`",
                    f"- CSR credibility signal / greenwashing-risk level: `{signal}`",
                    f"- Justification: {justification}",
                ]
            )
        )
    return sections


def build_traceability_report_markdown(report: dict) -> str:
    csr_claims = list(report.get("claims", []))
    environmental_claims = list(report.get("environmental_claims", []))

    csr_table = [
        "| Claim ID | Claim preview | Domain | Label | CSR credibility signal | Corporate source | Page | External evidence title | External evidence URL | Evidence relevance |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *build_traceability_table_rows(csr_claims, environmental=False),
    ]
    environmental_table = [
        "| Claim ID | Claim preview | Label | Greenwashing-risk level | Corporate source | Page | External evidence title | External evidence URL | Evidence relevance |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *build_traceability_table_rows(environmental_claims, environmental=True),
    ]

    lines = [
        f"# {report['company_name']} CSR Claim Assessment: Traceability Report",
        "",
        "This report links each prioritized CSR claim to its original corporate source and selected external evidence. It is designed to support traceability and auditability of the final system output, but it is not a definitive CSR audit.",
        "",
        "## Overall CSR Assessment Summary",
        "",
        f"- Total CSR claims assessed: {report.get('total_csr_claims_assessed', 0)}",
        f"- CSR label counts: {format_counts_inline(report.get('csr_label_counts', {}))}",
        f"- CSR evidence relevance counts: {format_counts_inline(report.get('csr_evidence_relevance_counts', {}))}",
        f"- CSR credibility signal counts: {format_counts_inline(report.get('csr_credibility_signal_counts', {}))}",
        "",
        "## Overall CSR Claim Traceability Table",
        "",
        *csr_table,
        "",
        "## Environmental Greenwashing-Risk Sub-Assessment Summary",
        "",
        f"- Total environmental claims assessed: {report.get('total_environmental_claims_assessed', 0)}",
        f"- Environmental label counts: {format_counts_inline(report.get('environmental_label_counts', {}))}",
        f"- Environmental greenwashing-risk counts: {format_counts_inline(report.get('environmental_greenwashing_risk_counts', {}))}",
        f"- Environmental evidence relevance counts: {format_counts_inline(report.get('environmental_evidence_relevance_counts', {}))}",
        "",
        "## Environmental Claim Traceability Table",
        "",
        *environmental_table,
        "",
        "## Detailed Claim Notes",
        "",
        *build_detailed_claim_notes(csr_claims),
    ]
    return "\n".join(lines)


def build_final_report(project_root: Path, assessments: list[dict], company_name: str) -> dict:
    claims = load_csv_rows(project_root / "agent_2" / "claims.csv")
    normalized_claims = load_csv_rows(project_root / "agent_3" / "normalized_claims.csv")
    prioritized_claims = load_csv_rows(project_root / "agent_3" / "prioritized_claims.csv")
    excluded_claims = load_csv_rows(project_root / "agent_3" / "excluded_claims.csv")
    future_claims = load_csv_rows(project_root / "agent_3" / "future_claims.csv")

    report_rows = [normalize_report_claim_family(row) for row in build_report_rows(assessments)]
    environmental_claims = filter_claims_by_family(report_rows, "environmental")
    primary_claim_rows = report_rows
    normalized_claim_lookup = build_normalized_claim_lookup(normalized_claims)
    primary_claim_rows = enrich_report_rows(primary_claim_rows, normalized_claim_lookup)
    environmental_claim_rows = enrich_report_rows(environmental_claims, normalized_claim_lookup)

    csr_label_counts = count_labels(primary_claim_rows)
    csr_credibility_signal_counts = count_credibility_signal_levels(primary_claim_rows)
    csr_evidence_relevance_counts = count_evidence_relevance(primary_claim_rows)
    environmental_label_counts = count_labels(environmental_claim_rows)
    environmental_greenwashing_risk_counts = count_risk_levels(environmental_claim_rows)
    environmental_evidence_relevance_counts = count_evidence_relevance(environmental_claim_rows)
    total_claims = len(primary_claim_rows)
    total_environmental_claims = len(environmental_claim_rows)
    future_claims_count = len(future_claims)
    run_metadata = build_run_metadata(company_name, claims, normalized_claims, prioritized_claims, excluded_claims, future_claims, primary_claim_rows, project_root)
    verdict_label = "Mixed Evidence with Specific Concern Signals"
    verdict_reason = ""
    weighted_net = round(sum(claim.get("judgment_score", 0.0) for claim in primary_claim_rows) / max(total_claims, 1), 3)
    weak_evidence_share = round((csr_evidence_relevance_counts["BACKGROUND"] + csr_evidence_relevance_counts["UNRELATED"]) / max(total_claims, 1), 3)
    support_share = round((csr_label_counts["SUPPORTED"] + csr_label_counts["PARTIALLY_SUPPORTED"]) / max(total_claims, 1), 3)
    concern_share = round((csr_label_counts["PARTIALLY_CONTRADICTED"] + csr_label_counts["CONTRADICTED"]) / max(total_claims, 1), 3)

    support_claims = sorted([claim for claim in primary_claim_rows if claim.get("judgment_score", 0.0) > 0], key=lambda claim: claim.get("judgment_score", 0.0), reverse=True)
    concern_claims = sorted([claim for claim in primary_claim_rows if claim.get("judgment_score", 0.0) < 0], key=lambda claim: claim.get("judgment_score", 0.0))

    key_findings = []
    for claim in support_claims[:2]:
        source = claim.get("top_evidence_url", "") or "No selected source"
        key_findings.append(f"Support: [{claim['normalized_claim_id']}] {claim['claim_text']} Source: {source}")
    for claim in concern_claims[:2]:
        source = claim.get("top_evidence_url", "") or "No selected source"
        key_findings.append(f"Concern: [{claim['normalized_claim_id']}] {claim['claim_text']} Source: {source}")

    final_report = {
        "company_name": company_name,
        "run_metadata": run_metadata,
        "total_claims_analyzed": total_claims,
        "total_csr_claims_assessed": total_claims,
        "total_environmental_claims_assessed": total_environmental_claims,
        "claims_excluded_from_main_analysis": len(excluded_claims),
        "future_claims_excluded": future_claims_count,
        "csr_label_counts": csr_label_counts,
        "csr_evidence_relevance_counts": csr_evidence_relevance_counts,
        "csr_credibility_signal_counts": csr_credibility_signal_counts,
        "environmental_label_counts": environmental_label_counts,
        "environmental_greenwashing_risk_counts": environmental_greenwashing_risk_counts,
        "environmental_evidence_relevance_counts": environmental_evidence_relevance_counts,
        "label_counts": csr_label_counts,
        "greenwashing_risk_counts": csr_credibility_signal_counts,
        "evidence_relevance_counts": csr_evidence_relevance_counts,
        "final_conclusion": "",
        "verdict_label": verdict_label,
        "verdict_reason": verdict_reason,
        "evidence_weighting": {
            "weighted_net": weighted_net,
            "support_share": support_share,
            "concern_share": concern_share,
            "weak_evidence_share": weak_evidence_share,
        },
        "key_findings": key_findings,
        "claims": primary_claim_rows,
        "all_claims": primary_claim_rows,
        "environmental_claims": environmental_claim_rows,
        "excluded_claims": excluded_claims,
        "normalized_claim_lookup_size": len(normalized_claim_lookup),
    }
    final_report["verdict_label"], verdict_reason = infer_balanced_verdict(final_report)
    final_report["verdict_reason"] = build_required_verdict_reason(final_report)
    final_report["final_conclusion"] = build_required_final_conclusion(final_report)
    final_report["verdict_rationale"] = build_required_verdict_rationale(final_report)
    return final_report


def save_final_report_artifacts(project_root: Path, report: dict) -> None:
    output_dir = project_root / "agent_9"
    save_report_csv(report["claims"], output_dir / "final_report.csv")
    save_report_csv(report["claims"], output_dir / "final_csr_assessment.csv")
    save_report_csv(report.get("environmental_claims", []), output_dir / "final_environmental_subassessment.csv")
    save_report_json(report, output_dir / "final_report.json")
    (output_dir / "final_summary.md").write_text(build_summary_markdown(report), encoding="utf-8")
    (output_dir / "final_traceability_report.md").write_text(build_traceability_report_markdown(report), encoding="utf-8")
