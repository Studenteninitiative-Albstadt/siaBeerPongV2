#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from sqlalchemy import text

# -------------------------------------------------
# Flask / DB Setup
# -------------------------------------------------

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tournament.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "change-me"

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---- CORS (robust, auch bei Fehlern / Preflight) ----
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}

@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin")
    if origin and (origin in ALLOWED_ORIGINS):
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
    else:
        resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return resp

@app.route("/<path:_any>", methods=["OPTIONS"])
@app.route("/", methods=["OPTIONS"])
def cors_preflight(_any=None):
    return make_response(("", 204))

# -------------------------------------------------
# Models (UTC-aware defaults)
# -------------------------------------------------

class Tournament(db.Model):
    __tablename__ = "tournaments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Neues Turnier")
    mode = db.Column(db.String(20), default="groups")
    participant_count = db.Column(db.Integer, default=8)
    cups_per_game = db.Column(db.Integer, default=6)
    table_count = db.Column(db.Integer, default=2)
    finale_with_10_cups = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    current_phase = db.Column(db.String(20), default="group")  # group, playin, ko, finished


class TournamentData(db.Model):
    __tablename__ = "tournament_data"
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    data_type = db.Column(db.String(20))           # 'groups', 'playin', 'group_standings', 'teams'
    group_name = db.Column(db.String(50), nullable=True)
    payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tournament = db.relationship('Tournament', backref='data_entries')


class KOBracket(db.Model):
    __tablename__ = "ko_brackets"
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    bracket_type = db.Column(db.String(20))   # 'main', 'consolation'
    round_name = db.Column(db.String(50))     # 'Achtelfinale', 'Viertelfinale', ...
    match_data = db.Column(db.Text)           # JSON
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tournament = db.relationship('Tournament', backref='ko_entries')

class MatchEvent(db.Model):
    __tablename__ = "match_events"
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
    match_id = db.Column(db.String(50), nullable=False) # z.B. 'Gruppe A-1'
    
    action_type = db.Column(db.String(50), nullable=False) # 'cup_hit', 'rerack', 'undo'
    team_key = db.Column(db.String(10), nullable=False)    # 'team1' oder 'team2'
    team_name = db.Column(db.String(120), nullable=True)   # Klartext-Team (da Teams nicht in DB)
    player_name = db.Column(db.String(100), nullable=True) # Wer hat geworfen?
    cup_index = db.Column(db.Integer, nullable=True)       # Welcher Becher (0-9)?
    cup_layout = db.Column(db.Integer, nullable=True)      # 6 oder 10 (Layout zum Zeitpunkt des Wurfs)
    phase_label = db.Column(db.String(20), nullable=True)  # 'group', 'playin', 'ko'
    previous_state = db.Column(db.Text, nullable=True)     # JSON String für Undo bei Rerack
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tournament = db.relationship('Tournament', backref='match_events')

class CupPosition(db.Model):
    __tablename__ = "cup_positions"
    id = db.Column(db.Integer, primary_key=True)
    layout_size = db.Column(db.Integer, nullable=False)   # 6 oder 10
    cup_index = db.Column(db.Integer, nullable=False)     # 0..5 oder 0..9
    row = db.Column(db.Integer, nullable=True)
    col = db.Column(db.Integer, nullable=True)
    x = db.Column(db.Float, nullable=True)
    y = db.Column(db.Float, nullable=True)

# -------------------------------------------------
# DB init + leichte Auto-Migration (SQLite)
# -------------------------------------------------

def _table_columns(conn, table: str) -> List[str]:
    cur = conn.execute(text(f'PRAGMA table_info("{table}")'))
    return [r[1] for r in cur.fetchall()]

def _add_column(conn, table: str, name: str, coltype: str, default_sql: str | None = None):
    sql = f'ALTER TABLE "{table}" ADD COLUMN "{name}" {coltype}'
    if default_sql is not None:
        sql += f' DEFAULT {default_sql}'
    conn.execute(text(sql))

