# Agent 8 - Evidence Analyzer plan

## Goal

Take each normalized claim and compare it with the best reranked external evidence in order to assign a final stance label.

## Current labels

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `CONTRADICTED`

## Current model choice

- `qwen2.5:14b`

This is stronger than the model used in `Query Generator` because this task is more sensitive and requires better judgment.

## Input

- `normalized_claims.csv`
- `ranked_evidence.csv`

## Output

- `claim_assessments.csv`

Minimum fields:
- `normalized_claim_id`
- `claim_text`
- `final_label`
- `justification`
- `top_evidence_url`
- `top_evidence_title`
- `supporting_excerpt`

## Pipeline for this agent

1. load normalized claims
2. load reranked evidence
3. keep the top 3 evidence rows per claim
4. build a structured prompt per claim
5. ask the local LLM to classify the claim
6. save the result in CSV format

## Why top 3 evidence rows

- one evidence row may be too weak
- more than 3 starts adding too much noise for the MVP
- top 3 is a good balance between context and simplicity

## Important prompt rules

The current analyzer is instructed to:
- use only the provided evidence
- avoid inventing facts
- prefer `UNSUPPORTED` over `CONTRADICTED` when evidence is weak
- keep justification short and concrete

## What to validate after running it

1. are labels reasonable?
2. does the model avoid using `CONTRADICTED` too aggressively?
3. are justifications concrete enough?
4. is the selected evidence aligned with the label?

## What can improve later

- add a confidence field
- use chunk-level evidence instead of full extracted text
- compare with a smaller NLI baseline
- add secondary evidence references
