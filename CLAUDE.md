# CLAUDE.md - BeerPong v2 Development Guide

## 🛠 Tech Stack
- **Frontend:** Vue 3 (Composition API), Pinia, Vite, Bootstrap 5.
- **Backend:** Django 4.x, Django REST Framework, Django Channels (WebSockets), Redis.
- **Database:** SQLite (Dev), PostgreSQL (Prod).
- **Orchestration:** Docker Compose.

## 📋 Aktuelle Feature-Liste & Bugs
1. **Live-Sync Fix:** Admin-Panel Becher-Klicks synchronisieren nicht zuverlässig mit der Live-View (außer beim letzten Spiel).
2. **Admin UI:** Gruppen-Tabellen vergrößern, Header abkürzen (St, Pkt, S, N, Diff, +).
3. **Re-Rack Upgrade:** Drag & Drop Positionierung für aktive Becher (statt An-/Aus-Klicken).
4. **Hit-Flow:** "Überspringen" entfernen, Spieler-Auswahl mit Highlight + Bestätigen-Button.
5. **Undo/Re-Rack State:** Re-Rack muss im Undo-Verlauf gespeichert werden. Punkte-Korrektur bei Undo sicherstellen.
6. **Spielabschluss-Flow:** Komplexer Dialog-Baum für Nachwurf, Overtime (3 Becher) und finalen Abschluss mit "Zurück"-Option.

## 🏗 Architektur-Notizen
- **WebSockets:** Kommunikation über `tournament_{id}` Gruppe.
- **State:** Pinia Store `tournament.js` ist die Single Source of Truth im Frontend.
- **API:** Alle Match-Updates laufen über `POST /api/tournaments/{id}/group-match/`.

## 🛠 Befehle
- `docker compose up --build -V` (Start mit frischen Volumes)
- `docker exec -it bp-backend python manage.py migrate`
- `docker exec -it bp-backend python manage.py createsuperuser`
