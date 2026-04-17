# Deploy Assets

Dieser Ordner sammelt die Produktionsartefakte rund um Nginx. Er ist bewusst vom eigentlichen App-Code getrennt.

## Aufbau

| Pfad | Zweck |
| --- | --- |
| `host-nginx/` | Konfiguration fuer den Nginx auf dem Server-Host mit TLS-Termination |
| `nginx/` | Container-Nginx fuer SPA-Auslieferung, Static Files, API- und WS-Proxy |

## Schichten im Produktivbetrieb

1. Host-Nginx nimmt `https://sia-bp.butzke.it` entgegen.
2. Er leitet auf `127.0.0.1:${APP_HTTP_PORT}` weiter.
3. Der interne App-Nginx serviert die gebaute SPA und proxied `/auth`, `/tournaments`, `/django-admin`, `/health` und `/ws` an Django.

## Was nicht hier liegt

- TLS-Zertifikate selbst
- Docker-Compose-Dateien
- Django-Settings

Die eigentliche Orchestrierung liegt im Projektroot in `docker-compose.prod.yml`.
