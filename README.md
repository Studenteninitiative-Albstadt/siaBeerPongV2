# SIA BeerPong V2 - Tournament Management System

Das offizielle Turniermanagement-System der SIA. Diese Applikation bietet eine hochverfügbare, echtzeitfähige Plattform zur Organisation von Beer-Pong-Turnieren, optimiert für den Einsatz auf Beamern (LiveView) und mobilen Endgeräten.

## System-Architektur

Das System basiert auf einem modernen, entkoppelten Stack:

```text
[ Frontend ] <---( WebSockets / REST )---> [ Backend ] <---> [ Redis ]
(Vue 3 SPA)                                (Django DRF)      (Real-time)
```

## Repository-Struktur

| Verzeichnis | Inhalt |
|---|---|
| `beerpong/` | Aktive Applikation & Docker-Orchestrierung. |
| `beerpong/django_backend/` | Kern-API, Turnierlogik & WebSocket-Server. |
| `beerpong/frontend/` | Responsive UI für Admin, LiveView und Mobile. |

## Deployment (Production)

Die gesamte Infrastruktur ist für den Betrieb in Docker-Containern optimiert.

```bash
cd beerpong
docker-compose up -d --build
```

**Services:**
- **Frontend**: Port 5173 (Vite / Production Build)
- **Backend**: Port 8000 (Daphne ASGI Server)
- **Redis**: Interner Message Broker für Echtzeit-Updates

---
*Version: 2.0.0 - Production Ready*
