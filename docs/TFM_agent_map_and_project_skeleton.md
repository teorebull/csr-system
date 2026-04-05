# Mapa d'agents i esquelet del projecte

## Objectiu del document

Aquest document concreta el disseny del sistema a un nivell operatiu:
- quins agents o nodes hi haurà
- quina responsabilitat tindrà cadascun
- quins inputs i outputs tindrà
- quines llibreries o serveis open source encaixen millor
- quina estructura de projecte convé preparar

L'objectiu no es construir un sistema amb agents massa autonoms, sino un workflow controlat amb comportament agentiu localitzat.

## Principi general d'arquitectura

Es recomana diferenciar clarament entre:

- `Orquestracio`: LangGraph
- `Schemas`: Pydantic
- `Components reutilitzables`: PyMuPDF, sentence-transformers, trafilatura, rerankers, NLI, etc.
- `Logica propia del TFM`: tipus de claims, scoring, criteris de qualitat, integracio entre etapes

## Pipeline global

```text
Input usuari
  ->
Document Loader
  ->
Claim Extractor
  ->
Claim Normalizer
  ->
Query Generator
  ->
Web Search
  ->
Evidence Fetcher
  ->
Source Filter / Reranker
  ->
Evidence Analyzer
  ->
LLM Judge / Aggregator
  ->
Final Report
```

## Agent map

## 1. Document Loader

### Funcio
Carrega documents corporatius i extreu text estructurat inicial per pagines o seccions.

### Input
- `company_name`
- `document_paths` o URLs de documents

### Output
- `documents`
- `pages`
- `raw_text`
- `document_metadata`

### Llibreries recomanades
- `PyMuPDF`
- opcionalment `unstructured`

### Codi propi necessari
- heuristiques de segmentacio basica
- neteja de headers/footers repetits
- identificacio de pagines utilitzables

### Observacions
No intentaria fer un parser PDF sofisticat. Per al TFM, n'hi ha prou amb un carregador robust i traçable.

## 2. Claim Extractor

### Funcio
Detecta afirmacions CSR verificables a partir del text dels documents.

### Input
- `document_sections`
- `company_name`

### Output
- `claims_candidates`

### Camps suggerits de sortida
- `claim_id`
- `claim_text`
- `source_document`
- `source_page`
- `source_excerpt`
- `claim_type`
- `topic`
- `time_reference`
- `priority`

### Components recomanats
- LLM amb sortida estructurada
- `spaCy` per detectar entitats, xifres, dates i reforcar validacions

### Codi propi necessari
- prompt d'extraccio
- definicio de claim types i topics
- filtres per eliminar frases massa vagues o no verificables

### Recomanacio practica
Aquest node ha de ser un dels mes importants del projecte. Millor pocs claims pero bons que molts claims sorollosos.

## 3. Claim Normalizer

### Funcio
Agrupa claims equivalents, elimina duplicats i en genera una forma canonica.

### Input
- `claims_candidates`

### Output
- `normalized_claims`
- `claim_groups`

### Components recomanats
- `sentence-transformers`
- `RapidFuzz`
- `scikit-learn` per clustering simple si cal

### Codi propi necessari
- llindars de similitud
- criteris de merge
- preservacio de provenance dels claims originals

### Recomanacio practica
Fes una normalitzacio conservadora. Es pitjor fusionar claims diferents que mantenir-ne dos de similars.

## 4. Query Generator

### Funcio
Genera consultes orientades a trobar evidencia externa rellevant per cada claim.

### Input
- `normalized_claim`

### Output
- `queries`

### Camps suggerits
- `query_id`
- `claim_id`
- `query_text`
- `query_type`
- `rationale`

### Components recomanats
- LLM amb prompt restringit i sortida Pydantic

### Tipus de query utiles
- query literal del claim
- empresa + tema + any
- query de verificacio critica
- query amb paraules clau com `lawsuit`, `controversy`, `investigation`, `fine`, `emissions`, `labor`, segons el topic

### Codi propi necessari
- plantilles per tipus de claim
- variants per dimensions temporals i geografiques

## 5. Web Search

### Funcio
Executa les consultes i retorna candidats de fonts externes.

### Input
- `queries`

### Output
- `search_results`

### Camps suggerits
- `url`
- `title`
- `snippet`
- `source_name`
- `rank`
- `query_id`

### Components recomanats
- `duckduckgo-search`
- `SearxNG` si tens infraestructura per autoallotjar-la

### Codi propi necessari
- deduplicacio de resultats per URL
- normalitzacio de dominis
- limit de resultats per query

### Risc principal
Es la part menys estable si treballes nomes amb OSS.

## 6. Evidence Fetcher

### Funcio
Descarrega i extreu el contingut textual net de les fonts seleccionades.

### Input
- `search_results`

### Output
- `evidence_documents`
- `evidence_snippets`

### Components recomanats
- `trafilatura`

### Codi propi necessari
- control d'errors i timeouts
- chunking en fragments curts utilitzables
- eliminacio de contingut buit o poc informatiu

## 7. Source Filter / Reranker

### Funcio
Filtra fonts de baixa qualitat i reranqueja la millor evidencia respecte a cada claim.

### Input
- `normalized_claims`
- `evidence_snippets`

### Output
- `ranked_evidence`

### Camps suggerits
- `claim_id`
- `evidence_id`
- `relevance_score`
- `credibility_score`
- `rank`

### Components recomanats
- `FlagEmbedding` amb `bge-reranker`
- cross-encoders de `sentence-transformers`

