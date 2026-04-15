# SIA BeerPong - App context

Dies ist das zentrale Arbeitsverzeichnis für den Turniermanager. Es verwaltet die Orchestrierung der verschiedenen Services und den Übergang von Flask zu Django.

## Service-Infrastruktur

Das Projekt wird über `docker-compose.yml` orchestriert.

```text
       [ Externer Zugriff ]
               |
    +----------+----------+
    |                     |
[ frontend ] <---> [ backend (django) ] <---> [ redis ]
(Port 5173)        (Port 8000)                (WebSocket Layer)
```

- **redis**: Ermöglicht asynchrone Kommunikation über Django Channels.
- **backend**: Django REST API für Datenpersistenz und Turnierlogik.
- **frontend**: Single-Page-Application für Admin, Teilnehmer und Mobile.

## Der Turnier-Workflow (Logical Flow)

Die Orchestrierung des Turniers folgt einer festen Phasen-Logik:

```text
[ SETUP ] --> [ GRUPPENPHASE ] --> [ PLAY-IN ] --> [ KO-PHASE ]
    |               |                  |               |
    |               |                  |               +--> Siegerehrung
    |               |                  +--> Tie-Break & Wildcards
    |               +--> Tischzuweisung & Live-Stats
    +--> Team-Registration & Wizard
```

## Verzeichnis-Inhalt

```text
.
├── docker-compose.yml     # Definiert Services & Volumes
├── django_backend/        # AKTIV: Kernlogik & Datenbank
├── frontend/              # AKTIV: UI-Logik & State-Management
└── backend/               # LEGACY: Referenz-Code (Flask)
```

## Wichtige Schnittstellen

| Endpunkt | Service | Zweck |
|---|---|---|
| `:5173/` | Frontend | Startseite / App |
| `:8000/django-admin/` | Backend | Direkte Datenbank-Administration |
| `:8000/health` | Backend | API-Healthcheck |

---
*Status: 15. April 2026*
