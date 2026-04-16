# SIA BeerPong - App context

Dies ist das Herzstück des Turniermanagers. Hier wird die Orchestrierung der Produktiv-Services gesteuert.

## Produktiv-Stack (Orchestrierung)

Das System nutzt `docker-compose.yml`, um eine hochverfügbare Umgebung zu gewährleisten.

```text
       [ Externer Zugriff ]
               |
    +----------+----------+
    |                     |
[ frontend ] <---> [ backend (django) ] <---> [ redis ]
(Vue 3 SPA)        (REST API + WS)            (Real-time State)
```

## Produktiver Turnier-Workflow

Der Workflow ist automatisiert und synchronisiert alle Clients (Admin, Beamer, Mobile) in Echtzeit:

```text
[ SETUP ] --> [ GRUPPENPHASE ] --> [ PLAY-IN ] --> [ KO-PHASE ]
    |               |                  |               |
    |               |                  |               +--> Finale & Siegerehrung
    |               |                  +--> Tie-Break & Platzierungen
    |               +--> Live-Tische & Standings
    +--> Team-Management & Wizard
```

## Verzeichnis-Inhalt

- `docker-compose.yml`: Definiert Container-Limits und Environments.
- `django_backend/`: Produktives Backend (Django 5.x).
- `frontend/`: Produktives Frontend (Vue 3 / Pinia).
- `backend/`: Veraltetes Archiv (Legacy - Nur zu Dokumentationszwecken).

---
*Version: 2.0.0 - Production State*
