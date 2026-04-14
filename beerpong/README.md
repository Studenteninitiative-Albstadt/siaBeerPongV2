# 🍺 SIA BeerPong Tournament Manager

UI-first Demo für Beer-Pong-Turniere. Der aktuelle Stand ist **single‑client** und speichert alles im Browser; der Backend-Server liefert nur den Turnierplan. Mehrbenutzer‑Sync, echte Persistenz und Play‑In/KO‑Automatik sind noch nicht angebunden.

---

## 📋 Projektübersicht

- **Zweck (aktuell):** Schnelles Ausprobieren des Frontends (Wizard, Gruppenphase, rudimentäres KO-Bracket) für lokale Demozwecke.
- **Status:** Aktive Entwicklung, viele Features noch nicht verkabelt (siehe „Bekannte Lücken“).

---

## 🏗️ Architektur & Tech-Stack

### Frontend
- **Framework:** Vue 3 (Composition API)
- **Build-Tool:** Vite
- **Styling:** Bootstrap 5
- **Socket.IO Client:** vorhanden, aber nur Lauschen; keine tatsächliche Mehrbenutzer-Sync.
- **Node-Version:** 20 (Alpine)

### Backend (läuft, wird aber kaum genutzt)
- **Framework:** Flask (Python 3.12)
- **DB:** SQLite (`tournament.db`)
- **Echtzeit:** Flask-SocketIO + Eventlet
- **CORS:** offen (`*`)
- **ORM:** Flask-SQLAlchemy
- **Derzeitige Nutzung:** einzig der Endpoint `/compute-tournament-plan` wird vom Frontend aufgerufen.

### DevOps
- **Containerisierung:** Docker + Docker Compose
- **Frontend-Port:** 5173 (Vite Dev Server)
- **Backend-Port:** 5000 (Flask + SocketIO)
- **Volume Mounts:** Live-Code-Änderungen ohne Rebuild

---

## 🏁 Bekannte Lücken (Stand jetzt)

- Keine Persistenz: Teams, Spiele, Ergebnisse und Tiebreaks leben nur im Browser-State.
- Kein Mehrbenutzerbetrieb: Keine Speicherung via REST, keine Socket-Broadcasts; zweite Clients sehen keine Änderungen.
- Play‑In nicht funktionsfähig: UI-Props passen nicht zum Backend-API, es erfolgt kein Request an `/compute-playin-from-tables`.
- Gruppen/Matches nicht aus Backend: Gruppen werden clientseitig deterministisch verteilt; Round-Robin wird lokal erzeugt.
- KO-Bracket nur für 4 oder 8 Teams, Seeding rein alphabetisch; keine Live-Updates oder Speicherung.
- Tiebreak-Logik nur im Client; Head‑to‑Head und Backend‑Tiebreak-Modelle werden nicht genutzt.

---

## 📊 Datenmodelle

### Tournament
```
id (PK)
mode: String (default: "groups")
participant_count: Integer (default: 8)
cups_per_game: Integer (default: 6)
created_at: DateTime
```
*Speichert globale Turnier-Konfiguration*

### Team
```
id (PK)
name: String
group_name: String (nullable)
```
*Repräsentiert ein Team/Spielerpaar*

### GroupMatch
```
id (PK)
group_name: String
team1: String
team2: String
winner: String (nullable)
cups_team1: Integer (nullable)
cups_team2: Integer (nullable)
order_index: Integer
```
*Einzelne Gruppenspiele mit Live-Scores*

### Tiebreak
```
id (PK)
group_name: String
mode: String (z.B. "cups", "rage")
payload: Text (JSON)
resolved: Boolean
```
*Handelt Tiebreak-Szenarien in Gruppen*

---

## 🎮 Funktionalitäten

### Phase 1: Turnier-Konfiguration (Wizard)
- ✅ Teams eingeben (2–128, lokal)
- ✅ Cups pro Spiel setzen (6/10/custom)
- 🚧 Modus-Auswahl: UI aktuell nur „groups“; andere Modi fehlen.
- ✅ Turnierplan wird vom Backend berechnet (`/compute-tournament-plan`).

### Phase 2: Gruppenphase
- ⚠️ Gruppeneinteilung rein clientseitig (deterministische Verteilung, kein Shuffle, kein Backend).
- ✅ Round-Robin pro Gruppe wird lokal erzeugt; Ergebnisse werden nur im Browser gehalten.
- 🚫 Kein Speichern/Broadcast: Neue Tabs/Clients sehen keine Änderungen.
- ✅ Tiebreak-UI (Mini-Runde, Rage-Cage, Rage-4) läuft clientseitig; kein Backend-/H2H-Abgleich.

### Phase 3: Play-In
- 🚫 Derzeit nicht verkabelt: UI erwartet andere Props als das Backend liefert; kein Request an `/compute-playin-from-tables`.

