# Repositoris open source reutilitzables per al TFM

Objectiu: trobar el maxim de codi reutilitzable possible per reduir al minim el desenvolupament propi del sistema.

## Llegenda

- `A`: reutilitzable directament al codi del TFM
- `B`: es pot estudiar o adaptar amb certa cautela
- `C`: nomes referencia o exemple
- `Safe`: llicencia permissiva o normal per a un TFM
- `Risky`: llicencia copyleft o situacio mes delicada

## 1. Document Loader / PDF parsing

### `docling`
- Repo: `https://github.com/docling-project/docling`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: molt bo per parsing de PDFs, estructura i exportacio
- Comentari: una de les millors opcions si vols estalviar molta feina en documents

### `unstructured`
- Repo: `https://github.com/Unstructured-IO/unstructured`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: ingestio molt madura, molts formats
- Comentari: bona si al final tens formats mes enlla de PDF

### `pypdf`
- Repo: `https://github.com/py-pdf/pypdf`
- Llicencia: `BSD-3-Clause` al repositori
- Reutilitzacio: `A`
- Valor: alternativa simple per text extraction

### `pdfplumber`
- Repo: `https://github.com/jsvine/pdfplumber`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: bo per text i taules

### `marker`
- Repo: `https://github.com/datalab-to/marker`
- Llicencia: `GPL-3.0`
- Reutilitzacio: `C`
- Valor: tecnicament fort
- Comentari: referencia interessant, pero millor no reutilitzar-lo directament si vols evitar complicacions de llicencia

## 2. Claim extraction

### `reportparse`
- Repo: `https://github.com/climate-nlp/reportparse`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: molt alineat amb sustainability reports, environmental claims i ESG topics
- Comentari: es probablement el repositori mes rellevant de tota la cerca per al teu cas

### `transformers`
- Repo: `https://github.com/huggingface/transformers`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: backbone per classificacio, NLI i altres tasques de NLP

### `GLiNER`
- Repo: `https://github.com/urchade/GLiNER`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: extraccio flexible d'entitats i spans utiles

### `spaCy`
- Repo: `https://github.com/explosion/spaCy`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: suport per frases, entitats, regles i validacions lleugeres

### `green_guard`
- Repo: `https://github.com/salitahir/green_guard`
- Llicencia: `MIT`
- Reutilitzacio: `B`
- Valor: molt alineat amb el tema ESG/greenwashing
- Comentari: sembla immadur, millor com a inspiracio que com a base central

## 3. Claim normalization / deduplication

### `RapidFuzz`
- Repo: `https://github.com/rapidfuzz/RapidFuzz`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: deduplicacio fuzzy molt facil d'integrar

### `sentence-transformers`
- Repo: `https://github.com/huggingface/sentence-transformers`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: similitud semantica i embeddings

### `dedupe`
- Repo: `https://github.com/dedupeio/dedupe`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: deduplicacio mes potent, pero possiblement massa per al teu cas

## 4. Query generation

### `KeyBERT`
- Repo: `https://github.com/MaartenGr/KeyBERT`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: molt bo per generar paraules clau a partir de claims

### `taxonomy4good`
- Repo: `https://github.com/HiveGuard-AI/taxonomy4good`
- Llicencia: `MIT`
- Reutilitzacio: `B`
- Valor: taxonomia i vocabulari de sostenibilitat per expandir queries

### `haystack`
- Repo: `https://github.com/deepset-ai/haystack`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: pot ajudar a reduir glue code, pero potser et sobra framework

## 5. Web search

### `ddgs`
- Repo: `https://github.com/deedy5/ddgs`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: millor opcio simple i practica per cerca web

### `SearXNG`
- Repo: `https://github.com/searxng/searxng`
- Llicencia: `AGPL-3.0`
- Reutilitzacio: `C`
- Valor: bo si el muntes com a servei separat
- Comentari: licencia mes delicada

### `google-search-results-python`
- Repo: `https://github.com/serpapi/google-search-results-python`
- Llicencia: `MIT`
- Reutilitzacio: `B`
- Valor: client bo, pero depen d'un servei extern propietari

