# Benchmark V1 Summary

## Status
Benchmark v1 is now initialized and reviewed for five environmental claims.
Benchmark v2 draft rows have been added from a clean no-cache rebuild and are pending manual review.

Files:
- `BENCHMARK_METHODOLOGY.md`
- `BENCHMARK_REVIEW_GUIDE.md`
- `BENCHMARK_DATASET.csv`

## Benchmark Rows

### bm_001
- Claim: definition of carbon neutrality through carbon credits
- Purpose: check whether indirect contextual evidence is handled as partial support rather than contradiction

### bm_002
- Claim: renewable electricity matching through PPAs / EACs / green power products
- Purpose: test a classic greenwashing-risk claim around procurement method versus actual impact

### bm_003
- Claim: 4% greenhouse-gas intensity reduction promise
- Purpose: calibrate a high-visibility environmental target where evidence raises concern but does not directly falsify the exact metric

### bm_004
- Claim: carbon neutral every year since FY13
- Purpose: test a strong stakeholder-facing historical claim that currently has only indirect evidence

### bm_005
- Claim: taking action to reduce total emissions and improve supply-chain resilience
- Purpose: contradiction calibration for broad action-oriented commitments that should not be over-penalized by contextual criticism

## Reviewed Reference Labels

| Benchmark ID | Include | Claim Quality | Support | Relevance | Risk |
|---|---|---|---|---|---|
| `bm_001` | yes | high | `PARTIALLY_SUPPORTED` | `INDIRECT` | `MEDIUM` |
| `bm_002` | yes | high | `PARTIALLY_SUPPORTED` | `INDIRECT` | `MEDIUM` |
| `bm_003` | yes | high | `UNVERIFIED` | `DIRECT` | `MEDIUM` |
| `bm_004` | yes | high | `UNVERIFIED` | `INDIRECT` | `MEDIUM` |
| `bm_005` | yes | medium | `PARTIALLY_SUPPORTED` | `DIRECT` | `MEDIUM` |
## How To Use Benchmark V1
Use this benchmark before and after any major pipeline change.

For each row, compare:
- whether the claim is included correctly
- whether the support label matches
- whether the evidence relevance matches
- whether the greenwashing-risk label matches

This benchmark should be treated as the current reference evaluation set for the environmental greenwashing pipeline.

## Current Claim Target
The pipeline is now configured to allow up to 15 prioritized claims total per run.
For the Microsoft environmental pilot, the target is to keep the main analysis broad enough to reach roughly 15 substantive claims when the source material supports it.
