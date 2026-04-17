# Stores

Pinia bildet den globalen Client-State fuer Auth und Turnierdaten.

## `auth.js`

Aufgaben:

- liest `access_token` und `refresh_token` aus `localStorage`
- decodiert Rollenflags direkt aus dem JWT
- exposes:
- `isAuthenticated`
- `isOrga`
- `isLiveview`
- `isRoot`
- `username`
- `login()` und `logout()`

## `tournament.js`

Aufgaben:

- haelt `tournament`, `teams`, `teamPlayers`, `topPlayers`, `groupPhase`, `groupStandings`, `playin`, `koPreview`, `koPhase`
- laedt Vollsnapshots ueber `load()`
- merged Teilupdates ueber `_apply()`
- verbindet WebSockets fuer normale User und Mobile-User

## Wichtige Merge-Details

- Gruppenspiele werden per `match.id` in den Snapshot integriert.
- einzelne KO-Match-Updates werden zuerst per `id` gemappt
- falls noetig per `ko_round`, `ko_bracket_type` und `ko_match_index`
- dadurch koennen materialisierte KO-Matches spaeter denselben UI-Slot uebernehmen

Der Store ist die zentrale Uebersetzungsschicht zwischen REST/WS und Vue-Komponenten.
