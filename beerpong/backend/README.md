# Legacy Flask Backend

Dieser Ordner enthaelt das alte Flask-/Socket.IO-Backend. Er ist heute nur noch Archivmaterial und wird weder vom aktiven Dev- noch vom Prod-Compose benutzt.

## Inhalt

| Datei | Bedeutung |
| --- | --- |
| `app.py` | Monolithisches Flask-Backend mit SQLite, Socket.IO und eigener KO-/Gruppenlogik |
| `Dockerfile` | Startet `python app.py` direkt |
| `requirements.txt` | Flask, Flask-SocketIO, SQLAlchemy, Eventlet |
| `tournament.db` | alte SQLite-Datenbank des Flask-Stacks |

## Was hier noch wichtig ist

- Das alte Backend lauscht in `app.py` auf Port `5001`.
- Es bringt eigene Auto-Migrationen fuer SQLite-Tabellen mit.
- Einige Legacy-Pfade im Frontend kennen diesen Stack noch indirekt, vor allem `PlayInView.vue`.

## Was hier nicht mehr gilt

- Keine JWT-Rollen
- Kein Django-Admin
- Kein Channels-WebSocket
- Keine Postgres-/Prod-Pipeline

Wenn du am aktiven System arbeitest, ist fast immer `django_backend/` die richtige Stelle.
