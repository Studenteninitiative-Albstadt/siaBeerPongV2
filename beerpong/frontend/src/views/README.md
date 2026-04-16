# Frontend Views (Produktions-Schnittstellen)

Zusammenführung spezialisierter UI-Komponenten für maximale User Experience während des Turniers.

## Ansichten-Portfolio

| View | Zweck | Zielgruppe |
|---|---|---|
| `AdminView.vue` | Vollständige Steuerung. | Turnierleitung |
| `LiveView.vue` | Gruppenphasen-Übersicht. | Zuschauer (Beamer) |
| `LiveViewKO.vue` | Finalrunden-Visualisierung. | Zuschauer (Beamer) |
| `MobileView.vue` | Persönlicher Turnier-Status. | Teilnehmer (QR-Zugriff) |

## Produktions-Design-Standards

### Dynamisches 3/4-Split-Layout
Die Live-Ansichten nutzen eine intelligente Höhenaufteilung:
- **Oben (Live-Action)**: Proportionale 3D-Tisch-Visualisierung (Auto-Scaling).
- **Unten (Kontext)**: Statistische Daten (Standings/Brackets) und QR-Code-Gateway.

### Adaptive Visualisierung (3D)
Die in `LiveView` & `LiveViewKO` verwendeten 3D-Tische sind über die Master-Variable `--tw` (Table Width) proportional skalierbar. Dies garantiert:
- **Null-Overflow**: Tische ragen niemals in untere UI-Elemente.
- **Präzision**: Becher-Positionen bleiben in allen Auflösungen identisch.

### Mobile-Infrastruktur
Jedes Turnier generiert einen eindeutigen `mobileAccessToken`, der in der `LiveView` quadratisch und verzerrungsfrei (aspect-ratio fix) als QR-Code dargestellt wird.

---
*Version: 2.0.0 - Design Finalized*
