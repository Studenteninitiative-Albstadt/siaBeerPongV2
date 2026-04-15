# SIA BeerPong - Django Backend

Das Backend dient als zentrale Datenquelle und Zustandsmaschine für alle Turniere. Es nutzt Django REST Framework (DRF) für die API und Django Channels für Echtzeit-Kommunikation.

## Architektur & Komponenten

```text
       [ Request ]
           |
   +-------v-------+
   |   ASGI / WSGI | <---( Daphne Server )
   +-------+-------+
           |
   +-------v-------+      +-------------------+
   |   Middleware  | <----| SimpleJWT (Auth)  |
   +-------+-------+      +-------------------+
           |
   +-------v-------+      +-------------------+
   |   DRF Views   | <----| Serializers       |
   +-------+-------+      +---------+---------+
           |                        |
   +-------v-------+      +---------v---------+
   |   Services    | <----| Models (SQLite)   |
   +---------------+      +-------------------+
```

- **Daphne**: ASGI-Server, der sowohl HTTP als auch WebSockets bedient.
- **Services (`tournament/services.py`)**: Enthält die Kernlogik für Gruppengenerierung, Standings-Berechnungen und Snapshots.
- **Models**: Definieren die Turnierstruktur (Turniere, Teams, Gruppen-Matches, KO-Matches).

## Datenmodell-Übersicht

```text
[ Tournament ]
      |
      +---< [ Table ] (Tisch-Zuordnung)
      |
      +---< [ Team ] ----< [ Player ] (Spieler-Statistiken)
      |
      +---< [ Match ] (Phasen: group, playin, ko)
      |        |
      |        +---< [ CupHit ] (Einzelne Treffer für Top-Player)
      |
      +---< [ Tiebreak ] (Metadaten & KO-Vorschau)
```

## Echtzeit-Updates (WebSockets)

Das Backend sendet Statusänderungen automatisch an alle verbundenen Clients (Admin, Live, Mobile).

```text
Mutation (API) --> Service Logik --> Database Save --> WebSocket Broadcast
```

- **Consumer**: `tournament/consumers.py` verwaltet Verbindungen.
- **Routing**: `tournament/routing.py` definiert WS-Endpunkte.

---
*Status: 15. April 2026*
