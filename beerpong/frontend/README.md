# Frontend

Dies ist die aktive Vue-SPA fuer Admin, LiveView, MobileView und RefereeView.

## Stack

| Paket | Einsatz |
| --- | --- |
| `vue` | UI |
| `vue-router` | Hash-Routing |
| `pinia` | globaler Zustand |
| `bootstrap` | Basis-Layout und Komponenten |
| `qrcode` | QR-Code-Rendering in LiveView |
| `vite` | Dev-Server und Build |
| `@vitejs/plugin-vue` | Vue-Support fuer Vite |

## Einstiegspunkte

| Datei | Zweck |
| --- | --- |
| `index.html` | setzt Favicon und Dokumenttitel `SIA Bier Pong` |
| `src/main.js` | startet App, Pinia, Router und globalen Fetch-Interceptor |
| `src/App.vue` | Root-Komponente |
| `src/style.css` | globale Styles |

## Betriebsarten

### Dev

- `npm run dev`
- typischerweise ueber `docker-compose.yml`
- `VITE_API_BASE` ist standardmaessig leer, daher gleiche Origin / Proxy

### Produktion

- Build erfolgt ueber `deploy/nginx/Dockerfile`
- Ergebnis landet als statische SPA im Nginx-Image
- API- und WebSocket-Zugriffe gehen ueber denselben Host

## Route-Ziele

| Route | Bedeutung |
| --- | --- |
| `/#/login` | Login |
| `/#/admin` | Root-Admin |
| `/#/referee` | Schiedsrichter |
| `/#/live` | Beamer |
| `/#/mobile` | oeffentliche Mobile-Seite |

## Verzeichnisse

| Ordner | Zweck |
| --- | --- |
| `public/` | statische Assets wie Logo/Favicon |
| `src/` | kompletter Quellcode |

Mehr Details liegen in den Unterordner-READMEs.
