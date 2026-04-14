# Feature-Briefing: Interaktive Tisch-Ansicht & Becher-Tracking

## 1. Zielsetzung
Erweiterung des Turniermanagers um interaktive Beer-Pong-Tische. Wir wechseln von einem simplen Cup-Counter zu einem exakten Tracking einzelner Becher (10er-Grid-System). 

## 2. Backend Anpassungen (Django)
Bitte erweitere die bestehenden Models und Services:
* **Match Model Update:** * Füge JSONFields für den Tisch-Zustand hinzu: `cups_state_team1` und `cups_state_team2` (bildet das 1-10 Raster ab).
    * Füge Booleans hinzu: `team1_rerack_used`, `team2_rerack_used` (Standard: False).
* **MatchEvent Model (Neu):**
    * Für die "Undo"-Funktion brauchen wir ein Event-Log pro Match. (Felder: `match` (FK), `action_type` (z.B. 'cup_hit', 'rerack'), `player` (FK, nullable), `cup_index`, `timestamp`).
* **WebSockets:** Der `TournamentConsumer` muss die neuen Events (`cup_hit`, `undo_action`, `rerack`) verarbeiten, die Datenbank updaten und den neuen State an alle Clients broadcasten.

## 3. Frontend: Admin-Ansicht (Turnierleitung)
* **Layout:** Vertikale Liste der aktiven Tische (Top-Down 2D-Ansicht).
* **Interaktion Becher-Hit:** Klick auf einen aktiven Becher öffnet eine Schnellauswahl (Modal/Popover), um den treffenden Spieler auszuwählen.
* **Undo-Button:** Sendet ein `undo_action` Event an den WebSocket, woraufhin der Server das letzte `MatchEvent` rückgängig macht.
* **Rearrange/Re-Rack Button:** Erlaubt es, die verbleibenden Becher im Grid neu anzuordnen (Button wird deaktiviert, wenn das Limit von 1 pro Team erreicht ist).

## 4. Frontend: Live-Ansicht (Beamer)
* **Layout:** Horizontale Anordnung der Tische nebeneinander.
* **Design:** Isometrische/3D-ähnliche Darstellung der Tische mittels CSS/SVGs. Aktuelle Spielernamen und Teamnamen müssen prominent sichtbar sein.
* **Animationen:** Das Verschwinden eines getroffenen Bechers (durch WebSocket-Event) soll sanft animiert werden (z.B. Fade-Out/Scale-Down).

## 5. Nächste Schritte für dich (Claude)
Bitte beginne mit dem Backend-Teil:
1. Zeige mir die notwendigen Änderungen für die `models.py` (inkl. MatchEvent).
2. Skizziere, wie das initiale JSON-Grid für z.B. 6 Becher aufgebaut ist.
