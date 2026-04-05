# Estructura de referencia del TFM

## 1. Formulacio del TFM

### Titol provisional
`Sistema multi-agent per a l'analisi de credibilitat del discurs CSR i deteccio d'indicis de greenwashing`

### Problema
Les empreses publiquen informes i declaracions de sostenibilitat, pero aquestes afirmacions no sempre son consistents amb evidencia externa. Cal un sistema que pugui extreure claims, contrastar-los i generar una avaluacio estructurada de credibilitat.

### Objectiu general
Dissenyar i implementar un sistema multi-agent orquestrat amb LangGraph capac d'analitzar el discurs CSR d'una empresa, extreure claims rellevants, contrastar-los amb evidencia externa i estimar el nivell de suport i el risc potencial de greenwashing.

### Objectius especifics
1. Definir una representacio formal dels claims i de l'evidencia mitjancant esquemes Pydantic.
2. Implementar un pipeline seqüencial multi-agent per a extraccio, cerca, contrast i judici final.
3. Desenvolupar un metode de classificacio de claims: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`.
4. Definir un index agregat de credibilitat discursiva.
5. Avaluar la qualitat del sistema sobre casos reals d'empreses.

### Pregunta de recerca
`Fins a quin punt un sistema multi-agent basat en LLMs i evidencia externa pot ajudar a avaluar la credibilitat del discurs de sostenibilitat d'una empresa i detectar indicis de greenwashing?`

### Hipotesi
Un pipeline estructurat amb agents especialitzats, esquemes rigids i contrast amb fonts externes pot produir analisis mes tracables i utils que una resposta monolitica d'un unic LLM.

## 2. Abast del projecte

### Inclòs
- Empreses concretes
- Documents CSR / ESG / sustainability reports
- Claims sobre sostenibilitat, emissions, energia, cadena de subministrament, etica, drets laborals i governanca responsable
- Evidencia externa textual accessible via web
- Classificacio i score final

### Exclos
- Verificacio juridica completa
- Fact-checking exhaustiu sobre tota l'empresa
- Analisi multimodal profunda de grafics o PDFs escanejats
- Monitoratge continu en temps real

## 3. Especificacions del sistema

### Requisits funcionals
1. El sistema ha de rebre una consulta en llenguatge natural sobre una empresa.
2. Ha de seleccionar o rebre documents corporatius rellevants.
3. Ha d'extreure claims CSR rellevants.
4. Ha de normalitzar i deduplicar claims.
5. Ha de generar consultes de cerca per claim.
6. Ha de recuperar evidencia externa tracable.
7. Ha de classificar cada claim segons el nivell de suport.
8. Ha de generar una justificacio textual per claim.
9. Ha de calcular un score agregat.
10. Ha de produir una conclusio final sobre possibles indicis de greenwashing.

### Requisits no funcionals
1. Tracabilitat: cada resultat ha d'estar vinculat a fonts i passos intermedis.
2. Robustesa de format: us d'esquemes Pydantic.
3. Modularitat: agents separats amb inputs/outputs definits.
4. Reproductibilitat: prompts, parametres i flux documentats.
5. Explicabilitat: justificacions clares per claim.
6. Escalabilitat moderada: arquitectura ampliable a mes empreses o fonts.
7. Mantenibilitat: codi documentat i components encapsulats.

## 4. Disseny conceptual del sistema

```text
Usuari
  ->
Input en llenguatge natural sobre una empresa
  ->
Document Selector / Loader
  ->
Claim Extractor
  ->
Claim Normalizer / Deduplicator
  ->
Query Generator
  ->
Web Search + Source Filter
  ->
Evidence Analyzer
  ->
LLM Judge / Aggregator
  ->
Output final:
- claims
- evidencia
- stance
- justificacio
- credibility score
- conclusio de greenwashing
```

## 5. Arquitectura proposada amb LangGraph

### Per que LangGraph?
- Permet orquestrar passos explicits
- Facilita estat compartit entre nodes
- Es millor que un agent autonom lliure quan vols tracabilitat
- Permet retries, branching i validacio d'estat

### Estat global del graf
El graf pot mantenir un objecte `PipelineState` amb:
- `company_name`
- `user_query`
- `documents`
- `claims`
- `search_queries`
- `evidence_items`
- `claim_assessments`
- `final_report`

