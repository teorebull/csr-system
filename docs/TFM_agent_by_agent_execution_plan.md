# Pla d'execucio agent per agent

Objectiu: treballar el TFM de forma seqüencial, agent per agent, sense barrejar etapes. La idea es validar cada mòdul abans de passar al següent.

## Decisions actuals fixades

### Empresa pilot
- `Microsoft`

### Document pilot
- `Environmental Sustainability Report`

### Definicio operativa de claim
- qualsevol afirmacio oficial de l'empresa relacionada amb sostenibilitat, CSR, etica, governanca o impacte social/ambiental
- no cal que sigui numerica
- pot ser una politica, una practica, un resultat, una declaracio o un compromís verificable

### Claims que es tractaran a part
- claims futurs o aspiracionals
- etiqueta actual: `FUTURE`
- no entren de moment en el comput principal del MVP

### Rúbrica actual
- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `CONTRADICTED`
- `FUTURE`

### Fonts externes admeses
- reguladors i organismes publics
- ONG reconegudes
- informes independents o d'auditoria
- premsa economica o generalista fiable
- articles d'experts o think tanks amb autoria clara
- webs institucionals fiables

### Fonts excloses de moment
- xarxes socials
- fonts sense autoria clara
- contingut clarament promocional

## Regla de treball

No avancem al següent agent fins que l'anterior estigui prou clar en aquests tres punts:

1. que fa
2. quin input rep
3. quin output dona

I, si reutilitzem un repositori extern:

4. quant codi ens estalvia
5. si realment encaixa amb el cas pilot

## Agent 1. Document Loader

### Objectiu
Carregar el document corporatiu i convertir-lo en text usable.

### Input
- ruta del PDF o document

### Output
- text extret per pagines o concatenat
- metadades minimes del document

### Eines candidates
- `PyMuPDF`
- `docling`
- `reportparse` com a reader mes ric, si val la pena

### Decisio actual
- ens quedem amb `PyMuPDF`
- `reportparse` es descarta per ara per complexitat d'instal lacio i integracio

### Que s'ha de validar abans de passar al seguent agent
1. el text del PDF surt de manera llegible
2. no hi ha massa soroll greu
3. es pot localitzar el contingut per pagina

### Pregunta a resoldre en aquest agent
- resposta actual: `PyMuPDF` ja basta per al document pilot de Microsoft

### Sortida minima recomanada d'aquest agent
- text per pagina o text concatenat
- nom del document
- ruta del document
- nombre de pagines
- metadata basica si esta disponible

### Estat actual
- `Document Loader` es considera validat per al MVP
- el text i el `pages.csv` del document pilot son prou bons per alimentar el seguent agent

### Millores futures possibles
- millor neteja de soroll de pagina
- millor tractament de taules
- segmentacio per seccions
- suport per altres formats

### Nota sobre metadata
La metadata del PDF pot ser util, pero no es el centre del pipeline.

Metadata minima recomanada:
- `title`
- `author` si existeix
- `subject` si existeix
- `creationDate` si existeix
- `page_count`

Si la metadata ve buida o es poc fiable, no passa res. El que realment importa es el text usable del document.

## Agent 2. Claim Extractor

### Objectiu
Extreure frases o fragments que contenen claims rellevants.

### Input
- text del document carregat

### Output
- llista de claims candidats

### Eines candidates
- `reportparse`
- LLM amb sortida estructurada
- suport amb `spaCy` o regles simples si cal

### Decisio provisional actual
- usar un `LLM` per extreure claims
- guardar la sortida en un `CSV`
- afegir un petit preprocessament abans de la crida al model
- fer una crida per pagina a partir del `pages.csv`
- afegir post-filtratge per reduir soroll

### Que s'ha de validar abans de passar al seguent agent
1. els claims extrets son realment afirmacions oficials
2. no es limiten nomes a claims numerics
3. no s'omple de frases massa vagues o inutils
4. els claims futurs es poden marcar a part