def ensure_sqlite_schema():
    """Fügt fehlende Spalten in bestehenden Tabellen hinzu (zerstörungsfrei)."""
    engine = db.engine
    with engine.begin() as conn:
        db.create_all()

        # ---- tournaments
        try:
            cols = _table_columns(conn, "tournaments")
            need = {
                "name": ("TEXT", "'Neues Turnier'"),
                "mode": ("TEXT", "'groups'"),
                "participant_count": ("INTEGER", "8"),
                "cups_per_game": ("INTEGER", "6"),
                "table_count": ("INTEGER", "2"),
                "finale_with_10_cups": ("INTEGER", "0"),
                # UTC via SQLite
                "created_at": ("TEXT", "CURRENT_TIMESTAMP"),
                "current_phase": ("TEXT", "'group'"),
            }
            for col, (ctype, dflt) in need.items():
                if col not in cols:
                    _add_column(conn, "tournaments", col, ctype, dflt)
        except Exception as e:
            print("Schema check tournaments failed:", repr(e))

        # ---- tournament_data
        try:
            cols = _table_columns(conn, "tournament_data")
            need_td = {
                "tournament_id": ("INTEGER", None),
                "data_type": ("TEXT", None),
                "group_name": ("TEXT", "NULL"),
                "payload": ("TEXT", "NULL"),
                "created_at": ("TEXT", "CURRENT_TIMESTAMP"),
            }
            for col, (ctype, dflt) in need_td.items():
                if col not in cols:
                    _add_column(conn, "tournament_data", col, ctype, dflt)
        except Exception as e:
            print("Schema check tournament_data failed:", repr(e))

        # ---- ko_brackets
        try:
            cols = _table_columns(conn, "ko_brackets")
            need_ko = {
                "tournament_id": ("INTEGER", None),
                "bracket_type": ("TEXT", "'main'"),
                "round_name": ("TEXT", "'Round'"),
                "match_data": ("TEXT", "'{}'"),
                "created_at": ("TEXT", "CURRENT_TIMESTAMP"),
            }
            for col, (ctype, dflt) in need_ko.items():
                if col not in cols:
                    _add_column(conn, "ko_brackets", col, ctype, dflt)
        except Exception as e:
            print("Schema check ko_brackets failed:", repr(e))

        # ---- match_events
        try:
            cols = _table_columns(conn, "match_events")
            need_events = {
                "tournament_id": ("INTEGER", None),
                "match_id": ("TEXT", "NULL"),
                "action_type": ("TEXT", "NULL"),
                "team_key": ("TEXT", "NULL"),
                "team_name": ("TEXT", "NULL"),
                "player_name": ("TEXT", "NULL"),
                "cup_index": ("INTEGER", "NULL"),
                "cup_layout": ("INTEGER", "NULL"),
                "phase_label": ("TEXT", "NULL"),
                "previous_state": ("TEXT", "NULL"),
                "timestamp": ("TEXT", "CURRENT_TIMESTAMP"),
            }
            for col, (ctype, dflt) in need_events.items():
                if col not in cols:
                    _add_column(conn, "match_events", col, ctype, dflt)
        except Exception as e:
            print("Schema check match_events failed:", repr(e))

        # ---- cup_positions
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            if "cup_positions" not in inspector.get_table_names():
                CupPosition.__table__.create(bind=engine, checkfirst=True)
        except Exception as e:
            print("Schema check cup_positions failed:", repr(e))

with app.app_context():
    ensure_sqlite_schema()

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def json_dumps(obj: Any) -> str:
    def _default(o):
        if isinstance(o, datetime):
            return o.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return str(o)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=_default)

def json_loads(s: str | None) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None

def letters() -> List[str]:
    return list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

POW2 = [4, 8, 16, 32, 64, 128]

def choose_ko_size(qualified: int) -> int:
    for k in POW2:
        if k >= qualified:
            return k
    return qualified

def balanced_sizes(n: int, groups: int) -> List[int]:
    base = n // groups
    rem = n % groups
    return [base + (1 if i < rem else 0) for i in range(groups)]

def group_count_by_band(n: int) -> int:
    if n <= 4:  return 1
    if n <= 8:  return 2
    if n <= 11: return 3
    if n <= 16: return 4
    return max(4, round(n/4.5))

def compute_structure(n: int) -> Dict[str, Any]:
    if n < 2 or n > 128:
        return {"error": "Teilnehmerzahl muss zwischen 2 und 128 liegen."}

    g = group_count_by_band(n)
    if n == 12:
        sizes = [3, 3, 3, 3]
        g = 4
    else:
        sizes = balanced_sizes(n, g)
        if n >= 17:
            while max(sizes) > 5:
                g += 1
                sizes = balanced_sizes(n, g)

    group_names = [f"Gruppe {letters()[i]}" for i in range(g)]
    groups = [{"name": name, "size": size} for name, size in zip(group_names, sizes)]

    qualified = sum(2 if s >= 2 else 0 for s in sizes)
    ko_size = choose_ko_size(qualified)
    slots_needed = max(0, ko_size - qualified)

    candidates = []
    for name, size in zip(group_names, sizes):
        if size >= 3:
            candidates.append({"group": name, "position": 3, "label": f"3. {name}"})
        if size >= 4:
            candidates.append({"group": name, "position": 4, "label": f"4. {name}"})

    return {
        "groups": groups,
        "ko_size": ko_size,
        "qualified_per_group": 2,
        "playin_needed": slots_needed > 0,
        "playin_slots_needed": slots_needed,
        "playin_candidates": candidates
    }

