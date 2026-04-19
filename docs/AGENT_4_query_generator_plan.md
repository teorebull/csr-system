# Agent 4 - Query Generator plan

## Goal

Take each normalized claim and generate a small set of focused web search queries.

## Current decision

For the MVP, the agent will generate exactly 3 queries per claim:

1. `core`
2. `verification`
3. `critical`

This will be done automatically, claim by claim.

## Why this design

The purpose of this agent is not to be highly creative.

Its purpose is to create direct and useful queries that can later be sent to the web search agent.

This is important because a raw claim is often not enough to retrieve:
- independent verification
- external reporting
- criticism or contradiction

So the query generator creates three evidence-seeking angles for the same claim.

## Query types

### `core`
- direct search version of the claim
- captures the main content of the claim in concise web-search form

### `verification`
- aimed at retrieving independent or third-party evidence
- should favor terms like review, verification, audit, external, independent, report when relevant

### `critical`
- aimed at retrieving criticism, controversy, contradiction, complaint, investigation, lawsuit, or greenwashing signals

## Input

- `normalized_claim_id`
- `claim_text`
- `claim_type`
- `topic`
- optionally `document_name`

## Output

- `queries.csv`

Minimum columns:
- `normalized_claim_id`
- `query_type`
- `query_text`

## Model choice

The current recommendation is to use a local model through `Ollama`.

### Recommended model
- `mistral-nemo:latest`

### Why
- lower latency
- easier to run repeatedly across many claims
- good enough for controlled query generation
- query generation is simpler than claim extraction or evidence analysis

### Alternative
- `qwen2.5:14b` if you later want to compare quality

## Pipeline for this agent

1. read `normalized_claims.csv`
2. take one normalized claim
3. send that claim to the LLM
4. receive exactly 3 structured queries
5. store them in a list of rows
6. repeat for all claims
7. save everything to `queries.csv`

## Why claim by claim

This is better than sending all claims in one prompt because:
- easier to debug
- easier to keep query-to-claim alignment
- easier to store clean outputs
- less risk of skipped or merged claims

## Prompting strategy

The prompt should ask the model to:
- include the company name in every query
- keep each query short and natural for web search
- avoid being too broad
- generate exactly one query per query type
- return structured output

## What to validate after running it

1. does each claim get exactly 3 queries?
2. are the `core` queries direct and concise?
3. do the `verification` queries actually invite third-party evidence?
4. do the `critical` queries create a real chance to retrieve criticism or contradiction?
5. are the queries short enough to work well in web search?

## What can improve later

- topic-aware critical query vocabulary
- richer verification terms depending on claim type
- optional rationale field
- model comparison between `mistral-nemo` and `qwen2.5`