### Pregunta a resoldre en aquest agent
- resposta provisional: farem extractor propi amb `LLM`

### Preprocessament recomanat abans del claim extraction
- dividir el document per pagines o blocs manejables
- eliminar parts massa buides
- mantenir la referencia de pagina
- si cal, eliminar soroll repetitiu evident com headers i footers

### Sortida recomanada del Claim Extractor
CSV amb com a minim aquestes columnes:
- `claim_id`
- `document_name`
- `page_number`
- `claim_text`
- `claim_type`
- `topic`
- `is_future`
- `is_verifiable`
- `is_reporting_claim`
- `claim_quality_score`
- `source_excerpt`

### Pipeline actual de l'Agent 2
1. llegir el `pages.csv` generat a l'Agent 1
2. per cada pagina util, fer una crida al model
3. rebre zero o mes claims d'aquella pagina
4. afegir aquests claims a una taula temporal
5. quan acaben totes les pagines, guardar-ho en un `claims.csv`

### Nota metodologica
L'ús de prompt engineering aqui es important per reduir soroll.

El model pot al lucionar o extreure frases massa vagues si la instruccio es massa oberta. Per aixo s'ha restringit la definicio de claim, s'han afegit exclusions clares i s'ha obligat el model a ser mes conservador.

La idea no es eliminar completament el risc, sino reduir-lo i deixar la sortida prou neta per al seguent agent.

### Estat actual
- `Claim Extractor` es considera suficient per continuar amb el MVP
- ja produeix un `claims.csv` usable
- encara hi ha una mica de soroll, sobretot en claims de reporting o metodologia, pero no bloqueja el pas al seguent agent

### Millores futures possibles
- separar millor reporting claims i claims substantius
- fer el prompt encara mes fi
- millorar el tractament de pagines amb molt format de taula
- afegir una revisio o filtre extra si cal

### Emmagatzematge actual recomanat
- `CSV` per al MVP, per simplicitat i facilitat d'inspeccio manual
- si el projecte creix, es pot afegir `JSON` o `SQLite` mes endavant

## Agent 3. Claim Normalizer

### Objectiu
Eliminar duplicats i unificar claims equivalents.

### Input
- claims candidats

### Output
- claims normalitzats
- claims futurs separats si cal

### Eines candidates
- `RapidFuzz`
- `sentence-transformers`

### Que s'ha de validar abans de passar al seguent agent
1. claims repetits agrupats correctament
2. claims diferents no fusionats per error

### Decisio actual
- fer una versio simple basada en text normalization + `SequenceMatcher`
- separar els claims `FUTURE` en un fitxer a part
- mantenir el codi senzill i facil d'entendre

### Sortida actual recomanada del Claim Normalizer
- `normalized_claims.csv`
- `future_claims.csv`

### Pipeline actual de l'Agent 3
1. llegir el `claims.csv` generat pel `Claim Extractor`
2. separar els claims futurs
3. comparar els claims restants entre si
4. fusionar duplicats o quasi duplicats obvis
5. guardar una versio normalitzada per al seguent agent

### Estat actual
- `Claim Normalizer` ja te una primera implementacio funcional
- fa deduplicacio simple i separa `FUTURE`
- es suficient per continuar amb el MVP

### Millores futures possibles
- usar `RapidFuzz`
- usar embeddings per similitud semantica
- millorar l'eleccio de la forma canonica del claim
- refinar el llindar de similitud segons resultats reals

## Agent 4. Query Generator

### Objectiu
Generar consultes per buscar evidencia externa.

### Input
- claim normalitzat

### Output
- exactament 3 queries utiles per claim

### Eines candidates
- LLM
- `KeyBERT`
- vocabulari de suport com `taxonomy4good`

### Decisio actual
- generar les queries automaticament
- fer-ho claim per claim
- usar sortida estructurada
- generar exactament 3 queries per claim:
  - `core`
  - `verification`
  - `critical`
- usar un model local via `Ollama`
- prioritzar baixa latencia i simplicitat sobre maxima potencia