def round_robin(team_names: List[str]) -> List[Dict[str, Any]]:
    matches = []
    order = 0
    
    teams = list(team_names)
    if len(teams) < 2: return []
    if len(teams) % 2 != 0: teams.append(None)
    
    total_rounds = len(teams) - 1
    matches_per_round = len(teams) // 2
    
    for r in range(total_rounds):
        for m in range(matches_per_round):
            t1 = teams[m]
            t2 = teams[-1 - m]
            if t1 is not None and t2 is not None:
                matches.append({
                    "team1": t1,
                    "team2": t2,
                    "winner": None,
                    "cups_team1": None,
                    "cups_team2": None,
                    "cups_state_team1": None,
                    "cups_state_team2": None,
                    "team1_rerack_used": False,
                    "team2_rerack_used": False,
                    "order_index": order
                })
                order += 1
        teams.insert(1, teams.pop())
        
    return matches

# -------------------------------------------------
# API – Turnierverwaltung
# -------------------------------------------------

@app.post("/tournaments/create")
def api_create_tournament():
    data = request.json or {}

    def pick(*keys, default=None):
        for k in keys:
            if k in data and data[k] is not None:
                return data[k]
        return default

    def as_int(v, default):
        try: return int(v)
        except Exception: return default

    def as_bool(v, default):
        try:
            if isinstance(v, bool): return v
            if isinstance(v, (int, float)): return bool(v)
            if isinstance(v, str): return v.strip().lower() in {"1","true","yes","y","on"}
            return default
        except Exception:
            return default

    try:
        name = str(pick("name", default="Neues Turnier"))
        mode = str(pick("mode", default="groups"))
        participant = max(2, min(128, as_int(pick("participantCount","participant_count", default=8), 8)))
        cups = max(1, min(20, as_int(pick("cupsPerGame","cups_per_game", default=6), 6)))
        tables = max(1, min(20, as_int(pick("tableCount","table_count", default=2), 2)))
        finale10 = as_bool(pick("finaleWith10Cups","finale_with_10_cups", default=False), False)

        t = Tournament(
            name=name, mode=mode,
            participant_count=participant,
            cups_per_game=cups,
            table_count=tables,
            finale_with_10_cups=finale10,
            current_phase="group",
        )
        db.session.add(t)
        db.session.commit()
        return jsonify({
            "id": t.id,
            "name": t.name,
            "participantCount": t.participant_count,
            "cupsPerGame": t.cups_per_game,
            "tableCount": t.table_count,
            "finaleWith10Cups": t.finale_with_10_cups,
            "mode": t.mode,
            "currentPhase": t.current_phase,
            "createdAt": t.created_at.isoformat() if t.created_at else None
        })
    except Exception as e:
        print("ERROR /tournaments/create:", repr(e))
        return jsonify({"error": "invalid payload", "detail": str(e)}), 400

@app.route("/tournaments", methods=["GET", "OPTIONS"])
def api_list_tournaments():
    if request.method == "OPTIONS":
        return make_response(("", 204))
    try:
        rows = Tournament.query.order_by(Tournament.created_at.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "name": r.name,
                "participant_count": r.participant_count,
                "cups_per_game": r.cups_per_game,
                "table_count": r.table_count,
                "finale_with_10_cups": r.finale_with_10_cups,
                "mode": r.mode,
                "current_phase": r.current_phase,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                # camel mirrors
                "participantCount": r.participant_count,
                "tableCount": r.table_count,
                "cupsPerGame": r.cups_per_game,
                "finaleWith10Cups": r.finale_with_10_cups,
                "currentPhase": r.current_phase,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            })
        return jsonify(out)
    except Exception as e:
        print("ERROR /tournaments:", repr(e))
        return jsonify([]), 200

