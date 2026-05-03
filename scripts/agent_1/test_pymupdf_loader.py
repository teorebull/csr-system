import csv
import os
from pathlib import Path

import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "agent_1" / "pymupdf"
COMBINED_PAGES_CSV = OUTPUT_DIR / "pages.csv"
COMBINED_METADATA_CSV = OUTPUT_DIR / "documents_metadata.csv"
MAX_DOCUMENTS = int(os.environ.get("MAX_DOCUMENTS", "5"))
MAX_PAGES_PER_DOCUMENT = int(os.environ.get("MAX_PAGES_PER_DOCUMENT", "0"))


def build_document_id(pdf_path: Path, index: int) -> str:
    """Create a stable, readable document id for pipeline artifacts."""
    safe_stem = pdf_path.stem.lower().replace(" ", "_")
    return f"doc_{index}_{safe_stem}"


def find_input_pdfs(raw_dir: Path) -> list[Path]:
    """Find PDF inputs for the document loader."""
    pdfs = sorted(raw_dir.glob("*.pdf")) + sorted(raw_dir.glob("*.PDF"))
    unique_pdfs = []
    seen_paths = set()

    for pdf in pdfs:
        resolved_path = str(pdf.resolve()).lower()

        if resolved_path in seen_paths:
            continue

        seen_paths.add(resolved_path)
        unique_pdfs.append(pdf)

    return unique_pdfs[:MAX_DOCUMENTS]


def infer_document_name(pdf_path: Path, metadata: dict) -> str:
    """Pick a readable document name from metadata or filename."""
    title = str(metadata.get("title", "")).strip()

    if title:
        return title

    return pdf_path.stem.replace("-", " ").replace("_", " ").strip()


def clean_page_text(text: str) -> str:
    """Remove empty lines and extra spaces."""
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def extract_pdf_pages(pdf_path: str) -> tuple[list[dict], dict]:
    """Read the PDF and return pages plus basic metadata."""
    pages = []

    with pymupdf.open(pdf_path) as document:
        metadata = document.metadata

        for page in document:
            text = page.get_text("text", sort=True)
            text = clean_page_text(text)

            pages.append(
                {
                    "page_number": page.number + 1,
                    "text": text,
                }
            )

        pdf_metadata = {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creation_date": metadata.get("creationDate", ""),
            "page_count": document.page_count,
        }

    return pages, pdf_metadata


def find_repeated_lines(pages: list[dict]) -> set[str]:
    """Find short lines repeated across pages.

    These are often headers or footers.
    """
    line_counts = {}

    for page in pages:
        lines = page["text"].splitlines()

        if not lines:
            continue

        possible_repeated_lines = [lines[0], lines[-1]]

        for line in possible_repeated_lines:
            if len(line) > 120:
                continue

            if line not in line_counts:
                line_counts[line] = 0

            line_counts[line] += 1

    repeated_lines = set()

    for line, count in line_counts.items():
        if count >= 3:
            repeated_lines.add(line)

    return repeated_lines


def preprocess_pages(pages: list[dict]) -> tuple[list[dict], set[str], int]:
    """Apply simple preprocessing to the extracted pages."""
    repeated_lines = find_repeated_lines(pages)
    processed_pages = []
    low_text_pages = 0

    for page in pages:
        lines = page["text"].splitlines()
        cleaned_lines = []

        for line in lines:
            if line in repeated_lines:
                continue

            cleaned_lines.append(line)

        processed_text = "\n".join(cleaned_lines).strip()

        if len(processed_text) < 40:
            low_text_pages += 1

        processed_pages.append(
            {
                "page_number": page["page_number"],
                "text": processed_text,
            }
        )

    return processed_pages, repeated_lines, low_text_pages


def join_pages(pages: list[dict]) -> str:
    """Join processed pages into a single text."""
    all_pages_text = []

    for page in pages:
        if len(page["text"]) < 40:
            continue

        all_pages_text.append(f"[Page {page['page_number']}]\n{page['text']}")

    return "\n\n".join(all_pages_text)


def save_text_output(pdf_path: Path, full_text: str) -> Path:
    """Save processed text so it can be inspected manually."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{pdf_path.stem}_processed.txt"
    output_file.write_text(full_text, encoding="utf-8")
    return output_file


def save_page_csv(pdf_path: Path, pages: list[dict]) -> Path:
    """Save page-level text in CSV format."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{pdf_path.stem}_pages.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["page_number", "text"])

        for page in pages:
            writer.writerow([page["page_number"], page["text"]])

    return output_file


