# Agent 3 - Claim Normalizer plan

## Goal

Take the raw `claims.csv` from `Claim Extractor`, separate future claims, merge obvious duplicate or near-duplicate claims, and prioritize which claims enter the main external-evidence analysis.

## Input

- `claims.csv` from `Claim Extractor`

## Output

- `normalized_claims.csv`
- `prioritized_claims.csv`
- `excluded_claims.csv`
- `future_claims.csv`

## What Claim Normalizer does now

1. reads the extracted claims CSV
2. separates claims where `is_future = true`
3. compares non-future claims
4. merges claims that are very similar and share the same topic and claim type
5. assigns `evaluation_priority`, `main_analysis`, `exclusion_reason`, `analytical_value_score`, and `analytical_value_reason`
6. caps the main-analysis set with `MAX_PRIORITIZED_CLAIMS_TOTAL` to reduce downstream noise and runtime
7. saves one normalized CSV for current claims
8. saves a prioritized CSV for the main analysis
9. saves excluded claims separately, including claims that fall below the cap
10. saves a separate CSV for future claims

## Why this is enough for now

- simple to understand
- easy to inspect manually
- removes obvious duplicate rows
- keeps provenance through original claim ids and page numbers
- keeps document provenance through `document_id`, `document_name`, and `source_locations`
- reduces downstream time and noise by excluding low-information claims from the main analysis
- prioritizes claims with higher external analytical value, such as carbon neutrality, carbon credits, Scope 3 methodology, supplier methodology, renewable electricity accounting, EACs/RECs/PPAs, and water inventory boundaries
- demotes dense internal metric-table claims that are hard to verify externally without company source data
- keeps excluded claims visible for traceability instead of deleting them

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
- `document_id`
- `document_name`
- `claim_text`
- `claim_type`
- `topic`
- `original_claim_ids`
- `page_numbers`
- `source_locations`
- `source_excerpts`
- `group_size`
- `evaluation_priority`
- `main_analysis`
- `exclusion_reason`
- `analytical_value_score`
- `analytical_value_reason`

### `prioritized_claims.csv`
- highest-value claims with `main_analysis = true`
- capped by `MAX_PRIORITIZED_CLAIMS_TOTAL`, default `14`
- used by downstream search, reranking, and evidence analysis

### `excluded_claims.csv`
- low-priority claims kept out of the main analysis
- current exclusion reasons include reporting/meta claims, exact internal metric tables, medium-priority claims, very low-information claims, and high-priority claims that fall below the main-analysis cap
- capped high-priority rows use `below_main_analysis_priority_cap`

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
4. are low-priority claims excluded for defensible reasons?
5. are high-priority but lower-value claims capped transparently?
6. is the output easier to use for the next agent?

## What can improve later

- use `RapidFuzz` instead of `SequenceMatcher`
- use sentence embeddings for semantic similarity
- better canonical claim selection
- more precise handling of borderline duplicates
