# Komponenten

Dieser Ordner enthaelt die grossen UI-Bausteine, die von den Views zusammengesetzt werden.

## Bereiche

### Shell und generische UI

- `HeaderBar.vue`: Kopfzeile fuer Admin-/Live-Seiten
- `MatchTableControls.vue`: Tischbedienung fuer Cup-Hits, Undo, Rerack, Overtime
- `LiveTable3D.vue`: visuelle Tisch-/Cup-Darstellung
- `ConfettiOverlay.vue`: visuelles Sieger-Feedback

### Gruppenphase

- `GroupsView/`: komplette Gruppenphase mit Standings, Queue, Tiebreaks und KO-Uebergang
- `GroupStandingsTable.vue`: gruppenuebergreifende oder spezielle Tabellenansicht

### KO und Play-In

- `PlayInView.vue`: Play-In-Logik und KO-Uebergang
- `KnockoutView.vue`: Admin-Steuerung fuer KO
- `KnockoutPreview.vue` / `KnockoutPreviewTree.vue`: KO-Vorschau vor dem Start
- `KnockoutResultsTree.vue`: aktueller Ergebnisbaum fuer Admin, Live und Mobile
- `KnockoutBracket.vue`: manueller Bracket-Editor / Ergebnishelfer
- `TournamentBracketTree.vue`: Basisdarstellung, aus der Preview-/Result-Komponenten abgeleitet sind
- `LiveViewKO.vue`: KO-spezifischer Live-Block fuer die Beamer-Ansicht

### Wizard und Meta

- `TournamentWizard.vue`: Turnieranlage

## Dateien mit Legacy-/Scaffold-Charakter

- `HelloWorld.vue`: ungenutzter Scaffold-Rest
- `InfoPanel.vue`: derzeit nicht im aktiven Import-Graph

## Wichtiger Ist-Zustand

- Der aktive KO-Baum fuer Admin, Live und Mobile basiert auf `KnockoutResultsTree.vue`.
- `PlayInView.vue` kennt noch einen Legacy-Fallback auf Port `5001`, passend zum alten Flask-Backend.
