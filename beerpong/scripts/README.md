# Scripts

Dieser Ordner enthaelt kleine Deploy-Helfer ausserhalb von Django und Frontend.

## Dateien

| Datei | Zweck |
| --- | --- |
| `verify_required_env.sh` | prueft Pflichtvariablen in `.env` und blockiert den Start bei Platzhalter-Secrets |

## `verify_required_env.sh`

Die Pruefung erzwingt unter anderem:

- gesetzte Werte fuer Domain, App-Port, DB, Admin-Login und Live-Login
- kein `PLEASECHANGEME` in:
- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_SUPERUSER_PASSWORD`
- `LIVEVIEW_PASSWORD`

Der Prod-Stack startet `env-check` vor dem eigentlichen Backend, damit fehlende oder Platzhalter-Secrets frueh abbrechen.
