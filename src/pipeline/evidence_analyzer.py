from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Literal
from urllib import request

from pydantic import BaseModel

from src.pipeline._io import read_csv_rows, write_csv_rows


LOCAL_MODEL = "qwen2.5:14b"
TOP_K_EVIDENCE = 3
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


class ClaimAssessment(BaseModel):
    """Structured judgment for one claim/evidence bundle."""

    normalized_claim_id: str
    final_label: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNVERIFIED", "PARTIALLY_CONTRADICTED", "CONTRADICTED"]
    greenwashing_risk_level: Literal["LOW", "MEDIUM", "HIGH", "UNCLEAR"]
    evidence_relevance: Literal["DIRECT", "INDIRECT", "BACKGROUND", "UNRELATED"]
    justification: str
    risk_reasoning: str
    top_evidence_url: str
    top_evidence_title: str
    supporting_excerpt: str


VALID_LABELS = {"SUPPORTED", "PARTIALLY_SUPPORTED", "UNVERIFIED", "PARTIALLY_CONTRADICTED", "CONTRADICTED"}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "UNCLEAR"}
VALID_EVIDENCE_RELEVANCE = {"DIRECT", "INDIRECT", "BACKGROUND", "UNRELATED"}
CONTRADICTION_LABELS = {"PARTIALLY_CONTRADICTED", "CONTRADICTED"}


def load_csv_rows(csv_path: Path) -> list[dict]:
    """Load evidence or claim rows from disk."""

    return read_csv_rows(csv_path)


def build_claim_lookup(claims: list[dict]) -> dict:
    """Index normalized claims by claim id."""

    return {claim["normalized_claim_id"]: claim for claim in claims}


def group_top_evidence(rows: list[dict], top_k: int) -> dict:
    """Keep the top evidence rows for each claim."""

    grouped = {}
    for row in rows:
        claim_id = row["normalized_claim_id"]
        grouped.setdefault(claim_id, []).append(row)

    top_grouped = {}
    for claim_id, evidence_rows in grouped.items():
        sorted_rows = sorted(evidence_rows, key=lambda item: int(item.get("evidence_rank", 999)))
        top_grouped[claim_id] = sorted_rows[:top_k]
    return top_grouped


def build_evidence_block(evidence_rows: list[dict]) -> str:
    """Format evidence rows into the prompt payload."""

    blocks = []
    for index, row in enumerate(evidence_rows, start=1):
        extracted_text = row.get("extracted_text", "").strip()
        if len(extracted_text) > 2500:
            extracted_text = extracted_text[:2500]

        blocks.append(
            f"""
Evidence {index}
Title: {row.get('title', '')}
URL: {row.get('url', '')}
Query type: {row.get('query_type', '')}
Relevance score: {row.get('relevance_score', '')}
Snippet: {row.get('snippet', '')}
Extracted text:
{extracted_text}
""".strip()
        )

    return "\n\n".join(blocks)