@app.get("/tournaments/<int:t_id>")
def api_get_tournament(t_id: int):
    t = Tournament.query.get_or_404(t_id)
    return jsonify({
        "id": t.id,
        "name": t.name,
        "participant_count": t.participant_count,
        "cups_per_game": t.cups_per_game,
        "table_count": t.table_count,
        "finale_with_10_cups": t.finale_with_10_cups,
        "mode": t.mode,
        "current_phase": t.current_phase,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "participantCount": t.participant_count,
        "cupsPerGame": t.cups_per_game,
        "finaleWith10Cups": t.finale_with_10_cups,
        "tableCount": t.table_count,
        "currentPhase": t.current_phase,
        "createdAt": t.created_at.isoformat() if t.created_at else None
    })

@app.post("/tournaments/<int:t_id>/update")
def api_update_tournament(t_id: int):
    t = Tournament.query.get_or_404(t_id)
    data = request.json or {}

    if "name" in data: t.name = str(data["name"])
    if "mode" in data: t.mode = str(data["mode"])
    if "participantCount" in data: t.participant_count = int(data["participantCount"])
    if "participant_count" in data: t.participant_count = int(data["participant_count"])
    if "cupsPerGame" in data: t.cups_per_game = int(data["cupsPerGame"])
    if "cups_per_game" in data: t.cups_per_game = int(data["cups_per_game"])
    if "tableCount" in data: t.table_count = int(data["tableCount"])
    if "table_count" in data: t.table_count = int(data["table_count"])
    if "finaleWith10Cups" in data: t.finale_with_10_cups = bool(data["finaleWith10Cups"])
    if "finale_with_10_cups" in data: t.finale_with_10_cups = bool(data["finale_with_10_cups"])
    if "currentPhase" in data: t.current_phase = str(data["currentPhase"])
    if "current_phase" in data: t.current_phase = str(data["current_phase"])

    db.session.commit()
    return jsonify({"ok": True})

@app.delete("/tournaments/<int:t_id>")
def api_delete_tournament(t_id: int):
    t = Tournament.query.get_or_404(t_id)
    TournamentData.query.filter_by(tournament_id=t_id).delete()
    KOBracket.query.filter_by(tournament_id=t_id).delete()
    db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True})

# -------------------------------------------------
# API – Struktur / Planung
# -------------------------------------------------

@app.post("/tournaments/<int:t_id>/compute-plan")
def api_compute_plan(t_id: int):
    t = Tournament.query.get_or_404(t_id)
    n = int((request.json or {}).get("participantCount") or t.participant_count)
    plan = compute_structure(n)
    return jsonify(plan)

# -------------------------------------------------
# API – Teams speichern/laden
# -------------------------------------------------

@app.post("/tournaments/<int:t_id>/save-teams")
def api_save_teams(t_id: int):
    Tournament.query.get_or_404(t_id)
    payload = request.json or {}
    teams = payload.get("teams") or []
    if not isinstance(teams, list):
        return jsonify({"error": "teams must be a list"}), 400

    TournamentData.query.filter_by(tournament_id=t_id, data_type="teams").delete()
    db.session.add(TournamentData(
        tournament_id=t_id, data_type="teams", group_name=None, payload=json_dumps({"teams": teams})
    ))
    db.session.commit()
    return jsonify({"ok": True, "count": len(teams)})

@app.get("/tournaments/<int:t_id>/load-teams")
def api_load_teams(t_id: int):
    Tournament.query.get_or_404(t_id)
    row = TournamentData.query.filter_by(tournament_id=t_id, data_type="teams")\
        .order_by(TournamentData.created_at.desc()).first()
    data = json_loads(row.payload) if row else {}
    return jsonify(data or {"teams": []})

# -------------------------------------------------
# API – Gruppenphase: Full Save + Single-Match Save
# -------------------------------------------------

@app.post("/tournaments/<int:t_id>/save-group-phase")
def api_save_group_phase(t_id: int):
    Tournament.query.get_or_404(t_id)
    payload = request.json or {}
    TournamentData.query.filter_by(tournament_id=t_id, data_type="groups").delete()
    db.session.add(TournamentData(
        tournament_id=t_id, data_type="groups", group_name=None, payload=json_dumps(payload)
    ))
    db.session.commit()
    return jsonify({"ok": True})

