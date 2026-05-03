# Agent 8 - Evidence Analyzer plan

## Goal

Take each normalized claim and compare it with the best reranked external evidence in order to assign a factual support label and a greenwashing-risk level.
It also records whether the evidence is directly relevant to the specific claim or only background context.

## Current labels

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNVERIFIED`
- `PARTIALLY_CONTRADICTED`
- `CONTRADICTED`

These labels are still strict factual-support labels. Contextual criticism or methodology caveats do not automatically support or contradict a numerical claim.
`UNVERIFIED` means the selected external evidence is insufficient to confirm or challenge the claim; it does not mean the claim is false.

## Current greenwashing risk levels

- `LOW`
- `MEDIUM`
- `HIGH`
- `UNCLEAR`

The risk level captures whether the evidence raises useful concerns such as selective framing, accounting caveats, emissions growth, data-center energy demand, REC/market-based accounting concerns, or mismatch between commitments and performance.

## Current evidence relevance levels

- `DIRECT`
- `INDIRECT`
- `BACKGROUND`
- `UNRELATED`

This field is separate from factual support and risk. It prevents broad or lateral criticism from being treated as strong claim-specific evidence.

## Current model choice

- `qwen2.5:14b`

This is stronger than the model used in `Query Generator` because this task is more sensitive and requires better judgment.

## Input

- `prioritized_claims.csv`
- `ranked_evidence.csv`

## Output

- `claim_assessments.csv`

Minimum fields:
- `normalized_claim_id`
- `claim_text`
- `final_label`
- `greenwashing_risk_level`
- `evidence_relevance`
- `justification`
- `risk_reasoning`
- `top_evidence_url`
- `top_evidence_title`
- `supporting_excerpt`

## Pipeline for this agent

1. load prioritized claims
2. load reranked evidence
3. keep the top 3 evidence rows per claim
4. build a structured prompt per claim
5. reuse a cached assessment if the claim and selected evidence have not changed
6. ask the local LLM to classify factual support, evidence relevance, and greenwashing risk separately when no cache entry exists
7. apply deterministic guardrails between evidence relevance and risk
8. clean generated text fields to remove runtime contamination
9. save the result in CSV format and update the cache

## Cache

Agent 8 writes a cache file at `data/processed/agent_8/assessment_cache.json`.

The cache key is based on:
- schema version
- claim text
- claim type and topic
- selected evidence URLs, titles, query types, scores, and text samples

This makes repeated runs much faster when reranking output has not changed.

## Why top 3 evidence rows

- one evidence row may be too weak
- more than 3 starts adding too much noise for the MVP
- top 3 is a good balance between context and simplicity

## Important prompt rules

The current analyzer is instructed to:
- use only the provided evidence
- avoid inventing facts
- prefer `UNVERIFIED` over contradiction labels when evidence is weak
- keep factual support strict for quantitative claims
- use `UNVERIFIED` for numerical claims unless the evidence confirms at least one specific value, year, scope, or directly comparable number
- use `PARTIALLY_CONTRADICTED` when evidence directly conflicts with part of the claim but does not fully contradict the whole claim
- allow `UNVERIFIED` claims to still receive `MEDIUM` or `HIGH` greenwashing risk when evidence provides relevant risk context
- set `evidence_relevance` to show whether the evidence is `DIRECT`, `INDIRECT`, `BACKGROUND`, or `UNRELATED`
- force `UNRELATED` evidence to `UNCLEAR` greenwashing risk
- prevent `BACKGROUND` evidence from producing `HIGH` greenwashing risk
- reserve `HIGH` risk for direct or clearly strong indirect evidence with serious claim-specific concerns
- keep justification short and concrete
- clean `justification`, `risk_reasoning`, and `supporting_excerpt` before writing outputs

## What to validate after running it

1. are labels reasonable?
2. does the model avoid using `CONTRADICTED` too aggressively?
3. are justifications concrete enough?
4. is the selected evidence aligned with the label?
5. does `evidence_relevance` prevent unrelated evidence from inflating greenwashing risk?

## What can improve later

- add a confidence field
- use chunk-level evidence instead of full extracted text
- compare with a smaller NLI baseline
- add secondary evidence references
- improve validation of quoted excerpts to prevent LLM paraphrase or typo leakage
