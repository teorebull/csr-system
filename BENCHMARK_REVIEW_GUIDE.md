# Benchmark Review Guide

## How To Review The Benchmark
The file `BENCHMARK_DATASET.csv` contains an initial benchmark draft.

Each row includes:
- the pipeline's current output
- a proposed benchmark annotation
- notes explaining the draft judgment

## What You Should Check

For each row, review these columns carefully:
- `benchmark_include`
- `benchmark_claim_quality`
- `benchmark_support`
- `benchmark_relevance`
- `benchmark_risk`
- `benchmark_notes`

## Review Questions

### 1. Should this claim be in the benchmark?
Choose:
- `yes`
- `no`

Use `no` if:
- the claim is clearly about the wrong company
- the claim is not really environmental
- the claim is too malformed or noisy to evaluate meaningfully

### 2. How good is the claim itself?
Choose:
- `high`
- `medium`
- `low`

### 3. Is the support label correct?
Choose one:
- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNVERIFIED`
- `PARTIALLY_CONTRADICTED`
- `CONTRADICTED`

### 4. Is the evidence relevance correct?
Choose one:
- `DIRECT`
- `INDIRECT`
- `BACKGROUND`
- `UNRELATED`

### 5. Is the greenwashing-risk level correct?
Choose one:
- `LOW`
- `MEDIUM`
- `HIGH`
- `UNCLEAR`

## Suggested Review Workflow

1. Read the `claim_text`
2. Check the `top_evidence_url` and `top_evidence_title`
3. Read the pipeline's `justification` and `risk_reasoning`
4. Decide whether the claim belongs in the benchmark
5. Correct the proposed benchmark labels if needed
6. Add a short explanation in `review_notes`

## Special Cases To Watch

### Wrong-company claims
If the claim is not actually about Microsoft, mark:
- `benchmark_include = no`
- `benchmark_claim_quality = low`
- explain the issue in `review_notes`

### Broad commitment claims
Be careful with broad commitments such as:
- carbon neutrality targets
- general climate action statements

These often deserve:
- `PARTIALLY_SUPPORTED` or `UNVERIFIED`
instead of contradiction unless the evidence clearly conflicts with the same commitment.

### Context-only criticism
If the evidence only raises general concerns but does not address the same claim directly, prefer:
- `INDIRECT` or `BACKGROUND`
- and avoid contradiction unless the conflict is clear and specific

## Goal Of The Review
The goal is not to make every claim look good or bad.
The goal is to create a small, stable, human-reviewed set that can be reused whenever the pipeline changes.
