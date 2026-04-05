# Decisions actuals i seguents passos

## 1. Scope actual del sistema

### Input del sistema
- L'usuari selecciona una empresa des d'un `dropdown`.
- Els documents d'aquesta empresa ja venen predefinits pel sistema.
- Els documents seran principalment `PDF`, tot i que mes endavant pot caldre acceptar altres formats.

### Tipus de claims a analitzar
- qualsevol afirmacio o statement oficial de l'empresa relacionat amb sostenibilitat, CSR, etica, governanca o impacte social/ambiental
- no nomes claims numerics
- tambe poden ser compromisos, politiques, declaracions corporatives, practiques descrites o afirmacions qualitatives

### Definicio operativa actual de claim
Un claim es qualsevol afirmacio oficial feta per l'empresa en documents corporatius que descrigui una practica, politica, resultat, compromís o posicionament relacionat amb sostenibilitat, etica, governanca o responsabilitat corporativa, i que pugui ser contrastat totalment o parcialment amb evidencia externa.

### Claims que, de moment, es tractaran a part
- claims clarament futurs o aspiracionals

Tractament actual:
- es poden detectar i etiquetar com a `future`
- no entren de moment en l'avaluacio principal del MVP

### Fonts externes acceptades
- articles
- noticies
- mitjans o fonts amb credibilitat minima
- articles d'experts
- webs fiables
- reguladors
- ONG reconegudes
- informes independents o d'auditoria

### Criteri orientatiu de qualitat de fonts externes
Prioritat mes alta:
- reguladors i organismes publics
- ONG reconegudes
- informes independents o d'auditoria
- premsa economica o generalista de reputacio alta

Prioritat acceptable:
- articles d'experts o think tanks amb autoria clara
- webs institucionals o organitzacions reconegudes

Prioritat baixa o a penalitzar:
- blogs sense autoria clara
- agregadors
- contingut promocional
- pagines sense data o sense font clara

### Fonts que, de moment, es recomana no incloure
- xarxes socials

Motiu:
- redueixen la fiabilitat del sistema
- compliquen molt la justificacio academica
- afegeixen soroll i mes feina de filtratge

### Output final esperat
- resum final argumentat sobre si l'empresa presenta o no indicis de greenwashing
- percentatge o score final de greenwashing
- resultat per claim amb justificacio i evidencia associada

### Notes metodologiques actuals
- les fonts de la propia empresa no comptaran com a evidencia externa principal
- l'angles sera l'idioma principal del MVP
- altres idiomes es poden acceptar si no compliquen gaire el pipeline

## 2. Decisions tecnologiques actuals

### Ja decidit
- Orquestracio: `LangGraph`
- Document Loader: `PyMuPDF`
- Claim Extractor: `LLM structured output`
- Claim Normalizer: `sentence-transformers` + `RapidFuzz`
- Web Search: `duckduckgo-search` o `SearxNG`
- Reranker: `bge-reranker`
- Evidence Analyzer: `NLI + LLM`
- Judge: `LLM`

## 3. Recomanacions concretes per als moduls encara no tancats

### 3.1 Embeddings i deduplicacio
Recomanacio:
- `sentence-transformers`

Motiu:
- es molt reutilitzable
- evita entrenar res
- va be per similitud semantica entre claims

Model suggerit:
- `all-MiniLM-L6-v2` per simplicitat inicial

### 3.2 Postprocessat NLP lleuger
Recomanacio:
- `spaCy`

Motiu:
- et pot ajudar a detectar dates, quantitats, organitzacions i petites validacions
- no cal que sigui el nucli de l'extractor, nomes suport

### 3.3 Cerca web
Recomanacio inicial:
- `duckduckgo-search`

Motiu:
- es rapid de provar
- et permet fer un primer prototip sense muntar infraestructura

Recomanacio si mes endavant cal mes control:
- `SearxNG`

### 3.4 Extraccio de text web
Recomanacio:
- `trafilatura`

Motiu:
- et neteja les pagines recuperades i et deixa text usable per l'analisi

### 3.5 Reranking
Recomanacio:
- `FlagEmbedding` amb `bge-reranker`

Motiu:
- es una de les millors peces reutilitzables per prioritzar evidencia realment rellevant

### 3.6 Evidence Analyzer
Recomanacio:
- baseline amb `NLI`
- consolidacio final amb `LLM`

Motiu:
- el NLI et dona una base mes interpretable
- l'LLM et permet resoldre casos amb mes context i redactar justificacions

### 3.7 Judge final
Recomanacio:
- `LLM` amb sortida estructurada via schemas Pydantic

Motiu:
- et permet produir un resultat coherent i agregat sense muntar massa logica manual des del principi

## 4. Decisio metodologica important

El sistema no ha d'intentar demostrar legalment que una empresa fa greenwashing.

El sistema ha de produir:
- indicis
- nivell de suport dels claims
- percentatge o index de credibilitat / greenwashing basat en evidencia

Per tant, una formulacio mes segura es:

- `Greenwashing Risk Score`
- `Indicis de greenwashing`

En lloc de presentar-ho com una veritat absoluta.

## 5. Com calcular el percentatge final

Per no complicar massa el TFM, es recomana reutilitzar el score de credibilitat i transformar-lo en risc de greenwashing.

### Opcio simple

```text
Credibility Score =
(1.0 * supported + 0.5 * partially_supported + 0.0 * unsupported - 0.5 * contradicted) / total_claims
```

Despres:

```text
Greenwashing Risk Percentage = (1 - normalized_credibility_score) * 100
```

On `normalized_credibility_score` es pot escalar a rang `0..1`.

La idea important es que:
- mes claims contradits o no sostinguts -> mes risc
- mes claims sostinguts -> menys risc

## 6. Recomanacio de MVP realista

Per falta de temps, el MVP hauria de fer nomes aixo:

1. seleccionar una empresa pilot
2. carregar els documents corporatius ja associats
3. extreure claims rellevants de qualsevol tipus oficial relacionat amb CSR / etica / sostenibilitat / governanca
4. marcar a part els claims futurs
5. deduplicar els claims restants
6. generar queries
7. recuperar unes poques fonts externes fiables
8. classificar els claims
9. produir un resum final i un percentatge de risc de greenwashing

### Empresa pilot actual
- `Microsoft`

### Documents a incloure
- sustainability reports
- annual reports
- governance reports
- code of ethics
- altres documents corporatius oficials rellevants

No incloure de moment:
- xarxes socials
- moltes empreses alhora
- moltes fonts exotiques
- UI complexa
- comparatives molt grans entre models

## 7. Seguent pas prioritari

L'ordre correcte de treball a partir d'ara es:

1. decidir exactament el conjunt d'eines finals
2. preparar l'entorn i dependències
3. provar `PyMuPDF` amb un PDF real
4. definir el prompt del `Claim Extractor`
5. provar una extraccio petita i manualment revisar-la
6. implementar la normalitzacio de claims
7. connectar la cerca web
8. connectar fetch + neteja de text
9. connectar reranking
10. definir stance i score final

## 8. Missatge clau de treball

Com que no hi ha tant temps, cada modul s'ha de construir aixi:

- primer una versio minima que funcioni
- despres validacio manual
- nomes despres refinament

L'objectiu no es fer el sistema perfecte, sino un sistema modular, reutilitzable, traçable i defensable per al TFM.
