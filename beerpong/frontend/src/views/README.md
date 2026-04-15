# Frontend Views (Seiten)

Die Views kombinieren Komponenten zu funktionalen Einheiten für verschiedene Benutzergruppen.

## Haupt-Views & Verantwortlichkeiten

| Datei | Zielgruppe | Hauptaufgabe |
|---|---|---|
| `AdminView.vue` | Orga-Team | Turnieranlage, Phasen-Steuerung (Groups/KO). |
| `LiveView.vue` | Teilnehmer | Beamer-Übersicht, QR-Code für Mobile, Live-Scores. |
| `MobileView.vue` | Spieler | Persönlicher Spielplan, Gruppenstände, KO-Bracket. |
| `LoginView.vue` | Alle | JWT-Handshake für Authentifizierung. |

## Der Admin-Workflow (Phasen-Umschaltung)

Die `AdminView` steuert das Turnier über einen internen `step`-State.

```text
[ Step 0-3: Wizard ] --> [ Step 4: Gruppen ] --> [ Step 7: Play-In ] --> [ Step 5: KO-Phase ]
         |                       |                       |                      |
         v                       v                       v                      v
   Initial-Setup           Live-Scoring            Wildcards              Final-Runden
```

## Besonderheiten der LiveView

- **Beamer-Optimierung**: Große Schriften, hoher Kontrast, QR-Code-Overlay.
- **Auto-Umschaltung**: Wechselt bei Turnierphasen-Änderung (via WebSockets) automatisch das Layout.

---
*Status: 15. April 2026*
