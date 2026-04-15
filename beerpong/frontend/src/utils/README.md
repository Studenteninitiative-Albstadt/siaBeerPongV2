# Frontend Utilities

Hier befinden sich die algorithmischen Komponenten, die den physischen Turnierfluss steuern und Datenformate normalisieren.

## Tischbelegungs-Logik (`tableAssignments.js`)

Diese Komponente ist essenziell für einen reibungslosen Ablauf vor Ort. Sie berechnet, welche Spiele auf welchen physischen Tischen stattfinden.

```text
[ Alle offenen Matches ]
           |
   +-------v-------+
   | Pass 1: Persisted | (Matches mit fester Tisch-ID vom Backend)
   +-------+-------+
           |
   +-------v-------+
   | Pass 2: In-Progress | (Laufende Spiele ohne ID stabil halten)
   +-------+-------+
           |
   +-------v-------+
   | Pass 3: Waiting | (Nachrücken auf freie Tische)
   +---------------+
```

- **Stable Table Mapping**: Verhindert, dass laufende Spiele "springen" (z.B. von Tisch 2 auf Tisch 1), nur weil ein vorheriges Spiel beendet wurde.
- **Match-Key**: Eindeutige Identifizierung von Paarungen, um den Zustand auch bei Snapshots konsistent zu halten.

## KO-Phasen Utilities

- **Bracket-Positionierung**: Berechnet die grafischen Pfade im KO-Baum.
- **Cups-State**: Normalisiert die Darstellung der 6 bzw. 10 Cups pro Team (True/False für getroffene Becher).

---
*Status: 15. April 2026*
