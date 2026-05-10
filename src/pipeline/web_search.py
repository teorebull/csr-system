from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

from ddgs import DDGS

from src.schemas.query import SearchQuery, SearchResult


MAX_RESULTS = 8
EXTRA_EXCLUDED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "news.ycombinator.com",
]

HIGH_QUALITY_DOMAINS = {
    "npr.org",
    "wired.com",
    "theverge.com",
    "trellis.net",
    "theregister.com",
    "businessgreen.com",
    "reuters.com",
    "apnews.com",
    "carbonbrief.org",
    "iea.org",
    "sec.gov",
    "cdp.net",
    "ghgprotocol.org",
    "theconversation.com",
    "stand.earth",
    "computerweekly.com",
    "datacenterdynamics.com",
    "grist.org",
    "greenbiz.com",
    "esgdive.com",
    "policyreview.info",
    "enabledemissions.com",
    "theguardian.com",
    "cleantechnica.com",
    "renewableenergyworld.com",
}

LOW_QUALITY_DOMAIN_HINTS = {
    "windowsforum.com",
    "websitehostingreview.org",
    "bot.to",
    "tipranks.com",
    "allaboutai.com",
    "hashlytics.io",
    "poniaktimes.com",
    "richardhartley.com",
    "the-14.com",
}


def normalize_company_name(company_name: str) -> list[str]:
    company_name = company_name.lower().strip().replace("&", " and ").replace("-", " ")
    parts = company_name.split()
    ignored_words = {"inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "ltd", "ltd.", "llc", "plc", "group", "holdings", "ag", "sa", "nv", "the"}
    keywords = []

    for part in parts:
        if part and part not in ignored_words and len(part) >= 3:
            keywords.append(part)

    return keywords


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def score_source_quality(url: str) -> tuple[float, str]:
    domain = get_domain(url).removeprefix("www.")

    if not domain:
        return 0.0, "unknown"

    if domain in HIGH_QUALITY_DOMAINS:
        return 1.0, "high"

    for weak_hint in LOW_QUALITY_DOMAIN_HINTS:
        if weak_hint in domain:
            return -0.5, "low"

    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 1.0, "high"

    if domain.endswith(".org"):
        return 0.5, "medium"

    return 0.0, "unknown"


def is_company_owned_domain(url: str, company_keywords: list[str]) -> bool:
    domain = get_domain(url)

    if not domain:
        return False

    if any(excluded_domain in domain for excluded_domain in EXTRA_EXCLUDED_DOMAINS):
        return True

    return any(keyword in domain for keyword in company_keywords)


def mentions_company(result: dict, company_keywords: list[str]) -> bool:
    title = result.get("title", "").lower()
    snippet = result.get("body", "").lower()
    url = result.get("href", "").lower()
    combined_text = f"{title} {snippet} {url}"

    if "microsoft word" in title and "microsoft" not in snippet and "microsoft" not in url:
        return False

    if "microsoft" not in combined_text:
        return False

    return any(keyword in combined_text for keyword in company_keywords)


def filter_external_results(results: list[dict], company_name: str) -> list[dict]:
    company_keywords = normalize_company_name(company_name)
    filtered_results = []

    for result in results:
        url = result.get("href", "")
        if is_company_owned_domain(url, company_keywords):
            continue
        if not mentions_company(result, company_keywords):
            continue
        filtered_results.append(result)

    return filtered_results


def load_queries(csv_path: Path) -> list[dict]:
    queries = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            queries.append(row)

    return queries


def _query_claim_id(query: dict) -> str:
    return query.get("normalized_claim_id") or query.get("claim_id") or ""


def search_query(query: dict, ddgs_client: DDGS, company_name: str) -> list[dict]:
    query_text = query["query_text"].strip()
    if not query_text:
        return []

    try:
        results = ddgs_client.text(query_text, max_results=MAX_RESULTS)
    except Exception:
        return []

    results = filter_external_results(results, company_name)
    formatted_results = []

    for index, result in enumerate(results, start=1):
        source_quality_score, source_quality_label = score_source_quality(result.get("href", ""))
        formatted_results.append(
            {
                "normalized_claim_id": _query_claim_id(query),
                "claim_text": query.get("claim_text", ""),
                "query_type": query["query_type"],
                "query_text": query_text,
                "result_rank": index,
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", ""),
                "source": result.get("source", ""),
                "source_quality_score": source_quality_score,
                "source_quality_label": source_quality_label,
            }
        )

    return formatted_results


def search_all_queries(queries: list[dict], company_name: str) -> tuple[list[dict], list[SearchResult]]:
    all_results = []
    result_models: list[SearchResult] = []
    ddgs_client = DDGS()

    for query in queries:
        query_results = search_query(query, ddgs_client, company_name)
        for result in query_results:
            all_results.append(result)
            result_models.append(
                SearchResult(
                    result_id=f"{result['normalized_claim_id']}_{result['result_rank']}",
                    query_id=result["normalized_claim_id"],
                    claim_id=result["normalized_claim_id"],
                    url=result["url"],
                    title=result["title"],
                    snippet=result["snippet"],
                    source_name=result["source"] or get_domain(result["url"]),
                    rank=result["result_rank"],
                    published_at=None,
                )
            )

    return all_results, result_models
