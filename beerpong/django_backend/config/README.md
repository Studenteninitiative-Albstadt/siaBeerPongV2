# Django Project Configuration

Dieser Ordner bildet die operative Basis des Django-Backends und steuert die globale Infrastruktur.

## Projekt-Struktur

| Datei | Zweck |
|---|---|
| `settings.py` | Globale Einstellungen (Datenbank, Auth, Channels, Redis). |
| `asgi.py` | Asynchrone Gateway-Schnittstelle (Daphne / WebSockets). |
| `urls.py` | Zentrales URL-Routing für alle Sub-Apps. |
| `wsgi.py` | Synchrone Schnittstelle (für klassische Webserver). |

## Kern-Konfiguration (Workflows)

```text
       [ Request ]
           |
   +-------v-------+      +-------------------+
   |   asgi.py     | <----| Routing (WS/HTTP) |
   +-------+-------+      +-------------------+
           |
   +-------v-------+      +-------------------+
   |  settings.py  | <----| Auth (SimpleJWT)  |
   +-------+-------+      | Redis (Channels)  |
           |              +-------------------+
   +-------v-------+
   |   urls.py     |
   +---------------+
```

- **Authentication**: JWT mit `12h` Access-Token und `7d` Refresh-Token.
- **WebSocket Layer**: Nutzt Redis als Channel Layer für skalierbare Echtzeit-Kommunikation.
- **CORS**: Erlaubt Frontend-Zugriff (Vite Standard-Port 5173).

---
*Status: 15. April 2026*
