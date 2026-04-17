# SIA Bier Pong V2

Dieses Repository enthaelt aktuell genau eine fachlich relevante Applikation: `beerpong/`. Dort liegen Frontend, Backend, Deploy-Konfiguration und die rekursive Projektdoku.

## Repository-Aufbau

| Pfad | Zweck |
| --- | --- |
| `beerpong/` | aktives SIA-Bier-Pong-Projekt |
| `.claude/` | editor-/agentenspezifische Metadaten, nicht Teil der Laufzeit |

## Einstieg

Wenn du am System arbeitest, starte hier:

- `beerpong/README.md` fuer den Gesamtueberblick
- `beerpong/django_backend/README.md` fuer Backend und API
- `beerpong/frontend/README.md` fuer SPA, Routen und Stores
- `beerpong/deploy/README.md` fuer Produktionspfad und Nginx

## Aktueller Betriebsstand

- Dev-Stack: `beerpong/docker-compose.yml`
- Prod-Stack: `beerpong/docker-compose.prod.yml`
- aktives Backend: Django/DRF/Channels
- aktives Frontend: Vue 3 / Vite / Pinia
- Legacy-Flask-Backend liegt nur noch archiviert unter `beerpong/backend/`
