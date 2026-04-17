# Views

Diese Komponenten sind die eigentlichen Routen-Ziele des Frontends.

## Dateien

| Datei | Route | Zweck |
| --- | --- | --- |
| `LoginView.vue` | `/#/login` | JWT-Login |
| `AdminView.vue` | `/#/admin` | Root-Admin fuer Wizard, Gruppen, Play-In, KO und Referee-Zuweisung |
| `RefereeView.vue` | `/#/referee` | Schiedsrichter-Bedienoberflaeche fuer zugewiesene Matches |
| `LiveView.vue` | `/#/live` | Beamer-Ansicht inkl. Landing, Gruppenphase, KO und QR-Code |
| `MobileView.vue` | `/#/mobile` | oeffentliche Turnieransicht per Token |

## Wichtige Klarstellung

`LiveViewKO.vue` gehoert fachlich zur Live-Ansicht, liegt aber nicht in diesem Ordner, sondern unter `components/`.

## Zustandsquellen pro View

- `AdminView.vue`: arbeitet eng mit `tournament`-Store und den grossen Phasenkomponenten
- `RefereeView.vue`: pollt/abonniert die eigene Assignment-Info und sendet Match-Events zurueck
- `LiveView.vue`: nutzt Store + WebSocket, zeigt fuer KO `LiveViewKO.vue`
- `MobileView.vue`: nutzt Public-REST + Mobile-WebSocket, hat zusaetzlich Polling-Fallback

## Sichtbarer Rollen-Split

- Root-Admin sieht Turnierverwaltung und Referee-Zuweisung
- normaler Orga-User landet in der Referee-Ansicht
- Live-User landet in der Beamer-Ansicht
- Mobile-Gaeste sehen nur lesenden Turnierzustand
