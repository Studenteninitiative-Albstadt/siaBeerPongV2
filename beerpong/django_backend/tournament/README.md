# Tournament Application

Diese Applikation implementiert die gesamte Turnier-Domänenlogik, von der API bis zur WebSocket-Synchronisation.

## Dateisystem & Zuständigkeiten

| Datei | Zweck |
|---|---|
| `models.py` | Datenstruktur für Turniere, Teams, Gruppen & Matches. |
| `views.py` | DRF-ViewSet mit über 15 spezialisierten Endpunkten (Snapshots, Updates). |
| `services.py` | Das "Gehirn" des Backends: Gruppenberechnungen & Seeding. |
| `consumers.py` | WebSocket-Handler für Echtzeit-Kommunikation. |
| `serializers.py` | Transformation zwischen DB-Objekten und JSON. |
| `auth.py` | Implementiert JWT-Authentifizierung & Rollenprüfung. |

## Der "Snapshot"-Mechanismus

Statt viele kleine API-Calls zu machen, nutzt das System einen Snapshot-Ansatz.

```text
[ Client Connect ]
      |
      v
[ GET /load-all-data ] -----------------+
      |                                 |
      v                                 v
[ API Response ] <---( Snapshot )--- [ Services.build_snapshot ]
      |
      +---( Store in Pinia )
```

## Berechtigungs-Workflow

Das System unterscheidet zwischen Orga (Admin), LiveView (Beamer) und Mobile (Public).

```text
Rolle       | Token-Typ       | Berechtigung
------------|-----------------|---------------------------------
Orga        | JWT (is_orga)   | Vollzugriff (CRUD + Mutation)
LiveView    | JWT (is_live)   | Read-Only + Snapshot
Mobile      | UUID (Token)    | Read-Only Mobile-State
```

---
*Status: 15. April 2026*
