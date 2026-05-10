# Entrega 10 Maig

## Context
This project is now best described as a working research prototype for CSR and greenwashing-risk analysis.

The important point for the delivery is not to perfect the codebase, but to freeze a usable version, document it clearly, and show that the pipeline can be run and interpreted.

## What Has Been Built

### Multi-agent pipeline
The current system is organized into 9 agents:

1. Document loader
2. Claim extractor
3. Claim normalizer and prioritizer
4. Query generator
5. Web search
6. Evidence fetcher
7. Evidence reranker
8. Evidence analyzer
9. Judge / final report builder

### Current working path
The live path is:

`PDFs -> claims -> queries -> web search -> fetch -> rerank -> judge -> report`

This is the path that should be described as the main implementation.

### Experimental side path
FAISS and local embeddings were explored as an internal retrieval layer.

They are useful to mention, but they should be presented as an experimental side path, not as the main operational evidence route.

## Materials and Methods

### Pipeline overview
The system reads company disclosure PDFs, extracts claims, filters and prioritizes the claims, searches the web for external evidence, ranks the evidence, classifies support or contradiction, and then produces a final report.

### Why this stack
- LangGraph: to keep the workflow modular and agent-based.
- Local models: to keep the system reproducible and low-cost.
- Web retrieval: to check claims against external sources instead of relying only on the company documents.
- Embeddings / FAISS: explored to improve internal retrieval, but kept separate from the web-evidence path.

### Agent inputs and outputs
- Agent 1: PDF documents -> pages and metadata
- Agent 2: pages -> candidate claims
- Agent 3: claims -> normalized claims, prioritized claims, future claims, excluded claims
- Agent 4: prioritized claims -> queries
- Agent 5: queries -> web search results
- Agent 6: search results -> extracted evidence passages
- Agent 7: claims + evidence -> ranked evidence rows
- Agent 8: ranked evidence + claims -> support labels, risk labels, reasoning
- Agent 9: claim assessments -> final report and final verdict

## Current Architecture

The current working architecture is:

`PDFs -> claim extraction -> claim normalization/prioritization -> query generation -> web search -> evidence extraction -> reranking -> evidence analysis -> final judgment`

The final report uses the claim-level outputs, but the top-level verdict should be read as a synthesis, not a simple count of labels.

## Results So Far

### Microsoft baseline
The Microsoft run is the strongest current example.

Observed signal:
- 134 claims extracted
- 126 claims normalized
- 15 claims prioritized for main analysis
- 6 claims analyzed in the final Microsoft judge summary used for the thesis-style report
- 4 direct evidence matches
- 2 indirect evidence matches

The current Microsoft output shows that the pipeline can recover directly supported claims and also expose unresolved claims without treating every gap as failure.

### Interpreting results
The important result is not that every claim is verified.

The important result is that:
- some claims are clearly supported
- some claims remain unverified because external coverage is incomplete
- the final judge can distinguish support from mere absence of evidence

### Company and document variation
Different companies and document sets change performance materially.

Microsoft produced the most usable baseline.
Other runs were more fragile because of document selection, claim mix, and evidence coverage.

## Problems and Limitations

- Some claims are repetitive and metric-heavy.
- Some claims are hard to verify externally.
- Some documents contain future-looking statements that should not drive the main verdict.
- Different companies produce very different evidence coverage.
- Embeddings/FAISS were explored, but not yet integrated as the main live retrieval path.
- The system is better at evidence screening than at perfect factual completeness.

## Final Judge Direction

The judge should not treat every unverified claim as negative.

The report should instead distinguish:
- supported claims
- partial support
- coverage gaps
- real concern signals

This is the key reason the judge was revised.

## Streamlit Plan

Streamlit can be added as a lightweight front end for:
- selecting a company
- reading the latest `final_summary.md`
- showing the final JSON/CSV outputs
- displaying the report in a clean thesis-friendly format

This is enough for a first prototype interface.

## What Must Be Ready By Tomorrow

You do not need to write a lot more if the prototype is stable.

You mainly need:
- one clean working Microsoft run
- one clear architecture description
- one results section with the key counts
- one limitations section
- one block diagram
- one summary table

That is enough for a preliminary delivery.

## What Can Be Refined Tomorrow

- wording of the verdicts
- wording of the results section
- figure captions
- thesis style and transitions
- Streamlit presentation polish

## Bottom Line

The thesis should present the system honestly as a reproducible prototype.

The code does not need to be fully finished to be useful for the delivery, as long as the main pipeline is stable and the written explanation is clear.