def save_metadata_csv(pdf_path: str, metadata: dict) -> Path:
    """Save basic PDF metadata in CSV format."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{Path(pdf_path).stem}_metadata.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["field", "value"])

        for key, value in metadata.items():
            writer.writerow([key, value])

    return output_file


def save_removed_lines(pdf_path: str, repeated_lines: set[str]) -> Path:
    """Save removed repeated lines for review."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{Path(pdf_path).stem}_removed_lines.txt"
    output_file.write_text("\n".join(sorted(repeated_lines)), encoding="utf-8")
    return output_file


def save_combined_pages(rows: list[dict]) -> Path:
    """Save all page rows from all documents into one CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with COMBINED_PAGES_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "document_id",
                "document_name",
                "document_path",
                "page_number",
                "text",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    return COMBINED_PAGES_CSV


def save_combined_metadata(rows: list[dict]) -> Path:
    """Save one metadata row per processed document."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with COMBINED_METADATA_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "document_id",
                "document_name",
                "document_path",
                "title",
                "author",
                "subject",
                "creation_date",
                "page_count",
                "pages_saved",
                "low_text_pages",
                "repeated_lines_removed",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    return COMBINED_METADATA_CSV


def main() -> None:
    pdf_paths = find_input_pdfs(RAW_DIR)

    if not pdf_paths:
        print(f"No PDF files found in: {RAW_DIR}")
        return

    print("Running PyMuPDF document loader...")
    print(f"Documents selected: {len(pdf_paths)}")
    print(f"Max documents: {MAX_DOCUMENTS}")
    print(f"Max pages per document: {MAX_PAGES_PER_DOCUMENT or 'all'}")

    combined_page_rows = []
    combined_metadata_rows = []

    for index, pdf_path in enumerate(pdf_paths, start=1):
        document_id = build_document_id(pdf_path, index)
        print(f"Processing {document_id}: {pdf_path.name}")

        pages, metadata = extract_pdf_pages(str(pdf_path))
        processed_pages, repeated_lines, low_text_pages = preprocess_pages(pages)

        if MAX_PAGES_PER_DOCUMENT > 0:
            processed_pages = processed_pages[:MAX_PAGES_PER_DOCUMENT]

        document_name = infer_document_name(pdf_path, metadata)
        full_text = join_pages(processed_pages)

        text_output = save_text_output(pdf_path, full_text)
        pages_output = save_page_csv(pdf_path, processed_pages)
        metadata_output = save_metadata_csv(str(pdf_path), metadata)
        removed_lines_output = save_removed_lines(str(pdf_path), repeated_lines)

        for page in processed_pages:
            combined_page_rows.append(
                {
                    "document_id": document_id,
                    "document_name": document_name,
                    "document_path": str(pdf_path.relative_to(PROJECT_ROOT)),
                    "page_number": page["page_number"],
                    "text": page["text"],
                }
            )

        combined_metadata_rows.append(
            {
                "document_id": document_id,
                "document_name": document_name,
                "document_path": str(pdf_path.relative_to(PROJECT_ROOT)),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creation_date": metadata.get("creation_date", ""),
                "page_count": metadata.get("page_count", ""),
                "pages_saved": len(processed_pages),
                "low_text_pages": low_text_pages,
                "repeated_lines_removed": len(repeated_lines),
            }
        )

        print(f"Pages: {metadata['page_count']}")
        print(f"Pages saved: {len(processed_pages)}")
        print(f"Low-text pages after preprocessing: {low_text_pages}")
        print(f"Repeated lines removed: {len(repeated_lines)}")
        print(f"Characters extracted: {len(full_text)}")
        print(f"Saved processed text to: {text_output}")
        print(f"Saved pages CSV to: {pages_output}")
        print(f"Saved metadata CSV to: {metadata_output}")
        print(f"Saved removed lines to: {removed_lines_output}")

    combined_pages_output = save_combined_pages(combined_page_rows)
    combined_metadata_output = save_combined_metadata(combined_metadata_rows)

    print(f"Combined page rows: {len(combined_page_rows)}")
    print(f"Saved combined pages to: {combined_pages_output}")
    print(f"Saved combined metadata to: {combined_metadata_output}")
    print()
    print("Manual checks:")
    print("1. Is the processed text still readable?")
    print("2. Did repeated headers or footers disappear?")
    print("3. Are page numbers still preserved?")
    print("4. Could you move to claim extraction from this output?")


if __name__ == "__main__":
    main()