@app.post("/tournaments/<int:t_id>/group-match")
def api_save_group_match(t_id: int):
    """Single-Match Update für Gruppenphase."""
    t = Tournament.query.get_or_404(t_id)
    body = request.json or {}

    gname = (body.get("group_name") or "").strip()
    mid = body.get("id")
    team1 = body.get("team1")
    team2 = body.get("team2")
    cups1 = int(body.get("cups_team1") or 0)
    cups2 = int(body.get("cups_team2") or 0)
    winner = body.get("winner")
    order_index = int(body.get("order_index") or 0)

    cups_state_team1 = body.get("cups_state_team1")
    cups_state_team2 = body.get("cups_state_team2")
    team1_rerack_used = bool(body.get("team1_rerack_used") or False)
    team2_rerack_used = bool(body.get("team2_rerack_used") or False)
    
    event_data = body.get("event_data")

    # Aktuelles Gruppen-Payload laden
    row = TournamentData.query.filter_by(
        tournament_id=t_id, data_type="groups"
    ).order_by(TournamentData.created_at.desc()).first()
    payload = json_loads(row.payload) if row else {}

    if "group_phase" in payload and isinstance(payload["group_phase"], dict):
        # defensive: falls alter Wrapper geschrieben wurde
        payload = payload["group_phase"]

    matches_by_group: Dict[str, List[Dict[str, Any]]] = payload.get("matches") or {}
    if not isinstance(matches_by_group, dict):
        matches_by_group = {}

    lst = matches_by_group.get(gname) or []
    # Match per id oder order_index suchen
    idx = -1
    if mid:
        for i, m in enumerate(lst):
            if str(m.get("id")) == str(mid):
                idx = i
                break
    if idx < 0:
        for i, m in enumerate(lst):
            if int(m.get("order_index") or -1) == order_index \
               and m.get("team1") == team1 and m.get("team2") == team2:
                idx = i
                break

    # Vorhandene States behalten, wenn nichts geliefert
    if idx >= 0:
        existing = lst[idx]
        if cups_state_team1 is None:
            cups_state_team1 = existing.get("cups_state_team1")
        if cups_state_team2 is None:
            cups_state_team2 = existing.get("cups_state_team2")
        if (body.get("team1_rerack_used") is None) and existing.get("team1_rerack_used"):
            team1_rerack_used = existing.get("team1_rerack_used")
        if (body.get("team2_rerack_used") is None) and existing.get("team2_rerack_used"):
            team2_rerack_used = existing.get("team2_rerack_used")

    norm = {
        "id": mid or f"{gname}-{order_index+1}",
        "group_name": gname,
        "team1": team1, "team2": team2,
        "cups_team1": cups1, "cups_team2": cups2,
        "winner": winner,
        "cups_state_team1": cups_state_team1,
        "cups_state_team2": cups_state_team2,
        "team1_rerack_used": team1_rerack_used,
        "team2_rerack_used": team2_rerack_used,
        "order_index": order_index
    }

    if idx >= 0:
        lst[idx] = norm
    else:
        lst.append(norm)
    matches_by_group[gname] = lst
    payload["matches"] = matches_by_group

    # persistieren
    TournamentData.query.filter_by(tournament_id=t_id, data_type="groups").delete()
    db.session.add(TournamentData(
        tournament_id=t_id, data_type="groups", payload=json_dumps(payload)
    ))
    # Standings neu berechnen/ablegen (best effort)
    try:
        standings = compute_standings_from_groups_payload(payload)
        TournamentData.query.filter_by(tournament_id=t_id, data_type="group_standings").delete()
        db.session.add(TournamentData(
            tournament_id=t_id, data_type="group_standings", payload=json_dumps(standings)
        ))
    except Exception as e:
        print("group-match → standings failed:", repr(e))

    # Process Match Event log (DB speichern + Socket Broadcasten)
    if event_data:
        action = event_data.get("action_type")
        team_key = event_data.get("team_key")
        if action == "undo":
            last_event = MatchEvent.query.filter_by(
                tournament_id=t_id, match_id=norm["id"], team_key=team_key
            ).order_by(MatchEvent.timestamp.desc()).first()
            if last_event:
                db.session.delete(last_event)
            socketio.emit("undo_update", {"match_id": norm["id"], "team_key": team_key, "tournament_id": t_id}, broadcast=True)
        elif action:
            me = MatchEvent(
                tournament_id=t_id,
                match_id=norm["id"],
                action_type=action,
                team_key=team_key,
                team_name=event_data.get("team_name"),
                player_name=event_data.get("player_name"),
                cup_index=event_data.get("cup_index"),
                cup_layout=event_data.get("cup_layout"),
                phase_label=t.current_phase,
                previous_state=event_data.get("previous_state")
            )
            db.session.add(me)
            socketio.emit(f"{action}_update", {
                "tournament_id": t_id,
                "match_id": norm["id"],
                "team_key": team_key,
                "cup_index": event_data.get("cup_index"),
                "player_name": event_data.get("player_name"),
                "previous_state": event_data.get("previous_state"),
                "team_name": event_data.get("team_name"),
                "cup_layout": event_data.get("cup_layout"),
                "phase_label": t.current_phase
            }, broadcast=True)

    db.session.commit()
    return jsonify(norm)

