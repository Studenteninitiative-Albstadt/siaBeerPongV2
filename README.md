# SIA BeerPong V2 - Project Root

Dieses Repository enthält den Quellcode für das BeerPong Turniermanagement-System der SIA. Das Projekt befindet sich in einer Übergangsphase von einer Flask-basierten Architektur zu einem modernen Django/Vue 3 Stack.

## Repository-Struktur auf hoher Ebene

```text
.
├── beerpong/               # Haupt-Anwendungskontext
│   ├── django_backend/     # AKTIV: Django REST Framework + Channels (Port 8000)
│   ├── frontend/           # AKTIV: Vue 3 + Vite + Pinia (Port 5173)
│   ├── backend/            # LEGACY: Altes Flask/Socket.IO Backend (Port 5001)
│   └── docker-compose.yml  # Orchestrierung der aktiven Services
├── CLAUDE.md               # Projektspezifische Entwickler-Richtlinien
└── .gitignore              # Ausschlussregeln für Build-Artefakte & DBs
```

## System-Architektur & Datenfluss

Das System nutzt einen hybriden Ansatz aus REST für CRUD-Operationen und WebSockets für Echtzeit-Updates während des Turniers.

```text
[ Browser / Client ] <----( HTTPS / REST )----> [ Django Backend ]
       ^                                               |
       |                                               |
       +------( WSS / WebSockets )----[ Redis ]<-------+
                                        ^
                                        |
[ Mobile App ] <------------------------+
```

## Kern-Komponenten & Zuständigkeiten

1. **Orchestrierung (`beerpong/`)**: Definiert die Laufzeitumgebung via Docker.
2. **Business Logic (`django_backend/`)**: Verwaltet Turniere, Teams, Gruppen und die KO-Phasen-Persistenz.
3. **User Interface (`frontend/`)**: Bietet drei spezialisierte Ansichten:
    - **Admin**: Volle Kontrolle über den Turnierablauf.
    - **LiveView**: Beamer-optimierte Anzeige für Teilnehmer.
    - **Mobile**: Read-only Status für Spieler via QR-Code.

## Schnellstart

Um die aktive Umgebung lokal zu starten:

```bash
cd beerpong
docker-compose up --build
```

---
*Status: 15. April 2026*
