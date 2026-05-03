import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Literal
from urllib import request

from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


MODEL_NAME = "qwen2.5:14b"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_1" / "pymupdf" / "pages.csv"
LEGACY_INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_1" / "pymupdf" / "2025-Microsoft-Environmental-Data-Fact-Sheet-PDF_pages.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_2" / "claims.csv"
CACHE_JSON = PROJECT_ROOT / "data" / "processed" / "agent_2" / "claim_extraction_cache.json"
DOCUMENT_NAME = "Microsoft Environmental Sustainability Report"
DEFAULT_DOCUMENT_ID = "doc_1_2025-microsoft-environmental-data-fact-sheet-pdf"
PROMPT_SCHEMA_VERSION = "claim_extractor_v3_multi_document"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MAX_PAGES_PER_DOCUMENT = int(os.environ.get("MAX_PAGES_PER_DOCUMENT", "9"))
SKIP_FIRST_PAGE_PER_DOCUMENT = os.environ.get("SKIP_FIRST_PAGE_PER_DOCUMENT", "true").strip().lower() == "true"


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


def load_pages(csv_path: Path) -> list[dict]:
    """Load the pages from the CSV file."""
    pages = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            pages.append(
                {
                    "document_id": row.get("document_id", DEFAULT_DOCUMENT_ID),
                    "document_name": row.get("document_name", DOCUMENT_NAME),
                    "document_path": row.get("document_path", ""),
                    "page_number": row["page_number"],
                    "text": row["text"],
                }
            )

    return pages


def is_ollama_available() -> bool:
    """Check whether Ollama is reachable before making uncached LLM calls."""
    try:
        with request.urlopen(OLLAMA_TAGS_URL, timeout=5):
            return True
    except Exception:
        return False


def load_claim_cache(cache_path: Path) -> dict:
    """Load cached page-level claim extraction results."""
    if not cache_path.exists():
        return {}

    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_claim_cache(cache: dict, cache_path: Path) -> None:
    """Persist page-level claim extraction cache."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def build_cache_key(document_id: str, document_name: str, page_number: str, page_text: str) -> str:
    """Build a stable cache key for one document page."""
    payload = {
        "document_id": document_id,
        "document_name": document_name,
        "page_number": str(page_number),
        "page_text_hash": hashlib.sha256(page_text.encode("utf-8")).hexdigest(),
        "model_name": MODEL_NAME,
        "prompt_schema_version": PROMPT_SCHEMA_VERSION,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def claim_to_cache_row(claim: Claim) -> dict:
    """Convert a parsed claim into a JSON-serializable cache row."""
    return {
        "claim_text": claim.claim_text,
        "claim_type": claim.claim_type,
        "is_verifiable": claim.is_verifiable,
        "claim_quality_score": claim.claim_quality_score,
        "is_reporting_claim": claim.is_reporting_claim,
        "topic": claim.topic,
        "is_future": claim.is_future,
        "source_excerpt": claim.source_excerpt,
    }


def select_pages_for_extraction(pages: list[dict]) -> list[dict]:
    """Apply simple per-document page limits before LLM extraction."""
    grouped_pages = {}

    for page in pages:
        document_id = page.get("document_id", DEFAULT_DOCUMENT_ID)

        if document_id not in grouped_pages:
            grouped_pages[document_id] = []

        grouped_pages[document_id].append(page)

    selected_pages = []

    for document_id, document_pages in grouped_pages.items():
        sorted_pages = sorted(document_pages, key=lambda row: int(row.get("page_number", "0")))

        if SKIP_FIRST_PAGE_PER_DOCUMENT and len(sorted_pages) > 1:
            sorted_pages = sorted_pages[1:]

        if MAX_PAGES_PER_DOCUMENT > 0:
            sorted_pages = sorted_pages[:MAX_PAGES_PER_DOCUMENT]

        selected_pages.extend(sorted_pages)
        print(f"Pages selected for {document_id}: {len(sorted_pages)}")

    return selected_pages


def build_prompt(document_name: str, page_number: str, page_text: str) -> str:
    """Build the prompt for claim extraction."""
    return f"""
You are extracting CSR claims from an official corporate document.
Document: {document_name}
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


