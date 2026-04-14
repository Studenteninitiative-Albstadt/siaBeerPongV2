# SIA BeerPong Tournament Manager

Aktueller Stand des Projekts im Verzeichnis `beerpong/`: ein produktiv nutzbarer Beer-Pong-Turniermanager mit Vue-Frontend, Django-Backend, JWT-Login, WebSockets, persistenter Speicherung und separaten Ansichten fuer Orga, Beamer/LiveView und Mobile.

Die Anwendung ist funktional, aber nicht in allen Bereichen konsequent "backend-first". Teile der Turnierlogik liegen bereits sauber im Django-Backend, andere Teile werden aktuell noch im Frontend berechnet und anschliessend in die API geschrieben. Diese README beschreibt genau diesen IST-Zustand.

---

## Projektstatus

- Architekturstand: Vue 3 + Vite + Pinia im Frontend, Django + DRF + Channels + Redis im Backend.
- Login und Rollenmodell sind aktiv: `orga` und `liveview`.
- Turniere, Teams, Gruppenspiele, Play-In-Matches und KO-Matches werden persistent gespeichert.
- Gruppen-Matchupdates werden in Echtzeit per WebSocket an verbundene Clients verteilt.
- Mobile-Zugriff funktioniert ueber einen oeffentlichen Turnier-Token.
- Das alte Flask-Backend liegt noch im Repo, ist aber nicht Teil des aktiven Docker-Stacks.

### Kurzfazit

Was heute bereits gut funktioniert:

- Turnier anlegen, laden, loeschen
- Teams und Spielernamen erfassen
- Gruppenphase live spielen, inklusive Cup-Tracking, Undo und Re-Rack
- Live-Standings und Multitab-Synchronisation
- Play-In-Matches festlegen und Sieger auswaehlen
- KO-Phase spielen und persistent fortschreiben
- LiveView mit QR-Code fuer Mobile-Ansicht

Was aktuell noch nicht sauber bis zum Ende ausmodelliert ist:

- Gruppenerzeugung und Play-In-Ermittlung sind primaer frontendgetrieben
- `tableCount` aus dem Wizard wird im Django-Backend noch nicht gespeichert
- Mobile-"Top-Spieler" basiert aktuell auf Teamwerten, nicht auf echten Spielerstatistiken
- Play-In-Zusatzdaten wie `ko_size`, Ranking-Kandidaten oder Policy-Notes werden beim Reload nicht vollstaendig rekonstruiert
- Es gibt keine automatisierten Tests

---

## Architektur

### Frontend

- Vue `3.5`
- Vite `7`
- Pinia fuer Auth- und Turnier-State
- Vue Router mit Hash-Routing
- Bootstrap `5`
- QR-Code-Generierung fuer den mobilen Zugang

Zentrale Ansichten:

- `LoginView`: JWT-Login
- `AdminView`: Turnierverwaltung, Wizard, Gruppenphase, Play-In, KO
- `LiveView`: Beamer-/Live-Ansicht mit Live-Tischen, Gruppenrotation und QR-Code
- `MobileView`: oeffentliche Mobile-Ansicht per Token

### Backend

- Django `5.x`
- Django REST Framework
- `rest_framework_simplejwt` fuer JWT
- Django Channels + Redis fuer WebSockets
- SQLite als aktuelle Datenbank
- Custom User-Modell mit Rollenflags `is_orga` und `is_liveview`

Wichtige Eigenschaften:

- REST fuer CRUD und Turniermutationen
- WebSocket-Channel pro Turnier unter `/ws/tournament/{id}/`
- Vollstaendige Snapshot-Auslieferung ueber `load-all-data`
- Trefferhistorie pro Match ueber `CupHit`

### Infrastruktur

- Docker Compose startet `frontend`, `backend` und `redis`
- Vite proxyt lokal auf das Django-Backend
- Daphne startet das ASGI-Backend im Container

---

## Rollen und Zugriff

### Orga

- Vollzugriff auf Turniere und alle Mutationen
- Zugriff auf Wizard, Gruppenphase, Play-In und KO

### LiveView

- Zugriff auf Turnierliste, LiveView und Live-Daten
- Keine Orga-Mutationen ueber die normale UI

