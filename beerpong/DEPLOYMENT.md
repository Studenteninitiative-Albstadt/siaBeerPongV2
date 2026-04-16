# Deployment: `sia-bp.butzke.it`

Diese produktive Bereitstellung ist bewusst getrennt vom lokalen Dev-Setup. Das bestehende `docker-compose.yml` bleibt für Hot Reload lokal erhalten, der Server benutzt stattdessen `docker-compose.prod.yml`.

## Architektur

- Host-Nginx auf dem Server terminiert TLS fuer `sia-bp.butzke.it`.
- Der Host-Nginx proxyt auf `127.0.0.1:18080`.
- Auf `127.0.0.1:18080` laeuft ein app-internes Nginx-Container-Gateway.
- Das Container-Nginx serviert das gebaute Vue-Frontend, proxyt API/WebSocket an Django und liefert `collectstatic` aus.
- Django laeuft als ASGI-App unter Gunicorn mit `uvicorn.workers.UvicornWorker`.
- Postgres und Redis sind nur intern im Compose-Netz sichtbar und kollidieren nicht mit deinen bestehenden Host-Ports `5000`, `5173` oder `5432`.

## Dateien

- [`.env`](./.env) enthaelt alle produktiven Variablen mit Platzhaltern fuer Secrets.
- [`docker-compose.prod.yml`](./docker-compose.prod.yml) ist der produktive Stack.
- [`deploy/nginx/nginx.conf`](./deploy/nginx/nginx.conf) ist das app-interne Nginx.
- [`deploy/host-nginx/sia-bp.butzke.it.conf`](./deploy/host-nginx/sia-bp.butzke.it.conf) ist die Vorlage fuer das Host-Nginx.
- [`scripts/verify_required_env.sh`](./scripts/verify_required_env.sh) blockiert den Start, solange Platzhalter wie `PLEASECHANGEME` noch gesetzt sind.

## Server-Schritte

1. DNS bei GoDaddy setzen:
   `sia-bp.butzke.it` als `A`-Record auf die IPv4 deines Netcup-Servers zeigen lassen.
2. Repo auf dem Server auschecken:
   ```bash
   git clone <dein-repo> /srv/siaBeerPongV2
   cd /srv/siaBeerPongV2/beerpong
   ```
3. [`.env`](./.env) direkt auf dem Server bearbeiten:
   - `DJANGO_SECRET_KEY`
   - `POSTGRES_PASSWORD`
   - `DJANGO_SUPERUSER_PASSWORD`
   - `LIVEVIEW_PASSWORD`
4. Stack bauen und starten:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
5. Host-Nginx-Datei installieren:
   ```bash
   sudo cp deploy/host-nginx/sia-bp.butzke.it.conf /etc/nginx/sites-available/sia-bp.butzke.it
   sudo ln -s /etc/nginx/sites-available/sia-bp.butzke.it /etc/nginx/sites-enabled/sia-bp.butzke.it
   ```
6. TLS-Zertifikat holen:
   ```bash
   sudo certbot --nginx -d sia-bp.butzke.it
   ```
7. Nginx testen und laden:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Betrieb

- Logs:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f
  ```
- Neustart:
  ```bash
  docker compose -f docker-compose.prod.yml up -d
  ```
- Stoppen:
  ```bash
  docker compose -f docker-compose.prod.yml down
  ```
- App-Health:
  `https://sia-bp.butzke.it/health`

## Ressourcen

Der Stack ist auf mehrere gleichzeitige Referee-Eingaben plus grob 50 Zuschauer ausgelegt:

- `WEB_CONCURRENCY=4` startet vier ASGI-Worker.
- `worker_processes auto` und `worker_connections 4096` im Nginx reichen fuer die erwartete Last locker aus.
- Redis entkoppelt die WebSocket-Verteilung zwischen den ASGI-Workern.

Auf einem kleinen VPS solltest du fuer einen sauberen Betrieb mindestens 2 vCPU und 4 GB RAM einplanen. Wenn der Server kleiner ist, `WEB_CONCURRENCY` eher auf `2` setzen.

## Handlungsbedarf von dir

- DNS-Eintrag fuer `sia-bp.butzke.it` setzen.
- Die vier Secret-Werte in [`.env`](./.env) ersetzen.
- Host-Nginx und `certbot` auf dem Netcup-Server einrichten.
- Sicherstellen, dass in der Firewall nur `80` und `443` offen sind; `18080` bleibt lokal auf `127.0.0.1`.
- Vor dem ersten echten Turnier einen kompletten Testlauf machen:
  Admin-Login, LiveView, MobileView, WebSockets, Referee-Flow, Gruppenphase und KO-Phase.
