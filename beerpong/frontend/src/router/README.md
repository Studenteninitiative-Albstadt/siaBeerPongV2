# Frontend Router & Access Control

Der Router verwaltet die Navigation innerhalb der SPA und implementiert die rollenbasierte Zugriffskontrolle (RBAC).

## Routing-Strategie

Das System nutzt `createWebHashHistory`, um Kompatibilität mit einfachen Webservern (ohne URL-Rewriting) sicherzustellen.

```text
[ URL Hash ]
     |
     v
[ router.beforeEach ] -----------------+
     |                                 |
     v                                 v
[ Auth Store Check ] <----( JWT Token / LocalStorage )
     |
     +---( valid )------> [ Target View ]
     |
     +---( invalid )----> [ /login ]
```

## Zugriffsregeln (Permissions)

| Pfad | Erforderliche Rolle | Beschreibung |
|---|---|---|
| `/admin` | `requiresOrga` | Nur für Benutzer mit `is_orga` Flag im JWT. |
| `/live` | `requiresAuth` | Für Orga- und LiveView-User (Beamer). |
| `/mobile` | `public` | Zugriff für Spieler (Token-basiert via URL). |
| `/login` | `public` | Einstiegspunkt für Authentifizierung. |

---
*Status: 15. April 2026*
