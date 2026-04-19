# Agent 7 - Reranker plan

## Goal

Take extracted evidence candidates and order them by how relevant they are to each normalized claim.

## Current MVP design

The current version uses a simple and fully open-source approach with no extra heavy dependencies.

It does not yet use embeddings or transformer rerankers.

Instead, it combines:
- keyword overlap between claim and evidence title
- keyword overlap between claim and evidence snippet
- keyword overlap between claim and extracted text
- a small bonus for higher search rank
- a small bonus depending on query type

## Why this is acceptable now

- easy to understand
- easy to debug
- no extra installation burden
- good enough for an MVP reranking step

## Input

- `normalized_claims.csv`
- `evidence_candidates.csv`

## Output

- `ranked_evidence.csv`

## Main output fields

- `normalized_claim_id`
- `claim_text`
- `query_type`
- `query_text`
- `result_rank`
- `title`
- `url`
- `source`
- `snippet`
- `content_type`
- `relevance_score`
- `evidence_rank`
- `extraction_notes`
- `extracted_text`

## Current filtering before reranking

Only evidence rows are kept if:
- `extraction_success = true`
- extracted text is long enough to be useful

## Pipeline for this agent

1. load normalized claims
2. load extracted evidence candidates
3. remove failed or empty evidence rows
4. compute a simple relevance score per claim-evidence pair
5. rank evidence rows within each claim
6. save ranked evidence to CSV

## What to validate after running it

1. do clearly relevant sources move to the top?
2. do weak or off-topic sources fall lower?
3. is the ranking reasonable for each claim?
4. is the output good enough for the next evidence analysis step?

## What can improve later

- `RapidFuzz`
- `sentence-transformers`
- `rerankers`
- cross-encoder reranking
- chunk-level reranking instead of whole-document reranking
