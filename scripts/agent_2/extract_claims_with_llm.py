from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from src.pipeline.claim_extractor import (
    DEFAULT_DOCUMENT_ID,
    DOCUMENT_NAME,
    build_cache_key,
    extract_claims_from_pages,
    is_ollama_available,
)
from src.utils.company import company_to_slug


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Microsoft")
COMPANY_SLUG = company_to_slug(COMPANY_NAME)
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_1" / "pymupdf" / "pages.csv"
LEGACY_INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_1" / "pymupdf" / "2025-Microsoft-Environmental-Data-Fact-Sheet-PDF_pages.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_2" / "claims.csv"
CACHE_JSON = PROJECT_ROOT / "data" / "processed" / COMPANY_SLUG / "agent_2" / "claim_extraction_cache.json"


def load_pages(csv_path: Path) -> list[dict]:
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


def load_claim_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}

    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_claim_cache(cache: dict, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def save_claims_csv(claims: list[dict], output_path: Path) -> None:
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
    claims, cache, stats = extract_claims_from_pages(pages, cache)
    save_claim_cache(cache, CACHE_JSON)
    save_claims_csv(claims, OUTPUT_CSV)

    print(f"Claims extracted: {len(claims)}")
    print(f"Claim extraction cache hits: {stats['cache_hits']}")
    print(f"Claim extraction cache misses: {stats['cache_misses']}")
    print(f"Saved to: {OUTPUT_CSV}")
    print(f"Saved cache to: {CACHE_JSON}")


if __name__ == "__main__":
    main()
