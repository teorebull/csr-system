# Current Pipeline Implementation

## Overview
This project implements a multi-agent pipeline for analyzing corporate sustainability claims and estimating greenwashing risk. The current implementation uses a LangGraph-based orchestration layer over reusable pipeline modules.

The system is designed to:
- extract claims from company disclosure documents
- prioritize the most analytically useful claims
- retrieve external evidence
- assess whether claims are supported, partially supported, unverified, or contradicted
- estimate greenwashing risk from the evidence pattern

## Main Entry Point
The main runtime entry point is:
- `run_graph.py`

This file is responsible for:
- building the LangGraph workflow
- choosing the start and stop nodes
- loading input documents from `data/raw`
- resuming from intermediate artifacts when needed
- printing per-node timing and runtime information

## Graph Orchestration
The LangGraph node wrappers are implemented in:
- `src/graph/nodes.py`

This file connects the reusable pipeline modules to the graph runtime and also handles:
- per-stage CSV artifact writing
- environmental-claim filtering for the main verdict path
- use of the LangGraph-specific artifact tree under `data/processed/langgraph/`
- cache reuse for expensive LLM stages

## Pipeline Stages

### Agent 1: Document Loader
- File: `src/pipeline/document_loader.py`
- Purpose: load PDF documents and extract page-level text.
- Output: document metadata and page text used by downstream claim extraction.

### Agent 2: Claim Extractor
- File: `src/pipeline/claim_extractor.py`
- Purpose: use an LLM to extract candidate claims from page text.
- Current implementation notes:
  - supports caching
  - can be limited by page count and character count for smoke tests
  - is one of the slowest stages on uncached runs

### Agent 3: Claim Normalizer and Prioritizer
- File: `src/pipeline/claim_normalizer.py`
- Purpose:
  - merge duplicate or near-duplicate claims
  - split future-looking claims from current claims
  - prioritize claims for main analysis

Current Agent 3 design decisions:
- global prioritized-claim cap: `15`
- per-document prioritized-claim cap: `3`
- future-looking claims are excluded from the main evaluation
- hard-to-verify internal methodology or boundary claims are penalized
- claims are classified into families:
  - `environmental`
  - `governance_ai`
  - `other`

This claim-family separation is important because the final environmental greenwashing verdict should not be distorted by governance or Responsible AI transparency claims.

### Agent 4: Query Generator
- File: `src/pipeline/query_generator.py`
- Purpose: generate search queries for prioritized claims.
- Model currently used: `mistral-nemo:latest`
- Notes:
  - this stage depends on Ollama availability
  - if Ollama is unavailable, downstream retrieval cannot proceed correctly

### Agent 5: Web Search
- File: `src/pipeline/web_search.py`
- Purpose: retrieve external search results for generated queries.
- Includes filtering for:
  - company-owned domains
  - low-value or irrelevant sources
  - some social or noisy domains

### Agent 6: Evidence Fetcher
- File: `src/pipeline/evidence_fetcher.py`
- Purpose: download and extract evidence text from articles and PDFs.
- Uses:
  - `trafilatura` for web text extraction
  - `PyMuPDF` for PDFs

### Agent 7: Reranker
- File: `src/pipeline/reranker.py`
- Purpose: rank evidence items by usefulness for each claim.
- Uses embedding-based and heuristic scoring.
- Current goals:
  - favor claim-specific evidence
  - reduce noisy contextual matches

### Agent 8: Evidence Analyzer
- File: `src/pipeline/evidence_analyzer.py`
- Purpose: evaluate each prioritized claim against its retrieved evidence.
- Output fields include:
  - support label
  - greenwashing risk level
  - evidence relevance
  - justification and risk reasoning

Important current behavior:
- contradiction labels were tightened so weak contextual criticism is less likely to be treated as direct contradiction
- cache support is enabled to reduce rerun cost