def build_cache_key(claim: dict, evidence_rows: list[dict]) -> str:
    """Create a stable cache key for one assessment."""

    key_payload = {
        "schema_version": "priority_labels_v1",
        "claim_text": claim.get("claim_text", ""),
        "claim_type": claim.get("claim_type", ""),
        "topic": claim.get("topic", ""),
        "evidence": [
            {
                "url": row.get("url", ""),
                "title": row.get("title", ""),
                "query_type": row.get("query_type", ""),
                "relevance_score": row.get("relevance_score", ""),
                "text_sample": row.get("extracted_text", "")[:1000],
            }
            for row in evidence_rows
        ],
    }
    serialized = json.dumps(key_payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_assessment_cache(cache_path: Path) -> dict:
    """Load cached claim assessments from disk."""

    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_assessment_cache(cache: dict, cache_path: Path) -> None:
    """Persist the assessment cache to disk."""

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def is_ollama_available() -> bool:
    """Check whether the local Ollama service is available."""

    try:
        with request.urlopen(OLLAMA_TAGS_URL, timeout=5):
            return True
    except Exception:
        return False


def build_prompt(claim: dict, evidence_rows: list[dict]) -> str:
    """Build the assessment prompt for one claim."""

    evidence_block = build_evidence_block(evidence_rows)
    return f"""
You are analyzing a corporate CSR claim against external evidence.

Your task:
Read the claim and the evidence below and assign exactly one final label.
Also assign a greenwashing risk level based on whether the evidence raises useful concerns, caveats, or contextual risks.
Also assign evidence relevance, which measures whether the selected evidence is actually about the specific claim.

Allowed labels:
- SUPPORTED
- PARTIALLY_SUPPORTED
- UNVERIFIED
- PARTIALLY_CONTRADICTED
- CONTRADICTED

Allowed greenwashing risk levels:
- LOW
- MEDIUM
- HIGH
- UNCLEAR

Allowed evidence relevance values:
- DIRECT
- INDIRECT
- BACKGROUND
- UNRELATED

Important rules:
- use only the evidence provided here
- do not invent missing facts
- if the evidence is weak or unrelated, prefer UNVERIFIED over contradiction labels
- only use PARTIALLY_CONTRADICTED or CONTRADICTED when the evidence directly addresses the same claim, scope, metric, year, boundary, or definition and clearly conflicts with it
- evidence about controversy, criticism, strategy changes, partnerships, emissions growth, or general reputation does not by itself contradict a specific claim
- for methodology, definition, scope, inventory, boundary, or reporting-process claims, evidence about bad outcomes or criticism does not count as contradiction unless it directly disproves the stated method or definition
- if the evidence only raises caution or context, prefer PARTIALLY_SUPPORTED or UNVERIFIED instead of contradiction labels
- if evidence_relevance is UNRELATED, set greenwashing_risk_level to UNCLEAR
- if evidence_relevance is BACKGROUND, do not set greenwashing_risk_level higher than MEDIUM
- if evidence_relevance is INDIRECT or BACKGROUND, do not use contradiction labels
- only set greenwashing_risk_level to HIGH when evidence_relevance is DIRECT or clearly INDIRECT and the evidence raises a serious claim-specific concern
- keep the justification short and concrete
- keep risk_reasoning short and focused on greenwashing-risk context
- return valid JSON only

Return exactly one JSON object with these fields:
- normalized_claim_id
- final_label
- greenwashing_risk_level
- evidence_relevance
- justification
- risk_reasoning
- top_evidence_url
- top_evidence_title
- supporting_excerpt

Claim:
- normalized_claim_id: {claim['normalized_claim_id']}
- claim_text: {claim['claim_text']}
- claim_type: {claim['claim_type']}
- topic: {claim['topic']}

Evidence:
{evidence_block}
""".strip()


def call_ollama(prompt: str) -> str:
    """Send the assessment prompt to the local model."""

    payload = {"model": LOCAL_MODEL, "prompt": prompt, "stream": False, "format": "json"}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["response"]


def normalize_label(label: str) -> str:
    """Normalize model output into one of the supported labels."""

    label = str(label).strip().upper()
    label = re.sub(r"\s+", "_", label)
    replacements = {
        "PARTIAL": "PARTIALLY_SUPPORTED",
        "PARTIALLYSUPPORTED": "PARTIALLY_SUPPORTED",
        "PARTIALLY SUPPORTED": "PARTIALLY_SUPPORTED",
        "UN_SUPPORTED": "UNVERIFIED",
        "UNSUPORTED": "UNVERIFIED",
        "UNSUPPORTED": "UNVERIFIED",
        "NOT_SUPPORTED": "UNVERIFIED",
        "INSUFFICIENT": "UNVERIFIED",
        "INSUFFICIENT_EVIDENCE": "UNVERIFIED",
        "UNVERIFIED": "UNVERIFIED",
        "PARTIAL_CONTRADICTION": "PARTIALLY_CONTRADICTED",
        "PARTIALLY CONTRADICTED": "PARTIALLY_CONTRADICTED",
        "PARTIALLY_CONTRADICTED": "PARTIALLY_CONTRADICTED",
        "SUPPORTED": "SUPPORTED",
        "CONTRADICTED": "CONTRADICTED",
    }
    return replacements.get(label, label)


def normalize_risk_level(risk_level: str) -> str:
    """Normalize the risk label into the supported scale."""

    risk_level = str(risk_level).strip().upper()
    risk_level = re.sub(r"\s+", "_", risk_level)
    replacements = {"LOW_RISK": "LOW", "MEDIUM_RISK": "MEDIUM", "MODERATE": "MEDIUM", "MODERATE_RISK": "MEDIUM", "HIGH_RISK": "HIGH", "UNKNOWN": "UNCLEAR", "INSUFFICIENT": "UNCLEAR", "INSUFFICIENT_EVIDENCE": "UNCLEAR"}
    return replacements.get(risk_level, risk_level)


def normalize_evidence_relevance(evidence_relevance: str) -> str:
    """Normalize evidence relevance into the supported scale."""

    evidence_relevance = str(evidence_relevance).strip().upper()
    evidence_relevance = re.sub(r"\s+", "_", evidence_relevance)
    replacements = {"DIRECTLY_RELEVANT": "DIRECT", "PARTLY_DIRECT": "INDIRECT", "PARTIAL": "INDIRECT", "PARTIALLY_RELEVANT": "INDIRECT", "CONTEXT": "BACKGROUND", "CONTEXTUAL": "BACKGROUND", "GENERAL_BACKGROUND": "BACKGROUND", "NOT_RELEVANT": "UNRELATED", "IRRELEVANT": "UNRELATED", "NO_RELEVANCE": "UNRELATED"}
    return replacements.get(evidence_relevance, evidence_relevance)


def enforce_risk_relevance_rules(data: dict) -> dict:
    """Clamp risk labels when the relevance signal is weak."""

    relevance = normalize_evidence_relevance(data.get("evidence_relevance", "UNRELATED"))
    risk_level = normalize_risk_level(data.get("greenwashing_risk_level", "UNCLEAR"))
    if relevance not in VALID_EVIDENCE_RELEVANCE:
        relevance = "UNRELATED"
    if risk_level not in VALID_RISK_LEVELS:
        risk_level = "UNCLEAR"
    if relevance == "UNRELATED":
        risk_level = "UNCLEAR"
    elif relevance in {"INDIRECT", "BACKGROUND"} and risk_level == "HIGH":
        risk_level = "MEDIUM"
    elif relevance == "BACKGROUND" and risk_level == "HIGH":
        risk_level = "MEDIUM"
    elif relevance != "DIRECT" and risk_level == "HIGH":
        risk_level = "MEDIUM"
    data["evidence_relevance"] = relevance
    data["greenwashing_risk_level"] = risk_level
    return data


def is_methodology_claim_text(claim_text: str) -> bool:
    """Detect methodology-style claims that need stricter handling."""

    lowered = str(claim_text).lower()
    markers = [
        "defines",
        "definition",
        "criteria",
        "inventory includes",
        "calculates and reports",
        "uses an operational control approach",
        "reflects what is in scope",
        "published the criteria",
        "methodology",
        "boundary",
    ]
    return any(marker in lowered for marker in markers)


def enforce_label_relevance_rules(data: dict, claim_text: str) -> dict:
    """Prevent contradiction labels when the evidence is too indirect."""

    label = normalize_label(data.get("final_label", "UNVERIFIED"))
    relevance = normalize_evidence_relevance(data.get("evidence_relevance", "UNRELATED"))
    supporting_excerpt = clean_supporting_excerpt(data.get("supporting_excerpt", ""))

    if label in CONTRADICTION_LABELS and relevance != "DIRECT":
        data["final_label"] = "UNVERIFIED"
        return data

    if relevance in {"INDIRECT", "BACKGROUND"} and label not in {"SUPPORTED", "UNVERIFIED"}:
        data["final_label"] = "UNVERIFIED"
        return data

    if label in CONTRADICTION_LABELS and is_methodology_claim_text(claim_text) and not supporting_excerpt:
        data["final_label"] = "UNVERIFIED"
        return data

    data["final_label"] = label
    return data


def coerce_model_output(data: dict, claim_text: str) -> dict:
    """Clean and validate the raw model response."""

    data["final_label"] = normalize_label(data.get("final_label", "UNVERIFIED"))
    if data["final_label"] not in VALID_LABELS:
        data["final_label"] = "UNVERIFIED"
    data = enforce_risk_relevance_rules(data)
    data = enforce_label_relevance_rules(data, claim_text)
    for field in ["normalized_claim_id", "justification", "risk_reasoning", "top_evidence_url", "top_evidence_title", "supporting_excerpt"]:
        if data.get(field) is None:
            data[field] = ""
    return data


def clean_supporting_excerpt(text: str) -> str:
    """Trim and sanitize the excerpt copied into the report."""

    text = str(text).strip()
    if not text or "<system-reminder>" in text.lower():
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600].strip() if len(text) > 600 else text


