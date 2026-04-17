# Tournament Migrations

Diese Migrationen beschreiben die bisherige Schemaentwicklung der aktiven Django-App.

## Historie

| Migration | Inhalt |
| --- | --- |
| `0001_initial.py` | Grundschema fuer Turnier, Teams, Matches, Tiebreaks, Tabellen usw. |
| `0002_cup_hit.py` | `CupHit` fuer Top-Spieler / Treffer-Tracking |
| `0003_match_cup_state.py` | JSON-Cup-States an Matches |
| `0004_*history*` | Undo-/Historienfelder und Rerack-nahe Daten |
| `0005_*history*` | Nachschaerfung der History-Felder |
| `0006_match_is_overtime.py` | Overtime-Flag an Matches |
| `0007_tournament_table_count.py` | `table_count` am Turnier |
| `0008_user_is_root_matchassignment_adminaction.py` | Root-Rolle, Referee-Zuweisung, Admin-Log |

## Hinweis

Das aktive Schema lebt hier. Das alte Flask-Schema in `backend/tournament.db` hat mit diesen Migrationen nichts zu tun.
