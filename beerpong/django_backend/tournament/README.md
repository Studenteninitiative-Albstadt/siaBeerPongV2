# Tournament App

Hier steckt die komplette Fachlogik des Turniers: Teams, Spieler, Gruppenphase, Play-In, KO-Phase, Referee-Zuweisung, CupHits, Snapshots und WebSocket-Broadcasts.

## Dateien

| Datei | Zweck |
| --- | --- |
| `models.py` | Datenmodell |
| `serializers.py` | JWT-Payload und Turnier-Serializer |
| `permissions.py` | `IsOrga`, `IsOrgaOrLiveview`, `IsRoot` |
| `views.py` | REST-Endpunkte und Mutationslogik |
| `services.py` | Strukturplanung, Standings, KO-Steuerung, Snapshot-Builder |
| `auth.py` | Token- und Mobile-Token-Helfer |
| `consumers.py` | WebSocket-Consumer fuer Turnier- und Personal-Updates |
| `routing.py` | WS-Route `/ws/tournament/<id>/` |
| `admin.py` | Django-Admin-Registrierung |
| `migrations/` | Schemahistorie |

## Datenmodell

| Modell | Zweck |
| --- | --- |
| `User` | Rollenflags `is_orga`, `is_liveview`, `is_root` |
| `Tournament` | Stammobjekt inkl. `mobile_access_token`, `table_count`, `status` |
| `Player` | globaler Spielername + `total_cups_hit` |
| `Team` | Turnierteam mit zwei optionalen Spielern |
| `Table` | physische Tische |
| `Match` | Gruppen-, Play-In- und KO-Matches inkl. Cup-State, Undo-Historie, Rerack, Overtime, Tisch, KO-Metadaten |
| `Tiebreak` | Gruppentiebreaks, `ko_preview`, `ko_control` und sonstige Metadaten |
| `CupHit` | einzelne Treffer fuer Top-Spieler |
| `MatchAssignment` | Referee -> Match |
| `AdminAction` | serverseitiges Audit-Log fuer Admin-/Referee-Aktionen |

## Rollen und Berechtigungen

- `mobile_state`: `AllowAny`, aber nur mit gueltigem Turnier-Token
- Read-Actions wie `list`, `retrieve`, `load-all-data`, `group-standings`, `load-ko-bracket`, `load-playin`, `load-teams`: `IsOrgaOrLiveview`
- Standard fuer Mutationen: `IsOrga`
- `assign-referee`: explizit `IsRoot`

## REST-Endpunkte

### Turnier allgemein

- `GET /tournaments`
- `POST /tournaments`
- `GET /tournaments/<id>`
- `DELETE /tournaments/<id>`
- `POST /tournaments/<id>/update`
- `POST /tournaments/<id>/compute-plan`
- `GET /tournaments/<id>/load-all-data`

### Teams und Gruppenphase

- `POST /tournaments/<id>/save-teams`
- `GET /tournaments/<id>/load-teams`
- `POST /tournaments/<id>/save-team-players`
- `POST /tournaments/<id>/generate-groups`
- `POST /tournaments/<id>/save-group-phase`
- `POST /tournaments/<id>/group-match`
- `GET /tournaments/<id>/group-standings`

### Play-In und KO

- `POST /tournaments/<id>/save-playin`
- `GET /tournaments/<id>/load-playin`
- `POST /tournaments/<id>/save-ko-preview`
- `POST /tournaments/<id>/save-ko-bracket`
- `GET /tournaments/<id>/load-ko-bracket`
- `POST /tournaments/<id>/start-ko-next-round`
- `POST /tournaments/<id>/ko-match`

### Referee und Mobile

- `GET /tournaments/<id>/referees`
- `GET /tournaments/<id>/my-assignment`
- `POST /tournaments/<id>/assign-referee`
- `GET /tournaments/<id>/mobile-state?token=<uuid>`

### Sonstiges

- `GET /health`

## Snapshot-Logik

`services.get_full_state()` ist der zentrale Serializer fuer das Frontend. Er liefert unter anderem:

- `tournament`
- `teams`
- `team_players`
- `top_players`
- `group_phase`
- `group_standings`
- `playin`
- `ko_preview`
- `ko_phase`

Das Frontend arbeitet damit sowohl beim initialen Laden als auch bei vielen WebSocket-Updates.

## WebSocket-Verhalten

- Kanal pro Turnier: `tournament_<id>`
- personalisierte Kanaele pro User: `user_<id>`
- Auth-Modi:
- `?token=<jwt>` fuer Admin, Live und Referee
- `?mobile_token=<uuid>` fuer Mobile-Gaeste

Broadcasts kommen vor allem aus `views.py` nach Match-Updates, Phasenwechseln, Referee-Zuweisungen und Vollsnapshots.

## Wichtige Ist-Zustandsdetails

- KO-Runden werden serverseitig ueber `ko_control` freigegeben, inklusive der Reihenfolge `Spiel um Platz 3` vor `Finale`.
- `top_players` wird aus `CupHit` aggregiert, nicht aus reinem Anzeige-Score.
- `save-ko-bracket` arbeitet heute als Upsert ueber bestehende KO-Matches statt sie pauschal neu anzulegen.
- `save-playin` loescht Play-In-Matches weiterhin hart und speichert nur einen reduzierten Zustand; dieser Pfad ist funktional, aber deutlich einfacher als Gruppen- und KO-Phase.
