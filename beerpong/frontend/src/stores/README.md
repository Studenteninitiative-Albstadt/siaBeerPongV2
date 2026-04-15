# Pinia State Management

Die Stores verwalten den globalen Zustand der Anwendung und synchronisieren ihn mit dem Backend.

## Daten-Synchronisations-Workflow

Das System arbeitet nach dem Prinzip der "Single Source of Truth" (Backend).

```text
[ WebSocket Event ] ----+
                        |
[ REST API Call ] ------+---> [ Store Action ]
                              |
                      +-------v-------+
                      |  Pinia State  | <---( mergeSnapshot )
                      +-------+-------+
                              |
                      +-------v-------+
                      |   Vue UI      | (Reaktive Anzeige)
                      +---------------+
```

## Vorhandene Stores

| Store | Zweck |
|---|---|
| `auth.js` | JWT-Handshake, Login-Status und Rollen (Admin/Live). |
| `tournament.js` | Gesamter Turnier-Status: Snapshot, Gruppen, KO, Play-In. |

- **`auth.js`**: Speichert Token im `localStorage`, um Sessions bei Reloads zu erhalten.
- **`tournament.js`**: Enthält die Kern-Logik `mergeSnapshot()`, die Teil-Updates vom WebSocket in den Store integriert.

---
*Status: 15. April 2026*
