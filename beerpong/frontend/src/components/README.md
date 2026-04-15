# Vue Komponenten-Bibliothek

Die Komponenten sind modular aufgebaut und werden je nach Turnierphase in den Views kombiniert.

## Kategorisierung der Komponenten

### 1. Turnier-Management
- `TournamentWizard.vue`: Geführtes Setup für neue Turniere (Teams, Modi, Gruppen).
- `TournamentBracketTree.vue`: Visualisierung des gesamten Turnier-Verlaufs.
- `MatchTableControls.vue`: Steuerung einzelner Spiele (Score, Undo, Re-Rack).

### 2. Gruppenphase (`GroupsView/`)
- `GroupsView.vue`: Container für die Gruppen-Ansicht.
- `GroupTable.vue`: Tabellenberechnung & Standings pro Gruppe.
- `TiebreakControls.vue`: Manuelle Steuerung bei Punkte-Gleichstand.

### 3. Knockout (KO) Phase
- `KnockoutBracket.vue`: Dynamische Generierung des Turnierbaums.
- `KnockoutView.vue`: Admin-Oberfläche für die KO-Runden.
- `LiveViewKO.vue`: Beamer-optimierte KO-Darstellung.

### 4. Sonstiges & UI
- `HeaderBar.vue`: Navigation & Status-Anzeige.
- `InfoPanel.vue`: Seitenleiste für Turnier-Statistiken.
- `ConfettiOverlay.vue`: Belohnungs-Effekt bei Turniersieg.

## Komponenten-Workflow (Beispiel: Gruppenspiel)

```text
[ AdminView ]
      |
      +---< [ GroupsView ]
                  |
                  +---< [ GroupTable ] (Anzeige Standings)
                  |
                  +---< [ MatchTableControls ] (Eingabe Score)
                              |
                              +---( API Call: /group-match )
```

---
*Status: 15. April 2026*
