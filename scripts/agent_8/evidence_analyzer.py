import csv
import json
from pathlib import Path
from typing import Literal
from urllib import request
import re

from pydantic import BaseModel


CLAIMS_CSV = "data/processed/agent_3/normalized_claims.csv"
RANKED_EVIDENCE_CSV = "data/processed/agent_7/ranked_evidence.csv"
OUTPUT_CSV = "data/processed/agent_8/claim_assessments.csv"
LOCAL_MODEL = "qwen2.5:14b"
TOP_K_EVIDENCE = 3
OLLAMA_URL = "http://localhost:11434/api/generate"


class ClaimAssessment(BaseModel):
    normalized_claim_id: str
    final_label: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED"]
    justification: str
    top_evidence_url: str
    top_evidence_title: str
    supporting_excerpt: str


VALID_LABELS = {"SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED"}


def load_csv_rows(csv_path: str) -> list[dict]:
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


def build_prompt(claim: dict, evidence_rows: list[dict]) -> str:
    """Build the analysis prompt for one claim."""
    evidence_block = build_evidence_block(evidence_rows)

    return f"""
You are analyzing a corporate CSR claim against external evidence.

Your task:
Read the claim and the evidence below and assign exactly one final label.

Allowed labels:
- SUPPORTED
- PARTIALLY_SUPPORTED
- UNSUPPORTED
- CONTRADICTED

Definitions:

- SUPPORTED:
  the external evidence clearly supports the main substance of the claim

- PARTIALLY_SUPPORTED:
  the evidence supports only part of the claim, or supports it with important limitations, uncertainty, or missing scope

- UNSUPPORTED:
  the evidence does not provide enough support to confirm the claim

- CONTRADICTED:
  the evidence clearly conflicts with the claim

Important rules:
- use only the evidence provided here
- do not invent missing facts
- if the evidence is weak or unrelated, prefer UNSUPPORTED over CONTRADICTED
- only use CONTRADICTED if there is clear conflict
- use PARTIALLY_SUPPORTED only when the evidence clearly supports a specific part of the claim
- if the evidence is only thematically related but does not really confirm the claim, use UNSUPPORTED
- keep the justification short and concrete
- the supporting excerpt should be copied from the best evidence, not paraphrased heavily
- return valid JSON only

Return exactly one JSON object with these fields:
- normalized_claim_id
- final_label
- justification
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


def normalize_label(label: str) -> str:
    """Normalize the model label before validation."""
    label = str(label).strip().upper()
    label = re.sub(r"\s+", "_", label)

    replacements = {
        "PARTIAL": "PARTIALLY_SUPPORTED",
        "PARTIALLYSUPPORTED": "PARTIALLY_SUPPORTED",
        "PARTIALLY SUPPORTED": "PARTIALLY_SUPPORTED",
        "UNSUPPORTED": "UNSUPPORTED",
        "SUPPORTED": "SUPPORTED",
        "CONTRADICTED": "CONTRADICTED",
    }

    if label in replacements:
        return replacements[label]

    return label


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


def parse_model_output(raw_text: str) -> ClaimAssessment:
    """Parse the Ollama response into the Pydantic schema."""
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "")
        raw_text = raw_text.replace("```", "")
        raw_text = raw_text.strip()

    data = json.loads(raw_text)

    if "final_label" in data:
        data["final_label"] = normalize_label(data["final_label"])

    if "supporting_excerpt" in data:
        data["supporting_excerpt"] = clean_supporting_excerpt(data["supporting_excerpt"])

    return ClaimAssessment.model_validate(data)


def analyze_claim(claim: dict, evidence_rows: list[dict]) -> ClaimAssessment:
    """Run the model for one claim and its top evidence."""
    prompt = build_prompt(claim, evidence_rows)
    raw_response = call_ollama(prompt)
    return parse_model_output(raw_response)


def analyze_all_claims(claim_lookup: dict, grouped_evidence: dict) -> list[dict]:
    """Analyze all claims that have reranked evidence."""
    assessments = []

    for claim_id, claim in claim_lookup.items():
        evidence_rows = grouped_evidence.get(claim_id, [])

        if not evidence_rows:
            assessments.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim["claim_text"],
                    "final_label": "UNSUPPORTED",
                    "justification": "No external evidence was available for this claim.",
                    "top_evidence_url": "",
                    "top_evidence_title": "",
                    "supporting_excerpt": "",
                }
            )
            continue

        print(f"Analyzing {claim_id}...")

        try:
            response = analyze_claim(claim, evidence_rows)
            assessments.append(
                {
                    "normalized_claim_id": response.normalized_claim_id,
                    "claim_text": claim["claim_text"],
                    "final_label": response.final_label,
                    "justification": response.justification,
                    "top_evidence_url": response.top_evidence_url,
                    "top_evidence_title": response.top_evidence_title,
                    "supporting_excerpt": response.supporting_excerpt,
                }
            )
        except Exception as error:
            print(f"Error analyzing {claim_id}: {error}")
            assessments.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim["claim_text"],
                    "final_label": "UNSUPPORTED",
                    "justification": f"Automatic analysis failed: {error}",
                    "top_evidence_url": "",
                    "top_evidence_title": "",
                    "supporting_excerpt": "",
                }
            )

    return assessments


def save_assessments_csv(rows: list[dict], output_path: str) -> None:
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
                "justification",
                "top_evidence_url",
                "top_evidence_title",
                "supporting_excerpt",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main() -> None:
    if not Path(CLAIMS_CSV).exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not Path(RANKED_EVIDENCE_CSV).exists():
        print(f"Ranked evidence CSV not found: {RANKED_EVIDENCE_CSV}")
        return

    print("Loading normalized claims...")
    claims = load_csv_rows(CLAIMS_CSV)
    claim_lookup = build_claim_lookup(claims)

    print("Loading ranked evidence...")
    ranked_evidence = load_csv_rows(RANKED_EVIDENCE_CSV)
    grouped_evidence = group_top_evidence(ranked_evidence, TOP_K_EVIDENCE)

    print("Analyzing claims against evidence...")
    assessments = analyze_all_claims(claim_lookup, grouped_evidence)

    save_assessments_csv(assessments, OUTPUT_CSV)

    print(f"Claim assessments created: {len(assessments)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
