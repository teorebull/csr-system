# Benchmark Methodology

## Purpose
This benchmark is a small, thesis-specific evaluation set for the current greenwashing-risk pipeline. It is intended to measure whether the system is improving or regressing as the implementation changes.

The benchmark is not meant to replace large public fact-verification datasets. Instead, it evaluates the actual task addressed by this project:
- corporate sustainability claim selection
- external evidence relevance
- support / contradiction judgment
- greenwashing-risk interpretation

## Why A Custom Benchmark Was Created
Generic datasets such as FEVER are useful as references, but they do not directly match this project's scope. This project focuses on company disclosures, environmental claims, and external evidence that may support, weaken, or contextualize those claims.

Because of that mismatch, the benchmark here is built from the project's own pipeline outputs and then reviewed manually.

## Benchmark Scope
The current benchmark focuses on:
- `environmental` claims only
- claims selected from the current LangGraph artifact tree
- the evidence already retrieved by the current system

Governance / Responsible AI claims are intentionally excluded from the main benchmark used for the environmental greenwashing verdict.

## Evaluation Levels
The benchmark evaluates the pipeline at three levels.

### 1. Claim Selection Quality
Question:
- Was this a good claim to include in the main analysis?

Fields used:
- `benchmark_include`
- `benchmark_claim_quality`
- `benchmark_claim_notes`

Suggested interpretation:
- `high`: externally contestable and materially relevant for greenwashing analysis
- `medium`: useful but weaker, narrower, or more contextual
- `low`: noisy, weakly framed, internal, or not clearly analyzable

### 2. Evidence Relevance Quality
Question:
- Is the retrieved evidence actually about the claim?

Allowed labels:
- `DIRECT`
- `INDIRECT`
- `BACKGROUND`
- `UNRELATED`

### 3. Final Judgment Quality
Question:
- Is the pipeline's final label and greenwashing-risk judgment reasonable?

Support labels:
- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNVERIFIED`
- `PARTIALLY_CONTRADICTED`
- `CONTRADICTED`

Risk labels:
- `LOW`
- `MEDIUM`
- `HIGH`
- `UNCLEAR`

## Benchmark Construction Process
The benchmark is constructed in four steps:

1. Select current environmental claims from the pipeline outputs.
2. Capture the pipeline's current evidence, labels, and reasoning.
3. Add a proposed benchmark annotation for each claim.
4. Review and correct the proposed benchmark manually.

## Human Review Policy
The benchmark is LLM-assisted but human-supervised.

This means:
- the initial table may contain draft labels
- the student reviews each row
- the reviewed labels become the benchmark reference set

The benchmark should therefore be described as:
- a small domain-specific, human-reviewed evaluation set

## Acceptance Goals
This benchmark should be used to evaluate whether new pipeline changes improve the system.

Reasonable internal targets are:
- no clearly wrong-company claims in the final environmental set
- very low or zero `UNRELATED` evidence in the final evaluated set
- contradiction labels should be rare and strongly justified
- support labels should align with claim-specific evidence
- the final verdict should remain consistent with the claim-level labels

## Supervision Guidance
During manual review, check the following for each row:

1. Is the claim actually about Microsoft?
2. Is the claim a good environmental greenwashing candidate?
3. Is the retrieved evidence truly about the same claim?
4. Is the support label too weak or too strong?
5. Is the risk label too weak or too strong?
6. Does the evidence justify the judgment, or is it only contextual criticism?

## Files
The benchmark package currently includes:
- `BENCHMARK_METHODOLOGY.md`
- `BENCHMARK_REVIEW_GUIDE.md`
- `BENCHMARK_DATASET.csv`

## Current Note
The benchmark reference set no longer keeps the known wrong-company leakage row.
Company-identity filtering is still an acceptance criterion, but it should be checked on fresh pipeline outputs rather than kept in the benchmark rows.
