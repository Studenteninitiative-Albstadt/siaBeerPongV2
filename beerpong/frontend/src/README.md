# Frontend Source-Struktur

Diese Ebene bildet das Herzstück der User Experience und das State-Management der Applikation.

## Dateisystem & Zuständigkeiten

| Verzeichnis | Zweck |
|---|---|
| `views/` | Haupt-Seiten (Login, Admin, Live, Mobile). |
| `components/` | Wiederverwendbare UI-Elemente (Bracket, Tabellen, Wizard). |
| `stores/` | Pinia-State (Turnierdaten & Authentifizierung). |
| `router/` | Navigation & Zugriffsregeln. |
| `utils/` | Hilfsfunktionen für Tischbelegung & KO-Darstellung. |
| `api.js` | Zentraler API-Client für alle Anfragen. |

## Zentrales State-Management (`stores/`)

Das System synchronisiert den lokalen Zustand (`Pinia`) kontinuierlich mit dem Backend (`Django`).

```text
[ API Fetch / WebSocket Update ]
           |
   +-------v-------+
   |  Pinia Store  | <----( mergeSnapshot )
   +-------+-------+
           |
   +-------v-------+      +-------------------+
   |   Vue Views   | <----| Computed Props    |
   +---------------+      +-------------------+
```

## Utility-Logik (`utils/`)

- `tableAssignments.js`: Berechnet, welches Spiel auf welchem physischen Tisch stattfindet, um Staus zu vermeiden.
- `koDisplay.js`: Hilfsfunktionen für die Berechnung von Bracket-Positionen im KO-Baum.

---
*Status: 15. April 2026*