### Agent 9: Judge / Final Report Builder
- File: `src/pipeline/judge_aggregator.py`
- Purpose:
  - aggregate claim-level judgments
  - produce a final summary
  - generate the overall greenwashing-related verdict

Current design decision:
- the main final verdict uses the `environmental` subset of claims only
- governance / AI claims remain visible in the broader pipeline artifacts but should not drive the environmental greenwashing conclusion

## Artifact Structure

### Legacy Script Pipeline
Legacy script outputs are stored in:
- `data/processed/agent_*`

### Current LangGraph Pipeline
LangGraph outputs are stored separately in:
- `data/processed/langgraph/agent_*`

This separation was introduced to avoid mixing old script results with the current LangGraph implementation.

## Current LangGraph Outputs
The LangGraph path writes artifacts for multiple stages, including:
- `agent_2/claims.csv`
- `agent_2/claim_extraction_cache.json`
- `agent_3/normalized_claims.csv`
- `agent_3/prioritized_claims.csv`
- `agent_3/excluded_claims.csv`
- `agent_3/future_claims.csv`
- `agent_4/queries.csv`
- `agent_5/search_results.csv`
- `agent_6/evidence_candidates.csv`
- `agent_7/ranked_evidence.csv`
- `agent_8/claim_assessments.csv`
- `agent_8/assessment_cache.json`
- `agent_9/final_report.csv`
- `agent_9/final_report.json`
- `agent_9/final_summary.md`

## Current Design Decisions

### Claim Prioritization
- No more than `15` total prioritized claims
- No more than `3` prioritized claims per document
- Claims are ranked by analytical usefulness, not just extracted volume

### Claim Family Separation
- Environmental claims are the primary basis for the greenwashing judgment
- Governance / AI transparency claims are retained separately

### Evidence Handling
- Direct evidence should matter more than indirect or background evidence
- Weak contextual criticism should not automatically create contradiction labels
- Missing evidence should lead to `UNVERIFIED`, not automatic greenwashing conclusions

### Performance Strategy
Performance has been improved by:
- adding persistent Agent 2 cache reuse
- adding persistent Agent 8 cache reuse
- supporting resumed execution from downstream stages

## Current Strengths
- The end-to-end architecture exists and runs
- The pipeline is modular and reusable
- The LangGraph and legacy paths are separated
- Expensive LLM stages now reuse caches
- The claim set can be capped globally and per document
- Environmental claims can be isolated from governance / AI claims for the final verdict

## Current Limitations
- Query generation depends on local Ollama availability
- Some evidence is still indirect rather than strongly claim-specific
- Multi-document behavior is still being stabilized
- Final summary prose is still being refined
- A few broad claims remain difficult to verify externally even after prioritization improvements

## Current Status
The codebase should be described as:
- a functionally complete research prototype at the architectural level
- with ongoing refinement of claim selection, retrieval quality, evidence relevance, and final judgment quality

It is more accurate to present this as an implemented and operational prototype under validation, rather than a fully finalized production system.

## Key Files
- `run_graph.py`
- `src/graph/nodes.py`
- `src/pipeline/document_loader.py`
- `src/pipeline/claim_extractor.py`
- `src/pipeline/claim_normalizer.py`
- `src/pipeline/query_generator.py`
- `src/pipeline/web_search.py`
- `src/pipeline/evidence_fetcher.py`
- `src/pipeline/reranker.py`
- `src/pipeline/evidence_analyzer.py`
- `src/pipeline/judge_aggregator.py`

## Suggested Description for the Report
The current implementation is a LangGraph-orchestrated multi-agent pipeline that processes company disclosure documents, extracts and prioritizes analytically material claims, retrieves external evidence, and produces an evidence-based greenwashing-risk judgment. The implementation includes artifact persistence, cache reuse, per-document claim balancing, and claim-family separation to ensure that the final environmental verdict is not distorted by governance or AI-transparency disclosures.
