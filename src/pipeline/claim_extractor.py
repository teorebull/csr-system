from __future__ import annotations

import hashlib
import json
from typing import Literal
from urllib import request

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel


MODEL_NAME = "qwen2.5:14b"
PROMPT_SCHEMA_VERSION = "claim_extractor_v3_multi_document"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MAX_PAGES_PER_DOCUMENT = 9
SKIP_FIRST_PAGE_PER_DOCUMENT = True
DOCUMENT_NAME = "Corporate CSR document"
DEFAULT_DOCUMENT_ID = "doc_1_corporate_csr_document"


class Claim(BaseModel):
    """Structured claim extracted from a source page."""

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
        "human_rights",
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
    """Batch of claims returned by the model for one page."""

    claims: list[Claim]


def is_ollama_available() -> bool:
    """Check whether the local Ollama endpoint is reachable."""

    try:
        with request.urlopen(OLLAMA_TAGS_URL, timeout=5):
            return True
    except Exception:
        return False


def build_cache_key(document_id: str, document_name: str, page_number: str | int, page_text: str) -> str:
    """Create a stable cache key for one page extraction request."""

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
    """Convert a structured claim into a cache-friendly row."""

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


def load_pages_from_state(pages: list[dict]) -> list[dict]:
    """Select and order the pages that should be sent to the extractor."""

    grouped_pages: dict[str, list[dict]] = {}

    for page in pages:
        grouped_pages.setdefault(page.get("document_id", DEFAULT_DOCUMENT_ID), []).append(page)

    selected_pages = []
    for document_pages in grouped_pages.values():
        sorted_pages = sorted(document_pages, key=lambda row: int(row.get("page_number", 0)))

        if SKIP_FIRST_PAGE_PER_DOCUMENT and len(sorted_pages) > 1:
            sorted_pages = sorted_pages[1:]

        if MAX_PAGES_PER_DOCUMENT > 0:
            sorted_pages = sorted_pages[:MAX_PAGES_PER_DOCUMENT]

        selected_pages.extend(sorted_pages)

    return selected_pages


def build_prompt(document_name: str, page_number: str | int, page_text: str) -> str:
    """Build the extraction prompt for a single document page."""

    return f"""
You are extracting CSR claims from an official corporate document.
Document: {document_name}
Page number: {page_number}

Your goal:
Extract only strong, specific, official claims made by the company that are useful for later credibility analysis.

Definition of a valid claim:
 A claim is a concrete statement made by the company about its sustainability, environment, climate, ethics, governance, labor, human rights, supply chain, social impact, or corporate responsibility practices, policies, results, commitments, or actions.

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
 Set `is_reporting_claim` to false for substantive operational, policy, practice, result, governance, labor, human rights, ethics, supply-chain, or commitment claims.

Claim quality rubric:
Assign `claim_quality_score` from 0 to 4. Prefer substantive claims that are specific, attributable, and useful for later verification.

Source excerpt:
`source_excerpt` must be copied exactly from the page text.
Do not paraphrase it.

Page text:

{page_text}
""".strip()


def extract_claims_from_page(llm, document_name: str, page_number: str | int, page_text: str) -> list[Claim]:
    """Run the model on one page and return structured claims."""

    structured_llm = llm.with_structured_output(ClaimList)
    prompt = build_prompt(document_name, page_number, page_text)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response.claims


def extract_claims_from_pages(pages: list[dict], cache: dict | None = None) -> tuple[list[dict], dict, dict[str, int]]:
    """Extract claims from all eligible pages, reusing cached results when possible."""

    cache = cache or {}
    llm = None
    model_name = MODEL_NAME
    all_claims = []
    claim_id = 1
    cache_hits = 0
    cache_misses = 0

    for page in load_pages_from_state(pages):
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
        else:
            if llm is None:
                llm = ChatOllama(model=model_name, temperature=0.1)

            cache_misses += 1
            try:
                claims = extract_claims_from_page(llm, document_name, page_number, page_text)
            except Exception:
                continue

            page_claims = [claim_to_cache_row(claim) for claim in claims]
            cache[cache_key] = {
                "document_id": document_id,
                "document_name": document_name,
                "document_path": page.get("document_path", ""),
                "page_number": str(page_number),
                "model_name": model_name,
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

    filtered_claims = [
        claim
        for claim in all_claims
        if claim["is_verifiable"] and claim["claim_quality_score"] >= 3 and not claim["is_reporting_claim"]
    ]

    return filtered_claims, cache, {"cache_hits": cache_hits, "cache_misses": cache_misses}
