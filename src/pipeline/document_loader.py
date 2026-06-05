from __future__ import annotations

import csv
from pathlib import Path

import pymupdf


def clean_page_text(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def sanitize_document_title(pdf_path: str, raw_title: str) -> str:
    title = " ".join(str(raw_title or "").split()).strip()
    fallback = Path(pdf_path).stem.replace("-", " ").replace("_", " ").strip()

    if not title:
        return fallback

    lowered = title.lower()
    if lowered.startswith("microsoft word -") or lowered.endswith(".docx") or lowered.endswith(".doc"):
        return fallback

    if len(title) < 5:
        return fallback

    return title


def extract_pdf_pages(pdf_path: str) -> tuple[list[dict], dict]:
    pages = []

    with pymupdf.open(pdf_path) as document:
        metadata = document.metadata

        for page in document:
            text = page.get_text("text", sort=True)
            text = clean_page_text(text)

            pages.append({"page_number": page.number + 1, "text": text})

        pdf_metadata = {
            "title": sanitize_document_title(pdf_path, metadata.get("title", "")),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creation_date": metadata.get("creationDate", ""),
            "page_count": document.page_count,
        }

    return pages, pdf_metadata


def find_repeated_lines(pages: list[dict]) -> set[str]:
    line_counts: dict[str, int] = {}

    for page in pages:
        lines = page["text"].splitlines()

        if not lines:
            continue

        possible_repeated_lines = [lines[0], lines[-1]]

        for line in possible_repeated_lines:
            if len(line) > 120:
                continue

            line_counts[line] = line_counts.get(line, 0) + 1

    return {line for line, count in line_counts.items() if count >= 3}


def preprocess_pages(pages: list[dict]) -> tuple[list[dict], set[str], int]:
    repeated_lines = find_repeated_lines(pages)
    processed_pages = []
    low_text_pages = 0

    for page in pages:
        cleaned_lines = []

        for line in page["text"].splitlines():
            if line in repeated_lines:
                continue

            cleaned_lines.append(line)

        processed_text = "\n".join(cleaned_lines).strip()

        if len(processed_text) < 40:
            low_text_pages += 1

        processed_pages.append({"page_number": page["page_number"], "text": processed_text})

    return processed_pages, repeated_lines, low_text_pages


def join_pages(pages: list[dict]) -> str:
    all_pages_text = []

    for page in pages:
        if len(page["text"]) < 40:
            continue

        all_pages_text.append(f"[Page {page['page_number']}]\n{page['text']}")

    return "\n\n".join(all_pages_text)


def load_document_pages(pdf_path: str) -> tuple[list[dict], dict, set[str], int, str]:
    pages, metadata = extract_pdf_pages(pdf_path)
    processed_pages, repeated_lines, low_text_pages = preprocess_pages(pages)
    full_text = join_pages(processed_pages)
    return processed_pages, metadata, repeated_lines, low_text_pages, full_text
