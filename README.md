# SIA BeerPong V2 - Project Root

Dieses Repository enthält das BeerPong Turniermanagement-System der SIA. Das Projekt zeichnet sich durch eine hybride Architektur aus Django (Backend) und Vue 3 (Frontend) aus, mit einem starken Fokus auf Echtzeit-Visualisierung.

## Repository-Struktur

```text
.
├── beerpong/               # Haupt-Anwendungskontext
│   ├── django_backend/     # AKTIV: Django REST Framework + Channels
│   ├── frontend/           # AKTIV: Vue 3 + Vite (Modern 3D LiveView)
│   ├── backend/            # LEGACY: Altes Flask Backend (Referenz)
│   └── docker-compose.yml  # Orchestrierung
└── .gitignore              # Ausschlussregeln (Builds/DBs)
```

## Aktueller technischer Fokus

- **Echtzeit-Synchronisation**: Nahtloser Datenfluss zwischen Admin-Konsole und Beamer-Ansicht via WebSockets/Redis.
- **Responsive 3D-Visualisierung**: Dynamisch skalierende Turniertische, die sich proportional an jede Fenstergröße (Beamer/Vollbild) anpassen.
- **Rollenbasiertes UI**: Spezialisierte Ansichten für Organisation (Admin), Zuschauer (Live) und Spieler (Mobile).

## Schnellstart

```bash
cd beerpong
docker-compose up --build
```

---
*Status: 15. April 2026 - Major UI & Documentation Update*
