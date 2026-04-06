# Agent 1 - Document Loader test plan

Objectiu: decidir quina eina farem servir per al primer agent del pipeline per carregar i extreure text del document pilot de Microsoft.

Document pilot:
- Microsoft Environmental Sustainability Report

Eines a comparar:
1. `PyMuPDF`
2. `reportparse`

No decidirem encara res sobre claims, stance o greenwashing. Aqui nomes validem el carregador del document.

## Pregunta principal

Quina eina ens dona una millor relacio entre:
- facilitat d'ús
- qualitat del text extret
- control sobre les pagines
- codi que ens estalvia
- complexitat d'instal lacio

## Criteri de decisio

Triar l'eina que:
- sigui prou bona per al document pilot
- sigui facil d'entendre i mantenir
- no introdueixi una complexitat absurda per al TFM

## Prova 1. PyMuPDF

### Objectiu
Comprovar si `PyMuPDF` ja extreu prou be el text del PDF per poder passar al seguent agent.

### Que has de provar
1. carregar el PDF
2. extreure text pagina per pagina
3. mirar si el text surt en ordre raonable
4. mirar si hi ha massa soroll
5. mirar si es poden localitzar frases rellevants per pagina

### Que has de revisar manualment
1. el text es llegeix be o surt trencat?
2. hi ha headers i footers repetits molestant molt?
3. les taules destrueixen massa el text?
4. les frases importants son recognoscibles?
5. pots trobar facilment una frase i saber de quina pagina ve?

### Senyals que `PyMuPDF` ja et basta
- el text es majoritariament llegible
- les seccions importants es poden seguir
- el soroll es tolerable
- no necessites gaire mes que text per pagina

### Senyals que `PyMuPDF` no basta
- el text surt molt desordenat
- hi ha massa trossos inservibles
- les pagines tenen layouts que trenquen massa la lectura
- les parts importants del document es perden o queden molt mal extretes

## Prova 2. reportparse

### Objectiu
Comprovar si `reportparse` et resol millor el parsing i et dona estructura o senyals utiles que t'estalviin feina mes endavant.

### Abast de la prova
No cal provar tot `reportparse`.

Prova nomes:
1. reader amb `pymupdf`
2. si es viable, algun annotator basic rellevant

No et fiquis d'entrada amb:
- `deepdoctection`
- taules
- figures
- layouts complicats

### Que has de provar
1. si s'instal la sense massa drama
2. si pot llegir el document pilot
3. si et dona una sortida mes estructurada que `PyMuPDF`
4. si et detecta ja coses útils com:
   - `environmental_claim`
   - `esg_bert`
   - `standard_keyword`

### Que has de revisar manualment
1. et dona frases o segments útils?
2. el format de sortida es facil de reutilitzar?
3. et resol una part real del problema o nomes afegeix pes?
4. el cost d'instal lacio i dependències compensa el benefici?

### Senyals que `reportparse` et convé
- et detecta claims o topics útils del document pilot
- et dona CSV o JSON reutilitzable directament
- et redueix molt el codi del primer i segon agent

### Senyals que `reportparse` no et convé
- la instal lacio es massa pesada
- el guany respecte `PyMuPDF` es petit
- es queda massa limitat a sustainability / climate i no et serveix prou per a la resta de documents

## Com comparar les dues eines

Omple aquesta taula despres de provar-les:

| Criteri | PyMuPDF | reportparse |
|---|---|---|
| Facilitat d'instal lacio |  |  |
| Facilitat d'ús |  |  |
| Qualitat del text |  |  |
| Estructura reutilitzable |  |  |
| Codi que t'estalvia |  |  |
| Complexitat afegida |  |  |
| Decisio final |  |  |

## Decisio possible al final de l'Agent 1

### Opcio A
Quedar-nos amb `PyMuPDF`.

Interpretacio:
- parsing prou bo
- menys dependències
- mes simple per al TFM

### Opcio B
Usar `reportparse` per al primer tram del pipeline.

Interpretacio:
- aporta valor real en parsing o deteccio inicial de claims/temes

### Opcio C
Usar `PyMuPDF` com a base i `reportparse` nomes com a prova o referencia.

Interpretacio:
- `reportparse` es interessant, pero no prou per convertir-lo en peca central

## Decisio actual

- ens quedem amb `PyMuPDF`
- `reportparse` es descarta per ara per complexitat d'instal lacio i integracio

## Estat actual de Document Loader

### Que fa ara
- obre el PDF pilot amb `PyMuPDF`
- extreu text per pagina
- fa una neteja basica de linies buides i espais
- detecta i elimina linies repetides probables de header o footer
- guarda una versio processada del text
- guarda un `pages.csv` amb text per pagina
- guarda metadata basica del PDF

### Per que el donem per validat
- el text del document pilot de Microsoft surt de forma prou llegible
- es conserva la referencia de pagina
- el `pages.csv` serveix com a input del seguent agent
- la complexitat es baixa i el codi es senzill d'entendre

### Que es podria millorar mes endavant
- neteja millor de headers i footers repetits
- tractament millor de pagines amb taules complexes
- segmentacio per blocs o seccions, no nomes per pagina
- suport addicional per altres formats de documents
- guardar metadades una mica mes riques si realment aporten valor

## Resultat que volem tenir abans de passar a l'Agent 2

Abans de passar al Claim Extractor, hem de poder dir una frase com aquesta:

> Per al document pilot de Microsoft, hem validat que l'eina X ens permet carregar el PDF i obtenir text prou usable per extreure claims oficials de sostenibilitat.

Quan aquesta frase sigui veritat, passem a l'Agent 2.
