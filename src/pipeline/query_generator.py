from __future__ import annotations

from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.pipeline._io import read_csv_rows
from src.schemas.query import SearchQuery, SearchQueryType


LOCAL_MODEL = "mistral-nemo:latest"
DEFAULT_DOCUMENT_NAME = "Corporate CSR document"
QUERY_TYPE_MAP = {
    "verification": SearchQueryType.VERIFICATION,
    "contradiction": SearchQueryType.CONTROVERSY,
    "criticism": SearchQueryType.CONTROVERSY,
    "methodology": SearchQueryType.REGULATORY,
    "context": SearchQueryType.TEMPORAL,
}


class QueryItem(BaseModel):
    """Single model-generated search query suggestion."""

    normalized_claim_id: str
    query_type: Literal["verification", "contradiction", "criticism", "methodology", "context"]
    query_text: str


class QueryList(BaseModel):
    """Structured query bundle returned by the LLM."""

    queries: list[QueryItem]


def load_claims(csv_path: Path) -> list[dict]:
    """Load normalized claims from disk for query generation."""

    return read_csv_rows(csv_path)


def build_prompt(claim: dict, company_name: str) -> str:
    """Build the query-generation prompt for one claim."""

    document_name = str(claim.get("document_name", "")).strip() or DEFAULT_DOCUMENT_NAME
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

Rules:
- include the company name in every query
- include the claim family or CSR category when relevant
- keep each query short and natural for web search
- do not make the queries too broad
- do not simply copy the full claim if it is too long
- prefer useful, contrastable sources over exact-number-only fact checking
- for quantitative claims, keep the metric, scope, year range, and unit if useful
- for qualitative claims, search for external assessment, controversy, implementation evidence, and limitations
- do not use social media as a target source
- generate exactly one query for each type
- return the result in structured format

Claim information:
- company_name: {company_name}
- normalized_claim_id: {claim['normalized_claim_id']}
- document_name: {document_name}
- claim_family: {claim.get('claim_family', 'other')}
- claim_text: {claim['claim_text']}
- claim_type: {claim['claim_type']}
- topic: {claim['topic']}
""".strip()


def generate_queries_for_claim(llm, claim: dict, company_name: str) -> list[QueryItem]:
    """Ask the model for the five core searches for one claim."""

    structured_llm = llm.with_structured_output(QueryList)
    prompt = build_prompt(claim, company_name)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response.queries


def is_ai_governance_claim(claim: dict) -> bool:
    """Detect claims that should be treated as AI governance related."""

    text = " ".join(
        [
            str(claim.get("claim_text", "")),
            str(claim.get("document_name", "")),
            str(claim.get("topic", "")),
        ]
    ).lower()
    markers = {
        "responsible ai",
        "artificial intelligence",
        "generative ai",
        "ai system",
        "ai systems",
        "machine learning",
        "ai governance",
        "frontier model",
        "ai safety",
        "ai transparency",
    }
    return any(marker in text for marker in markers)


def build_supplemental_queries(claim: dict, company_name: str) -> list[dict]:
    """Add hand-crafted fallback queries for weak or broad claims."""

    def _rows(pairs: list[tuple[str, str]]) -> list[dict]:
        return [
            {"normalized_claim_id": claim_id, "query_type": query_type, "query_text": query_text}
            for query_type, query_text in pairs
        ]

    claim_id = claim["normalized_claim_id"]
    claim_text = claim["claim_text"].lower()
    claim_family = str(claim.get("claim_family", "other")).lower().strip()
    company = str(company_name).strip()

    if claim_family == "governance_ai" and is_ai_governance_claim(claim):
        return _rows([
            ("verification", f"{company} responsible AI standard transparency note governance"),
            ("contradiction", f"{company} responsible AI criticism accountability"),
            ("criticism", f"{company} responsible AI concerns external review"),
            ("methodology", f"{company} responsible AI standard NIST AI Risk Management Framework"),
            ("context", f"{company} responsible AI report ethics governance"),
        ])

    if claim_family == "other":
        return _rows([
            ("verification", f"{company} CSR report policy statement commitment"),
            ("contradiction", f"{company} CSR criticism accountability report"),
            ("criticism", f"{company} corporate responsibility concerns external review"),
            ("methodology", f"{company} corporate responsibility disclosure policy report"),
            ("context", f"{company} CSR external analysis report"),
        ])

    if "scope 2" not in claim_text:
        return []

    return _rows([
        ("verification", f"{company} Scope 2 location-based market-based emissions data"),
        ("verification", f"{company} greenhouse gas emissions Scope 2 data"),
        ("verification", f"{company} CDP Scope 2 location-based market-based emissions"),
        ("methodology", f"{company} Scope 2 market-based location-based emissions renewable energy certificates RECs"),
        ("methodology", f"{company} Scope 2 emissions GHG Protocol market-based location-based accounting"),
        ("criticism", f"{company} renewable energy certificates Scope 2 emissions greenwashing criticism"),
        ("context", f"{company} electricity demand Scope 2 emissions location-based"),
    ])


def _map_query_type(query_type: str) -> SearchQueryType:
    """Map the local query type to the schema enum."""

    return QUERY_TYPE_MAP.get(query_type, SearchQueryType.OTHER)


def generate_queries_for_all_claims(claims: list[dict], company_name: str) -> tuple[list[dict], list[SearchQuery]]:
    """Generate search queries for every prioritized claim."""

    llm = ChatOllama(model=LOCAL_MODEL, temperature=0.0)
    all_queries = []
    search_queries = []

    for claim in claims:
        claim_id = claim["normalized_claim_id"]
        claim_text = claim["claim_text"].strip()

        if not claim_text:
            continue

        try:
            queries = generate_queries_for_claim(llm, claim, company_name)
        except Exception:
            continue

        for index, query in enumerate(queries, start=1):
            all_queries.append(
                {
                    "normalized_claim_id": claim_id,
                    "claim_text": claim_text,
                    "query_type": query.query_type,
                    "query_text": query.query_text,
                }
            )
            search_queries.append(
                SearchQuery(
                    query_id=f"{claim_id}_q{index}",
                    claim_id=claim_id,
                    query_text=query.query_text,
                    query_type=_map_query_type(query.query_type),
                    rationale=query.query_type,
                )
            )

        supplemental_rows = build_supplemental_queries(claim, company_name)
        all_queries.extend(supplemental_rows)

        for index, row in enumerate(supplemental_rows, start=len(queries) + 1):
            search_queries.append(
                SearchQuery(
                    query_id=f"{claim_id}_q{index}",
                    claim_id=claim_id,
                    query_text=row["query_text"],
                    query_type=_map_query_type(row["query_type"]),
                    rationale="supplemental",
                )
            )

    return all_queries, search_queries