### Phase 4: K.O.-Phase
- ⚠️ Bracket nur für 4 oder 8 Teams, Seeding alphabetisch.
- 🚫 Keine Speicherung oder Echtzeit-Updates; reine Client-State-Demo.

---

## 🚀 Installation & Ausführung

### Mit Docker (Empfohlen)

```bash
cd /path/to/beerpong
docker-compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:5000

### Lokal (Entwicklung ohne Docker)

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Backend läuft auf `http://localhost:5000` (wird momentan nur für `/compute-tournament-plan` benötigt).

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Frontend läuft auf `http://localhost:5173`

---

## 📁 Projektstruktur

```
beerpong/
├── docker-compose.yml          # Service-Orchestrierung
├── README.md                   # Diese Datei
│
├── backend/
│   ├── app.py                  # Haupt-App (Models, Routes, SocketIO)
│   ├── requirements.txt        # Python Dependencies
│   ├── Dockerfile              # Python 3.12-slim Image
│   └── tournament.db           # SQLite Datenbank (erstellt beim Start)
│
└── frontend/
    ├── index.html              # Entry Point
    ├── package.json            # Node Dependencies & Scripts
    ├── vite.config.js          # Vite Konfiguration
    ├── Dockerfile              # Node 20-Alpine Image
    ├── public/                 # Statische Assets
    └── src/
        ├── main.js             # Socket.IO Setup + App Mount
        ├── App.vue             # Main Component (Workflow)
        ├── style.css           # Global CSS
        ├── assets/             # Images, Fonts etc.
        └── components/
            ├── HeaderBar.vue              # Header mit Title
            ├── TournamentWizard.vue       # Setup-Wizard (Steps 0-3)
            ├── GroupsView/
            │   ├── GroupsView.vue         # Container für Gruppenphase
            │   ├── GroupCard.vue          # Einzelne Gruppe
            │   ├── GroupHeader.vue        # Gruppenüberschrift
            │   ├── GroupMatches.vue       # Match-Container
            │   ├── GroupTable.vue         # Gruppen-Tabelle
            │   ├── TournamentInfo.vue     # Turnierinfos
            │   ├── TournamentFooter.vue   # Footerzeile
            │   ├── TiebreakControls.vue   # Tiebreak UI
            │   ├── TiebreakMini.vue       # Schneller Tiebreak
            │   └── TiebreakRage.vue       # Rage-Spiel UI
            ├── PlayInView.vue             # Play-In-Matches
            ├── KnockoutView.vue           # K.O.-Bracket Anzeige
            ├── KnockoutPreview.vue        # K.O.-Vorschau
            ├── ConfettiOverlay.vue        # Animationen
            └── HelloWorld.vue             # Demo-Komponente
```

---

## 🔌 API & WebSocket Events (Backend-Fähigkeiten vs. aktueller UI-Einsatz)

### REST (implementiert)

| Endpoint | Methode | Hinweis |
|----------|---------|---------|
| `/compute-tournament-plan` | POST | **einziger Endpoint, den die UI aktuell nutzt** |
| `/compute-playin-from-tables` | POST | Play-In-Berechnung (von der UI derzeit nicht aufgerufen) |
| `/teams` | GET / POST | Team-Liste / Team anlegen |
| `/teams/<id>` | DELETE | Team löschen |
| `/tournament` | GET / POST | Turnier-Config lesen/setzen |
| `/generate-groups` | POST | Gruppen + Round-Robin in DB erzeugen (UI ruft nicht auf) |
| `/group-matches` | GET | Gruppenspiele aus DB |
| `/group-matches/<group>/<match_id>/result` | POST | Ergebnis speichern |
| `/health` | GET | Healthcheck |

### Socket.IO (Server → Client Broadcasts)
- `hello` (bei Connect)
- `teams_updated`, `teams_deleted`
- `group_matches_updated`
- `match_updated`
- `tournament_updated`

**Client → Server:** aktuell nichts; das Frontend lauscht nur.

---

## ⚙️ Konfiguration

### Environment Variables (optional)

**Backend** (in Docker oder `.env`):
```bash
FLASK_ENV=development        # oder production
SECRET_KEY=your-secret-key   # Sicherheitsschlüssel
DATABASE_URL=sqlite:///...   # Datenbank-Pfad
DEBUG=True
```

**Frontend** (in Docker):
```bash
VITE_API_URL=http://localhost:5000
```

### Wichtige Config-Werte in `app.py`

```python
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SECRET_KEY"] = "change-me"  # ⚠️ Produktion anpassen!
CORS(app, origins="*")  # ⚠️ In Produktion eingrenzen!
```

---

## 🔍 Feature-Details

