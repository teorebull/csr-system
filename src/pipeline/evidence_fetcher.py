from __future__ import annotations

import csv
import os
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pymupdf
import requests
import trafilatura


REQUEST_TIMEOUT = 20
PIPELINE_MODE = os.environ.get("PIPELINE_MODE", "normal").strip().lower()

MODE_SETTINGS = {
    "fast": {"min_source_quality_score": 0.0, "max_total_urls": 50, "max_urls_per_claim": 3},
    "normal": {"min_source_quality_score": 0.0, "max_total_urls": 100, "max_urls_per_claim": 5},
    "strict": {"min_source_quality_score": 0.5, "max_total_urls": 50, "max_urls_per_claim": 3},
    "thorough": {"min_source_quality_score": 0.0, "max_total_urls": 150, "max_urls_per_claim": 6},
}
MODE_CONFIG = MODE_SETTINGS.get(PIPELINE_MODE, MODE_SETTINGS["normal"])
QUERY_TYPE_PRIORITY = {"verification": 1.0, "methodology": 0.95, "criticism": 0.9, "contradiction": 0.9, "context": 0.75}


def _claim_terms(text: str) -> list[str]:
    lowered = str(text).lower()
    terms = []
    for pattern in [
        r"scope\s*1",
        r"scope\s*2",
        r"scope\s*3",
        r"human rights",
        r"responsible ai",
        r"labor",
        r"supply chain",
        r"carbon removal",
        r"renewable electricity",
        r"carbon neutral",
        r"carbon neutrality",
        r"water",
        r"waste",
        r"diversity",
        r"inclusion",
    ]:
        if re.search(pattern, lowered):
            terms.append(pattern.replace(r"\\s*", " ").replace(r"\\", ""))
    return terms


def _text_mentions_any(text: str, terms: list[str]) -> bool:
    lowered = str(text).lower()
    return any(term.replace("\\", "") in lowered for term in terms)


def load_search_results(csv_path: Path) -> list[dict]:
    results = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            results.append(row)
    return results


def parse_source_quality_score(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def filter_low_quality_sources(results: list[dict]) -> list[dict]:
    filtered_results = []
    min_source_quality_score = MODE_CONFIG["min_source_quality_score"]

    for result in results:
        quality_score = parse_source_quality_score(result.get("source_quality_score", "0"))
        if quality_score < min_source_quality_score:
            continue
        filtered_results.append(result)

    return filtered_results


def normalize_url(url: str) -> str:
    parsed = urlparse(str(url).strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{scheme}://{netloc}{path}"


def parse_result_rank(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 999


def selection_score(result: dict) -> tuple[float, float, int]:
    source_quality_score = parse_source_quality_score(result.get("source_quality_score", "0"))
    query_priority = QUERY_TYPE_PRIORITY.get(result.get("query_type", ""), 0.5)
    rank = parse_result_rank(result.get("result_rank", ""))
    return source_quality_score, query_priority, -rank


def select_best_results(results: list[dict]) -> list[dict]:
    sorted_results = sorted(results, key=selection_score, reverse=True)
    selected_results = []
    seen_urls = set()
    per_claim_counts = {}
    max_total_urls = MODE_CONFIG["max_total_urls"]
    max_urls_per_claim = MODE_CONFIG["max_urls_per_claim"]

    for result in sorted_results:
        claim_id = result.get("normalized_claim_id", "")
        url_key = normalize_url(result.get("url", ""))

        if not claim_id or not url_key:
            continue
        if claim_id in per_claim_counts or url_key in seen_urls:
            continue

        selected_results.append(result)
        seen_urls.add(url_key)
        per_claim_counts[claim_id] = 1

        if len(selected_results) >= max_total_urls:
            break

    for result in sorted_results:
        claim_id = result.get("normalized_claim_id", "")
        url_key = normalize_url(result.get("url", ""))

        if not url_key or url_key in seen_urls:
            continue
        if per_claim_counts.get(claim_id, 0) >= max_urls_per_claim:
            continue

        selected_results.append(result)
        seen_urls.add(url_key)
        per_claim_counts[claim_id] = per_claim_counts.get(claim_id, 0) + 1

        if len(selected_results) >= max_total_urls:
            break

    return selected_results


def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def fetch_article_text(url: str) -> tuple[str, bool, str]:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "", False, "Could not download article content."

        extracted_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not extracted_text:
            return "", False, "Trafilatura could not extract article text."

        return extracted_text, True, "article extracted"
    except Exception as error:
        return "", False, f"Article extraction failed: {error}"


def fetch_pdf_text(url: str) -> tuple[str, bool, str]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        pdf_bytes = BytesIO(response.content)
        all_pages_text = []

        with pymupdf.open(stream=pdf_bytes.read(), filetype="pdf") as document:
            for page in document:
                page_text = page.get_text("text", sort=True).strip()
                if page_text:
                    all_pages_text.append(f"[Page {page.number + 1}]\n{page_text}")

        extracted_text = "\n\n".join(all_pages_text)
        if not extracted_text:
            return "", False, "PDF opened but no text was extracted."

        return extracted_text, True, "pdf extracted"
    except Exception as error:
        return "", False, f"PDF extraction failed: {error}"


def extract_evidence(result: dict) -> dict:
    url = str(result["url"]).strip()
    claim_id = result.get("normalized_claim_id") or result.get("claim_id") or ""

    if is_pdf_url(url):
        content_type = "pdf"
        extracted_text, extraction_success, extraction_notes = fetch_pdf_text(url)
    else:
        content_type = "article"
        extracted_text, extraction_success, extraction_notes = fetch_article_text(url)

    return {
        "normalized_claim_id": claim_id,
        "query_type": result["query_type"],
        "query_text": result["query_text"],
        "result_rank": result["result_rank"],
        "title": result["title"],
        "url": url,
        "source": result["source"],
        "source_quality_score": result.get("source_quality_score", "0"),
        "source_quality_label": result.get("source_quality_label", "unknown"),
        "snippet": result["snippet"],
        "content_type": content_type,
        "extracted_text": extracted_text,
        "extraction_success": extraction_success,
        "extraction_notes": extraction_notes,
    }


def keep_result_for_claim(result: dict) -> bool:
    claim_text = str(result.get("claim_text", result.get("query_text", "")))
    claim_terms = _claim_terms(claim_text)
    if not claim_terms:
        return True

    combined_text = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('extracted_text', '')}".lower()
    return _text_mentions_any(combined_text, claim_terms)


def extract_all_evidence(results: list[dict]) -> list[dict]:
    all_evidence = []

    for result in results:
        evidence = extract_evidence(result)
        if not evidence.get("extraction_success"):
            continue
        if not evidence.get("extracted_text", "").strip():
            continue
        if keep_result_for_claim(evidence):
            all_evidence.append(evidence)

    return all_evidence


def save_evidence_csv(rows: list[dict], output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "query_type",
                "query_text",
                "result_rank",
                "title",
                "url",
                "source",
                "source_quality_score",
                "source_quality_label",
                "snippet",
                "content_type",
                "extracted_text",
                "extraction_success",
                "extraction_notes",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)
