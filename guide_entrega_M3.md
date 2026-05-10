# Guide Entrega M3

## Objectiu Real
Tens M1 i M2 pràcticament definits. El que et queda de veritat és acabar M3: materials i mètodes + resultats, i unir-ho tot en una memòria llegible i coherent.

La prioritat ja no és millorar el sistema, sinó explicar-lo bé i presentar un PDF sòlid.

## Inici De M3

Al començament del capítol 3 hi ha d'anar:
- un títol molt curt
- `Chapter 3`
- `Materials and methods`

I aquest capítol ha d'explicar exactament:
- els aspectes més rellevants del disseny i desenvolupament del treball
- la metodologia escollida per fer el desenvolupament
- les alternatives considerades
- les decisions preses
- els criteris utilitzats per prendre aquestes decisions
- els productes obtinguts

Si aplica, també has d'incloure una secció d'`Economic evaluation of work` amb:
- despeses associades al desenvolupament i manteniment
- beneficis econòmics obtinguts
- anàlisi final de viabilitat del producte

En el teu cas, aquesta part econòmica només l’has d’incloure si realment la pots justificar bé; si no, millor no forçar-la.

## M1 + M2: Què Has De Tenir Clar

### M1
M1 ja hauria de quedar fixat com la base conceptual i de planificació del TFM.

Has de tenir:
- títol
- paraules clau
- abstract
- motivació personal
- objectius generals i parcials
- metodologia general
- pla de treball
- bibliografia inicial

Si alguna part encara és fluixa, només toca aclarir-la, no reinventar-la.

### M2
M2 és l'estat de l'art.

Has de fer que quedi clar:
- què s’ha investigat fins ara
- quins problemes hi ha en la detecció de greenwashing / credibilitat CSR
- quines aproximacions existeixen
- per què el teu enfocament és raonable

L’important no és tenir una llista infinita de papers, sinó una narrativa que justifiqui el teu projecte.

## Ara El Que Et Queda És M3

M3 ha de respondre tres preguntes:
1. Què has fet exactament?
2. Com ho has fet?
3. Què has obtingut?

Has de convertir el prototip en una memòria explicable.

## Pas A Pas Realista Per Acabar M3

### 1. Congela La Implementació
No facis més canvis grans al codi.

Només val la pena tocar coses si:
- una sortida és confusa
- el report visible encara és massa tècnic
- hi ha un error clar que fa impossible presentar el resultat

Objectiu d’aquest pas:
- tenir una versió de referència
- evitar que el projecte es torni a moure cada hora

### 2. Defineix La Versió Final Que Exploraràs Al PDF
Tria una sola versió del sistema per explicar-la.

Per exemple:
- Microsoft com a cas principal
- pipeline actual com a arquitectura de referència
- FAISS / embeddings com a branca experimental o complementària

No intentis explicar totes les versions del projecte com si fossin igual d’importants.

### 3. Escriu Primer L’Estructura De M3
Abans d’omplir text, fixa els apartats.

Proposta simple:
- 3.1 Materials i mètodes
- 3.2 Dades i configuració
- 3.3 Resultats
- 3.4 Limitacions
- 3.5 Discussió o síntesi final

### 4. Redacta Materials I Mètodes
Aquest apartat ha de ser molt clar.

Explica:
- què fa el sistema
- quins documents entra
- com es transformen els PDFs en claims
- com es generen consultes
- com es cerca evidència externa
- com es prioritzen els resultats
- com es decideix si una claim està suportada o no
- com es genera el veredicte final

No t’has de perdre en tecnicismes: el lector ha de seguir el flux.

### 5. Explica L’Arquitectura Amb Paraules Normals
Has de poder dir-ho així:

`PDFs -> claims -> consultes -> cerca web -> extracció d'evidència -> reranking -> anàlisi -> judici final -> report`

I després explicar cada bloc en un paràgraf curt.

