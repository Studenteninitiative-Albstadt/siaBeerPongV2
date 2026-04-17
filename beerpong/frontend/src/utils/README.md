# Utilities

Hier liegen die algorithmischen Helfer fuer Match-Queue, Tischzuweisung und KO-Anzeige.

## `tableAssignments.js`

Zustaendig fuer:

- Match-Keys und Tabellenummern
- Flattening der Gruppenmatches
- Erkennung von laufenden Spielen
- stabile Tischzuweisung fuer Gruppen- und KO-Spiele
- Berechnung von `active`, `upcoming` und `upcoming total`

### Aktuelles Verhalten

- schon zugewiesene Tische bleiben stabil
- laufende Spiele ohne persistierte `table_no` werden moeglichst nicht verdrängt
- wartende Spiele ruecken auf freie Tische nach
- parallele Doppelbelegung eines Teams wird verhindert
- eine vollstaendige Fairness-Sortierung ueber die komplette Queue wird nicht berechnet

## `koDisplay.js`

Zustaendig fuer:

- Normalisierung gespeicherter KO-Runden
- Propagation von Siegern in Folge-Runden
- Verwaltung von `Spiel um Platz 3` und `Finale`
- Ableitung der aktiven KO-Stufe (`main` vs. `placement`)
- Filter fuer die aktuell freigegebene KO-Stage
- Ermittlung, ob das Finale mit 10 Bechern gespielt werden soll

Diese Datei ist die wichtigste Anzeige-Logik fuer Admin, Live und Mobile in der KO-Phase.
