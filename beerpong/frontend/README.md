# SIA BeerPong - Vue 3 Frontend

Das Frontend ist eine moderne Single-Page-Application (SPA) auf Basis von Vue 3, Vite und Pinia. Es implementiert den kompletten Turnier-Ablauf von der Anmeldung bis zur Siegerehrung.

## Frontend-Architektur

```text
       [ Browser ]
           |
   +-------v-------+      +-------------------+
   |   Vue Router  | <----| Guards (Auth/Role)|
   +-------+-------+      +-------------------+
           |
   +-------v-------+      +-------------------+
   |   Views       | <----| Components        |
   +-------+-------+      +---------+---------+
           |                        |
   +-------v-------+      +---------v---------+
   |   Pinia Store | <----| API / WebSockets  |
   +---------------+      +-------------------+
```

- **Router**: Hash-basierte Navigation mit rollenbasierten Zugriffskontrollen.
- **Pinia**: Zentrales State-Management für Turnierdaten (`tournament.js`) und Authentifizierung (`auth.js`).
- **WebSockets**: Live-Synchronisation des Turnier-Status.

## Views & Navigations-Pfade

| Pfad | View | Zielgruppe |
|---|---|---|
| `/#/login` | LoginView | Alle (System-Einstieg) |
| `/#/admin` | AdminView | Turnier-Leitung (Wizard, Gruppen, KO) |
| `/#/live` | LiveView | Beamer / Teilnehmer (Live-Status) |
| `/#/mobile` | MobileView | Spieler (Read-Only via QR-Token) |

## Entwicklungs-Setup

Lokal (außerhalb von Docker):

```bash
cd frontend
npm install
npm run dev
```

Die API-URL wird über die Umgebungsvariable `VITE_API_BASE` gesteuert.

---
*Status: 15. April 2026*
