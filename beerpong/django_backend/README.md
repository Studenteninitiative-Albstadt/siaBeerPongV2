# Django Backend

Dies ist das aktive Backend des Projekts. Es liefert REST-Endpunkte, WebSockets, Rollen, Turnierpersistenz und den kompletten Snapshot-State fuer Admin, LiveView, MobileView und RefereeView.

## Technischer Rahmen

| Bereich | Stand |
| --- | --- |
| Python | 3.12 |
| Framework | Django 5.x |
| API | Django REST Framework |
| Auth | SimpleJWT |
| Echtzeit | Channels + Redis |
| Dev-Server | `daphne` via `entrypoint.sh` |
| Prod-Server | `gunicorn` + `uvicorn.workers.UvicornWorker` via `entrypoint.prod.sh` |

## Wichtige Dateien

| Datei / Ordner | Zweck |
| --- | --- |
| `manage.py` | Django-Management-Kommandos |
| `config/` | globale Settings, Root-URLs, ASGI/WSGI |
| `tournament/` | komplette Fachlogik der App |
| `requirements.txt` | Django, DRF, JWT, Channels, Redis, Gunicorn, Uvicorn, Psycopg |
| `Dockerfile` | Dev-Image mit Daphne |
| `Dockerfile.prod` | Prod-Image fuer Gunicorn/Uvicorn |
| `entrypoint.sh` | Dev-Start mit Migrationen und Default-Usern `admin` / `live` |
| `entrypoint.prod.sh` | Prod-Start mit Env-Check, Migrationen, Collectstatic und Bootstrap-Usern |

## Laufzeitmodi

### Dev

- DB standardmaessig SQLite
- `DEBUG=True`
- `daphne` auf `0.0.0.0:8000`
- Default-User:
- `admin` / `admin`
- `live` / `live`

### Produktion

- DB per `DB_ENGINE=postgres`
- Redis fuer Channel Layer
- Postgres fuer Persistenz
- statische Dateien landen in `staticfiles/`
- Bootstrap-User:
- `DJANGO_SUPERUSER_*` wird als Root/Admin erzeugt
- `LIVEVIEW_*` wird als Beamer-User erzeugt
- Referee-Accounts werden nicht automatisch angelegt

## Schnittstellen

- REST unter `config/urls.py`
- WebSocket-Routing ueber `config/asgi.py` + `tournament/routing.py`
- Django-Admin unter `/django-admin/`

Weitere Details liegen in:

- `config/README.md`
- `tournament/README.md`
