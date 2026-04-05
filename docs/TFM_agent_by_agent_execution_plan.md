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
- `confidence`
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

## Agent 4. Query Generator

### Objectiu
Generar consultes per buscar evidencia externa.

### Input
- claim normalitzat

### Output
- 2 o 3 queries utiles per claim

### Eines candidates
- LLM
- `KeyBERT`
- vocabulari de suport com `taxonomy4good`

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

### Nota actual
- el score final no es prioritari ara mateix
- ara ens centrarem primer en fer funcionar el pipeline

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