## 6. Web page extraction / cleaning

### `trafilatura`
- Repo: `https://github.com/adbar/trafilatura`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: millor opcio per netejar text de pagines web

### `jusText`
- Repo: `https://github.com/miso-belica/jusText`
- Llicencia: `BSD-2-Clause`
- Reutilitzacio: `A`
- Valor: molt bona com a fallback per boilerplate removal

### `newspaper`
- Repo: `https://github.com/codelucas/newspaper`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: util per articles, encara que menys robust en alguns casos

## 7. Reranking / source filtering

### `rerankers`
- Repo: `https://github.com/AnswerDotAI/rerankers`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: wrapper de reranking molt practic

### `FlagEmbedding`
- Repo: `https://github.com/FlagOpen/FlagEmbedding`
- Llicencia: `MIT`
- Reutilitzacio: `A`
- Valor: molt bona opcio per `bge-reranker`

### `pyserini`
- Repo: `https://github.com/castorini/pyserini`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: fort en IR, pero probablement massa pesat pel teu TFM

## 8. Evidence analysis / claim verification

### `MiniCheck`
- Repo: `https://github.com/Liyan06/MiniCheck`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: molt interessant per verificar suport factual entre claim i document
- Comentari: molt probablement una de les millors peces per estalviar codi en aquesta etapa

### `transformers`
- Repo: `https://github.com/huggingface/transformers`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: permet NLI i stance models sense gaire infraestructura

### `multivers`
- Repo: `https://github.com/dwadden/multivers`
- Llicencia: `MIT`
- Reutilitzacio: `B`
- Valor: bona referencia per claim verification

### `naacl2018-fever`
- Repo: `https://github.com/sheffieldnlp/naacl2018-fever`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `B`
- Valor: molt bona referencia FEVER-style
- Comentari: mes com a inspiracio que com a dependencia central

## 9. Final aggregation / scoring / report generation

### `pandas`
- Repo: `https://github.com/pandas-dev/pandas`
- Llicencia: `BSD-3-Clause`
- Reutilitzacio: `A`
- Valor: agregacio i calcul de scores

### `Jinja`
- Repo: `https://github.com/pallets/jinja`
- Llicencia: `BSD-3-Clause`
- Reutilitzacio: `A`
- Valor: plantilles per informe final

### `WeasyPrint`
- Repo: `https://github.com/Kozea/WeasyPrint`
- Llicencia: `BSD-3-Clause`
- Reutilitzacio: `A`
- Valor: generar informes PDF des de HTML

## 10. Workflow orchestration

### `Prefect`
- Repo: `https://github.com/PrefectHQ/prefect`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: bona orquestracio de pipeline si al final no vols complicar-te amb massa agent logic

### `Dagster`
- Repo: `https://github.com/dagster-io/dagster`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: potent, pero mes pesat

### `Luigi`
- Repo: `https://github.com/spotify/luigi`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: mes simple i classic

## 11. Evaluation / experiment tracking

### `MLflow`
- Repo: `https://github.com/mlflow/mlflow`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: tracking d'experiments

### `DVC`
- Repo: `https://github.com/treeverse/dvc`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: versionat de dades i experiments

### `Aim`
- Repo: `https://github.com/aimhubio/aim`
- Llicencia: `Apache-2.0`
- Reutilitzacio: `A`
- Valor: alternativa a MLflow

## Stack final recomanat per estalviar el maxim de codi

Si vols minimitzar al maxim el codi propi, la combinacio mes atractiva es:

1. `reportparse` per parsing i possible ajuda en extraccio de claims ESG
2. `RapidFuzz` + `sentence-transformers` per normalitzacio
3. `KeyBERT` + `taxonomy4good` per query generation
4. `ddgs` per cerca web
5. `trafilatura` amb `jusText` com a fallback
6. `FlagEmbedding` o `rerankers` per reranking
7. `MiniCheck` per evidence analysis / suport factual
8. `pandas` + `Jinja` + `WeasyPrint` per score i informe final
9. `Prefect` per orquestracio si prefereixes menys complexitat que una arquitectura massa agentica

