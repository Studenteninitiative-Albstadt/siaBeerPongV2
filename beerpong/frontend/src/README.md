# Frontend Source

Dieser Ordner enthaelt den kompletten Quellcode der SPA.

## Top-Level-Dateien

| Datei | Zweck |
| --- | --- |
| `main.js` | initialisiert App, Pinia, Router, Bootstrap und `fetch.js` |
| `App.vue` | Root-Shell |
| `api.js` | zentraler API-Client inkl. `publicRequest()` fuer Mobile |
| `fetch.js` | globaler JWT-Interceptor fuer rohe `fetch()`-Aufrufe |
| `style.css` | globale Styles |

## Unterordner

| Ordner | Zweck |
| --- | --- |
| `assets/` | Quell-Assets aus dem Scaffold |
| `components/` | grosse UI-Bausteine |
| `router/` | Route-Definitionen und Guards |
| `stores/` | Pinia-Stores |
| `utils/` | Match- und KO-Helfer |
| `views/` | Routen-Ziele |

## Wichtige Architekturentscheidungen

- Routing ist hash-basiert, damit der Host nur `index.html` ausliefern muss.
- Viele Komponenten nutzen rohe `fetch()`-Aufrufe; `fetch.js` haengt dafuer global das JWT an.
- `api.js` trennt geschuetzte Requests von echten Public-Requests wie `mobile-state`.
- Der Turnierstore merged sowohl Vollsnapshots als auch Teilupdates vom WebSocket.
