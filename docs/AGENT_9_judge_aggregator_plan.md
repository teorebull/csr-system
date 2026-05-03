# Agent 9 - Judge / Aggregator plan

## Goal

Take the claim-level assessments and produce a final structured report for the user.

## Current MVP design

The current version combines rule-based aggregation with an LLM-generated analytical section.

The counts and global conclusion remain rule-based because:
- they are easier to control
- they are easier to explain
- they are easier to debug

After the structured report is built, a local LLM writes a deeper analytical section from already computed claim-level results. The LLM receives theme summaries and selected examples rather than the full raw claim list, so it should synthesize patterns instead of focusing on the last few claims. If the LLM call fails, the agent falls back to a deterministic analytical section.

## Input

- `claim_assessments.csv`
- `excluded_claims.csv` if available
- `future_claims.csv` if available

## Output

- `final_report.csv`
- `final_report.json`
- `final_summary.md`

## What this agent does now

1. loads the claim assessments
2. counts how many claims fall into each final label
3. counts how many claims fall into each greenwashing-risk level
4. counts how many claims fall into each evidence-relevance level
5. counts how many low-priority claims were excluded from main analysis
6. counts how many future claims were excluded
7. builds run metadata for reproducibility
8. builds a simple global conclusion using explicit rules
9. groups claims into broad themes for final synthesis
10. asks the local LLM for a deeper analysis based only on theme summaries and selected examples
11. writes final structured outputs

## Why this is enough for now

- the main analytical work has already been done in the previous agents
- the core judgment has already been done in the previous agents
- counts and conclusions stay deterministic
- the LLM is only used to explain patterns across the already computed data
- theme summaries reduce the risk that the final analysis becomes a shallow claim-by-claim recap

## What the final conclusion uses

The current conclusion logic looks mainly at:
- contradicted claims
- partially contradicted claims
- high greenwashing-risk claims
- unverified claims
- supported and partially supported claims
- excluded low-priority claims
- excluded future claims

The current report keeps factual support and greenwashing risk separate. This is important because a claim can be numerically unverified while still being useful for risk analysis if the evidence raises credible context or methodology concerns.

The report now also keeps evidence relevance separate. This makes it visible when a claim-level result depends on direct evidence versus indirect, background, or unrelated evidence.

The report also lists low-priority claims excluded from the main analysis so the system remains transparent instead of silently dropping difficult or low-value claims.

## Run metadata

The final JSON and Markdown summary include run metadata:
- generated timestamp in UTC
- pipeline mode
- documents processed, including `document_id` and document names when available
- model names used by the main LLM/embedding agents
- key settings such as Agent 8 top-k evidence
- artifact counts from Agents 2-8
- Agent 2 and Agent 8 cache availability/counts
- relative paths to the main output artifacts

## What can improve later

- add a credibility score
- replace simple risk counts with a weighted greenwashing risk score
- make the LLM final narrative cite multiple evidence URLs per theme
- incorporate richer evidence references in the final output
- add exact cache hit/miss counters to run metadata when agents persist those stats
