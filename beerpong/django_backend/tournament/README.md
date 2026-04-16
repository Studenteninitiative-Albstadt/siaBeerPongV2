# Tournament Application

Domänenlogik für die Verwaltung von Turnieren, Teams und Spieler-Statistiken.

## Dateisystem & Zuständigkeiten

| Datei | Zweck |
|---|---|
| `models.py` | Datenstruktur (Tournament, Team, Match, CupHit). |
| `views.py` | API-Endpoints (CRUD & Custom Actions wie `save-ko-preview`). |
| `services.py` | Berechnungs-Engine (Standings, Gruppen-Generation). |
| `consumers.py` | Echtzeit-Synchronisation via WebSockets. |

## Daten-Integrität

- **Snapshot-Architektur**: Das Backend liefert bei jedem Connect/Update einen vollständigen oder teilweisen Snapshot des Turnier-Zustands (`load-all-data`).
- **KO-Vorschau Persistenz**: Die berechneten KO-Paarungen werden im `Tiebreak`-Modell zwischengespeichert, um Konsistenz zwischen Admin-Vorschau und Live-Anzeige zu garantieren.
- **Single Source of Truth**: Alle kritischen Berechnungen (Punkte, Standings) finden im Backend statt, um Inkonsistenzen im Frontend zu vermeiden.

---
*Status: 15. April 2026 - Data Consistency Verified*