def clean_generated_text(text: str, max_length: int | None = None) -> str:
    """Remove markup and extra noise from generated prose."""

    text = str(text).strip()
    if not text:
        return ""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_length and len(text) > max_length:
        text = text[:max_length].strip()
    return text


def parse_model_output(raw_text: str, claim_text: str) -> ClaimAssessment:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw_text)
    data = coerce_model_output(data, claim_text)
    if "supporting_excerpt" in data:
        data["supporting_excerpt"] = clean_supporting_excerpt(data["supporting_excerpt"])
    if "justification" in data:
        data["justification"] = clean_generated_text(data["justification"], max_length=900)
    if "risk_reasoning" in data:
        data["risk_reasoning"] = clean_generated_text(data["risk_reasoning"], max_length=900)
    return ClaimAssessment.model_validate(data)


def analyze_claim(claim: dict, evidence_rows: list[dict]) -> ClaimAssessment:
    prompt = build_prompt(claim, evidence_rows)
    raw_response = call_ollama(prompt)
    return parse_model_output(raw_response, claim.get("claim_text", ""))


def assessment_to_row(response: ClaimAssessment, claim: dict) -> dict:
    return {
        "normalized_claim_id": response.normalized_claim_id,
        "claim_text": claim["claim_text"],
        "claim_family": claim.get("claim_family", "other"),
        "final_label": response.final_label,
        "greenwashing_risk_level": response.greenwashing_risk_level,
        "evidence_relevance": response.evidence_relevance,
        "justification": clean_generated_text(response.justification, max_length=900),
        "risk_reasoning": clean_generated_text(response.risk_reasoning, max_length=900),
        "top_evidence_url": response.top_evidence_url,
        "top_evidence_title": response.top_evidence_title,
        "supporting_excerpt": clean_supporting_excerpt(response.supporting_excerpt),
    }


