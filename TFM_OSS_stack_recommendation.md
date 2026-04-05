# Recomanacio de stack open source per al TFM

## Objectiu

Reutilitzar el maxim de components open source possibles per construir un pipeline controlat amb LangGraph per a:
- carregar documents CSR
- extreure claims
- normalitzar-los
- generar queries
- recuperar evidencia externa
- reranquejar fonts
- analitzar suport o contradiccio
- produir un informe final amb score de credibilitat

La idea central no es programar-ho tot des de zero, sino connectar peces madures i adaptar nomes la logica especifica del cas d'us.

## Recomanacio global

### Stack recomanat
- `LangGraph` + `Pydantic` per a l'orquestracio i l'estat tipat
- `PyMuPDF` per carregar i parsejar informes PDF
- `spaCy` com a suport de postprocessat i validacio lleugera
- `sentence-transformers` + `RapidFuzz` per deduplicacio i normalitzacio de claims
- LLM amb sortida estructurada per a extraccio de claims, query generation i judici final
- `duckduckgo-search` com a baseline practic o `SearxNG` si pots autoallotjar cerca
- `trafilatura` per netejar i extreure text de pagines web
- `FlagEmbedding` (`bge-reranker`) o un cross-encoder de `sentence-transformers` per reranking
- model NLI per fer una primera passada de suport/contradiccio
- `MLflow` per registrar experiments, artifacts i metriques

### Per que aquesta combinacio
- Minimitza codi propi.
- Es modular i defensable academicament.
- Evita reinventar parsers, retrievers i rankers.
- Et deixa concentrar en la contribucio real del TFM: disseny del pipeline, control del flux, tracabilitat i metodologia d'avaluacio.

## Recomanacio per etapa

## 1. Document loading / parsing

### Opcions
- `PyMuPDF`
- `unstructured`
- `pdfplumber`

### Recomanacio
Fer servir `PyMuPDF` com a opcio principal.

### Motiu
- Es rapid.
- Funciona be amb PDFs corporatius normals.
- Dona accés a pagina, text i metadades.

### Quan afegir una altra eina
- `unstructured` si necessites suport multiformat.
- `pdfplumber` si acabes necessitant tractar taules concretes.

## 2. Claim extraction

### Opcions
- LLM amb sortida estructurada
- `spaCy`
- `Transformers`

### Recomanacio
No intentis construir un extractor classic complet. El millor per al teu cas es:
- LLM per extreure claims en JSON o Pydantic
- `spaCy` per extreure entitats, dates, quantitats i reforcar validacions

### Motiu
Els claims CSR solen ser semantica i contextualment complexos. Un sistema purament de regles quedaria curt.

## 3. Claim normalization / deduplication

### Opcions
- `sentence-transformers`
- `RapidFuzz`
- `scikit-learn`

### Recomanacio
Combinar embeddings + fuzzy matching.

### Implementacio suggerida
- embedding de cada claim
- clustering o threshold semantic
- comprovacio lexical amb `RapidFuzz`
- preservacio de provenance dels claims originals

## 4. Query generation

### Opcions
- LLM amb prompt estructurat
- `LangChain` o `Haystack` com a wrappers opcionals

### Recomanacio
Mantenir-ho simple: un node propi a LangGraph que faci query generation amb prompt restringit.

### Motiu
No cal un framework addicional nomes per reescriure queries.

## 5. Web search / retrieval

### Opcions
- `duckduckgo-search`
- `SearxNG`
- clients API com `Tavily` o `SerpAPI`

### Recomanacio
- `SearxNG` si pots muntar una instancia i vols una base mes controlable
- `duckduckgo-search` com a baseline simple i barata

### Nota important
La cerca web es la part mes fragil si vols mantenir-te 100% open source. Si la universitat et permet usar una API externa, la qualitat practica sol millorar molt.

## 6. Fetch i neteja de contingut web

### Opcions
- `trafilatura`
- `newspaper3k`

### Recomanacio
`trafilatura`.

### Motiu
Acostuma a donar un text net i bastant robust per a analisi posterior.

