import csv
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pymupdf
import requests
import trafilatura


INPUT_CSV = "../../data/processed/agent_5/search_results.csv"
OUTPUT_CSV = "../../data/processed/agent_6/evidence_candidates.csv"
REQUEST_TIMEOUT = 20


def load_search_results(csv_path: str) -> list[dict]:
    """Load search results from Agent 5."""
    results = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            results.append(row)

    return results


def is_pdf_url(url: str) -> bool:
    """Detect whether a URL probably points to a PDF."""
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return path.endswith(".pdf")


def fetch_article_text(url: str) -> tuple[str, bool, str]:
    """Fetch and extract article text with trafilatura."""
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
    """Fetch and extract PDF text with PyMuPDF."""
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
    """Extract evidence text from one search result."""
    url = result["url"].strip()

    if is_pdf_url(url):
        content_type = "pdf"
        extracted_text, extraction_success, extraction_notes = fetch_pdf_text(url)
    else:
        content_type = "article"
        extracted_text, extraction_success, extraction_notes = fetch_article_text(url)

    return {
        "normalized_claim_id": result["normalized_claim_id"],
        "query_type": result["query_type"],
        "query_text": result["query_text"],
        "result_rank": result["result_rank"],
        "title": result["title"],
        "url": url,
        "source": result["source"],
        "snippet": result["snippet"],
        "content_type": content_type,
        "extracted_text": extracted_text,
        "extraction_success": extraction_success,
        "extraction_notes": extraction_notes,
    }


def extract_all_evidence(results: list[dict]) -> list[dict]:
    """Run extraction for all search results."""
    all_evidence = []

    for result in results:
        claim_id = result["normalized_claim_id"]
        url = result["url"]
        print(f"Extracting evidence for {claim_id}: {url}")

        evidence_row = extract_evidence(result)
        all_evidence.append(evidence_row)

    return all_evidence


def save_evidence_csv(rows: list[dict], output_path: str) -> None:
    """Save extracted evidence to CSV."""
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


def main() -> None:
    if not Path(INPUT_CSV).exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading search results...")
    results = load_search_results(INPUT_CSV)

    print("Extracting article and PDF text...")
    evidence_rows = extract_all_evidence(results)

    save_evidence_csv(evidence_rows, OUTPUT_CSV)

    print(f"Evidence rows created: {len(evidence_rows)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