### Mobile

- Kein Login
- Zugriff ausschliesslich ueber `mobile_access_token`
- Endpoint: `GET /tournaments/{id}/mobile-state?token=...`
- WebSocket-Verbindung ueber `?mobile_token=...`

### Standard-Logins im Docker-Setup

Die Default-User werden beim Containerstart automatisch angelegt:

- `admin / admin` mit Orga-Rechten
- `live / live` mit LiveView-Rechten

---

## Datenmodell

### `Tournament`

Speichert u. a.:

- Name
- Modus
- Teilnehmerzahl
- Becher pro Spiel
- `finale_with_10_cups`
- Status: `group`, `playin`, `ko`, `finished`
- `mobile_access_token`

Wichtig: Ein Feld fuer `table_count` existiert im Django-Modell aktuell nicht mehr, obwohl das Frontend diese Einstellung weiterhin anbietet.

### `Player`

- Spielername
- `total_cups_hit`

### `Team`

- Gehoert zu einem Turnier
- Name
- Referenzen auf `player1` und `player2`
- `group_name`

### `Match`

Deckt drei Phasen ab:

- `group`
- `playin`
- `ko`

Zusaetzlich vorhanden:

- `cups_team1`, `cups_team2`
- `winner`
- `cups_state_team1`, `cups_state_team2`
- `hit_history_team1`, `hit_history_team2`
- Re-Rack-Flags
- KO-Metadaten wie Runde, Bracket-Typ und Match-Index

### `CupHit`

- Verknuepfung von Match, Team und Spieler
- Eintrag pro registriertem Treffer
- Grundlage fuer spaetere echte Spielerstatistiken

---

## Tatsaechlicher Feature-Stand

### 1. Turnierverwaltung

Ist implementiert:

- Turnier anlegen
- Turnierliste laden
- Turnier loeschen
- Turnier via `load-all-data` wiederherstellen

Aktuelle Einschraenkungen:

- Der Wizard fragt `tableCount` ab, das Django-Backend speichert diesen Wert aber derzeit nicht.
- `mode` wird zwar mitgefuehrt, die aktive Produktlogik ist faktisch auf Gruppenphase -> Play-In -> KO ausgelegt.

### 2. Team- und Spielererfassung

Ist implementiert:

- Teams werden ueber `save-teams` gespeichert
- Zu jedem Team koennen zwei Spieler hinterlegt werden
- Teamdaten werden beim Reload wieder geladen

Aktuelle Einschraenkungen:

- `Player` ist global und nicht turnierlokal eindeutig. Gleich benannte Spieler in mehreren Turnieren teilen sich aktuell denselben Datensatz.

### 3. Gruppenphase

Ist implementiert:

- Round-Robin-Matches pro Gruppe
- Live-Tischmodus mit Cup-Zustand statt nur Punktzahl
- Undo der letzten Treffer
- einmaliger Re-Rack pro Seite
- Schuetzenwahl pro Treffer, wenn Spielernamen vorhanden sind
- Persistente Matchupdates ueber `/group-match`
- Backend-berechnete Standings
- WebSocket-Broadcast bei Aenderungen

Wichtige Realitaet im aktuellen Flow:

- Die sichtbare Gruppenerzeugung passiert im Admin-Flow derzeit primaer im Frontend.
- Das Backend hat zwar `compute-plan` und `generate-groups`, die normale Admin-Oberflaeche erzeugt die Gruppen aber lokal und schreibt sie dann ueber `save-group-phase` zurueck.

Tiebreaks:

- Standard-Sortierung: Punkte -> Becherdifferenz -> Becher+ -> Name
- UI fuer Last-Cup-Shoot-Off / Rage-Cage-Sonderfaelle ist vorhanden
- Diese Tiebreak-Sonderlogik ist aktuell frontendseitig orchestriert

### 4. Play-In

Ist implementiert:

- Ermittlung eines KO-Ziels
- Ranking der Kandidaten aus Gruppenplatzierungen
- Play-In-Matches fuer exakte Gleichstaende am Cut-Off
- Rage-Cage-Hinweise fuer 3er-Gleichstaende
- Persistenz der erzeugten Play-In-Matches