### Nodes minims
1. `load_documents`
2. `extract_claims`
3. `normalize_claims`
4. `generate_queries`
5. `search_evidence`
6. `filter_sources`
7. `analyze_evidence`
8. `judge_and_aggregate`
9. `render_output`

## 6. Agents i responsabilitats

### 1. Claim Extractor
- Input: documents corporatius
- Output: llista de claims candidats
- Funcions:
  - extraccio
  - resum curt del claim
  - ubicacio al document
  - tema CSR
  - prioritzacio

### 2. Claim Normalizer
- Input: claims candidats
- Output: claims unics i normalitzats
- Funcions:
  - deduplicacio semantica
  - reformulacio clara
  - eliminacio de claims massa vagues

### 3. Query Generator
- Input: claim
- Output: consultes de cerca
- Funcions:
  - variants per tema
  - variants temporals
  - variants amb nom d'empresa i paraules clau de verificacio

### 4. Web Search
- Input: queries
- Output: fonts candidates
- Funcions:
  - cerca
  - recuperacio de snippets/meta
  - filtratge inicial de qualitat

### 5. Evidence Analysis
- Input: claim + evidencia
- Output: stance + justificacio
- Categories:
  - `SUPPORTED`
  - `PARTIALLY_SUPPORTED`
  - `UNSUPPORTED`
  - `CONTRADICTED`

### 6. LLM Judge
- Input: analisi per claim
- Output: informe final
- Funcions:
  - revisio de consistencia
  - agregacio
  - score global
  - conclusio final

## 7. Definicio formal de claim

### Definicio operativa
Un claim es una afirmacio explicita o implicita feta per l'empresa sobre practiques, resultats, compromisos o impactes relacionats amb sostenibilitat, responsabilitat social, governanca o etica corporativa, susceptible de ser contrastada amb evidencia externa.

### Tipus de claims
1. Performance claims
Ex: `Hem reduit les emissions un 30%`.

2. Commitment claims
Ex: `Assolirem neutralitat climatica el 2040`.

3. Policy claims
Ex: `Apliquem estandards estrictes de drets laborals`.

4. Recognition claims
Ex: `Som liders en sostenibilitat al sector`.

Es recomana limitar l'abast als tres primers, ja que el quart es mes ambigu i dificil de verificar.

## 8. Esquemes de dades amb Pydantic

### Claim
- `claim_id`
- `company`
- `source_document`
- `source_excerpt`
- `claim_text`
- `claim_type`
- `topic`
- `time_reference`
- `priority`

### SearchQuery
- `claim_id`
- `query_text`
- `query_type`
- `rationale`

### EvidenceItem
- `evidence_id`
- `claim_id`
- `url`
- `source_name`
- `source_type`
- `publication_date`
- `snippet`
- `relevance_score`
- `credibility_score`

### ClaimAssessment
- `claim_id`
- `stance`
- `justification`
- `supporting_evidence_ids`
- `confidence`
- `notes`

### FinalReport
- `company`
- `total_claims`
- `supported`
- `partially_supported`
- `unsupported`
- `contradicted`
- `credibility_score`
- `greenwashing_risk_level`
- `final_conclusion`

## 9. Score agregat

```text
Credibility Score =
(1.0 * supported + 0.5 * partially_supported + 0.0 * unsupported - 0.5 * contradicted) / total_claims
```

### Interpretacio suggerida
- `0.75 - 1.00`: credibilitat alta
- `0.40 - 0.74`: credibilitat moderada
- `0.00 - 0.39`: credibilitat baixa
- `< 0.00`: indicis forts d'inconsistencia o greenwashing

## 10. Criteris de qualitat de l'evidencia

### Dimensions per filtrar fonts
1. Rellevancia respecte al claim
2. Fiabilitat de la font
3. Tracabilitat
4. Actualitat temporal
5. Especificitat

### Tipus de fonts prioritaries
1. Reguladors i organismes publics
2. ONG reconegudes
3. Premsa de reputacio alta
4. Bases de dades ESG o informes independents
5. Web corporativa de tercers o informes d'auditoria

### Fonts a penalitzar
- blogs sense autoria clara
- contingut promocional
- agregadors sense verificacio
- pagines duplicades o sense data

## 11. Metodologia d'avaluacio

