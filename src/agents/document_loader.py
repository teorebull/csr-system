import pymupdf
from pathlib import Path


def clean_page_text(text: str) -> str:
    """Remove empty lines and extra spaces."""
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def load_pdf_text(pdf_path: str) -> str:
    """Open a PDF and return all its text."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    all_pages_text = []

    with pymupdf.open(path) as document:
        for page in document:
            page_text = page.get_text("text", sort=True)
            page_text = clean_page_text(page_text)

            if page_text:
                all_pages_text.append(f"[Page {page.number + 1}]\n{page_text}")

    return "\n\n".join(all_pages_text)


def load_documents(document_paths: list[str]) -> list[dict]:
    """Load several PDF documents and return a simple list."""
    documents = []

    for document_path in document_paths:
        document_text = load_pdf_text(document_path)

        documents.append(
            {
                "document_name": Path(document_path).name,
                "document_path": document_path,
                "text": document_text,
            }
        )

    return documents
