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
    is_verifiable: bool
    is_reporting_claim: bool
    claim_quality_score: Literal[0, 1, 2, 3, 4]
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
Extract only strong, specific, official claims made by the company that are useful for later credibility analysis.

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
- the company says it has maintained carbon neutrality
- the company says it applies carbon credits under specific conditions

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

Reporting or methodology statements:
Do not extract statements whose main purpose is only to describe:
- how data is reported
- how tables are organized
- what a section contains
- the existence of assurance or review work
- accounting methodology
- recalculation notes
- presentation format
- management criteria
- reporting boundaries explained only as technical disclosure language

Exception:
Only extract a reporting-related statement if it is itself an important governance, assurance, or verification claim that could matter for credibility analysis.

Important rule:
If you are unsure whether something is a real claim, do not extract it.
Prefer fewer high-quality claims over many noisy ones.

Future claims:
If the claim is mainly about a future target, future ambition, or future plan, mark `is_future` as true.

Verifiability:
Set `is_verifiable` to true only if the claim is concrete enough that an external source could reasonably support or challenge it.
Set `is_verifiable` to false if the statement is mainly methodological, presentational, vague, or not realistically checkable.

Reporting-claim classification:
Set `is_reporting_claim` to true if the statement is mainly about disclosure format, assurance, accounting methodology, data presentation, or reporting process.
Set `is_reporting_claim` to false for substantive operational, policy, practice, result, governance, labor, ethics, supply-chain, or commitment claims.
Claim quality rubric:
For each extracted claim, assign a `claim_quality_score` from 0 to 4 using this rubric:

- 0:
  not a valid claim
  the text is not really a company claim, or is too fragmentary, decorative, irrelevant, or purely reporting noise

- 1:
  very weak claim
  the text is mostly vague, methodological, presentational, or low-value for later analysis

- 2:
  borderline claim
  the text may contain a claim, but it is too broad, weakly specific, weakly attributable, or difficult to verify

- 3:
  solid claim
  the text is a real company claim, reasonably specific, substantive, and useful for later verification

- 4:
  strong claim
  the text is a clear, specific, substantive, attributable company claim and is highly useful for later verification or external comparison

When assigning `claim_quality_score`, consider these criteria:

1. Company statement:
Is this clearly presented as a statement about what the company does, has done, requires, reports, or commits to?

2. Specificity:
Is the statement specific enough to stand on its own, rather than vague or generic?

3. Substantiveness:
Is it about an actual policy, action, result, requirement, commitment, or governance practice, rather than formatting or presentation?

4. Verifiability:
Could this claim reasonably be supported or challenged later with internal or external evidence?

5. Analytical usefulness:
Would this claim be useful for later credibility or greenwashing analysis?

Scoring guidance:
- Score 4 if nearly all criteria are strongly satisfied.
- Score 3 if most criteria are satisfied.
- Score 2 if the claim is plausible but borderline.
- Score 1 if it is weak and low-value.
- Score 0 if it should not really count as a claim.

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
                    "is_verifiable": claim.is_verifiable,
                    "claim_quality_score": claim.claim_quality_score,
                    "is_reporting_claim": claim.is_reporting_claim,
                    "topic": claim.topic,
                    "is_future": claim.is_future,
                    "source_excerpt": claim.source_excerpt,
                }
            )
            claim_id += 1
        
    filtered_claims = []

    for claim in all_claims:
        if not claim['is_verifiable']:
            continue
        if claim['claim_quality_score'] < 3:
            continue
        if claim['is_reporting_claim']:
            continue
        
        filtered_claims.append(claim)

        

    return filtered_claims


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
                "is_verifiable",
                "claim_quality_score",
                "is_reporting_claim",
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
    pages = load_pages(INPUT_CSV)[1:4]

    print("Extracting claims...")
    claims = extract_claims_from_pages(pages)

    save_claims_csv(claims, OUTPUT_CSV)

    print(f"Claims extracted: {len(claims)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()