### Avaluacio recomanada
1. Seleccionar un conjunt petit pero representatiu d'empreses.
2. Recollir documents CSR oficials.
3. Executar el pipeline.
4. Fer una revisio manual d'una mostra de claims.
5. Comparar sortides del sistema amb criteri huma.

### Metriques possibles
- Precisio en extraccio de claims
- Qualitat de recuperacio d'evidencia
- Acord en classificacio de stance
- Percentatge de claims amb justificacio tracable
- Temps per analisi

### Gold standard minim
- `2-4` empreses
- `10-20` claims per empresa
- etiquetatge manual d'una mostra

## 12. Disseny experimental

### Experiment 1
Sense deduplicacio ni normalitzacio de claims.

### Experiment 2
Amb deduplicacio i normalitzacio.

### Experiment 3
Amb LLM Judge final.

També es pot comparar:
- pipeline estructurat
- una unica crida monolitica a un LLM

## 13. Seleccio de tecnologies

### Tecnologies proposades
- `Python`: ecosistema principal
- `LangGraph`: orquestracio
- `Pydantic`: validacio d'esquemes
- `LLM API`: extraccio, analisi i judici
- `Web search API` o equivalent: recuperacio externa
- `Jupyter` o scripts: experiments
- `pytest`: tests
- `logging`: tracabilitat
- `Sphinx` o docstrings estil Google/NumPy: documentacio

### Justificacio resumida
- Python per flexibilitat i ecosistema NLP
- Pydantic per robustesa de dades
- LangGraph per control explicit del workflow

## 14. Estructura del repositori

```text
project/
  data/
    raw/
    processed/
    evaluation/
  docs/
  notebooks/
  src/
    models/
    schemas/
    agents/
    graph/
    retrieval/
    evaluation/
    utils/
  tests/
  config/
```

## 15. Estructura de la memoria

1. Introduccio
2. Problema i motivacio
3. Objectius
4. Estat de l'art
5. Requisits i especificacions
6. Disseny del sistema
7. Arquitectura i model de dades
8. Implementacio
9. Metodologia experimental
10. Resultats
11. Discussio
12. Limitacions
13. Conclusions i treball futur

## 16. Contribucio academica defensable

1. Proposta d'un pipeline multi-agent tracable per a analisi CSR.
2. Definicio formal d'esquemes intermedis per controlar el flux.
3. Metode per agregar suport de claims en un index de credibilitat.
4. Marc d'avaluacio per detectar indicis de greenwashing a partir de discurs corporatiu.

## 17. Riscos i limitacions

1. Els LLM poden inventar relacions o exagerar suport.
2. La qualitat de la cerca externa condiciona tot el pipeline.
3. Alguns claims son massa vagues per ser verificables.
4. La classificacio de greenwashing no es equivalent a una prova legal.
5. El conjunt d'avaluacio pot ser limitat per temps de TFM.

## 18. Pla de treball recomanat

### Fase 1. Disseny
- concretar objectius
- definir claim
- definir esquemes Pydantic
- fer diagrama de blocs
- decidir tecnologies

### Fase 2. Prototip base
- carrega de documents
- extraccio de claims
- normalitzacio
- output estructurat

### Fase 3. Recuperacio externa
- generacio de queries
- cerca
- filtratge de fonts

### Fase 4. Analisi
- stance per claim
- justificacio
- score global

### Fase 5. Avaluacio
- casos reals
- revisio manual
- metriques i discussio

### Fase 6. Redaccio
- memoria
- figures
- annexos tecnics

## 19. Recomanacio practica

Si es vol fer viable dins d'un TFM, una versio minima pero forta seria:

1. `Input`: empresa + documents CSR
2. `Claim extractor + normalizer`
3. `Query generator`
4. `Web search`
5. `Evidence analysis`
6. `Final judge`
7. `Credibility score`

No cal afegir mes agents per ara. Es millor un sistema petit, ben justificat i ben avaluat, que un sistema molt ampli pero poc controlat.

## 20. Pitch curt del projecte

> Aquest TFM proposa un sistema multi-agent orquestrat amb LangGraph per analitzar la credibilitat del discurs CSR d'una empresa. El sistema extreu claims rellevants de documents corporatius, genera consultes per recuperar evidencia externa, avalua el grau de suport de cada afirmacio i produeix un informe final amb justificacions estructurades i un index agregat de credibilitat discursiva, amb l'objectiu d'identificar possibles indicis de greenwashing.