## 7. Reranking i source filtering

### Opcions
- `FlagEmbedding` amb `bge-reranker`
- cross-encoders de `sentence-transformers`
- filtres heuristics de domini / tipus de font

### Recomanacio
Combinar:
- un reranker semantic
- una politica simple de qualitat de fonts

### Politica de fonts suggerida
- prioritzar reguladors, ONGs reconegudes, informes independents i premsa de qualitat
- penalitzar press releases, blogs dubtosos i contingut sense autoria ni data

## 8. Evidence analysis / claim verification

### Opcions
- models NLI
- LLM judge amb sortida estructurada

### Recomanacio
Fer una estrategia hibrida:
- primera passada amb NLI per tenir un baseline transparent
- segona passada amb LLM judge per consolidar i justificar

### Motiu
El NLI sol no basta. L'LLM sol pot ser massa opac. La combinacio es mes forta academicament.

## 9. Orquestracio

### Opcions
- `LangGraph`
- `Haystack Pipelines`
- `Prefect` o `Dagster`

### Recomanacio
`LangGraph` com a nucli del sistema.

### Motiu
Ja encaixa amb el teu plantejament: workflow seqüencial, estat compartit, control de passos i comportament agentiu localitzat.

## 10. Avaluacio i experiment tracking

### Opcions
- `MLflow`
- `Ragas`
- `DeepEval`

### Recomanacio
- `MLflow` per experiments i artifacts
- scripts propis per metriques centrals
- `Ragas` o `DeepEval` nomes com a suport, no com a unica avaluacio

## Arquitectura de connexio recomanada

```text
Input usuari
  ->
LangGraph State
  ->
load_report (PyMuPDF)
  ->
extract_claims (LLM + Pydantic)
  ->
normalize_claims (sentence-transformers + RapidFuzz)
  ->
generate_queries (LLM)
  ->
search_web (duckduckgo-search o SearxNG)
  ->
fetch_clean_pages (trafilatura)
  ->
rerank_sources (bge-reranker + policy filter)
  ->
verify_claim (NLI + LLM judge)
  ->
aggregate_report (score + conclusio)
  ->
log_metrics (MLflow)
```

## Quines peces val la pena adaptar, i quines no

### Si val la pena adaptar
- prompts d'extraccio de claims
- prompts de query generation
- criteris de deduplicacio
- politica de qualitat de fonts
- rubric de scoring final
- tipus de claims i topics CSR

### No val la pena reinventar
- parser de PDFs
- motor de cerca
- embeddings
- rerankers
- vector DB complexa si el volum es petit
- un "agent society" massa sofisticat

## Codi propi que seguiras necessitant

Encara reutilitzant molt, hi ha peces que hauràs de definir tu:

- esquemes Pydantic del pipeline
- `PipelineState` del graf
- nodes de LangGraph
- adaptadors entre sortides de cada component
- llindars de deduplicacio
- model de scoring final
- conjunt d'avaluacio manual
- traçabilitat i logging de resultats

## Recomanacio final pel teu cas

La millor decisio per aquest TFM es construir un sistema petit pero molt ben connectat i justificat, no un sistema immens amb massa agents.

### Configuracio final que jo et recomanaria
1. `LangGraph` com a espina dorsal
2. `Pydantic` per tots els inputs i outputs
3. `PyMuPDF` per CSR reports
4. LLM estructurat per claims i queries
5. `sentence-transformers` + `RapidFuzz` per deduplicacio
6. `duckduckgo-search` o `SearxNG` per evidència externa
7. `trafilatura` per text web
8. `bge-reranker` per seleccionar la millor evidencia
9. NLI + LLM judge per stance final
10. `MLflow` per experiments

## Missatge clau per defensar davant tutor o tribunal

La contribucio del TFM no es crear un model nou ni implementar tots els components des de zero, sino dissenyar una arquitectura multi-agent controlada, modular i tracable que integri eines existents per resoldre un problema complex de verificacio de discurs CSR i deteccio d'indicis de greenwashing.