def analyze_all_claims(claim_lookup: dict, grouped_evidence: dict, cache: dict) -> list[dict]:
    assessments = []
    cache_hits = 0
    cache_misses = 0

    for claim_id, claim in claim_lookup.items():
        evidence_rows = grouped_evidence.get(claim_id, [])
        if not evidence_rows:
            assessments.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim["claim_text"],
                    "claim_family": claim.get("claim_family", "other"),
                    "final_label": "UNVERIFIED",
                    "greenwashing_risk_level": "UNCLEAR",
                    "evidence_relevance": "UNRELATED",
                    "justification": "No external evidence was available for this claim.",
                    "risk_reasoning": "No external evidence was available to assess greenwashing risk.",
                    "top_evidence_url": "",
                    "top_evidence_title": "",
                    "supporting_excerpt": "",
                }
            )
            continue

        cache_key = build_cache_key(claim, evidence_rows)
        if cache_key in cache:
            cached_row = cache[cache_key]
            cached_row["claim_text"] = claim["claim_text"]
            assessments.append(cached_row)
            cache_hits += 1
            continue

        cache_misses += 1
        try:
            response = analyze_claim(claim, evidence_rows)
            row = assessment_to_row(response, claim)
            assessments.append(row)
            cache[cache_key] = row
        except Exception as error:
            assessments.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim["claim_text"],
                    "claim_family": claim.get("claim_family", "other"),
                    "final_label": "UNVERIFIED",
                    "greenwashing_risk_level": "UNCLEAR",
                    "evidence_relevance": "UNRELATED",
                    "justification": f"Automatic analysis failed: {error}",
                    "risk_reasoning": "Automatic analysis failed, so greenwashing risk could not be assessed.",
                    "top_evidence_url": "",
                    "top_evidence_title": "",
                    "supporting_excerpt": "",
                }
            )

    return assessments


def save_assessments_csv(rows: list[dict], output_path: Path) -> None:
    write_csv_rows(
        rows,
        output_path,
        fieldnames=["normalized_claim_id", "claim_text", "final_label", "greenwashing_risk_level", "evidence_relevance", "justification", "risk_reasoning", "top_evidence_url", "top_evidence_title", "supporting_excerpt"],
    )
