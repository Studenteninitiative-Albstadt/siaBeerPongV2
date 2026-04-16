# Frontend Views (Seiten)

Kombination von Komponenten zu spezialisierten Benutzer-Schnittstellen.

## Übersicht der Haupt-Views

| View | Rolle | Fokus |
|---|---|---|
| `AdminView.vue` | Orga | Phasen-Management, Live-Scoring. |
| `LiveView.vue` | Beamer | Gruppen-Live-Status, 3/4 Split-Layout, QR-Code. |
| `LiveViewKO.vue` | Beamer | KO-Live-Status (Full-Bracket + Live Tables). |
| `MobileView.vue` | Spieler | Persönlicher Turnier-Status (Token-basiert). |

## Layout-Innovationen

### 3/4 Split-Architektur
Die Live-Ansichten (`LiveView` & `LiveViewKO`) nutzen nun ein dynamisches Höhen-Management:
- **Oben (ca. 70%)**: Fokus auf Live-Spiele (3D Tische).
- **Unten (ca. 30%)**: Kontext-Informationen (Gruppenstände, Brackets, QR-Code).

### Phasen-Synchronisation
Die `LiveView` schaltet automatisch zwischen Gruppen-Layout und KO-Layout (`LiveViewKO.vue`) um, sobald der Turnierstatus im Backend geändert wird.

### QR-Code Optimierung
Der QR-Code Bereich wurde für Beamer-Entfernungen optimiert:
- **Quadratisches Fix-Format**: Verhindert Verzerrungen.
- **Ultra-Compact URL**: Minimierte Schriftgrößen und radikaler Umbruch für lange Tokens.

---
*Status: 15. April 2026 - Split-Layout & KO-Views Documented*