## Stack alternatiu mes net si `reportparse` no et convenç

1. `docling`
2. `GLiNER` + `transformers`
3. `RapidFuzz` + `sentence-transformers`
4. `ddgs`
5. `trafilatura`
6. `FlagEmbedding`
7. `MiniCheck`
8. `pandas` + `Jinja` + `WeasyPrint`
9. `Prefect`

## No utilitzar llevat que sigui necessari

### `marker`
- Llicencia: `GPL-3.0`
- Motiu: millor evitar reutilitzacio directa

### `SearXNG`
- Llicencia: `AGPL-3.0`
- Motiu: millor nomes com a servei separat o referencia

### `ClaimBuster` i repos similars GPL
- Motiu: molt interessants academicament, pero pitjor per integrar directament

### Frameworks massa autonoms tipus multi-agent generals
- Motiu: probablement et fan escriure mes glue code i compliquen la defensa del TFM

## Repositoris especialment rellevants per al teu cas

### `reportparse`
- `https://github.com/climate-nlp/reportparse`
- molt directament alineat amb sustainability reporting

### `MiniCheck`
- `https://github.com/Liyan06/MiniCheck`
- molt bona opcio per suport factual claim vs evidence

### `docling`
- `https://github.com/docling-project/docling`
- excel lent per document intelligence

### `green_guard`
- `https://github.com/salitahir/green_guard`
- rellevant pel tema, pero millor mirar-lo com a inspiracio

## Recomanacio final meva

Si el teu objectiu principal es estalviar codi, jo faria primer una prova molt seriosa amb aquesta combinacio:

1. `reportparse`
2. `ddgs`
3. `trafilatura`
4. `FlagEmbedding`
5. `MiniCheck`
6. `pandas`

Si això t'encaixa, et pots estalviar una quantitat molt gran de desenvolupament propi en comparacio amb construir tots els agents manualment.

## Analisi concreta de `reportparse`

### Que cobreix realment
- parsing de sustainability reports
- lectura amb `pymupdf` o `deepdoctection`
- exportacio de resultats en JSON i CSV
- deteccio d'`environmental_claim`
- deteccio de topics ESG amb `esg_bert`
- deteccio de standards com `GRI`, `SASB`, `TCFD`
- deteccio de net-zero / reduction targets

### Que NO et cobreix
- no fa cerca web externa
- no fa claim verification contra fonts externes
- no fa stance final `supported / contradicted / ...`
- no fa conclusio final de greenwashing
- no esta pensat per ser la teva capa final d'orquestracio

### Punts forts pel teu cas
- es molt alineat amb corporate sustainability reports
- et podria estalviar molta feina en la fase inicial de parsing + deteccio de claims / topics
- te llicencia `Apache-2.0`
- ja integra models de tercers orientats a clima i ESG

### Punts febles pel teu cas
- esta molt centrat en sustainability reports, i tu vols tambe annual reports, governance reports i code of ethics
- el mode complet amb `deepdoctection` te una instal lacio mes complicada
- el propi repositori adverteix que hi ha soroll i que no s'ha d'esperar 100% de precisio
- encara no incorpora una capa LLM de judici final

### Recomanacio d'us
- provar primer `reportparse` en mode simple amb reader `pymupdf`
- NO entrar d'entrada a `deepdoctection`
- usar-lo com a prototip per veure si et resol parsing + claim/topic detection sobre el document pilot de Microsoft
- si t'ajuda molt, reaprofitar la seva sortida com a input del teu pipeline
- si et complica massa, quedar-te amb `PyMuPDF` + extraccio propia

### Veredicte
`reportparse` val molt la pena provar-lo, pero no l'assumiria encara com a columna vertebral de tot el projecte.

La millor posicio per ara es:
- `candidat prioritari per al primer tram del pipeline`
- no `solucio total`
