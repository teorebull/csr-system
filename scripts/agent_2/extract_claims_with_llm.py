import csv
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


MODEL_NAME = "qwen2.5:14b"
INPUT_CSV = "data/processed/agent_1/pymupdf/2025-Microsoft-Environmental-Data-Fact-Sheet-PDF_pages.csv"
OUTPUT_CSV = "data/processed/agent_2/claims.csv"
DOCUMENT_NAME = "Microsoft Environmental Sustainability Report"


class Claim(BaseModel):
    claim_text: str
    claim_type: Literal["result", "policy", "practice", "commitment", "statement"]
    topic: Literal[
        "environment",
        "climate",
        "emissions",
        "energy",
        "water",
        "waste",
        "ethics",
        "governance",
        "labor",
        "supply_chain",
        "social_impact",
        "other",
    ]
    is_future: bool
    source_excerpt: str


class ClaimList(BaseModel):
    claims: list[Claim]


def load_pages(csv_path: str) -> list[dict]:
    """Load the pages from the CSV file."""
    pages = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            pages.append(
                {
                    "page_number": row["page_number"],
                    "text": row["text"],
                }
            )

    return pages


def build_prompt(page_number: str, page_text: str) -> str:
    """Build the prompt for claim extraction."""
    return f"""
You are extracting CSR claims from an official corporate document.
Document: {DOCUMENT_NAME}
Page number: {page_number}
Your goal:

Extract only strong, specific, official claims made by the company.

Definition of a valid claim:
A claim is a concrete statement made by the company about its sustainability, environment, climate, ethics, governance, labor, supply chain, social impact, or corporate responsibility practices, policies, results, commitments, or actions.
A valid claim should usually include at least one of these:
- a company action
- a policy or governance rule
- a business practice
- a measurable result
- a target or commitment
- a requirement applied to operations or suppliers
- a statement that can be checked against external evidence

Good examples of claims:
- the company says it reduced emissions
- the company says it uses renewable electricity
- the company says suppliers must follow certain standards
- the company says it applies a policy, audit, governance measure, or ethical rule

Do NOT extract:
- section titles
- headings
- page furniture
- captions
- footnotes
- repeated headers or repeated boilerplate
- isolated keywords
- generic context about sustainability or climate
- vague branding language
- purely aspirational or decorative language
- incomplete text fragments
- statements that are too broad to verify
- background information not presented as the company's own claim

Important rule:
If you are unsure whether something is a real claim, do not extract it.
Future claims:
If the claim is mainly about a future target, future ambition, or future plan, mark `is_future` as true.
Verifiability:
Set `is_verifiable` to true only if the claim is concrete enough that an external source could reasonably support or challenge it.

Confidence:
Give a confidence score from 0.0 to 1.0.
Use low confidence for borderline cases.

Source excerpt:
`source_excerpt` must be copied exactly from the page text.
Do not paraphrase it.
Return the result in structured format.

Page text:

{page_text}

""".strip()


def extract_claims_from_page(llm, page_number: str, page_text: str) -> list[Claim]:
    """Extract claims from one page."""
    structured_llm = llm.with_structured_output(ClaimList)

    prompt = build_prompt(page_number, page_text)

    response = structured_llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return response.claims


def extract_claims_from_pages(pages: list[dict]) -> list[dict]:
    """Run the model page by page and collect all claims."""
    llm = ChatOllama(
        model=MODEL_NAME,
        temperature=0.1,
    )

    all_claims = []
    claim_id = 1

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"].strip()

        if not page_text or len(page_text) < 40:
            continue

        print(f"Processing page {page_number}...")

        try:
            claims = extract_claims_from_page(llm, page_number, page_text)
        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            continue

        for claim in claims:
            all_claims.append(
                {
                    "claim_id": f"claim_{claim_id}",
                    "document_name": DOCUMENT_NAME,
                    "page_number": page_number,
                    "claim_text": claim.claim_text,
                    "claim_type": claim.claim_type,
                    "topic": claim.topic,
                    "is_future": claim.is_future,
                    "source_excerpt": claim.source_excerpt,
                }
            )
            claim_id += 1

    return all_claims


def save_claims_csv(claims: list[dict], output_path: str) -> None:
    """Save the extracted claims to a CSV file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "claim_id",
                "document_name",
                "page_number",
                "claim_text",
                "claim_type",
                "topic",
                "is_future",
                "source_excerpt",
            ],
        )
        writer.writeheader()

        for claim in claims:
            writer.writerow(claim)


def main() -> None:
    if not Path(INPUT_CSV).exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading pages...")
    pages = load_pages(INPUT_CSV)[:5]

    print("Extracting claims...")
    claims = extract_claims_from_pages(pages)

    save_claims_csv(claims, OUTPUT_CSV)

    print(f"Claims extracted: {len(claims)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()