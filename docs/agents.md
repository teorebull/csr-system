# Agent Guide

This project uses a small set of agents. Each one does one job.

## Agent 1. Document Loader

This agent reads the source documents.

It opens PDFs, cleans page text, removes repeated noise, and keeps the useful page content. It also stores basic metadata like title and page count.

Input:
- PDF files

Output:
- Clean pages
- Document metadata
- Full text for the document

## Agent 2. Claim Extractor

This agent finds candidate CSR claims inside the document pages.

It sends page text to an LLM and asks for short, concrete claims. It keeps only claims that are specific enough to verify later.

Input:
- Clean pages

Output:
- Extracted claims
- Cache of page-level results

## Agent 3. Claim Normalizer

This agent cleans up the extracted claims.

It removes near duplicates, groups similar claims, labels broad claim families, and separates future-looking claims from present claims. It also prioritizes claims that look useful for analysis.

Input:
- Extracted claims

Output:
- Normalized claims
- Prioritized claims
- Excluded claims
- Future claims

## Agent 4. Query Generator

This agent writes search queries for each claim.

It creates a small set of search angles for verification, contradiction, criticism, methodology, and context. It also adds hand-made fallback queries for weak or broad claims.

Input:
- Prioritized claims

Output:
- Search queries
- Structured query objects

## Agent 5. Web Search

This agent searches the web.

It runs each query, keeps results that mention the company, and filters out obvious self-published or low-value sources.

Input:
- Search queries

Output:
- Search results

## Agent 6. Evidence Fetcher

This agent opens the source pages.

It downloads articles or PDFs and extracts the actual text. It drops weak results and keeps only evidence that still looks relevant to the claim.

Input:
- Search results

Output:
- Evidence rows with extracted text

## Agent 7. Reranker

This agent decides which evidence matters most.

It scores each claim-evidence pair with text overlap, source quality, query type, and other small signals. The result is a shorter and better ordered evidence set.

Input:
- Claims
- Evidence rows

Output:
- Ranked evidence

## Agent 8. Evidence Analyzer

This agent compares claims with evidence.

It asks an LLM to label each claim as supported, partially supported, unverified, partially contradicted, or contradicted. It also records the greenwashing-risk signal and the short justification.

Input:
- Claims
- Top evidence per claim

Output:
- Claim assessments
- Assessment cache

## Agent 9. Judge Aggregator

This agent writes the final report.

It combines all claim assessments, counts the main labels, builds the final verdict, and assembles a human-readable report with summaries, examples, and metadata.

Input:
- Claims
- Normalized claims
- Prioritized claims
- Future claims
- Claim assessments

Output:
- Final report
- Final summary files

## Short flow

Documents -> claims -> normalized claims -> queries -> search -> evidence -> ranking -> analysis -> final report

Each agent keeps the work traceable and easier to debug.
