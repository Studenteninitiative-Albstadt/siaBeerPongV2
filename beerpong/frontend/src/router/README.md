# Router

Der Router definiert die Hash-Routen und die Frontend-seitigen Rollenchecks.

## Technische Grundlage

- `createWebHashHistory()`
- Redirect auf Basis des `auth`-Stores
- `document.title = 'SIA Bier Pong'` nach jedem Routenwechsel

## Route-Mapping

| Pfad | Meta | Zugriff |
| --- | --- | --- |
| `/login` | `public` | frei |
| `/admin` | `requiresRoot` | nur `is_root` oder Django-Staff |
| `/referee` | `requiresOrga` | `is_orga` |
| `/live` | `requiresAuth` | jeder eingeloggte User |
| `/mobile` | `public` | frei, Token-Pruefung passiert backendseitig |

## Root-Redirect

Beim Aufruf von `/` wird wie folgt umgeleitet:

- Root -> `/admin`
- normaler Orga/Referee -> `/referee`
- Liveview-User -> `/live`
- sonst -> `/login`

## Wichtig

Die eigentliche Sicherheit liegt im Backend. Der Router verhindert nur falsche UI-Navigation im Client.
