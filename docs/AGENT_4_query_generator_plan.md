# Agent 4 - Query Generator plan

## Goal

Take each prioritized normalized claim and generate focused web search queries for external evidence and greenwashing-risk analysis.

## Current decision

For the MVP, the agent reads `prioritized_claims.csv`, not the full `normalized_claims.csv`. This keeps the main analysis focused on high-priority claims that are more substantive and externally assessable.

It generates exactly 5 query types per claim:

1. `verification`
2. `contradiction`
3. `criticism`
4. `methodology`
5. `context`

For known hard cases such as Scope 2 accounting, it can add deterministic supplemental queries.

## Why this design

The purpose is to create direct and useful searches while avoiding time spent on low-priority reporting or internal metric-table claims.

The query generator should retrieve:
- independent verification
- external reporting
- criticism or contradiction
- methodology and accounting caveats
- broader context relevant to greenwashing risk

## Input

- `prioritized_claims.csv`

Important columns:
- `normalized_claim_id`
- `claim_text`
- `claim_type`
- `topic`
- `evaluation_priority`

## Output

- `queries.csv`

Minimum columns:
- `normalized_claim_id`
- `query_type`
- `query_text`

## Model choice

- `mistral-nemo:latest` via Ollama

This is lower latency and good enough for controlled query generation.

## Pipeline for this agent

1. read `prioritized_claims.csv`
2. take one prioritized claim
3. send that claim to the LLM
4. receive exactly 5 structured queries
5. add deterministic supplemental queries for known hard cases when useful
6. store all rows in `queries.csv`

## What to validate after running it

1. does each prioritized claim get useful queries?
2. are excluded low-priority claims absent from `queries.csv`?
3. do the `verification` queries invite third-party evidence?
4. do the `criticism` and `contradiction` queries create a real chance to retrieve risk evidence?
5. are methodology/context queries specific enough to avoid generic noise?

## What can improve later

- topic-aware query templates
- optional rationale field
- model comparison between `mistral-nemo` and `qwen2.5`