### 6. Escriu Els Resultats Amb El Cas Microsoft
Microsoft és el teu cas fort.

En resultats has de dir:
- quants documents vas processar
- quantes claims vas extreure
- quantes vas prioritzar
- quantes vas analitzar
- quina proporció d’evidència va ser directa / indirecta / feble
- quines claims es van veure clarament suportades
- quines van quedar sense prou verificació
- quin veredicte final obtens

Aquí no cal fer una exposició tècnica; cal fer una lectura argumentada.

### 7. Escriu El Que Signifiquen Els Resultats
No n’hi ha prou amb posar números.

Has d’explicar:
- què demostren aquests números
- per què el cas Microsoft és útil
- què et diu el resultat sobre el sistema
- què significa que hi hagi claims suportades però d’altres no verificades

### 8. Escriu Les Limitacions Sense Enfonsar El Projecte
Sigues honest però no derrotista.

Pots dir que:
- algunes claims són repetitives o massa mètriques
- algunes fonts externes no són prou específiques
- algunes claims futures no s’han d’interpretar com a prova principal
- el rendiment canvia molt segons empresa i documents
- el sistema és un prototip, no una auditoria legal completa

### 9. Fes Una Discussió Breu
Aquí has de resumir el valor del sistema.

Digues:
- què aporta el teu enfocament
- què has après del cas Microsoft
- per què la combinació de claims internes + evidència externa és útil
- quina és la lectura final sobre greenwashing

### 10. Tanca Amb Una Conclusió Clara
La conclusió ha de respondre directament:
- hi ha indicis de greenwashing o no?
- és un risc fort, moderat o feble?
- què és el més rellevant que has trobat?

## Com Has D’Explicar M1 I M2 Al Document Final

### M1 En El Document
No l’expliquis com una tasca administrativa.

Explica’l com la definició del projecte:
- problema
- objectius
- metodologia prevista
- planificació

### M2 En El Document
No facis una llista d’articles.

Fes una síntesi de la literatura:
- què s’ha fet en greenwashing / CSR credibility
- què falta encara
- on encaixa el teu projecte

### La Relació Entre M1, M2 I M3
El fil narratiu ha de ser aquest:
- M1 defineix què vols fer
- M2 justifica per què és rellevant
- M3 mostra com ho has fet i què n’ha sortit

## Què Fer En Quin Ordre

### Bloc 1
- fixa l’estructura final de la memòria
- decideix el títol final
- revisa abstract i objectius

### Bloc 2
- escriu Materials i Mètodes
- descriu l’arquitectura

### Bloc 3
- escriu Resultats
- usa Microsoft com a cas principal

### Bloc 4
- escriu Limitacions i Discussió
- tanca la conclusió

### Bloc 5
- crea la taula resum
- crea el diagrama del pipeline
- revisa bibliografia i citacions

### Bloc 6
- neteja el text final
- comprova format
- exporta el PDF

## Què Has De Deixar Clar Al Lector
El lector ha d’entendre que:
- el projecte és un prototip funcional
- s’ha provat amb un cas real fort
- hi ha una lectura argumentada de la credibilitat CSR
- el sistema no és perfecte, però és útil i defensable

## Què No Cal Fer Ara
- no reinventis el sistema
- no afegeixis més agents
- no facis més experiments arquitectònics
- no busquis perfecció en tots els resultats

## Resultat Final Que Busques
Un PDF on quedi clar:
- què proposava el projecte
- quina literatura el justifica
- com funciona la metodologia
- què mostren els resultats
- quins són els límits
- quina és la conclusió sobre greenwashing

## Prioritat De Les Properes Hores
1. escriure la memòria
2. netejar el report visible
3. preparar la figura i la taula
4. exportar i revisar el PDF

## Missatge Final
No necessites un sistema perfecte.

Necessites una memòria que expliqui bé un prototip útil, amb un cas principal clar i una conclusió defensable.
