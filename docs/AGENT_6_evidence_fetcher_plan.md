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
- `source_quality_score`
- `source_quality_label`
- `snippet`
- `content_type`
- `extracted_text`
- `extraction_success`
- `extraction_notes`

## Current extraction rule

- search results are filtered and selected before extraction according to `PIPELINE_MODE`
- low-quality sources are skipped using `source_quality_score`
- URLs are deduplicated globally before extraction
- total URLs and URLs per claim are capped to keep runs practical
- if the URL ends with `.pdf`, treat it as a PDF
- otherwise, treat it as an article or web page

Current modes:
- `fast`: max 50 total URLs, max 3 URLs per claim, keep score `>= 0.0`
- `normal`: max 100 total URLs, max 5 URLs per claim, keep score `>= 0.0`
- `strict`: max 50 total URLs, max 3 URLs per claim, keep score `>= 0.5`
- `thorough`: max 150 total URLs, max 6 URLs per claim, keep score `>= 0.0`

## Pipeline for this agent

1. read `search_results.csv`
2. skip clearly low-quality sources using Agent 5's quality score
3. deduplicate URLs globally
4. select the best URLs using source quality, query type, and search rank
5. cap total URLs and URLs per claim according to the pipeline mode
6. inspect each remaining URL
7. if it is a PDF, use `PyMuPDF`
8. otherwise, use `trafilatura`
9. save one row per URL with extracted text and extraction status

The agent now preserves the source-quality fields created by Agent 5 so Agent 7 can use them during reranking.

The default quality filter is intentionally conservative: `unknown` sources with score `0.0` still pass in `fast`, `normal`, and `thorough`, while sources explicitly marked as low quality with negative scores are skipped. `strict` mode keeps only sources with score `>= 0.5`.

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
