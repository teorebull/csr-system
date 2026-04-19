# CSR System Notes

Documents de treball actuals:

- `TFM_CSR_system_structure.md`
- `TFM_OSS_stack_recommendation.md`
- `docs/TFM_agent_map_and_project_skeleton.md`
- `docs/TFM_current_decisions_and_next_steps.md`
- `docs/TFM_reusable_oss_repositories.md`
- `docs/TFM_agent_by_agent_execution_plan.md`
- `docs/LANGGRAPH_REALISTIC_INTEGRATION_PLAN.md`

Aquest repositori es troba encara en fase de disseny. La documentacio recull:

- estructura conceptual del TFM
- seleccio de stack open source reutilitzable
- mapa d'agents, nodes i esquelet inicial del projecte

## Estructura inicial de codi

- `src/schemas/`: models Pydantic del pipeline
- `src/agents/`: nodes del workflow
- `src/graph/`: muntatge del pipeline amb LangGraph
- `src/retrieval/`: wrappers de cerca i fetch de pagines
- `src/evaluation/`: score i utilitats d'avaluacio
- `tests/`: proves base dels schemas i score

## Seguent pas natural

1. Instal lar dependències del projecte
2. Implementar `document_loader`
3. Implementar `claim_extractor`
4. Connectar un primer proveidor LLM amb sortida estructurada
5. Fer passar un cas minim de punta a punta

## Proves de l'Agent 1

- `scripts/agent_1/test_pymupdf_loader.py`
- `scripts/agent_1/test_reportparse_loader.py`
- `docs/AGENT_1_how_to_run.md`

## Agent 2

- `scripts/agent_2/extract_claims_with_llm.py`
- `docs/AGENT_2_claim_extractor_plan.md`

## Agent 3

- `scripts/agent_3/normalize_claims.py`
- `docs/AGENT_3_claim_normalizer_plan.md`

## Agent 4

- `docs/AGENT_4_query_generator_plan.md`

## Agent 6

- `scripts/agent_6/evidence_checker.py`
- `docs/AGENT_6_evidence_fetcher_plan.md`

## Agent 7

- `scripts/agent_7/reranker.py`
- `docs/AGENT_7_reranker_plan.md`

## Agent 8

- `scripts/agent_8/evidence_analyzer.py`
- `docs/AGENT_8_evidence_analyzer_plan.md`
