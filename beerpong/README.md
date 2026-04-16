# SIA BeerPong - App context

Zentrales Verzeichnis für die Orchestrierung und den Turnier-Lifecycle.

## Service-Infrastruktur

```text
       [ Externer Zugriff ]
               |
    +----------+----------+
    |                     |
[ frontend ] <---> [ backend (django) ] <---> [ redis ]
(Port 5173)        (Port 8000)                (WebSocket Layer)
```

## Turnier-Lifecycle & UI-Fokus

Der Lifecycle wird durch spezialisierte Frontend-Komponenten visualisiert:

1. **Setup**: Wizard-basierte Team-Erfassung.
2. **Gruppenphase**: Live-Scoring mit stabilen Tischzuweisungen.
3. **KO-Phase**: Dynamisches Bracket-Rendering und Beamer-optimierte 3D-Tischansicht.

## UI-Design-Prinzipien

- **Proportional Scaling**: Tische skalieren basierend auf Breite und Höhe, um Overlap zu vermeiden.
- **Visual Feedback**: Ball-Animationen und Becher-Zustände werden in Echtzeit visualisiert.
- **Compact Data**: Mobile Ansichten sind platzoptimiert (QR-Code Integration).

---
*Status: 15. April 2026 - Layout & Scaling Refined*
