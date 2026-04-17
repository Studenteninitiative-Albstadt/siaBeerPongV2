# Host Nginx

Dieser Ordner enthaelt die Konfiguration fuer den Nginx, der direkt auf dem VPS laeuft.

## Datei

| Datei | Zweck |
| --- | --- |
| `sia-bp.butzke.it.conf` | vHost fuer die Subdomain mit HTTP->HTTPS-Redirect und Reverse Proxy auf den internen App-Port |

## Erwartete Umgebung

- Domain: `sia-bp.butzke.it`
- Zertifikate unter `/etc/letsencrypt/live/sia-bp.butzke.it/`
- Weiterleitung auf `http://127.0.0.1:18080` beziehungsweise `APP_HTTP_PORT`

## Verhalten

- Port `80`: Redirect auf HTTPS
- Port `443`: Proxy auf den internen Docker-Nginx
- WebSocket-Upgrade ist aktiviert
- `proxy_buffering off` und lange Timeouts passen zum Livebetrieb mit vielen parallelen Clients

Diese Datei ist kein Container-Asset. Sie wird auf dem Host installiert.