# -------------------------------------------------
# API – Alle Daten laden (robust)
# -------------------------------------------------

@app.get("/tournaments/<int:t_id>/load-all-data")
def api_load_all(t_id: int):
    t = Tournament.query.get_or_404(t_id)

    # --- Teams (aus eigenem Slot)
    teams_row = TournamentData.query.filter_by(
        tournament_id=t_id, data_type="teams"
    ).order_by(TournamentData.created_at.desc()).first()
    teams_payload = json_loads(teams_row.payload) if teams_row else {}
    teams_from_slot = (teams_payload or {}).get("teams") or []

    # --- Groups payload (raw)
    group_row = TournamentData.query.filter_by(
        tournament_id=t_id, data_type="groups"
    ).order_by(TournamentData.created_at.desc()).first()
    group_phase = json_loads(group_row.payload) if group_row else {}

    # --- Standings ggf. vorhanden
    standings_row = TournamentData.query.filter_by(
        tournament_id=t_id, data_type="group_standings"
    ).order_by(TournamentData.created_at.desc()).first()
    group_standings = json_loads(standings_row.payload) if standings_row else {}

    # --- Teams ableiten (Fallback)
    def _iter_group_match_lists(payload):
        container = (payload or {}).get("matches") or (payload or {}).get("groups") or {}
        if isinstance(container, dict): return container.values()
        if isinstance(container, list): return container
        return []
    def derive_teams_from_group_phase(payload):
        names = set()
        for match_list in _iter_group_match_lists(payload):
            for m in (match_list or []):
                if m.get("team1"): names.add(m["team1"])
                if m.get("team2"): names.add(m["team2"])
        return sorted(names)

    teams = teams_from_slot if teams_from_slot else derive_teams_from_group_phase(group_phase)

    # --- Standings on-the-fly, falls fehlen
    if not group_standings and group_phase:
        try:
            group_standings = compute_standings_from_groups_payload(group_phase)
            TournamentData.query.filter_by(tournament_id=t_id, data_type="group_standings").delete()
            db.session.add(TournamentData(
                tournament_id=t_id, data_type="group_standings", payload=json_dumps(group_standings)
            ))
            db.session.commit()
        except Exception as e:
            print("compute_standings failed:", repr(e))
            group_standings = {}

    # --- KO-Runden
    ko_rows = KOBracket.query.filter_by(tournament_id=t_id).order_by(KOBracket.id.asc()).all()
    ko_rounds = [
        {
            "bracket_type": r.bracket_type,
            "round_name": r.round_name,
            "matches": (json_loads(r.match_data) or {}).get("matches", []),
            "id": r.id
        } for r in ko_rows
    ]

    # --- Play-In
    playin_row = TournamentData.query.filter_by(
        tournament_id=t_id, data_type="playin"
    ).order_by(TournamentData.created_at.desc()).first()
    playin = json_loads(playin_row.payload) if playin_row else {}

    return jsonify({
        "tournament": {
            "id": t.id,
            "name": t.name,
            "participant_count": t.participant_count,
            "cups_per_game": t.cups_per_game,
            "table_count": t.table_count,
            "finale_with_10_cups": t.finale_with_10_cups,
            "mode": t.mode,
            "current_phase": t.current_phase,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            # camelCase
            "participantCount": t.participant_count,
            "cupsPerGame": t.cups_per_game,
            "tableCount": t.table_count,
            "finaleWith10Cups": t.finale_with_10_cups,
            "currentPhase": t.current_phase,
            "createdAt": t.created_at.isoformat() if t.created_at else None
        },
        "teams": teams,
        "group_phase": group_phase,
        "group_standings": group_standings,
        "playin": playin,
        "ko_phase": {"rounds": ko_rounds}
    })

# -------------------------------------------------
# Tabellen/Standings (Berechnung)
# -------------------------------------------------

