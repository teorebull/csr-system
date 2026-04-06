# Agent 3 - Claim Normalizer plan

## Goal

Take the raw `claims.csv` from `Claim Extractor`, separate future claims, and merge obvious duplicate or near-duplicate claims.

## Input

- `claims.csv` from `Claim Extractor`

## Output

- `normalized_claims.csv`
- `future_claims.csv`

## What Claim Normalizer does now

1. reads the extracted claims CSV
2. separates claims where `is_future = true`
3. compares non-future claims
4. merges claims that are very similar and share the same topic and claim type
5. saves one normalized CSV for current claims
6. saves a separate CSV for future claims

## Why this is enough for now

- simple to understand
- easy to inspect manually
- removes obvious duplicate rows
- keeps provenance through original claim ids and page numbers

## How similarity is handled now

The current version uses a simple text normalization plus Python's `SequenceMatcher`.

This is intentionally simple for the MVP.

The normalizer currently only merges claims if:
- `topic` is the same
- `claim_type` is the same
- text similarity is high enough

## Current outputs

### `normalized_claims.csv`
- `normalized_claim_id`
- `document_name`
- `claim_text`
- `claim_type`
- `topic`
- `original_claim_ids`
- `page_numbers`
- `source_excerpts`
- `group_size`

### `future_claims.csv`
- original future claims preserved as-is

## Script created

- `scripts/agent_3/normalize_claims.py`

## How to run

```bash
python scripts/agent_3/normalize_claims.py
```

## What to validate

1. are obvious duplicates merged?
2. are different claims kept separate?
3. are future claims correctly moved out of the main set?
4. is the output easier to use for the next agent?

## What can improve later

- use `RapidFuzz` instead of `SequenceMatcher`
- use sentence embeddings for semantic similarity
- better canonical claim selection
- more precise handling of borderline duplicates