### Automatische Gruppeneinteilung
- Backend-Planer: Band-Logik (≤4→1, ≤8→2, ≤11→3, ≤16→4, danach ~4–5 pro Gruppe) mit balancierten Gruppengrößen.
- Frontend aktuell: verteilt Teams deterministisch per Index auf Gruppen und ignoriert den Backend-Plan. Zum echten Backend-Flow müsste `/generate-groups` benutzt werden.

### Tiebreak-Logik (bei Gruppen-Tie)
- Backend-Ranking (implementiert, aber UI nutzt es nicht): Punkte → Cups-Diff → H2H → Cups For → Name.
- Frontend-Ranking (genutzt): Punkte → Cups-Diff → Cups For → ursprüngliche Reihenfolge; kein H2H.
- Tiebreak-UI (Mini/Rage/Rage4) wirkt nur im Client-State, keine Persistenz oder Server-Abgleich.

### K.O.-Bracket-Größe
- Backend wählt die nächste 2er-Potenz, Bracket-Template nur für 4 oder 8 Teams hinterlegt.
- Frontend rendert ebenfalls nur 4er/8er Brackets; Seeding alphabetisch, keine Byes-Unterstützung.

---

## 📝 Development Workflow

### Code ändern → Live-Updates

1. **Backend:** Änderungen in `backend/app.py` → Docker-Container speichert automatisch (Volume Mount)
2. **Frontend:** Änderungen in `frontend/src/` → Vite Hot-Module-Reload

### Datenbank zurücksetzen

```bash
# Durch Volume-Mount können Sie die Datei löschen:
rm backend/tournament.db

# Oder im Backend:
docker exec bp-backend rm /app/tournament.db
docker restart bp-backend
```

### Logs anschauen

```bash
docker-compose logs -f backend    # Backend-Logs
docker-compose logs -f frontend   # Frontend-Logs
docker-compose logs -f            # Alle Logs
```

---

## ⚠️ Bekannte Limitierungen & TODO

### Aktuelle Limitierungen

| Bereich | Issue | Auswirkung |
|---------|-------|-----------|
| **Frontend↔Backend** | UI nutzt nur `/compute-tournament-plan`; keine REST/Sockets für Teams/Spiele | Reload verliert Daten, keine Mehrbenutzer-Sichtbarkeit |
| **Datenbank** | SQLite (Backend nutzt sie; UI schreibt nicht) | Persistenz nur via API, nicht über die Oberfläche |
| **Sicherheit** | CORS offen (`*`) | Nur für Development! |
| **Config** | Hardcoded in `app.py` | Secret-Key in Produktion unsicher |
| **Testing** | Keine Tests vorhanden | Fehlerpotenzial bei Änderungen |

### Empfehlung: Nächste Schritte

- [ ] **Tests hinzufügen:** pytest (Backend) + Vitest/Jest (Frontend)
- [ ] **Config externalisieren:** Environment-basierte Konfiguration für Prod
- [ ] **Database Migration:** Alembic für DB-Versionierung
- [ ] **API-Docs:** OpenAPI/Swagger Dokumentation
- [ ] **Input-Validierung:** Strenger validieren (Teams, Scores)
- [ ] **Error-Handling:** Konsistente Error-Messages
- [ ] **Logging:** Strukturiertes Logging (Backend + Frontend)
- [ ] **Backup-Strategie:** Automatische DB-Backups

---

## 🔒 Sicherheitshinweise

⚠️ **Für Produktion notwendig:**

1. **CORS einschränken:**
   ```python
   CORS(app, origins=["https://yourdomain.com"])
   ```

2. **Secret-Key sicher speichern:**
   ```python
   app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback")
   ```

3. **SQLite → PostgreSQL/MySQL migrieren**

4. **HTTPS/TLS enablen** (Reverse Proxy, z.B. Nginx)

5. **Input-Validierung verstärken** (Länge, Sonderzeichen, Injections)

6. **Rate Limiting** auf API-Endpoints

---

## 🤝 Beitragen

1. Feature-Branch erstellen: `git checkout -b feature/xyz`
2. Änderungen committen: `git commit -am "Add feature xyz"`
3. Push: `git push origin feature/xyz`
4. Pull Request + Review

---

## 📄 Lizenz

(Lizenztyp hier eintragen, z.B. MIT, Apache 2.0)

---

## 📞 Support & Fragen

Bei Fragen oder Issues:
- Issues im Repository erstellen
- Code-Kommentare beachten (vor allem in `app.py` Backend-Routes)
- Logs checken: `docker-compose logs`

---

### 📚 Weitere Ressourcen

- [Vue 3 Dokumentation](https://vuejs.org)
- [Flask Dokumentation](https://flask.palletsprojects.com)
- [Socket.IO Guide](https://socket.io)
- [Vite Guide](https://vitejs.dev)
- [Docker Compose Handbook](https://docs.docker.com/compose)

---

**Zuletzt aktualisiert:** 13. April 2026  
**Version:** 0.0.1 (Development)