### Model local recomanat ara mateix
- `mistral-nemo:latest`

### Per que aquest model
- es mes lleuger i rapid que `qwen2.5:14b`
- per query generation no cal el model mes fort del pipeline
- la tasca es mes simple: reformular i orientar la cerca
- redueix temps total quan hi ha molts claims

### Alternatives si cal
- `qwen2.5:14b` si vols mes qualitat
- `gemma3:12b` si el comportament del model et convenç mes

### Sortida recomanada del Query Generator
CSV amb com a minim aquestes columnes:
- `normalized_claim_id`
- `query_type`
- `query_text`

### Pipeline actual de l'Agent 4
1. llegir el `normalized_claims.csv`
2. per cada claim, fer una crida al model local
3. generar exactament 3 queries:
   - `core`
   - `verification`
   - `critical`
4. afegir les queries a una taula temporal
5. guardar un `queries.csv`

### Nota metodologica
El `Query Generator` no ha de ser creatiu de mes.

La seva funcio no es trobar la contradiccio per si sol, sino generar consultes prou bones per donar al `Web Search` oportunitats reals de trobar:
- suport
- verificacio externa
- critica o contradiccio

### Que s'ha de validar abans de passar al seguent agent
1. les queries no son massa generiques
2. les queries recuperen fonts potencialment utiles

## Agent 5. Web Search

### Objectiu
Buscar fonts externes candidates.

### Input
- queries

### Output
- llista de URLs i snippets

### Eines candidates
- `ddgs`
- `SearXNG` nomes si cal mes endavant

### Decisio actual
- usar `ddgs`
- recuperar resultats candidats a partir de `queries.csv`
- excloure dominis propietat de l'empresa
- mantenir nomes resultats externs que segueixen mencionant l'empresa

### Nota metodologica
Per aquest TFM, els resultats de la mateixa empresa no compten com a evidencia externa principal.

Per aixo, el `Web Search` aplica una politica simple:
- buscar normalment
- eliminar dominis corporatius propis
- conservar nomes resultats externs pero encara relacionats amb l'empresa

### Que s'ha de validar abans de passar al seguent agent
1. les fonts trobades son raonables
2. no hi ha massa soroll

## Agent 6. Evidence Fetcher

### Objectiu
Descarregar i netejar el text de les fonts recuperades.

### Input
- URLs

### Output
- text net de les pagines externes

### Eines candidates
- `trafilatura`
- `jusText` com a fallback

### Que s'ha de validar abans de passar al seguent agent
1. el text s'extreu be
2. el boilerplate no domina el contingut

## Agent 7. Reranker

### Objectiu
Ordenar la millor evidencia externa per a cada claim.

### Input
- claim
- evidencies recuperades

### Output
- top evidencies per claim

### Eines candidates
- `FlagEmbedding`
- `rerankers`

### Decisio actual
- usar una primera versio simple i open source
- no introduir encara embeddings ni cross-encoders
- puntuar la rellevancia amb heuristiques transparents i facils d'entendre

### Pipeline actual de l'Agent 7
1. llegir `normalized_claims.csv`
2. llegir `evidence_candidates.csv`
3. eliminar evidencies fallides o massa buides
4. calcular una puntuacio de rellevancia per claim-evidence
5. ordenar les evidencies dins de cada claim
6. guardar `ranked_evidence.csv`

### Sortida actual recomanada del Reranker
- `ranked_evidence.csv`

### Nota metodologica
Per al MVP, el reranking actual no es semanticament sofisticat.

Combina:
- overlap del claim amb title
- overlap del claim amb snippet
- overlap del claim amb extracted text
- un petit bonus pel rang original de cerca
- un petit bonus segons el tipus de query

### Estat actual
- `Reranker` ja te una primera implementacio funcional
- es suficient per prioritzar candidats abans de l'analisi final

### Millores futures possibles
- `RapidFuzz`
- `sentence-transformers`
- `rerankers`
- cross-encoders
- reranking per chunks en lloc de document complet

