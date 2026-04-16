# Frontend Utilities

Algorithmische Basis für den Turnierfluss und die visuelle Konsistenz.

## Tischbelegungs-Logik (`tableAssignments.js`)

Stellt sicher, dass Spiele stabil auf physischen Tischen bleiben.

```text
[ Alle offenen Matches ]
           |
   +-------v-------+
   | Pass 1: Persisted | (Matches mit fester Tisch-ID)
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

## Neue Visualisierungs-Logik

- **Proportional Scaling**: Die visuelle Darstellung der Tische (3D) folgt nun strengen mathematischen Verhältnissen (Breite zu Höhe, Bechergröße zu Breite).
- **Match-Key Identität**: Gewährleistet, dass Animationen auch bei Store-Updates (Merge) am korrekten Tisch abgespielt werden.
- **Cup-State Normalisierung**: Berechnet Becher-Arrays (6/10) basierend auf Hit-Counts und Overtime-Status.

---
*Status: 15. April 2026 - Scalable Design Logic Integrated*
