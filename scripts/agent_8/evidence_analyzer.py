import csv
csv.field_size_limit(10**7)
import hashlib
import json
from pathlib import Path
from typing import Literal
from urllib import request
import re

from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "prioritized_claims.csv"
RANKED_EVIDENCE_CSV = PROJECT_ROOT / "data" / "processed" / "agent_7" / "ranked_evidence.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_8" / "claim_assessments.csv"
CACHE_JSON = PROJECT_ROOT / "data" / "processed" / "agent_8" / "assessment_cache.json"
LOCAL_MODEL = "qwen2.5:14b"
TOP_K_EVIDENCE = 3
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


class ClaimAssessment(BaseModel):
    normalized_claim_id: str
    final_label: Literal[
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "UNVERIFIED",
        "PARTIALLY_CONTRADICTED",
        "CONTRADICTED",
    ]
    greenwashing_risk_level: Literal["LOW", "MEDIUM", "HIGH", "UNCLEAR"]
    evidence_relevance: Literal["DIRECT", "INDIRECT", "BACKGROUND", "UNRELATED"]
    justification: str
    risk_reasoning: str
    top_evidence_url: str
    top_evidence_title: str
    supporting_excerpt: str


VALID_LABELS = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNVERIFIED",
    "PARTIALLY_CONTRADICTED",
    "CONTRADICTED",
}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "UNCLEAR"}
VALID_EVIDENCE_RELEVANCE = {"DIRECT", "INDIRECT", "BACKGROUND", "UNRELATED"}


def load_csv_rows(csv_path: Path) -> list[dict]:
    """Load rows from a CSV file."""
    rows = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def build_claim_lookup(claims: list[dict]) -> dict:
    """Map normalized claim ids to claims."""
    lookup = {}

    for claim in claims:
        lookup[claim["normalized_claim_id"]] = claim

    return lookup


def group_top_evidence(rows: list[dict], top_k: int) -> dict:
    """Group top-k evidence rows by normalized claim id."""
    grouped = {}

    for row in rows:
        claim_id = row["normalized_claim_id"]

        if claim_id not in grouped:
            grouped[claim_id] = []

        grouped[claim_id].append(row)

    top_grouped = {}

    for claim_id, evidence_rows in grouped.items():
        sorted_rows = sorted(
            evidence_rows,
            key=lambda item: int(item["evidence_rank"]),
        )
        top_grouped[claim_id] = sorted_rows[:top_k]

    return top_grouped


def build_evidence_block(evidence_rows: list[dict]) -> str:
    """Create a readable evidence block for the prompt."""
    blocks = []

    for index, row in enumerate(evidence_rows, start=1):
        extracted_text = row.get("extracted_text", "").strip()

        if len(extracted_text) > 2500:
            extracted_text = extracted_text[:2500]

        block = f"""
Evidence {index}
Title: {row.get('title', '')}
URL: {row.get('url', '')}
Query type: {row.get('query_type', '')}
Relevance score: {row.get('relevance_score', '')}
Snippet: {row.get('snippet', '')}
Extracted text:
{extracted_text}
""".strip()
        blocks.append(block)

    return "\n\n".join(blocks)


