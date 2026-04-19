# Realistic LangGraph integration plan

## Short answer

Yes, the current agents can be integrated later with LangGraph.

But the best overall option for this thesis is **not** to force LangGraph too early.

The most realistic approach is:

1. build and validate each agent independently
2. keep clear inputs and outputs
3. once the core agents are stable, wrap them in LangGraph nodes

This gives you the benefits of LangGraph without turning the MVP into an orchestration project.

## Current situation

Right now the project already has three validated or usable agents:

- `Document Loader`
- `Claim Extractor`
- `Claim Normalizer`

These agents currently communicate through CSV files.

That is acceptable and even useful for the MVP because:

- it is easy to debug
- it is easy to inspect manually
- it gives strong traceability for the thesis

## Best overall option

### Best option for the MVP

Keep the current approach for now:

- each agent can be run independently
- each agent writes intermediate outputs
- CSV remains the main debug and inspection format

Then add LangGraph as an orchestration layer **after** the next core agents are implemented.

### Why this is the best option

If you force LangGraph right now, you risk spending too much time on:

- shared state design
- node wrappers
- execution flow plumbing
- debugging orchestration instead of debugging the agents themselves

That would slow down the thesis without giving much value yet.

### Honest recommendation

Do **not** make LangGraph the center of the implementation right now.

Make the **agents** the center first.

Then use LangGraph to connect them once:

- the data formats are stable
- the outputs are good enough
- the next retrieval agents are in place

## When LangGraph should enter

The best moment to introduce LangGraph is after these agents are stable:

1. `Document Loader`
2. `Claim Extractor`
3. `Claim Normalizer`
4. `Query Generator`
5. `Web Search`
6. `Evidence Fetcher`

At that point, the pipeline is large enough that orchestration starts paying off.

## Recommended migration strategy

### Phase 1. Current phase

Use scripts and CSV outputs.

Goal:
- validate the logic of each agent

### Phase 2. Refactor phase

Move the main logic from scripts into reusable functions.

Example:
- `load_pdf_pages(...)`
- `extract_claims_from_pages(...)`
- `normalize_claims(...)`

The scripts can still remain as thin wrappers for manual runs.

### Phase 3. LangGraph phase

Create LangGraph nodes that call those functions.

At that point LangGraph becomes the workflow layer, not the place where the business logic lives.

## Recommended LangGraph architecture

### Proposed nodes

1. `load_documents`
2. `extract_claims`
3. `normalize_claims`
4. `generate_queries`
5. `search_web`
6. `fetch_evidence`
7. `rerank_evidence`
8. `analyze_evidence`
9. `aggregate_report`

### Proposed state

The future shared state can look roughly like this:

```python
state = {
    "company_name": ..., 
    "document_paths": ..., 
    "pages": ..., 
    "claims": ..., 
    "normalized_claims": ..., 
    "future_claims": ..., 
    "queries": ..., 
    "search_results": ..., 
    "evidence_documents": ..., 
    "ranked_evidence": ..., 
    "claim_assessments": ..., 
    "final_report": ...
}
```

### Recommended rule

CSV files should remain optional artifacts for debugging and thesis traceability.

That means:

- main execution later can happen in memory through LangGraph state
- but important outputs can still be saved as CSV or JSON for inspection

## How current agents map to future nodes

### `Document Loader`

Now:
- script reads PDF and writes `pages.csv`

Later:
- node reads PDF and returns `pages`
- optional debug export still writes `pages.csv`

### `Claim Extractor`

Now:
- script reads `pages.csv` and writes `claims.csv`

Later:
- node receives `pages`
- returns `claims`
- optional debug export still writes `claims.csv`

### `Claim Normalizer`

Now:
- script reads `claims.csv` and writes `normalized_claims.csv`

Later:
- node receives `claims`
- returns `normalized_claims` and `future_claims`
- optional debug export still writes CSV outputs

## What should stay stable from now on

To make later integration easy, keep these things stable:

1. field names
2. claim ids
3. page provenance
4. document names
5. one clear responsibility per agent

This is much more important than introducing LangGraph immediately.

## Risks of introducing LangGraph too early

1. too much glue code too soon
2. harder debugging
3. false sense of progress
4. time spent on orchestration instead of claim quality and evidence quality

## Real recommendation

If the question is:

> Should LangGraph be used now as the main implementation layer?

The real answer is:

**No. Not yet.**

If the question is:

> Should the project still be designed so it can be orchestrated later with LangGraph?

The answer is:

**Yes. Definitely.**

## Decision summary

### For now
- continue agent by agent
- continue using CSV outputs
- keep scripts simple

### Slight refactor soon
- move agent logic into reusable functions when each agent stabilizes

### Later
- connect those functions through LangGraph
- keep CSV and JSON outputs as optional artifacts for debugging and thesis traceability
