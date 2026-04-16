# Vue Komponenten-Bibliothek

Modulare Bausteine für den Turnier-Workflow.

## Kern-Komponenten

### 1. Visualisierung & 3D
- **`LiveTable3D.vue`**: Master-Komponente für die Tisch-Darstellung. Nutzt nun **proportionales Scaling** (calc-based), um Becherpositionen über alle Auflösungen hinweg stabil zu halten.
- **`ConfettiOverlay.vue`**: Visuelles Feedback für Turniersiege.

### 2. Turnier-Struktur
- **`KnockoutResultsTree.vue`**: Render-Engine für das KO-Bracket.
- **`KnockoutPreviewTree.vue`**: Live-Vorschau der KO-Paarungen während der Gruppenphase.
- **`TournamentWizard.vue`**: Multi-Step Form für die Turnieranlage.

### 3. Steuerung
- **`MatchTableControls.vue`**: Zentrale Komponente für die Ergebniseingabe (Cups, Undo, Re-Rack).
- **`TiebreakControls.vue`**: Manuelle Entscheidungshilfe bei Punktegleichstand.

## Architektur-Muster

```text
[ View ] --> [ Container Component ] --> [ Presentational Component (3D/SVG) ]
   |                |                             |
   v                v                             v
(Layout)       (Logic/API)                   (Pure Visuals)
```

---
*Status: 15. April 2026 - Component Scaling Updated*