### Politica de qualitat suggerida
- prioritzar reguladors i fonts independents
- penalitzar contingut promocional
- tenir en compte la data de publicacio
- tenir en compte si la font es primària o secundaria

### Codi propi necessari
- rubric de qualitat
- pesos de reranking final

## 8. Evidence Analyzer

### Funcio
Compara el claim amb la millor evidencia i produeix una classificacio preliminar.

### Input
- `claim`
- `ranked_evidence`

### Output
- `claim_assessment_draft`

### Etiquetes
- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `CONTRADICTED`

### Components recomanats
- model NLI per baseline
- LLM per justificacio estructurada

### Codi propi necessari
- mapping entre sortides NLI i etiquetes del projecte
- criteris per detectar suport parcial
- tractament de manca d'evidencia

### Recomanacio practica
Fes primer un baseline simple i interpretable. Despres afegeix el judge final.

## 9. LLM Judge / Aggregator

### Funcio
Consolida els resultats parcials, revisa coherencia i produeix l'informe final.

### Input
- `claim_assessment_draft`
- `ranked_evidence`
- `all_claims`

### Output
- `final_report`

### Camps suggerits
- `claim_id`
- `final_stance`
- `justification`
- `supporting_evidence_ids`
- `confidence`
- `greenwashing_signal`

### Components recomanats
- LLM amb sortida estricta via Pydantic

### Codi propi necessari
- formula del score agregat
- llindars de risc
- text final de conclusio

## 10. Metrics / Evaluation Logger

### Funcio
Guardar artefactes, traces i metriques d'execucio i qualitat.

### Input
- outputs intermedis i finals del pipeline

### Output
- runs d'avaluacio
- artefactes
- metriques

### Components recomanats
- `MLflow`

### Codi propi necessari
- metriques de claims
- metriques de stance
- metriques de cobertura i traçabilitat

## Connexio en LangGraph

## Estat compartit suggerit

```python
class PipelineState(BaseModel):
    user_query: str
    company_name: str
    document_paths: list[str]
    documents: list[dict] = []
    claims_candidates: list[dict] = []
    normalized_claims: list[dict] = []
    search_queries: list[dict] = []
    search_results: list[dict] = []
    evidence_documents: list[dict] = []
    evidence_snippets: list[dict] = []
    ranked_evidence: list[dict] = []
    claim_assessments: list[dict] = []
    final_report: dict | None = None
```

## Ordre de nodes recomanat

1. `load_documents`
2. `extract_claims`
3. `normalize_claims`
4. `generate_queries`
5. `search_evidence`
6. `fetch_evidence`
7. `rerank_evidence`
8. `analyze_claims`
9. `aggregate_report`
10. `log_run`

## Patrons de workflow recomanats

- flux principal seqüencial
- fan-out per claim a partir de `normalize_claims`
- fan-in a `aggregate_report`
- validacio Pydantic despres de cada node
- retries nomes a nodes de xarxa o LLM

## Esquelet inicial del projecte

```text
csr-system/
  docs/
    TFM_CSR_system_structure.md
    TFM_OSS_stack_recommendation.md
    TFM_agent_map_and_project_skeleton.md
  data/
    raw/
    processed/
    evaluation/
  src/
    schemas/
      claim.py
      evidence.py
      query.py
      report.py
      state.py
    agents/
      document_loader.py
      claim_extractor.py
      claim_normalizer.py
      query_generator.py
      web_search.py
      evidence_fetcher.py
      reranker.py
      evidence_analyzer.py
      judge.py
    graph/
      workflow.py
      nodes.py
    retrieval/
      search_client.py
      page_fetcher.py
      source_policy.py
    evaluation/
      metrics.py
      goldset.py
      runner.py
    utils/
      logging.py
      config.py
  tests/
    test_schemas.py
    test_claim_normalization.py
    test_score.py
  notebooks/
  config/
    settings.example.yaml
  README.md
```

## Quins fitxers implementar primer

### Fase 1
- `src/schemas/state.py`
- `src/schemas/claim.py`
- `src/schemas/evidence.py`
- `src/graph/workflow.py`

### Fase 2
- `src/agents/document_loader.py`
- `src/agents/claim_extractor.py`
- `src/agents/claim_normalizer.py`

### Fase 3
- `src/agents/query_generator.py`
- `src/agents/web_search.py`
- `src/agents/evidence_fetcher.py`
- `src/agents/reranker.py`

### Fase 4
- `src/agents/evidence_analyzer.py`
- `src/agents/judge.py`
- `src/evaluation/metrics.py`

## Minima implementacio viable

Si has de retallar abast, el MVP academicament fort seria:

1. carregar un PDF CSR
2. extreure 10-20 claims rellevants
3. deduplicar-los
4. generar queries
5. recuperar 3-5 fonts per claim
6. classificar stance
7. calcular score final
8. guardar traça completa

## Decisions que et recomano deixar fixes aviat

1. Quins tipus de claims admet el sistema
2. Quins topics CSR cobriras
3. Quines fonts consideres fortes
4. Com definiràs `PARTIALLY_SUPPORTED`
5. Quina formula final de score faras servir
6. Quina mostra manual faras servir per avaluar

## Missatge de fons per al TFM

La teva aportacio no es escriure tots els components des de zero, sino demostrar criteri d'enginyeria i de recerca en:
- seleccio de tecnologies
- integracio modular
- control del workflow
- traçabilitat de decisions
- metodologia d'avaluacio
