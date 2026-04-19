# Agent 6 - Evidence Fetcher plan

## Goal

Take the URLs from `search_results.csv` and extract the actual text content of each source.

## Technology choice

- `trafilatura` for article or web page URLs
- `PyMuPDF` for PDF URLs

This is the current recommended open-source and free setup for the MVP.

## Input

- `search_results.csv`

## Output

- `evidence_candidates.csv`

Minimum columns:
- `normalized_claim_id`
- `query_type`
- `query_text`
- `result_rank`
- `title`
- `url`
- `source`
- `snippet`
- `content_type`
- `extracted_text`
- `extraction_success`
- `extraction_notes`

## Current extraction rule

- if the URL ends with `.pdf`, treat it as a PDF
- otherwise, treat it as an article or web page

## Pipeline for this agent

1. read `search_results.csv`
2. inspect each URL
3. if it is a PDF, use `PyMuPDF`
4. otherwise, use `trafilatura`
5. save one row per URL with extracted text and extraction status

## Why this is enough for now

- simple and understandable
- easy to debug
- preserves provenance
- open source and free
- strong enough for the MVP

## What to validate after running it

1. do article URLs produce usable text?
2. do PDF URLs produce usable text?
3. do failures stay recorded without crashing the pipeline?
4. is the extracted text good enough for later evidence comparison?

## What can improve later

- better handling of dynamic pages
- better PDF detection than `.pdf` suffix only
- chunking extracted text for later ranking
- extra metadata such as date or author