def extract_claims_from_page(llm, document_name: str, page_number: str, page_text: str) -> list[Claim]:
    """Extract claims from one page."""
    structured_llm = llm.with_structured_output(ClaimList)

    prompt = build_prompt(document_name, page_number, page_text)

    response = structured_llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return response.claims


def extract_claims_from_pages(pages: list[dict], cache: dict) -> tuple[list[dict], dict]:
    """Run the model page by page and collect all claims."""
    llm = None

    all_claims = []
    claim_id = 1
    cache_hits = 0
    cache_misses = 0

    for page in pages:
        document_id = page.get("document_id", DEFAULT_DOCUMENT_ID)
        document_name = page.get("document_name", DOCUMENT_NAME)
        page_number = page["page_number"]
        page_text = page["text"].strip()

        if not page_text or len(page_text) < 40:
            continue

        cache_key = build_cache_key(document_id, document_name, page_number, page_text)

        if cache_key in cache:
            page_claims = cache[cache_key].get("claims", [])
            cache_hits += 1
            print(f"Using cached claims for page {page_number}...")
        else:
            if llm is None:
                llm = ChatOllama(
                    model=MODEL_NAME,
                    temperature=0.1,
                )

            print(f"Processing page {page_number}...")
            cache_misses += 1

            try:
                claims = extract_claims_from_page(llm, document_name, page_number, page_text)
            except Exception as e:
                print(f"Error on page {page_number}: {e}")
                continue

            page_claims = [claim_to_cache_row(claim) for claim in claims]
            cache[cache_key] = {
                "document_id": document_id,
                "document_name": document_name,
                "document_path": page.get("document_path", ""),
                "page_number": str(page_number),
                "model_name": MODEL_NAME,
                "prompt_schema_version": PROMPT_SCHEMA_VERSION,
                "claims": page_claims,
            }

        for claim in page_claims:
            all_claims.append(
                {
                    "claim_id": f"claim_{claim_id}",
                    "document_id": document_id,
                    "document_name": document_name,
                    "document_path": page.get("document_path", ""),
                    "page_number": page_number,
                    "claim_text": claim["claim_text"],
                    "claim_type": claim["claim_type"],
                    "is_verifiable": claim["is_verifiable"],
                    "claim_quality_score": claim["claim_quality_score"],
                    "is_reporting_claim": claim["is_reporting_claim"],
                    "topic": claim["topic"],
                    "is_future": claim["is_future"],
                    "source_excerpt": claim["source_excerpt"],
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

        

    print(f"Claim extraction cache hits: {cache_hits}")
    print(f"Claim extraction cache misses: {cache_misses}")

    return filtered_claims, cache


def save_claims_csv(claims: list[dict], output_path: Path) -> None:
    """Save the extracted claims to a CSV file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "claim_id",
                "document_id",
                "document_name",
                "document_path",
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
    input_csv = INPUT_CSV if INPUT_CSV.exists() else LEGACY_INPUT_CSV

    if not input_csv.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        print(f"Legacy input CSV also not found: {LEGACY_INPUT_CSV}")
        return

    print("Loading pages...")
    pages = load_pages(input_csv)
    pages = select_pages_for_extraction(pages)

    cache = load_claim_cache(CACHE_JSON)
    pages_requiring_model = []

    for page in pages:
        page_text = page["text"].strip()

        if not page_text or len(page_text) < 40:
            continue

        if build_cache_key(
            page.get("document_id", DEFAULT_DOCUMENT_ID),
            page.get("document_name", DOCUMENT_NAME),
            page["page_number"],
            page_text,
        ) not in cache:
            pages_requiring_model.append(page)

    if pages_requiring_model and not is_ollama_available():
        print("Ollama is not reachable and some pages are not cached.")
        print("Start Ollama with `ollama serve` or rerun after cache has been populated.")
        print("Existing claims CSV was left unchanged.")
        return

    print("Extracting claims...")
    claims, cache = extract_claims_from_pages(pages, cache)
    save_claim_cache(cache, CACHE_JSON)

    save_claims_csv(claims, OUTPUT_CSV)

    print(f"Claims extracted: {len(claims)}")
    print(f"Saved to: {OUTPUT_CSV}")
    print(f"Saved cache to: {CACHE_JSON}")


if __name__ == "__main__":
    main()