Wichtige Einschraenkungen:

- Die Play-In-Berechnung findet aktuell im Frontend statt, nicht als kanonische Django-Service-Logik.
- Das Backend speichert beim Schritt `save-playin` nur die eigentlichen Play-In-Matches und setzt den Turnierstatus.
- Zusatzinformationen wie `ko_size`, `direct_qualified`, `ranking_candidates`, `rage_cage_groups` oder `policy_notes` werden beim spaeteren Reload nicht vollstaendig aus dem Backend rekonstruiert.

### 5. KO-Phase

Ist implementiert:

- KO-Vorschau
- automatisches Bracket-Seeding im Frontend
- Persistenz kompletter KO-Runden ueber `save-ko-bracket`
- Einzelupdates pro KO-Match ueber `ko-match`
- automatische Fortschreibung von Siegern ins naechste Match
- Spiel um Platz 3
- optional 10 Becher fuer Finale und Platz-3-Spiel
- Siegerbanner und Konfetti

Wichtige Realitaet:

- Die KO-Logik ist aktuell gemischt: Bracket-Aufbau und Propagation liegen im Frontend, Persistenz und Reload im Backend.
- Das Backend speichert KO-Runden sauber, berechnet aber die Bracket-Struktur nicht selbst.

### 6. LiveView

Ist implementiert:

- Auswahl eines aktiven Turniers
- WebSocket-Statusanzeige
- grosse Live-Darstellung aktiver Tische
- rotierende Gruppen-Tabellen
- QR-Code fuer die Mobile-Ansicht
- Anzeige der KO-Runden

Technische Besonderheit:

- Die LiveView nutzt sowohl Store/WebSocket-Daten als auch ein zusaetzliches Polling auf `load-all-data`, um die aktiven Tischdaten robust aktuell zu halten.

### 7. MobileView

Ist implementiert:

- tokenbasierter Aufruf per QR-Code
- Gruppenstaende
- KO-Uebersicht
- naechste Spiele

Aktuelle Einschraenkung:

- Der Tab "Top-Spieler" zeigt derzeit keine echten Einzelspieler-Rankings, sondern nutzt Teamwerte als Platzhalter, obwohl das Backend `CupHit` und `total_cups_hit` bereits erfasst.

---

## API und Echtzeit

### Auth

- `POST /auth/token`
- `POST /auth/token/refresh`

### Turniere

- `GET /tournaments`
- `POST /tournaments`
- `GET /tournaments/{id}`
- `DELETE /tournaments/{id}`
- `POST /tournaments/{id}/update`
- `GET /tournaments/{id}/load-all-data`

### Teams und Gruppenphase

- `POST /tournaments/{id}/compute-plan`
- `POST /tournaments/{id}/save-teams`
- `GET /tournaments/{id}/load-teams`
- `POST /tournaments/{id}/generate-groups`
- `POST /tournaments/{id}/save-group-phase`
- `POST /tournaments/{id}/group-match`
- `GET /tournaments/{id}/group-standings`

### Play-In und KO

- `POST /tournaments/{id}/save-playin`
- `GET /tournaments/{id}/load-playin`
- `POST /tournaments/{id}/save-ko-bracket`
- `GET /tournaments/{id}/load-ko-bracket`
- `POST /tournaments/{id}/ko-match`

### Oeffentlich / Health

- `GET /tournaments/{id}/mobile-state?token=...`
- `GET /health`

### WebSocket

- Route: `/ws/tournament/{id}/`
- Auth-Varianten:
  - `?token=<jwt>`
  - `?mobile_token=<uuid>`

Broadcast-Events kommen als `state.update` und transportieren je nach Mutation z. B.:

- `tournament_updated`
- `group_phase_updated`
- `match_updated`
- `phase_changed`
- `ko_updated`
- `ko_match_updated`

---

## Projektstruktur

