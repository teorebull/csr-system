from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.schemas.query import SearchQuery, SearchQueryType


LOCAL_MODEL = "mistral-nemo:latest"
DOCUMENT_NAME = "Microsoft Environmental Sustainability Report"


class QueryItem(BaseModel):
    normalized_claim_id: str
    query_type: Literal["verification", "contradiction", "criticism", "methodology", "context"]
    query_text: str


class QueryList(BaseModel):
    queries: list[QueryItem]


def load_claims(csv_path: Path) -> list[dict]:
    claims = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            claims.append(row)

    return claims


def build_prompt(claim: dict) -> str:
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
- normalized_claim_id: {claim['normalized_claim_id']}
- document_name: {DOCUMENT_NAME}
- claim_family: {claim.get('claim_family', 'other')}
- claim_text: {claim['claim_text']}
- claim_type: {claim['claim_type']}
- topic: {claim['topic']}
""".strip()


def generate_queries_for_claim(llm, claim: dict) -> list[QueryItem]:
    structured_llm = llm.with_structured_output(QueryList)
    prompt = build_prompt(claim)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response.queries


def build_supplemental_queries(claim: dict) -> list[dict]:
    claim_id = claim["normalized_claim_id"]
    claim_text = claim["claim_text"].lower()
    claim_family = str(claim.get("claim_family", "other")).lower().strip()

    if claim_family == "governance_ai":
        supplemental_queries = [
            ("verification", "Microsoft responsible AI standard transparency note governance"),
            ("contradiction", "Microsoft responsible AI criticism accountability"),
            ("criticism", "Microsoft responsible AI concerns external review"),
            ("methodology", "Microsoft responsible AI standard NIST AI Risk Management Framework"),
            ("context", "Microsoft responsible AI report ethics governance"),
        ]
        return [
            {"normalized_claim_id": claim_id, "query_type": query_type, "query_text": query_text}
            for query_type, query_text in supplemental_queries
        ]

    if claim_family == "other":
        supplemental_queries = [
            ("verification", "Microsoft CSR report policy statement commitment"),
            ("contradiction", "Microsoft CSR criticism accountability report"),
            ("criticism", "Microsoft corporate responsibility concerns external review"),
            ("methodology", "Microsoft corporate responsibility disclosure policy report"),
            ("context", "Microsoft CSR external analysis report"),
        ]
        return [
            {"normalized_claim_id": claim_id, "query_type": query_type, "query_text": query_text}
            for query_type, query_text in supplemental_queries
        ]

    if "scope 2" not in claim_text:
        return []

    supplemental_queries = [
        ("verification", "Microsoft Scope 2 location-based market-based emissions FY20 FY24 data"),
        ("verification", "Microsoft greenhouse gas emissions Scope 2 data Tracenable"),
        ("verification", "Microsoft CDP Scope 2 location-based market-based emissions"),
        ("methodology", "Microsoft Scope 2 market-based location-based emissions renewable energy certificates RECs"),
        ("methodology", "Microsoft Scope 2 emissions GHG Protocol market-based location-based accounting"),
        ("criticism", "Microsoft renewable energy certificates Scope 2 emissions greenwashing criticism"),
        ("context", "Microsoft data centers electricity demand Scope 2 emissions location-based"),
    ]

    return [
        {"normalized_claim_id": claim_id, "query_type": query_type, "query_text": query_text}
        for query_type, query_text in supplemental_queries
    ]


def _map_query_type(query_type: str) -> SearchQueryType:
    if query_type == "verification":
        return SearchQueryType.VERIFICATION
    if query_type in {"contradiction", "criticism"}:
        return SearchQueryType.CONTROVERSY
    if query_type == "methodology":
        return SearchQueryType.REGULATORY
    if query_type == "context":
        return SearchQueryType.TEMPORAL
    return SearchQueryType.OTHER


def generate_queries_for_all_claims(claims: list[dict]) -> tuple[list[dict], list[SearchQuery]]:
    llm = ChatOllama(model=LOCAL_MODEL, temperature=0.0)
    all_queries = []
    search_queries = []

    for claim in claims:
        claim_id = claim["normalized_claim_id"]
        claim_text = claim["claim_text"].strip()

        if not claim_text:
            continue

        try:
            queries = generate_queries_for_claim(llm, claim)
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

        supplemental_rows = build_supplemental_queries(claim)
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
