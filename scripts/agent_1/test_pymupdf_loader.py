import csv
from pathlib import Path

import pymupdf


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


def save_text_output(pdf_path: str, full_text: str) -> Path:
    """Save processed text so it can be inspected manually."""
    output_dir = Path("data/processed/agent_1/pymupdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{Path(pdf_path).stem}_processed.txt"
    output_file.write_text(full_text, encoding="utf-8")
    return output_file


def save_page_csv(pdf_path: str, pages: list[dict]) -> Path:
    """Save page-level text in CSV format."""
    output_dir = Path("data/processed/agent_1/pymupdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{Path(pdf_path).stem}_pages.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["page_number", "text"])

        for page in pages:
            writer.writerow([page["page_number"], page["text"]])

    return output_file


def save_metadata_csv(pdf_path: str, metadata: dict) -> Path:
    """Save basic PDF metadata in CSV format."""
    output_dir = Path("data/processed/agent_1/pymupdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{Path(pdf_path).stem}_metadata.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["field", "value"])

        for key, value in metadata.items():
            writer.writerow([key, value])

    return output_file


def save_removed_lines(pdf_path: str, repeated_lines: set[str]) -> Path:
    """Save removed repeated lines for review."""
    output_dir = Path("data/processed/agent_1/pymupdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{Path(pdf_path).stem}_removed_lines.txt"
    output_file.write_text("\n".join(sorted(repeated_lines)), encoding="utf-8")
    return output_file


def main() -> None:
    pdf_path = "data/raw/2025-Microsoft-Environmental-Data-Fact-Sheet-PDF.pdf"

    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        return

    print("Running PyMuPDF test...")

    pages, metadata = extract_pdf_pages(pdf_path)
    processed_pages, repeated_lines, low_text_pages = preprocess_pages(pages)
    full_text = join_pages(processed_pages)

    text_output = save_text_output(pdf_path, full_text)
    pages_output = save_page_csv(pdf_path, processed_pages)
    metadata_output = save_metadata_csv(pdf_path, metadata)
    removed_lines_output = save_removed_lines(pdf_path, repeated_lines)

    print(f"Pages: {metadata['page_count']}")
    print(f"Low-text pages after preprocessing: {low_text_pages}")
    print(f"Repeated lines removed: {len(repeated_lines)}")
    print(f"Characters extracted: {len(full_text)}")
    print(f"Saved processed text to: {text_output}")
    print(f"Saved pages CSV to: {pages_output}")
    print(f"Saved metadata CSV to: {metadata_output}")
    print(f"Saved removed lines to: {removed_lines_output}")
    print()
    print("Manual checks:")
    print("1. Is the processed text still readable?")
    print("2. Did repeated headers or footers disappear?")
    print("3. Are page numbers still preserved?")
    print("4. Could you move to claim extraction from this output?")


if __name__ == "__main__":
    main()
