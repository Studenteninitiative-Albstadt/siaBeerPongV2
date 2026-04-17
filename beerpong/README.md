# SIA Bier Pong

Dieses Verzeichnis enthaelt den aktiven Turnier-Stack fuer SIA Bier Pong. Das Projekt besteht heute aus einem Vue-Frontend, einem Django/Channels-Backend und Redis fuer Echtzeit-Sync. Fuer Produktion kommt zusaetzlich Postgres und eine zweistufige Nginx-Proxy-Kette dazu.

## Aktiver Stack

| Bereich | Stand heute |
| --- | --- |
| Frontend | Vue 3 + Vite + Pinia + Vue Router |
| Backend | Django + DRF + SimpleJWT + Channels |
| Echtzeit | WebSocket ueber Channels + Redis |
| Dev-Compose | `docker-compose.yml` mit Vite, Django, Redis |
| Prod-Compose | `docker-compose.prod.yml` mit Gunicorn/Uvicorn, Postgres, Redis, interner Nginx |
| Host-Proxy | optionaler Host-Nginx unter `deploy/host-nginx/` |

## Wichtige Laufwege

### Frontend-Routen

- `/#/login`: JWT-Login
- `/#/admin`: Root-Admin fuer Turnierleitung
- `/#/referee`: Schiedsrichter-Ansicht fuer `is_orga`
- `/#/live`: Beamer-/LiveView fuer Auth-User
- `/#/mobile?token=...&id=...`: oeffentliche Mobile-Ansicht per Turnier-Token

### Backend-Schnittstellen

- REST-Basis: `/tournaments`, `/auth/token`, `/auth/token/refresh`
- Public Mobile Snapshot: `/tournaments/<id>/mobile-state?token=<uuid>`
- Healthcheck: `/health`
- Django-Admin: `/django-admin/`
- WebSocket: `/ws/tournament/<id>/?token=<jwt>` oder `?mobile_token=<uuid>`

## Ordnerstruktur

| Pfad | Zweck |
| --- | --- |
| `backend/` | Legacy-Flask-Backend auf Port `5001`; nicht Teil des aktiven Stacks |
| `deploy/` | Produktions-Nginx und Host-Proxy-Konfiguration |
| `django_backend/` | Aktives Backend inkl. REST, WS, Rollen, Persistenz |
| `frontend/` | Aktive SPA fuer Admin, Live, Mobile und Referee |
| `scripts/` | Deploy-Helfer, aktuell der `.env`-Guard |

## Dev vs. Produktion

### Entwicklung

- `docker-compose.yml` startet:
- `frontend` auf `5173`
- `backend` auf `8000`
- `redis`
- Datenbank ist standardmaessig SQLite im Django-Container
- Backend laeuft ueber `daphne` mit Auto-Migrationsschritt beim Start

### Produktion

- `docker-compose.prod.yml` startet:
- `env-check`
- `db` (Postgres 16)
- `redis`
- `backend` (Gunicorn + Uvicorn Worker)
- `nginx` (SPA + Reverse Proxy)
- Host-Nginx aus `deploy/host-nginx/` terminiert TLS und leitet auf `127.0.0.1:${APP_HTTP_PORT}` weiter

## Rollenmodell

- `is_root`: voller Adminzugriff auf `/#/admin`
- `is_orga`: Referee-Zugriff auf `/#/referee`
- `is_liveview`: Beamer-/Live-Login
- Mobile-Gaeste brauchen keinen JWT-Login, nur den Turnier-Token

## Relevante Ist-Zustandsnotizen

- `backend/` ist weiterhin im Repo, wird aber von keinem aktiven Compose-Stack benutzt.
- `frontend/src/components/PlayInView.vue` enthaelt noch einen Legacy-Fallback auf Port `5001`; das passt zum alten Flask-Backend und ist kein Teil des sauberen Prod-Pfads.
- `frontend/public/vite.svg` und `frontend/src/assets/vue.svg` sind Vite-/Vue-Reste aus dem Scaffold.
- `frontend/dist/` ist nur ein Build-Artefakt. Wenn dort noch alte Favicons oder Texte liegen, ist das kein Quellcodezustand, sondern ein fehlender Rebuild.

## Weiterfuehrende Doku

- `backend/README.md`
- `deploy/README.md`
- `django_backend/README.md`
- `frontend/README.md`
- `scripts/README.md`