```text
beerpong/
|-- docker-compose.yml
|-- README.md
|-- backend/                   # Altes Flask-Backend, aktuell nicht im Compose-Stack aktiv
|-- django_backend/
|   |-- config/                # Django-Settings, URLConf, ASGI
|   |-- tournament/            # Models, Views, Services, Consumer, Auth, Permissions
|   |-- manage.py
|   |-- entrypoint.sh
|   `-- Dockerfile
`-- frontend/
    |-- public/
    |-- src/
    |   |-- components/
    |   |   |-- GroupsView/
    |   |   |-- KnockoutView.vue
    |   |   |-- PlayInView.vue
    |   |   |-- TournamentWizard.vue
    |   |   `-- MatchTableControls.vue
    |   |-- stores/
    |   |-- views/
    |   |-- router/
    |   |-- api.js
    |   |-- fetch.js
    |   `-- main.js
    |-- vite.config.js
    `-- Dockerfile
```

---

## Lokale Entwicklung

### Empfohlen: Docker Compose

```bash
cd beerpong
docker-compose up --build
```

Verfuegbare URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Django Admin: `http://localhost:8000/django-admin/`
- Healthcheck: `http://localhost:8000/health`

Hinweis: Die bisherige README nannte `/admin`; der aktuelle Django-Pfad ist `/django-admin/`.

### Optional: lokal ohne Docker

Backend:

```bash
cd beerpong/django_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py shell
```

Anschliessend ASGI-Server starten:

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Frontend:

```bash
cd beerpong/frontend
npm install
npm run dev
```

Fuer lokale Direktverbindung muss in `frontend/.env.local` gesetzt werden:

```bash
VITE_API_BASE=http://localhost:8000
```

Fuer WebSockets wird lokal ausserdem ein erreichbarer Redis-Server benoetigt.

---

## Wichtige Implementierungsdetails

### Vite-Proxy

Im Docker-Setup wird standardmaessig ueber Vite auf folgende Pfade geproxyt:

- `/tournaments`
- `/auth`
- `/health`
- `/ws`

### Globale Fetch-Authentifizierung

Das Frontend patcht `window.fetch` global in `src/fetch.js`, damit alle Requests automatisch den Bearer-Token tragen. Das ist relevant, weil nicht alle Komponenten den zentralen API-Client aus `src/api.js` nutzen.

### Snapshot-Modell

Der wichtigste Ladepunkt ist `GET /tournaments/{id}/load-all-data`. Der Endpoint liefert den zusammengesetzten Zustand fuer:

- Turnier-Metadaten
- Teams und Spielerzuordnung
- Gruppenphase
- Gruppenstandings
- Play-In-Matches
- KO-Runden

Dieses Snapshot-Modell ist die Grundlage fuer Reload, LiveView und MobileView.

---

## Bekannte technische Luecken

- Keine automatisierten Tests fuer Frontend oder Backend
- Keine formale API-Dokumentation
- SQLite ist die einzige aktiv konfigurierte Datenbank
- `tableCount` aus dem UI fehlt im Django-Datenmodell
- Play-In-Zusatzmetadaten werden nicht vollstaendig round-trip-faehig gespeichert
- Echte Spieler-Toplisten werden im Mobile-Frontend noch nicht aus `CupHit` aufgebaut
- Das Repo enthaelt noch Altlasten aus dem Flask-Vorgaenger, was die technische Trennschaerfe etwas verwischt

---

## Empfehlung fuer die naechste Planungsrunde

Wenn die naechsten Features strukturiert angegangen werden sollen, bieten sich aus dem IST-Zustand vor allem diese Baustellen an:

1. Turnierlogik fuer Gruppenaufbau und Play-In vom Frontend ins Django-Backend ziehen.
2. `tableCount` wieder sauber ins Django-Modell und in die Snapshot-API aufnehmen.
3. Play-In-Snapshots vollstaendig persistieren, damit Reload und Fortsetzen robust werden.
4. Echte Spielerstatistiken aus `CupHit` in LiveView und MobileView ausspielen.
5. Smoke-Tests fuer Kernflows aufsetzen.

---

## Veralteter Bestand im Repo

`beerpong/backend/` enthaelt das fruehere Flask-/Socket.IO-Backend. Es ist aktuell ein Referenz- bzw. Migrationsrest und wird durch `docker-compose.yml` nicht gestartet. Teile des Frontends und der Projektgeschichte erklaeren sich noch aus dieser frueheren Architektur.

---

Zuletzt aktualisiert: 14. April 2026
