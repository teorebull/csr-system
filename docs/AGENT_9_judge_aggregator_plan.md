# Agent 9 - Judge / Aggregator plan

## Goal

Take the claim-level assessments and produce a final structured report for the user.

## Current MVP design

The current version is rule-based.

It does not use an LLM for the final summary yet. This is intentional for the MVP because:
- it is easier to control
- it is easier to explain
- it is easier to debug

## Input

- `claim_assessments.csv`
- `future_claims.csv` if available

## Output

- `final_report.csv`
- `final_report.json`
- `final_summary.md`

## What this agent does now

1. loads the claim assessments
2. counts how many claims fall into each final label
3. counts how many future claims were excluded
4. builds a simple global conclusion using explicit rules
5. writes final structured outputs

## Why this is enough for now

- the main analytical work has already been done in the previous agents
- the final step only needs to summarize and aggregate
- a rule-based summary is enough for an MVP and avoids unnecessary variability

## What the final conclusion uses

The current conclusion logic looks mainly at:
- contradicted claims
- unsupported claims
- supported and partially supported claims
- excluded future claims

## What can improve later

- add a credibility score
- add a greenwashing risk score
- use an LLM to write a more polished final narrative
- incorporate richer evidence references in the final output
