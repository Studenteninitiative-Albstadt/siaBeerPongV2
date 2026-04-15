# SIA BeerPong - Legacy Backend (Flask)

Dieser Ordner enthält den ursprünglichen Backend-Stack. Er dient aktuell nur noch als Referenz für die Portierung der Logik in das neue Django-Backend.

## Stack & Architektur (V1)

```text
[ Client ] <---( Socket.IO )---> [ Flask Server ]
                                       |
                               +-------v-------+
                               |  SQLAlchemy   |
                               +-------+-------+
                                       |
                               [ tournament.db ] (SQLite)
```

- **Framework**: Flask mit `Flask-SocketIO`.
- **Datenbank**: SQLite (`tournament.db`).
- **Kommunikation**: Starker Fokus auf Event-basiertes Socket.IO (Echtzeit-Scores).

## Warum Legacy?

1. **Skalierbarkeit**: Flask-SocketIO stieß bei parallelen Turnieren an Grenzen.
2. **Typisierung/Struktur**: Fehlende Validierungsschichten (Serializers).
3. **Zustandsmodell**: Die Logik war stark in `app.py` konzentriert (Monolith).

## Migration-Status

- [x] Turnier-Modelle (Portiert nach Django)
- [x] Gruppengenerierung (Portiert nach `services.py`)
- [x] WebSocket-Events (Ersetzt durch Django Channels)
- [ ] Vollständige Abschaltung (Geplant nach Stabilisierung des Play-In-Flows)

---
*Status: 15. April 2026*
