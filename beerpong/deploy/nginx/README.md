# App Nginx

Dieser Ordner definiert den containerisierten Nginx, der innerhalb des Produktiv-Stacks laeuft.

## Dateien

| Datei | Zweck |
| --- | --- |
| `Dockerfile` | baut zuerst das Vite-Frontend und kopiert danach `dist/` in ein `nginx:alpine`-Image |
| `nginx.conf` | SPA-Serving, Static-Alias, Reverse Proxy auf Django und WebSocket-Upgrade |

## `nginx.conf` im Ist-Zustand

- `worker_processes auto`
- `worker_connections 4096`
- `upstream django_backend` mit Keepalive
- `/static/` wird direkt aus dem Volume serviert
- `/auth`, `/tournaments`, `/django-admin`, `/health` und `/ws` gehen an `backend:8000`
- alles andere faellt per `try_files` auf `index.html` zurueck

## Warum diese Schicht existiert

- Das Frontend wird als statische SPA ausgeliefert.
- Das Backend bleibt intern auf dem Docker-Netz.
- Die gleiche Nginx-Instanz uebernimmt HTTP und WS fuer alle Clients.
