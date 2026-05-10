from __future__ import annotations

import csv
import os
import re
from difflib import SequenceMatcher
from pathlib import Path


SIMILARITY_THRESHOLD = 0.88
MAX_PRIORITIZED_CLAIMS_TOTAL = int(os.environ.get("MAX_PRIORITIZED_CLAIMS_TOTAL", "15"))
MAX_PRIORITIZED_CLAIMS_PER_DOCUMENT = int(os.environ.get("MAX_PRIORITIZED_CLAIMS_PER_DOCUMENT", "15"))


def load_claims(csv_path: Path) -> list[dict]:
    claims = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            claims.append(row)

    return claims


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[“”\"'`´]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def are_similar_claims(claim_a: dict, claim_b: dict) -> bool:
    if claim_a["topic"] != claim_b["topic"]:
        return False

    if claim_a["claim_type"] != claim_b["claim_type"]:
        return False

    text_a = normalize_text(claim_a["claim_text"])
    text_b = normalize_text(claim_b["claim_text"])
    similarity = SequenceMatcher(None, text_a, text_b).ratio()
    return similarity >= SIMILARITY_THRESHOLD


def split_future_claims(claims: list[dict]) -> tuple[list[dict], list[dict]]:
    current_claims = []
    future_claims = []

    for claim in claims:
        is_future = str(claim["is_future"]).strip().lower() == "true"
        if is_future:
            future_claims.append(claim)
        else:
            current_claims.append(claim)

    return current_claims, future_claims


def classify_claim_family(claim: dict) -> str:
    topic = str(claim.get("topic", "")).lower().strip()
    document_name = str(claim.get("document_name", "")).lower()
    claim_text = str(claim.get("claim_text", "")).lower()

    governance_topics = {"ethics", "governance", "labor", "human_rights", "social_impact"}
    governance_markers = {
        "responsible ai",
        "generative ai",
        "frontier model",
        "frontier models",
        "transparency note",
        "ai risk management framework",
        "responsible ai standard",
        "azure openai",
        "ai safety",
    }

    if topic in governance_topics:
        return "governance_ai"
    if "responsible ai" in document_name or "ai transparency" in document_name:
        return "governance_ai"
    if any(marker in claim_text for marker in governance_markers):
        return "governance_ai"
    if topic in {"environment", "climate", "emissions", "energy", "water", "waste", "supply_chain"}:
        return "environmental"
    return "other"


def merge_claim_group(group: list[dict], normalized_id: int) -> dict:
    first_claim = group[0]
    original_ids = []
    document_ids = []
    document_names = []
    page_numbers = []
    source_locations = []
    excerpts = []

    for claim in group:
        original_ids.append(claim["claim_id"])
        document_id = claim.get("document_id", "")
        document_ids.append(document_id)
        document_names.append(claim.get("document_name", ""))
        page_numbers.append(str(claim["page_number"]))
        source_locations.append(f"{document_id}:p{claim['page_number']}" if document_id else f"p{claim['page_number']}")
        excerpts.append(claim["source_excerpt"])

    unique_page_numbers = sorted(set(page_numbers), key=lambda x: int(x))
    unique_document_ids = sorted(set(item for item in document_ids if item))
    unique_document_names = sorted(set(item for item in document_names if item))
    unique_source_locations = sorted(set(source_locations))
    unique_excerpts = []

    for excerpt in excerpts:
        if excerpt not in unique_excerpts:
            unique_excerpts.append(excerpt)

    return {
        "normalized_claim_id": f"normalized_claim_{normalized_id}",
        "document_id": "; ".join(unique_document_ids),
        "document_name": "; ".join(unique_document_names) if unique_document_names else first_claim["document_name"],
        "claim_text": first_claim["claim_text"],
        "claim_type": first_claim["claim_type"],
        "topic": first_claim["topic"],
        "claim_family": classify_claim_family(first_claim),
        "original_claim_ids": "; ".join(original_ids),
        "page_numbers": "; ".join(unique_page_numbers),
        "source_locations": "; ".join(unique_source_locations),
        "source_excerpts": " || ".join(unique_excerpts),
        "group_size": len(group),
    }


def normalize_claims(claims: list[dict]) -> list[dict]:
    normalized_claims = []
    used_indices = set()
    normalized_id = 1

    for index, claim in enumerate(claims):
        if index in used_indices:
            continue

        group = [claim]
        used_indices.add(index)

        for other_index in range(index + 1, len(claims)):
            if other_index in used_indices:
                continue

            other_claim = claims[other_index]
            if are_similar_claims(claim, other_claim):
                group.append(other_claim)
                used_indices.add(other_index)

        normalized_claim = merge_claim_group(group, normalized_id)
        normalized_claims.append(normalized_claim)
        normalized_id += 1

    return normalized_claims


def count_numbers(text: str) -> int:
    return len(re.findall(r"\d+(?:[,.]\d+)*", text))


def score_analytical_value(claim: dict) -> tuple[int, str]:
    claim_text = claim.get("claim_text", "")
    lowered = claim_text.lower()
    score = 0
    reasons = []

    strong_patterns = [
        ("carbon neutrality", 35, "carbon_neutrality"),
        ("carbon neutral", 35, "carbon_neutral"),
        ("carbon negative", 35, "carbon_negative"),
        ("renewable electricity", 34, "renewable_electricity"),
        ("100%", 20, "absolute_100_percent_claim"),
        ("scope 3", 18, "scope_3"),
        ("supply chain", 26, "supply_chain"),
        ("supplier", 24, "supplier"),
        ("human rights", 26, "human_rights"),
        ("annual spend", 30, "supplier_spend_methodology"),
        ("response-derived factor", 30, "supplier_response_factor"),
        ("carbon removal", 28, "carbon_removal"),
        ("high-quality carbon dioxide removal", 34, "high_quality_carbon_dioxide_removal"),
        ("carbon dioxide removal criteria", 30, "carbon_dioxide_removal_criteria"),
        ("carbon credit", 24, "carbon_credit"),
        ("offset", 22, "offset"),
        ("ppa", 18, "ppa"),
        ("recs", 18, "renewable_certificate"),
        ("eac", 18, "energy_attribute_certificate"),
        ("water", 24, "water"),
        ("water inventory", 28, "water_inventory"),
        ("operational control", 24, "operational_control"),
        ("data center", 22, "data_center"),
        ("responsible ai", 32, "responsible_ai"),
        ("transparency note", 24, "transparency_note"),
        ("ai risk management framework", 28, "ai_risk_management_framework"),
        ("responsible ai standard", 28, "responsible_ai_standard"),
        ("frontier models", 22, "frontier_models"),
        ("governing generative ai", 26, "generative_ai_governance"),
        ("generative ai releases", 24, "generative_ai_releases"),
        ("transparency", 16, "transparency"),
        ("safety", 14, "safety"),
        ("diversity", 18, "diversity"),
        ("inclusion", 18, "inclusion"),
        ("belonging", 18, "belonging"),
    ]

    for pattern, weight, reason in strong_patterns:
        if pattern in lowered:
            score += weight
            reasons.append(reason)

    if re.search(r"\bfy\d{2}\b", lowered) or re.search(r"\b20\d{2}\b", lowered):
        score += 3
        reasons.append("specific_year")

    if re.search(r"\d+(?:\.\d+)?\s?%", lowered):
        score += 3
        reasons.append("specific_percentage")

    if count_numbers(claim_text) >= 6:
        score -= 30
        reasons.append("dense_internal_metric_table")

    if "as follows" in lowered:
        score -= 20
        reasons.append("table_style_claim")

    if lowered.startswith("microsoft reports") and count_numbers(claim_text) >= 4:
        score -= 15
        reasons.append("internal_reporting_numbers")

    if "microsoft reports that its total water" in lowered:
        score -= 20
        reasons.append("internal_water_metric")

    if "operational control approach" in lowered:
        score -= 15
        reasons.append("internal_operational_control_methodology")

    if "market-based approach" in lowered:
        score -= 18
        reasons.append("internal_market_based_methodology")

    if "purchased eacs include" in lowered and claim_text.count(",") >= 4:
        score -= 18
        reasons.append("long_certificate_list")

    if "percentage of direct renewable electricity" in lowered:
        score -= 18
        reasons.append("direct_renewable_electricity_percentage")

    if "scope 3 emissions for fy" in lowered and count_numbers(claim_text) >= 2:
        score -= 18
        reasons.append("single_year_internal_scope_metric")

    if "percentage of renewable electricity consumption" in lowered:
        score -= 30
        reasons.append("internal_renewable_percentage_table")

    if "reflects what is in scope for our carbon negative commitment" in lowered:
        score -= 35
        reasons.append("internal_scope_boundary_statement")

    if "follow management" in lowered and "criteria" in lowered:
        score -= 35
        reasons.append("internal_management_criteria")

    if "inventory includes" in lowered:
        score -= 28
        reasons.append("inventory_composition_statement")

    if "calculates and reports" in lowered:
        score -= 24
        reasons.append("generic_reporting_process_statement")

    if "within its carbon neutrality boundary" in lowered and "certified" in lowered:
        score -= 18
        reasons.append("internal_credit_application_rule")

    if "published the criteria" in lowered and "carbon dioxide removal" in lowered:
        score += 8
        reasons.append("publicly_checkable_criteria_publication")

    if len(claim_text) < 60:
        score -= 20
        reasons.append("low_information")

    if not reasons:
        reasons.append("generic_medium_value")

    return score, "; ".join(reasons)


def prioritize_claim(claim: dict, max_prioritized_claims_total: int | None = None) -> dict:
    claim_text = claim.get("claim_text", "")
    lowered = claim_text.lower()
    topic = claim.get("topic", "").lower()

    priority = "MEDIUM"
    main_analysis = "false"
    exclusion_reason = "medium_priority_excluded_from_main_analysis"

    reporting_patterns = [
        "following sections",
        "compilation of environmental metrics",
        "this report",
        "this data fact sheet",
        "we report",
    ]
    high_value_terms = [
        "carbon neutral",
        "carbon neutrality",
        "carbon negative",
        "renewable electricity",
        "100%",
        "scope 3",
        "supplier",
        "supply chain",
        "water",
        "withdrawal",
        "consumption",
        "discharge",
        "data center",
        "offset",
        "carbon removal",
        "high-quality carbon dioxide removal",
        "carbon dioxide removal criteria",
        "ppa",
        "recs",
        "eac",
        "responsible ai",
        "human rights",
        "labor",
        "frontier model",
        "frontier models",
        "transparency note",
        "responsible ai standard",
        "ai risk management framework",
        "governing generative ai",
        "generative ai",
        "safety",
        "transparency",
    ]

    analytical_value_score, analytical_value_reason = score_analytical_value(claim)
    is_metric_table = " as follows" in lowered and count_numbers(claim_text) >= 6
    is_meta_reporting = any(pattern in lowered for pattern in reporting_patterns)
    is_high_value = any(term in lowered or term in topic for term in high_value_terms)
    is_low_external_verifiability = any(
        pattern in lowered
        for pattern in [
            "reflects what is in scope",
            "follow management",
            "inventory includes",
            "calculates and reports",
            "within its carbon neutrality boundary",
            "operational control",
        ]
    ) and "published the criteria" not in lowered

    if is_metric_table:
        priority = "LOW"
        main_analysis = "false"
        exclusion_reason = "internal_metric_table_difficult_to_verify_externally"
    elif is_meta_reporting:
        priority = "LOW"
        main_analysis = "false"
        exclusion_reason = "meta_or_reporting_claim_not_substantive"
    elif is_low_external_verifiability:
        priority = "MEDIUM"
        main_analysis = "false"
        exclusion_reason = "hard_to_verify_internal_methodology_or_boundary_claim"
    elif is_high_value or analytical_value_score >= 0:
        priority = "HIGH"
        main_analysis = "true"
        exclusion_reason = ""
    elif len(claim_text) < 60:
        priority = "LOW"
        main_analysis = "false"
        exclusion_reason = "too_short_or_low_information"

    enriched_claim = dict(claim)
    enriched_claim["evaluation_priority"] = priority
    enriched_claim["main_analysis"] = main_analysis
    enriched_claim["exclusion_reason"] = exclusion_reason
    enriched_claim["analytical_value_score"] = analytical_value_score
    enriched_claim["analytical_value_reason"] = analytical_value_reason
    return enriched_claim


def get_claim_document_ids(claim: dict) -> list[str]:
    document_id = str(claim.get("document_id", "")).strip()
    if not document_id:
        return []
    return [part.strip() for part in document_id.split(";") if part.strip()]


def get_primary_document_id(claim: dict) -> str:
    document_ids = get_claim_document_ids(claim)
    return document_ids[0] if document_ids else "unknown_document"


def select_prioritized_claims(sorted_candidates: list[dict], limit: int, per_document_limit: int) -> list[dict]:
    grouped_candidates: dict[str, dict[str, list[dict]]] = {}
    family_order: list[str] = []

    for claim in sorted_candidates:
        claim_family = str(claim.get("claim_family", "other")).strip().lower() or "other"
        document_id = get_primary_document_id(claim)
        if claim_family not in grouped_candidates:
            grouped_candidates[claim_family] = {}
            family_order.append(claim_family)
        grouped_candidates[claim_family].setdefault(document_id, []).append(claim)

    family_scores = {
        family: max(int(claim.get("analytical_value_score", 0)) for claims in docs.values() for claim in claims)
        for family, docs in grouped_candidates.items()
    }
    family_order.sort(key=lambda family: (family_scores.get(family, 0), family), reverse=True)

    document_positions: dict[str, int] = {}
    document_counts: dict[str, int] = {}
    prioritized_claims = []
    family_indices = {family: 0 for family in family_order}

    while len(prioritized_claims) < limit:
        made_progress = False
        for family in family_order:
            document_groups = grouped_candidates[family]
            if not document_groups:
                continue

            ordered_documents = sorted(
                document_groups.keys(),
                key=lambda document_id: (
                    len(document_groups[document_id]),
                    document_id,
                ),
                reverse=True,
            )
            if not ordered_documents:
                continue

            start_index = document_positions.get(family, 0)
            for offset in range(len(ordered_documents)):
                document_id = ordered_documents[(start_index + offset) % len(ordered_documents)]
                if document_counts.get(document_id, 0) >= per_document_limit:
                    continue

                claim_index = family_indices[family]
                document_claims = document_groups[document_id]
                if claim_index >= len(document_claims):
                    continue

                prioritized_claims.append(document_claims[claim_index])
                document_counts[document_id] = document_counts.get(document_id, 0) + 1
                family_indices[family] = claim_index + 1
                document_positions[family] = (ordered_documents.index(document_id) + 1) % len(ordered_documents)
                made_progress = True
                break

            if len(prioritized_claims) >= limit:
                return prioritized_claims

        if not made_progress:
            break

    return prioritized_claims


def prioritize_claims(claims: list[dict], max_prioritized_claims_total: int | None = None) -> tuple[list[dict], list[dict], list[dict]]:
    limit = max_prioritized_claims_total or MAX_PRIORITIZED_CLAIMS_TOTAL
    per_document_limit = MAX_PRIORITIZED_CLAIMS_PER_DOCUMENT
    enriched_claims = [prioritize_claim(claim, limit) for claim in claims]
    candidate_claims = [claim for claim in enriched_claims if claim["main_analysis"] == "true"]
    sorted_candidates = sorted(
        candidate_claims,
        key=lambda row: (
            int(row.get("analytical_value_score", 0)),
            1 if str(row.get("claim_family", "")).strip().lower() in {"governance_ai", "other"} else 0,
            row.get("normalized_claim_id", ""),
        ),
        reverse=True,
    )
    prioritized_claims = select_prioritized_claims(sorted_candidates, limit, per_document_limit)
    prioritized_ids = {claim["normalized_claim_id"] for claim in prioritized_claims}
    selected_counts_by_document: dict[str, int] = {}
    for claim in prioritized_claims:
        document_id = get_primary_document_id(claim)
        selected_counts_by_document[document_id] = selected_counts_by_document.get(document_id, 0) + 1
    excluded_claims = []

    for claim in enriched_claims:
        if claim["normalized_claim_id"] in prioritized_ids:
            claim["main_analysis"] = "true"
            claim["exclusion_reason"] = ""
            continue

        if claim["main_analysis"] == "true":
            claim["main_analysis"] = "false"
            document_id = get_primary_document_id(claim)
            if selected_counts_by_document.get(document_id, 0) >= per_document_limit:
                claim["exclusion_reason"] = "below_per_document_priority_cap"
            else:
                claim["exclusion_reason"] = "below_main_analysis_priority_cap"

        excluded_claims.append(claim)

    return enriched_claims, prioritized_claims, excluded_claims
