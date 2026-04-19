import csv
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel


INPUT_CSV = "../../data/processed/agent_3/normalized_claims.csv"
OUTPUT_CSV = "../../data/processed/agent_4/queries.csv"
LOCAL_MODEL = "mistral-nemo:latest"
DOCUMENT_NAME = "Microsoft Environmental Sustainability Report"


class QueryItem(BaseModel):
    normalized_claim_id: str
    query_type: Literal["core", "verification", "critical"]
    query_text: str


class QueryList(BaseModel):
    queries: list[QueryItem]


def load_claims(csv_path: str) -> list[dict]:
    """Load normalized claims from Agent 3."""
    claims = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            claims.append(row)

    return claims


def build_prompt(claim: dict) -> str:
    """Build a simple prompt for one normalized claim."""
    return f"""
You are generating web search queries for external evidence retrieval.

Your task:
Given one corporate CSR claim, generate exactly 3 search queries.

The 3 query types must be:
1. core
2. verification
3. critical

Definitions:

- core:
  a direct search query that captures the main content of the claim in a concise way

- verification:
  a query designed to retrieve independent or third-party evidence that could confirm, validate, or discuss the claim

- critical:
  a query designed to retrieve criticism, controversy, contradiction, lawsuits, investigations, complaints, or possible greenwashing signals related to the claim

Rules:
- include the company name in every query
- keep each query short and natural for web search
- do not make the queries too broad
- do not simply copy the full claim if it is too long
- focus on the key searchable concepts
- the verification query should favor third-party or independent evidence
- the critical query should explicitly search for possible challenge or criticism
- generate exactly one query for each type
- return the result in structured format

Claim information:
- normalized_claim_id: {claim['normalized_claim_id']}
- document_name: {DOCUMENT_NAME}
- claim_text: {claim['claim_text']}
- claim_type: {claim['claim_type']}
- topic: {claim['topic']}
""".strip()


def generate_queries_for_claim(llm, claim: dict) -> list[QueryItem]:
    """Generate 3 queries for one claim."""
    structured_llm = llm.with_structured_output(QueryList)
    prompt = build_prompt(claim)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response.queries


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

    return all_queries


def save_queries_csv(queries: list[dict], output_path: str) -> None:
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
    if not Path(INPUT_CSV).exists():
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
