# Agent 1 - How to run the tests

## Goal

Compare `PyMuPDF` and `reportparse` on the Microsoft pilot document.

## Test 1. PyMuPDF

Run:

```bash
python scripts/agent_1/test_pymupdf_loader.py "path/to/microsoft_report.pdf"
```

Expected result:
- a processed text file in `data/processed/agent_1/pymupdf/`
- a page-level CSV in `data/processed/agent_1/pymupdf/`
- a metadata CSV in `data/processed/agent_1/pymupdf/`
- a file with removed repeated lines in `data/processed/agent_1/pymupdf/`
- a short summary in the terminal

What to inspect:
1. Is the processed text readable?
2. Did repeated headers/footers disappear?
3. Is the page CSV useful for later claim extraction?
4. Is the metadata enough or mostly empty?
5. Could you extract claims from this output later?

## Test 2. reportparse

Run:

```bash
python scripts/agent_1/test_reportparse_loader.py "path/to/microsoft_report.pdf"
```

Expected result:
- a JSON file in `data/processed/agent_1/reportparse/`
- a sentence-level CSV in `data/processed/agent_1/reportparse/`

What to inspect:
1. Is the sentence CSV convenient?
2. Does the structure help more than the plain text from `PyMuPDF`?
3. Does this really save code for the next step?
4. Is the installation worth it?

## Final decision after Agent 1

Choose one of these:

1. `PyMuPDF` is enough
2. `reportparse` is worth integrating
3. `PyMuPDF` as base, `reportparse` only as reference
