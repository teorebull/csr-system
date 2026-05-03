import csv
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "prioritized_claims.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_4" / "queries.csv"
LOCAL_MODEL = "mistral-nemo:latest"
DOCUMENT_NAME = "Microsoft Environmental Sustainability Report"


class QueryItem(BaseModel):
    normalized_claim_id: str
    query_type: Literal[
        "verification",
        "contradiction",
        "criticism",
        "methodology",
        "context",
    ]
    query_text: str


class QueryList(BaseModel):
    queries: list[QueryItem]


def load_claims(csv_path: Path) -> list[dict]:
    """Load prioritized normalized claims from Agent 3."""
    claims = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            claims.append(row)

    return claims


def build_prompt(claim: dict) -> str:
    """Build a simple prompt for one normalized claim."""
    return f"""
You are generating web search queries for greenwashing-risk analysis.

Your task:
Given one corporate CSR claim, generate exactly 5 search queries.

The 5 query types must be:
1. verification
2. contradiction
3. criticism
4. methodology
5. context

Definitions:

- verification:
  finds factual evidence, datasets, reports, assurance statements, or independent discussion that can check the claim

- contradiction:
  finds evidence that could directly or indirectly challenge the claim, including rising emissions, missed targets, conflicting data, or weak performance

- criticism:
  finds credible external criticism, investigations, NGO analysis, media analysis, controversy, complaints, or greenwashing concerns

- methodology:
  finds information about accounting choices, boundaries, offsets, renewable energy certificates, market-based vs location-based emissions, scope exclusions, assurance, or measurement caveats

- context:
  finds broader context that helps a reasoning model judge whether the claim is complete or potentially misleading, such as trends over time, AI/datacenter growth, supply chain impacts, water use, waste, or absolute vs relative changes

Rules:
- include the company name in every query
- keep each query short and natural for web search
- do not make the queries too broad
- do not simply copy the full claim if it is too long
- focus on the key searchable concepts
- prefer useful, contrastable sources over exact-number-only fact checking
- for quantitative claims, keep the metric, scope, year range, and unit if useful
- for qualitative claims, search for external assessment, controversy, implementation evidence, and limitations
- do not assert a trend such as "rising" or "falling" unless it is clearly present in the claim
- if the claim is about market-based Scope 2 emissions, include accounting caveats such as location-based emissions, RECs, or renewable energy certificates
- if the claim is about total emissions or Scope 3 emissions, include supply chain, cloud, AI, or data center growth when useful
- for criticism queries, prefer concrete terms such as investigation, analysis, report, criticism, controversy, greenwashing, NGO, or media analysis
- do not use social media as a target source
- do not target company-owned pages only, but company reports may be useful when searching for methodology or assurance
- generate exactly one query for each type
- return the result in structured format

Good query style examples:
- Microsoft Scope 2 market-based emissions renewable energy certificates criticism
- Microsoft carbon negative claim data center AI emissions criticism
- Microsoft Scope 3 emissions supply chain growth sustainability analysis
- Microsoft emissions methodology market-based location-based assurance

Claim information:
- normalized_claim_id: {claim['normalized_claim_id']}
- document_name: {DOCUMENT_NAME}
- claim_text: {claim['claim_text']}
- claim_type: {claim['claim_type']}
- topic: {claim['topic']}
""".strip()


def generate_queries_for_claim(llm, claim: dict) -> list[QueryItem]:
    """Generate 5 queries for one claim."""
    structured_llm = llm.with_structured_output(QueryList)
    prompt = build_prompt(claim)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response.queries


def build_supplemental_queries(claim: dict) -> list[dict]:
    """Add deterministic searches for known hard cases."""
    claim_id = claim["normalized_claim_id"]
    claim_text = claim["claim_text"].lower()

    if "scope 2" not in claim_text:
        return []

    supplemental_queries = [
        (
            "verification",
            "Microsoft Scope 2 location-based market-based emissions FY20 FY24 data",
        ),
        (
            "verification",
            "Microsoft greenhouse gas emissions Scope 2 data Tracenable",
        ),
        (
            "verification",
            "Microsoft CDP Scope 2 location-based market-based emissions",
        ),
        (
            "methodology",
            "Microsoft Scope 2 market-based location-based emissions renewable energy certificates RECs",
        ),
        (
            "methodology",
            "Microsoft Scope 2 emissions GHG Protocol market-based location-based accounting",
        ),
        (
            "criticism",
            "Microsoft renewable energy certificates Scope 2 emissions greenwashing criticism",
        ),
        (
            "context",
            "Microsoft data centers electricity demand Scope 2 emissions location-based",
        ),
    ]

    return [
        {
            "normalized_claim_id": claim_id,
            "query_type": query_type,
            "query_text": query_text,
        }
        for query_type, query_text in supplemental_queries
    ]


def generate_queries_for_all_claims(claims: list[dict]) -> list[dict]:
    """Generate queries claim by claim and flatten them into rows."""
    llm = ChatOllama(model=LOCAL_MODEL, temperature=0.0)
    all_queries = []

    for claim in claims:
        claim_id = claim["normalized_claim_id"]
        claim_text = claim["claim_text"].strip()

        if not claim_text:
            continue

        print(f"Generating queries for {claim_id}...")

        try:
            queries = generate_queries_for_claim(llm, claim)
        except Exception as error:
            print(f"Error on {claim_id}: {error}")
            continue

        for query in queries:
            all_queries.append(
                {
                    "normalized_claim_id": claim_id,
                    "query_type": query.query_type,
                    "query_text": query.query_text,
                }
            )

        all_queries.extend(build_supplemental_queries(claim))

    return all_queries


def save_queries_csv(queries: list[dict], output_path: Path) -> None:
    """Save generated queries to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "query_type",
                "query_text",
            ],
        )
        writer.writeheader()

        for query in queries:
            writer.writerow(query)


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading normalized claims...")
    claims = load_claims(INPUT_CSV)

    print("Generating queries...")
    queries = generate_queries_for_all_claims(claims)

    save_queries_csv(queries, OUTPUT_CSV)

    print(f"Queries generated: {len(queries)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