def build_cache_key(claim: dict, evidence_rows: list[dict]) -> str:
    """Build a stable key from claim text and selected evidence."""
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
    """Load cached assessments if available."""
    if not cache_path.exists():
        return {}

    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_assessment_cache(cache: dict, cache_path: Path) -> None:
    """Save cached assessments for future runs."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def build_prompt(claim: dict, evidence_rows: list[dict]) -> str:
    """Build the analysis prompt for one claim."""
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

Definitions:

- SUPPORTED:
  the external evidence clearly supports the main substance of the claim

- PARTIALLY_SUPPORTED:
  the evidence supports only part of the claim, or supports it with important limitations, uncertainty, or missing scope

- UNVERIFIED:
  the evidence does not provide enough specific external support to confirm or challenge the claim

- PARTIALLY_CONTRADICTED:
  the evidence conflicts with part of the claim, or raises a direct tension with an important part of the claim, but does not fully contradict the whole claim

- CONTRADICTED:
  the evidence clearly conflicts with the claim

Greenwashing risk guidance:

- LOW:
  the claim is well substantiated and the evidence does not raise important caveats

- MEDIUM:
  the claim may be factually true or partly supported, but the evidence raises limitations, missing context, methodology caveats, or selective framing concerns

- HIGH:
  the evidence raises serious concerns such as materially higher real-world emissions, misleading accounting choices, contradiction between ambition and performance, or strong external criticism

- UNCLEAR:
  the evidence is too weak, unrelated, or insufficient to assess greenwashing risk

Evidence relevance guidance:

- DIRECT:
  the evidence directly discusses the same company, topic, metric, mechanism, or methodology as the claim

- INDIRECT:
  the evidence discusses the same company and a closely related topic, but not the exact metric or mechanism

- BACKGROUND:
  the evidence gives broader company or sector context, but does not directly assess the claim

- UNRELATED:
  the evidence is not meaningfully about the claim, even if it mentions the company or sustainability generally

Important rules:
- use only the evidence provided here
- do not invent missing facts
- if the evidence is weak or unrelated, prefer UNVERIFIED over contradiction labels
- only use CONTRADICTED if there is clear conflict
- use PARTIALLY_CONTRADICTED when there is direct partial conflict or strong tension, but not enough to say the whole claim is false
- use PARTIALLY_SUPPORTED only when the evidence clearly supports a specific part of the claim
- if the evidence is only thematically related but does not really confirm the claim, use UNVERIFIED
- a claim can be UNVERIFIED and still have MEDIUM or HIGH greenwashing risk if the evidence provides relevant risk context
- for quantitative claims with specific values, use SUPPORTED only when the evidence confirms the specific values or a clearly equivalent table
- for quantitative claims with specific values, use PARTIALLY_SUPPORTED only when the evidence confirms at least one specific value, year, scope, or directly comparable number from the claim
- contextual risk evidence alone does not support a specific numerical claim; keep the final_label UNVERIFIED and capture the concern in greenwashing_risk_level and risk_reasoning
- do not mark risk HIGH just because exact numbers are missing; HIGH requires a substantive concern in the evidence
- if evidence_relevance is UNRELATED, set greenwashing_risk_level to UNCLEAR
- if evidence_relevance is BACKGROUND, do not set greenwashing_risk_level higher than MEDIUM
- only set greenwashing_risk_level to HIGH when evidence_relevance is DIRECT or clearly INDIRECT and the evidence raises a serious claim-specific concern
- general criticism of the company does not justify HIGH risk for a narrow methodological claim unless it addresses the same mechanism or reporting boundary
- keep the justification short and concrete
- keep risk_reasoning short and focused on greenwashing-risk context
- the supporting excerpt should be copied from the best evidence, not paraphrased heavily
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
    """Call the local Ollama API and return raw text."""
    payload = {
        "model": LOCAL_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})

    with request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


def is_ollama_available() -> bool:
    """Check whether Ollama is reachable before overwriting outputs."""
    try:
        with request.urlopen(OLLAMA_TAGS_URL, timeout=5):
            return True
    except Exception:
        return False


def normalize_label(label: str) -> str:
    """Normalize the model label before validation."""
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

    if label in replacements:
        return replacements[label]

    return label


def normalize_risk_level(risk_level: str) -> str:
    """Normalize model risk labels before validation."""
    risk_level = str(risk_level).strip().upper()
    risk_level = re.sub(r"\s+", "_", risk_level)

    replacements = {
        "LOW_RISK": "LOW",
        "MEDIUM_RISK": "MEDIUM",
        "MODERATE": "MEDIUM",
        "MODERATE_RISK": "MEDIUM",
        "HIGH_RISK": "HIGH",
        "UNKNOWN": "UNCLEAR",
        "INSUFFICIENT": "UNCLEAR",
        "INSUFFICIENT_EVIDENCE": "UNCLEAR",
    }

    return replacements.get(risk_level, risk_level)


def normalize_evidence_relevance(evidence_relevance: str) -> str:
    """Normalize model evidence relevance labels before validation."""
    evidence_relevance = str(evidence_relevance).strip().upper()
    evidence_relevance = re.sub(r"\s+", "_", evidence_relevance)

    replacements = {
        "DIRECTLY_RELEVANT": "DIRECT",
        "PARTLY_DIRECT": "INDIRECT",
        "PARTIAL": "INDIRECT",
        "PARTIALLY_RELEVANT": "INDIRECT",
        "CONTEXT": "BACKGROUND",
        "CONTEXTUAL": "BACKGROUND",
        "GENERAL_BACKGROUND": "BACKGROUND",
        "NOT_RELEVANT": "UNRELATED",
        "IRRELEVANT": "UNRELATED",
        "NO_RELEVANCE": "UNRELATED",
    }

    return replacements.get(evidence_relevance, evidence_relevance)


def enforce_risk_relevance_rules(data: dict) -> dict:
    """Apply deterministic guardrails if the model violates risk/relevance rules."""
    relevance = normalize_evidence_relevance(data.get("evidence_relevance", "UNRELATED"))
    risk_level = normalize_risk_level(data.get("greenwashing_risk_level", "UNCLEAR"))

    if relevance not in VALID_EVIDENCE_RELEVANCE:
        relevance = "UNRELATED"

    if risk_level not in VALID_RISK_LEVELS:
        risk_level = "UNCLEAR"

    if relevance == "UNRELATED":
        risk_level = "UNCLEAR"
    elif relevance == "BACKGROUND" and risk_level == "HIGH":
        risk_level = "MEDIUM"

    data["evidence_relevance"] = relevance
    data["greenwashing_risk_level"] = risk_level
    return data


def coerce_model_output(data: dict) -> dict:
    """Coerce common malformed model output into the expected schema."""
    data["final_label"] = normalize_label(data.get("final_label", "UNVERIFIED"))

    if data["final_label"] not in VALID_LABELS:
        data["final_label"] = "UNVERIFIED"

    data = enforce_risk_relevance_rules(data)

    for field in [
        "normalized_claim_id",
        "justification",
        "risk_reasoning",
        "top_evidence_url",
        "top_evidence_title",
        "supporting_excerpt",
    ]:
        if data.get(field) is None:
            data[field] = ""

    return data


def clean_supporting_excerpt(text: str) -> str:
    """Remove clearly invalid or contaminated excerpt text."""
    text = str(text).strip()

    if not text:
        return ""

    if "<system-reminder>" in text.lower():
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > 600:
        text = text[:600].strip()

    return text


def clean_generated_text(text: str, max_length: int | None = None) -> str:
    """Remove runtime contamination from generated text fields."""
    text = str(text).strip()

    if not text:
        return ""

    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if max_length and len(text) > max_length:
        text = text[:max_length].strip()

    return text


def parse_model_output(raw_text: str) -> ClaimAssessment:
    """Parse the Ollama response into the Pydantic schema."""
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "")
        raw_text = raw_text.replace("```", "")
        raw_text = raw_text.strip()

    data = json.loads(raw_text)

    data = coerce_model_output(data)

    if "supporting_excerpt" in data:
        data["supporting_excerpt"] = clean_supporting_excerpt(data["supporting_excerpt"])

    if "justification" in data:
        data["justification"] = clean_generated_text(data["justification"], max_length=900)

    if "risk_reasoning" in data:
        data["risk_reasoning"] = clean_generated_text(data["risk_reasoning"], max_length=900)

    return ClaimAssessment.model_validate(data)


def analyze_claim(claim: dict, evidence_rows: list[dict]) -> ClaimAssessment:
    """Run the model for one claim and its top evidence."""
    prompt = build_prompt(claim, evidence_rows)
    raw_response = call_ollama(prompt)
    return parse_model_output(raw_response)


def assessment_to_row(response: ClaimAssessment, claim: dict) -> dict:
    """Convert a parsed assessment to the output row format."""
    return {
        "normalized_claim_id": response.normalized_claim_id,
        "claim_text": claim["claim_text"],
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
    """Analyze all claims that have reranked evidence."""
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
            print(f"Using cached assessment for {claim_id}...")
            continue

        print(f"Analyzing {claim_id}...")
        cache_misses += 1

        try:
            response = analyze_claim(claim, evidence_rows)
            row = assessment_to_row(response, claim)
            assessments.append(row)
            cache[cache_key] = row
        except Exception as error:
            print(f"Error analyzing {claim_id}: {error}")
            assessments.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim["claim_text"],
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

    print(f"Assessment cache hits: {cache_hits}")
    print(f"Assessment cache misses: {cache_misses}")

    return assessments


def save_assessments_csv(rows: list[dict], output_path: Path) -> None:
    """Save final claim assessments to CSV."""
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
                "supporting_excerpt",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main() -> None:
    if not CLAIMS_CSV.exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not RANKED_EVIDENCE_CSV.exists():
        print(f"Ranked evidence CSV not found: {RANKED_EVIDENCE_CSV}")
        return

    if not is_ollama_available():
        print("Ollama is not reachable. Start it with `ollama serve` before running Agent 8.")
        print("Existing claim assessments were left unchanged.")
        return

    print("Loading normalized claims...")
    claims = load_csv_rows(CLAIMS_CSV)
    claim_lookup = build_claim_lookup(claims)

    print("Loading ranked evidence...")
    ranked_evidence = load_csv_rows(RANKED_EVIDENCE_CSV)
    grouped_evidence = group_top_evidence(ranked_evidence, TOP_K_EVIDENCE)

    print("Analyzing claims against evidence...")
    cache = load_assessment_cache(CACHE_JSON)
    assessments = analyze_all_claims(claim_lookup, grouped_evidence, cache)
    save_assessment_cache(cache, CACHE_JSON)

    save_assessments_csv(assessments, OUTPUT_CSV)

    print(f"Claim assessments created: {len(assessments)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
