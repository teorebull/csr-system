# Agent 7 - Reranker plan

## Goal

Take extracted evidence candidates and order them by how relevant they are to each normalized claim.

## Current MVP design

The current version uses a hybrid open-source approach. It uses semantic embeddings through `transformers` and `torch` when available, and falls back to rule-based reranking if the embedding model cannot be loaded.

It combines:
- semantic similarity between the claim and compact evidence text using `sentence-transformers/all-MiniLM-L6-v2` loaded directly with `transformers`
- factual specificity diagnostics for years, percentages, water metrics, Scope categories, renewable-electricity accounting, carbon-credit terms, and supplier methodology terms
- keyword overlap between claim and evidence title
- keyword overlap between claim and evidence snippet
- keyword overlap between claim and extracted text
- a small bonus for higher search rank
- a small bonus depending on query type
- a small bonus or penalty from `source_quality_score` created by Agent 5
- a small greenwashing-risk signal based on terms such as AI, datacenter, Scope 3, methodology, assurance, RECs, offsets, supply chain, water, and waste

The ranking also applies light diversification so the top evidence for the LLM is not dominated by the same query type or the same URL when alternatives exist.

## Why this is acceptable now

- easy to understand
- easy to debug
- embeddings improve semantic matching beyond literal token overlap
- rule-based signals remain useful guardrails for source quality, query intent, and greenwashing-risk context
- specificity diagnostics help inspect whether semantically similar evidence is claim-specific, but they are not currently weighted in the final score because early validation made rankings less stable
- fallback behavior keeps the pipeline runnable if the embedding dependency is unavailable

## Input

- `prioritized_claims.csv`
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
- `source_quality_score`
- `source_quality_label`
- `snippet`
- `content_type`
- `semantic_similarity_score`
- `specificity_score`
- `specificity_notes`
- `final_rerank_score`
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
4. compute semantic similarity when embeddings are available
5. compute specificity diagnostics for claim-specific facts and mechanisms
6. combine semantic similarity with overlap, source quality, query type, and greenwashing-risk signals
7. rank evidence rows within each claim while preferring query-type and URL diversity
8. save ranked evidence to CSV

## What to validate after running it

1. do clearly relevant sources move to the top?
2. do weak or off-topic sources fall lower?
3. is the ranking reasonable for each claim?
4. is the output good enough for the next evidence analysis step?

## Latest validation notes

- The reranker now improves the handoff to Agent 8 by considering source quality and greenwashing-risk context, not only literal overlap with the claim.
- For Scope 3 and total-emissions claims, sources such as Trellis and NPR now rank higher when available.
- URL diversification prevents one repeated source from occupying the whole top 3 when other usable sources exist.
- Scope 2 remains weak because Agent 5 currently retrieves too few high-quality Scope 2 methodology/accounting sources. This is a retrieval issue, not only a reranking issue.
- Specificity diagnostics now inspect exact-metric alignment such as `discharge` versus `consumption`, fiscal years, percentages, Scope categories, RECs/PPAs, carbon credits, and supplier spend-factor methodology. These fields are currently diagnostic only.

## What can improve later

- `RapidFuzz`
- `rerankers`
- cross-encoder reranking
- chunk-level reranking instead of whole-document reranking