def compute_standings_from_groups_payload(payload: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    matches_by_group: Dict[str, List[Dict[str, Any]]] = payload.get("matches") or payload.get("groups") or {}
    tables: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # Teams initialisieren
    for gname, match_list in (matches_by_group or {}).items():
        team_names = set()
        for m in match_list or []:
            if m.get("team1"): team_names.add(m["team1"])
            if m.get("team2"): team_names.add(m["team2"])
        tables[gname] = {
            n: {"name": n, "points": 0, "wins": 0, "losses": 0, "cupsFor": 0, "cupsAgainst": 0}
            for n in team_names
        }

    # Spiele verarbeiten
    for gname, match_list in (matches_by_group or {}).items():
        for m in match_list or []:
            w = m.get("winner")
            t1, t2 = m.get("team1"), m.get("team2")
            c1, c2 = int(m.get("cups_team1") or 0), int(m.get("cups_team2") or 0)
            if not t1 or not t2:
                continue

            tables[gname][t1]["cupsFor"] += c1
            tables[gname][t1]["cupsAgainst"] += c2
            tables[gname][t2]["cupsFor"] += c2
            tables[gname][t2]["cupsAgainst"] += c1

            if w == t1:
                tables[gname][t1]["wins"] += 1
                tables[gname][t1]["points"] += 2
                tables[gname][t2]["losses"] += 1
            elif w == t2:
                tables[gname][t2]["wins"] += 1
                tables[gname][t2]["points"] += 2
                tables[gname][t1]["losses"] += 1

    out: Dict[str, List[Dict[str, Any]]] = {}
    for gname, rows in tables.items():
        lst = []
        for r in rows.values():
            r["cupsDiff"] = r["cupsFor"] - r["cupsAgainst"]
            lst.append(r)
        lst.sort(key=lambda r: (-r["points"], -r["cupsDiff"], -r["cupsFor"], r["name"]))
        out[gname] = lst
    return out

@app.get("/tournaments/<int:t_id>/group-standings")
def api_group_standings(t_id: int):
    Tournament.query.get_or_404(t_id)
    row = TournamentData.query.filter_by(tournament_id=t_id, data_type="groups").order_by(TournamentData.created_at.desc()).first()
    if not row:
        return jsonify({})
    payload = json_loads(row.payload) or {}
    standings = compute_standings_from_groups_payload(payload)

    TournamentData.query.filter_by(tournament_id=t_id, data_type="group_standings").delete()
    db.session.add(TournamentData(
        tournament_id=t_id, data_type="group_standings", payload=json_dumps(standings)
    ))
    db.session.commit()

    return jsonify(standings)

# -------------------------------------------------
# API – Play-In speichern/laden
# -------------------------------------------------

@app.post("/tournaments/<int:t_id>/save-playin")
def api_save_playin(t_id: int):
    Tournament.query.get_or_404(t_id)
    payload = request.json or {}
    TournamentData.query.filter_by(tournament_id=t_id, data_type="playin").delete()
    db.session.add(TournamentData(
        tournament_id=t_id, data_type="playin", payload=json_dumps(payload)
    ))
    t = Tournament.query.get(t_id)
    t.current_phase = "playin"
    db.session.commit()
    return jsonify({"ok": True})

@app.get("/tournaments/<int:t_id>/load-playin")
def api_load_playin(t_id: int):
    row = TournamentData.query.filter_by(tournament_id=t_id, data_type="playin").order_by(TournamentData.created_at.desc()).first()
    return jsonify(json_loads(row.payload) if row else {})

# -------------------------------------------------
# API – KO Bracket: Full Save / Load / Single-Match Save
# -------------------------------------------------

@app.post("/tournaments/<int:t_id>/save-ko-bracket")
def api_save_ko(t_id: int):
    Tournament.query.get_or_404(t_id)
    data = request.json or {}
    rounds: List[Dict[str, Any]] = data.get("rounds") or []

    KOBracket.query.filter_by(tournament_id=t_id).delete()

    if not rounds and "match_data" in data:
        rounds = [{
            "round_name": str(data.get("round_name") or "Round"),
            "bracket_type": str(data.get("bracket_type") or "main"),
            "matches": (data.get("match_data") or {}).get("matches") or []
        }]

    for r in rounds:
        db.session.add(KOBracket(
            tournament_id=t_id,
            bracket_type=str(r.get("bracket_type") or "main"),
            round_name=str(r.get("round_name") or "Round"),
            match_data=json_dumps({"matches": r.get("matches") or []})
        ))

    t = Tournament.query.get(t_id)
    t.current_phase = "ko"
    db.session.commit()
    return jsonify({"ok": True})

@app.get("/tournaments/<int:t_id>/load-ko-bracket")
def api_load_ko(t_id: int):
    rows = KOBracket.query.filter_by(tournament_id=t_id).order_by(KOBracket.id.asc()).all()
    out = [
        {
            "bracket_type": r.bracket_type,
            "round_name": r.round_name,
            "matches": (json_loads(r.match_data) or {}).get("matches", []),
            "id": r.id
        }
        for r in rows
    ]
    return jsonify({"rounds": out})

@app.post("/tournaments/<int:t_id>/ko-match")
def api_save_ko_match(t_id: int):
    """Single-Match Update in einer KO-Runde über round_index + match_index."""
    Tournament.query.get_or_404(t_id)
    body = request.json or {}

    r_idx = int(body.get("round_index") if body.get("round_index") is not None else -1)
    m_idx = int(body.get("match_index") if body.get("match_index") is not None else -1)
    if r_idx < 0 or m_idx < 0:
        return jsonify({"error": "round_index and match_index required"}), 400

    team1 = body.get("team1")
    team2 = body.get("team2")
    winner = body.get("winner")
    cups1 = int(body.get("cups_team1") or 0)
    cups2 = int(body.get("cups_team2") or 0)
    
    cups_state_team1 = body.get("cups_state_team1")
    cups_state_team2 = body.get("cups_state_team2")
    team1_rerack_used = bool(body.get("team1_rerack_used") or False)
    team2_rerack_used = bool(body.get("team2_rerack_used") or False)

    rows = KOBracket.query.filter_by(tournament_id=t_id).order_by(KOBracket.id.asc()).all()
    if not rows or r_idx >= len(rows):
        return jsonify({"error": "round index out of range"}), 404

    r = rows[r_idx]
    r_data = json_loads(r.match_data) or {}
    matches: List[Dict[str, Any]] = r_data.get("matches") or []

    if m_idx >= len(matches):
        return jsonify({"error": "match index out of range"}), 404

    # Update Match
    cur = matches[m_idx] if m_idx < len(matches) else {}
    cur.update({
        "team1": team1, "team2": team2,
        "winner": winner,
        "cups_team1": cups1, "cups_team2": cups2,
        "cups_state_team1": cups_state_team1,
        "cups_state_team2": cups_state_team2,
        "team1_rerack_used": team1_rerack_used,
        "team2_rerack_used": team2_rerack_used
    })
    matches[m_idx] = cur
    r_data["matches"] = matches
    r.match_data = json_dumps(r_data)

    db.session.commit()

    return jsonify(cur)

# -------------------------------------------------
# Health & Fehler
# -------------------------------------------------

@app.get("/health")
def api_health():
    return jsonify({"ok": True})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad Request"}), 400

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------
# WebSockets / Echtzeit Events
# -------------------------------------------------

@socketio.on("cup_hit")
def on_cup_hit(data):
    t_id = data.get("tournament_id")
    match_id = data.get("match_id")
    team_key = data.get("team_key")
    cup_index = data.get("cup_index")
    player = data.get("player_name")

    # Event für das Undo-Log speichern
    event = MatchEvent(
        tournament_id=t_id,
        match_id=match_id,
        action_type="cup_hit",
        team_key=team_key,
        player_name=player,
        cup_index=cup_index
    )
    db.session.add(event)
    db.session.commit()
    
    # An alle Clients (LiveView) weiterleiten
    emit("cup_hit_update", data, broadcast=True)

@socketio.on("undo_action")
def on_undo_action(data):
    t_id = data.get("tournament_id")
    match_id = data.get("match_id")
    
    # Letztes Event dieses Tisches finden und löschen
    last_event = MatchEvent.query.filter_by(tournament_id=t_id, match_id=match_id).order_by(MatchEvent.timestamp.desc()).first()
    if last_event:
        db.session.delete(last_event)
        db.session.commit()
        
    # Alle Clients informieren, dass ein Undo stattgefunden hat
    emit("undo_update", {"match_id": match_id, "tournament_id": t_id}, broadcast=True)

@socketio.on("rerack")
def on_rerack(data):
    emit("rerack_update", data, broadcast=True)

# -------------------------------------------------
# Dev Entry
# -------------------------------------------------

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