### Que s'ha de validar abans de passar al seguent agent
1. la millor evidencia queda a dalt
2. les fonts dubtoses baixen de prioritat

## Agent 8. Evidence Analyzer

### Objectiu
Comparar claim i evidencia per obtenir stance.

### Input
- claim
- top evidencies

### Output
- label de la rúbrica
- justificacio curta

### Eines candidates
- `MiniCheck`
- `transformers` amb NLI
- LLM com a consolidacio si cal

### Decisio actual
- usar un LLM local via `Ollama`
- model recomanat ara mateix: `qwen2.5:14b`
- analitzar cada claim amb les seves 3 millors evidencies
- usar sortida estructurada i guardar un CSV final d'avaluacions

### Pipeline actual de l'Agent 8
1. llegir `normalized_claims.csv`
2. llegir `ranked_evidence.csv`
3. quedar-se amb el top 3 d'evidencia per claim
4. construir un prompt estructurat per claim
5. classificar el claim com `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED` o `CONTRADICTED`
6. guardar `claim_assessments.csv`

### Sortida actual recomanada de l'Evidence Analyzer
- `claim_assessments.csv`

### Nota metodologica
Per al MVP, l'analitzador actual utilitza un LLM i no un sistema NLI separat.

La instruccio del prompt esta dissenyada per evitar contradiccions falses i forcar el model a preferir `UNSUPPORTED` quan l'evidencia es feble.

### Estat actual
- `Evidence Analyzer` ja te una primera implementacio funcional
- es suficient per fer una primera avaluacio claim-evidence en el MVP

### Millores futures possibles
- afegir un camp de confiança
- fer servir evidència per chunks en lloc de documents complets
- comparar amb una baseline NLI
- afegir evidència secundaria

### Que s'ha de validar abans de passar al seguent agent
1. el label te sentit
2. la justificacio es coherent
3. els `FUTURE` queden fora de l'avaluacio principal

## Agent 9. Judge / Aggregator

### Objectiu
Construir la sortida final per a l'usuari.

### Input
- resultats per claim

### Output
- resum final
- visio global del discurs
- risc o indicis de greenwashing

### Eines candidates
- `pandas`
- LLM opcional per redactar el resum final

### Decisio actual
- usar una primera versio rule-based
- no usar encara un LLM per al resum final
- generar sortides finals estructurades i faciles d'inspeccionar

### Pipeline actual de l'Agent 9
1. llegir `claim_assessments.csv`
2. comptar labels finals
3. comptar claims futurs exclosos
4. construir una conclusio global simple amb regles
5. guardar `final_report.csv`, `final_report.json` i `final_summary.md`

### Sortida actual recomanada del Judge / Aggregator
- `final_report.csv`
- `final_report.json`
- `final_summary.md`

### Nota metodologica
Per al MVP, aquest ultim agent no reavalua els claims.

La seva funcio es agregar i resumir els resultats ja produïts pels agents anteriors.

### Estat actual
- `Judge / Aggregator` ja te una primera implementacio funcional
- el MVP del pipeline ja es pot considerar complet

### Millores futures possibles
- afegir un credibility score
- afegir un greenwashing risk score
- usar un LLM per escriure una conclusio final mes rica
- incorporar evidència secundaria o cites addicionals al resum final

## Ordre real de treball a partir d'ara

1. Agent 1: provar `PyMuPDF` i `reportparse` amb el document pilot de Microsoft
2. Agent 2: decidir com extreure claims del document pilot
3. Agent 3: deduplicacio i separacio de `FUTURE`
4. Agent 4: query generation
5. Agent 5: cerca web
6. Agent 6: neteja de fonts
7. Agent 7: reranking
8. Agent 8: stance
9. Agent 9: agregacio final

## Decisio de metodologia

Des d'ara treballarem sempre aixi:

- un agent cada vegada
- primer mirar si hi ha codi reutilitzable
- despres provar-lo amb el cas pilot
- nomes si no serveix, escriure implementacio propia
