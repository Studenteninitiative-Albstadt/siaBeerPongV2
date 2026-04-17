# GroupsView Komponenten

Dieser Unterordner kapselt die komplette Gruppenphase.

## Dateien

| Datei | Zweck |
| --- | --- |
| `GroupsView.vue` | Hauptcontainer fuer Gruppenphase, Queue, Tische, Tiebreaks und KO-Uebergang |
| `GroupCard.vue` | einzelne Gruppenkarte |
| `GroupHeader.vue` | Kopfbereich einer Gruppe |
| `GroupMatches.vue` | Matchliste je Gruppe |
| `GroupTable.vue` | Gruppenstand / Tabellenansicht |
| `TournamentInfo.vue` | Metadatenblock zur laufenden Phase |
| `TournamentFooter.vue` | Footer-/Action-Bereich |
| `TiebreakControls.vue` | Steuerung fuer Gleichstaende |
| `TiebreakMini.vue` | kleine Tiebreak-Darstellung |
| `TiebreakRage.vue` | Rage-Cage-/Spezial-Tiebreak |

## Was `GroupsView.vue` heute leistet

- Laden und Mappen von Gruppen und Gruppenspielen
- Tischzuweisung ueber `tableAssignments.js`
- Live-Eingabe von Hits, Undo, Rerack und Overtime
- Team-/Spieler-Zuordnung
- KO-Vorschau-Transfer
- Schiedsrichter-/Store-kompatibler Snapshot-Sync
- Admin-Warteschlange mit Drag-and-Drop-Reihenfolge fuer wartende Gruppenspiele

## Queue-Logik

- Im Admin werden alle wartenden Gruppenspiele angezeigt.
- Drag-and-Drop aendert die `order_index`-Reihenfolge lokal und speichert sie ueber `save-group-phase`.
- Die automatische Tischzuweisung verhindert parallele Doppelbelegung eines Teams auf mehreren Tischen.
- Eine vollstaendige Fairness-Heuristik fuer die gesamte Queue existiert derzeit nicht; es wird also nicht garantiert, dass ein Team nie zwei Spiele direkt hintereinander hat.
