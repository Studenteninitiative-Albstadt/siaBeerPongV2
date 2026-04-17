# Django Config

Dieser Ordner enthaelt die globale Projektkonfiguration des Django-Backends.

## Dateien

| Datei | Zweck |
| --- | --- |
| `settings.py` | Settings fuer DB, JWT, Channels, CORS, Security, Static Files |
| `urls.py` | Root-URLs fuer Django-Admin, JWT und die `tournament`-App |
| `asgi.py` | kombiniert HTTP und WebSocket ueber Channels |
| `wsgi.py` | klassischer WSGI-Einstieg, derzeit nicht der Hauptpfad |

## Wichtige Settings aus `settings.py`

- `DB_ENGINE=sqlite` oder `postgres`
- `AUTH_USER_MODEL = tournament.User`
- `APPEND_SLASH = False`
- JWT:
- Access-Token 12 Stunden
- Refresh-Token 7 Tage
- Redis-Channel-Layer ueber `REDIS_HOST`
- Prod-Schutz fuer Cookies, Proxy-SSL und HSTS
- interne Hosts `127.0.0.1`, `localhost`, `backend`, `nginx` werden zu `ALLOWED_HOSTS` ergänzt, falls kein `*` gesetzt ist

## Root-URLs

| Pfad | Ziel |
| --- | --- |
| `/django-admin/` | Django-Admin |
| `/auth/token` | Login mit Custom JWT Payload |
| `/auth/token/refresh` | Token-Refresh |
| `''` | `tournament.urls` |

## Wichtige Besonderheit

`APPEND_SLASH` ist deaktiviert. Deshalb ist `/django-admin/` korrekt, waehrend `/django-admin` als 404 enden kann.
