from __future__ import annotations
from typing import Any, Dict, List
from .models import Tournament, Team, Match, Player, Tiebreak


# ── Structure helpers (ported 1:1 from Flask) ──────────────────────────────

def _letters() -> List[str]:
    return list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


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
    if n <= 4:   return 1
    if n <= 8:   return 2
    if n <= 11:  return 3
    if n <= 16:  return 4
    return max(4, round(n / 4.5))


def compute_structure(n: int) -> Dict[str, Any]:
    if n < 2 or n > 128:
        return {'error': 'Teilnehmerzahl muss zwischen 2 und 128 liegen.'}

    if n == 12:
        sizes, g = [3, 3, 3, 3], 4
    else:
        g = group_count_by_band(n)
        sizes = balanced_sizes(n, g)
        if n >= 17:
            while max(sizes) > 5:
                g += 1
                sizes = balanced_sizes(n, g)

    letters = _letters()
    group_names = [f'Gruppe {letters[i]}' for i in range(g)]
    groups = [{'name': name, 'size': size} for name, size in zip(group_names, sizes)]

    qualified = sum(2 if s >= 2 else 0 for s in sizes)
    ko_size = choose_ko_size(qualified)
    slots_needed = max(0, ko_size - qualified)

    candidates = []
    for name, size in zip(group_names, sizes):
        if size >= 3:
            candidates.append({'group': name, 'position': 3, 'label': f'3. {name}'})
        if size >= 4:
            candidates.append({'group': name, 'position': 4, 'label': f'4. {name}'})

    return {
        'groups': groups,
        'ko_size': ko_size,
        'qualified_per_group': 2,
        'playin_needed': slots_needed > 0,
        'playin_slots_needed': slots_needed,
        'playin_candidates': candidates,
    }


def round_robin(team_names: List[str]) -> List[Dict[str, Any]]:
    matches = []
    order = 0
    for i in range(len(team_names)):
        for j in range(i + 1, len(team_names)):
            matches.append({
                'team1': team_names[i],
                'team2': team_names[j],
                'winner': None,
                'cups_team1': None,
                'cups_team2': None,
                'order_index': order,
            })
            order += 1
    return matches


KO_ROUND_NAME_ORDER = {
    'runde der 256': 0,
    'runde der 128': 1,
    'runde der 64': 2,
    'runde der 32': 3,
    'sechzehntelfinale': 4,
    'achtelfinale': 5,
    'viertelfinale': 6,
    'halbfinale': 7,
    'finale': 8,
    'spiel um platz 3': 99,
}


def _ko_round_sort_key(round_data: Dict[str, Any]) -> tuple:
    """
    KO rounds must be ordered by tournament progression, not alphabetically.
    LiveView/MobileView consume get_full_state() directly, so a lexical sort on
    `ko_round` would place rounds like "Finale" before "Halbfinale".
    """
    bracket_type = str(round_data.get('bracket_type') or 'main').strip().lower()
    round_name = str(round_data.get('round_name') or '').strip()
    normalized_name = round_name.lower()
    match_count = len(round_data.get('matches') or [])

    bracket_rank = 1 if bracket_type == 'placement' else 0
    round_rank = KO_ROUND_NAME_ORDER.get(normalized_name, 10_000)

    return (
        bracket_rank,
        -match_count,
        round_rank,
        round_name,
    )


def sort_ko_rounds(rounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rounds, key=_ko_round_sort_key)


def _ko_match_in_progress(match_data: Dict[str, Any]) -> bool:
    if int(match_data.get('cups_team1') or 0) > 0 or int(match_data.get('cups_team2') or 0) > 0:
        return True
    if bool(match_data.get('is_overtime')):
        return True
    state1 = match_data.get('cups_state_team1') or []
    state2 = match_data.get('cups_state_team2') or []
    if isinstance(state1, list) and any(c is False for c in state1):
        return True
    if isinstance(state2, list) and any(c is False for c in state2):
        return True
    return False


def is_ko_round_complete(round_data: Dict[str, Any]) -> bool:
    matches = round_data.get('matches') or []
    if not matches:
        return False
    return all(
        (not m.get('team1')) or (not m.get('team2')) or bool(m.get('winner'))
        for m in matches
    )


def _ko_round_has_playable_matches(round_data: Dict[str, Any]) -> bool:
    return any(
        m.get('team1') and m.get('team2') and not m.get('winner')
        for m in (round_data.get('matches') or [])
    )


def _ko_round_has_started(round_data: Dict[str, Any]) -> bool:
    return any(
        (m.get('team1') and m.get('team2') and bool(m.get('winner')))
        or (m.get('team1') and m.get('team2') and _ko_match_in_progress(m))
        for m in (round_data.get('matches') or [])
    )


def derive_active_ko_main_round_index(
    rounds: List[Dict[str, Any]],
    explicit_index: Any = None,
) -> int:
    main_rounds = [r for r in sort_ko_rounds(rounds) if (r.get('bracket_type') or 'main') != 'placement']
    if not main_rounds:
        return 0

    try:
        idx = int(explicit_index)
    except (TypeError, ValueError):
        idx = None
    if idx is not None and 0 <= idx < len(main_rounds):
        return idx

    for idx, round_data in enumerate(main_rounds):
        matches = round_data.get('matches') or []
        if any(
            m.get('team1') and m.get('team2') and not m.get('winner') and _ko_match_in_progress(m)
            for m in matches
        ):
            return idx

    for idx, round_data in enumerate(main_rounds):
        matches = round_data.get('matches') or []
        if any(m.get('team1') and m.get('team2') and not m.get('winner') for m in matches):
            return idx

    return max(0, len(main_rounds) - 1)


def derive_active_ko_stage_kind(
    rounds: List[Dict[str, Any]],
    active_main_round_index: Any = None,
    explicit_stage_kind: Any = None,
) -> str:
    sorted_rounds = sort_ko_rounds(rounds)
    main_rounds = [r for r in sorted_rounds if (r.get('bracket_type') or 'main') != 'placement']
    placement_round = next(
        (r for r in sorted_rounds if (r.get('bracket_type') or 'main') == 'placement'),
        None,
    )
    if not main_rounds:
        return 'main'

    idx = derive_active_ko_main_round_index(sorted_rounds, active_main_round_index)
    if not placement_round or idx != len(main_rounds) - 1:
        return 'main'

    explicit = str(explicit_stage_kind or '').strip().lower()
    if explicit in {'main', 'placement'}:
        return explicit

    final_round = main_rounds[idx]
    placement_started = _ko_round_has_started(placement_round)
    final_started = _ko_round_has_started(final_round)
    placement_pending = _ko_round_has_playable_matches(placement_round)
    final_pending = _ko_round_has_playable_matches(final_round)

    if final_started:
        return 'main'
    if placement_started:
        return 'placement'
    if placement_pending and final_pending:
        return 'placement'
    if placement_pending and not final_pending:
        return 'placement'
    return 'main'


def get_ko_control_payload(tournament: Tournament) -> Dict[str, Any]:
    entry = Tiebreak.objects.filter(
        tournament=tournament,
        mode='ko_control',
        group_name='__ko_control__',
    ).order_by('-id').first()
    return entry.payload if entry and isinstance(entry.payload, dict) else {}


def set_ko_control_payload(tournament: Tournament, payload: Dict[str, Any]) -> Dict[str, Any]:
    control = payload if isinstance(payload, dict) else {}
    Tiebreak.objects.update_or_create(
        tournament=tournament,
        mode='ko_control',
        group_name='__ko_control__',
        defaults={
            'payload': control,
            'resolved': True,
        },
    )
    return control


# ── Group generation ────────────────────────────────────────────────────────

def generate_groups(tournament: Tournament, team_names: List[str]) -> Dict[str, Any]:
    """
    Distribute teams into groups, persist Team + Match objects,
    return the group_phase payload (same structure as Flask).
    Preserves existing player assignments on Team objects.
    """
    n = len(team_names)
    structure = compute_structure(n)
    if 'error' in structure:
        return structure

    # Clear existing group matches (but keep Team objects to preserve player info)
    Match.objects.filter(tournament=tournament, phase=Match.PHASE_GROUP).delete()
    # Remove teams that are no longer in the list
    Team.objects.filter(tournament=tournament).exclude(name__in=team_names).delete()

    group_phase: Dict[str, Any] = {'groups': {}, 'matches': {}}
    idx = 0

    for g_meta in structure['groups']:
        gname: str = g_meta['name']
        gsize: int = g_meta['size']
        slice_names = team_names[idx: idx + gsize]
        idx += gsize

        # Create or update Team objects (preserves player1/player2 on existing teams)
        for tname in slice_names:
            team, created = Team.objects.get_or_create(tournament=tournament, name=tname)
            if created or team.group_name != gname:
                team.group_name = gname
                team.save(update_fields=['group_name'])

        # Generate + persist round-robin matches
        matches_data = round_robin(slice_names)
        for m in matches_data:
            t1 = Team.objects.get(tournament=tournament, name=m['team1'])
            t2 = Team.objects.get(tournament=tournament, name=m['team2'])
            Match.objects.create(
                tournament=tournament,
                phase=Match.PHASE_GROUP,
                group_name=gname,
                team1=t1,
                team2=t2,
                order_index=m['order_index'],
                history_team1=[],
                history_team2=[],
            )

        group_phase['groups'][gname] = slice_names
        group_phase['matches'][gname] = matches_data

    return group_phase


# ── Standings calculation ───────────────────────────────────────────────────

def compute_standings(tournament: Tournament) -> Dict[str, List[Dict[str, Any]]]:
    """Calculate live standings from Match objects in DB."""
    matches = Match.objects.filter(
        tournament=tournament, phase=Match.PHASE_GROUP
    ).select_related('team1', 'team2', 'winner')

    tables: Dict[str, Dict[str, Any]] = {}

    for m in matches:
        gname = m.group_name or ''
        if gname not in tables:
            tables[gname] = {}
        for team in (m.team1, m.team2):
            if team.name not in tables[gname]:
                tables[gname][team.name] = {
                    'name': team.name, 'points': 0, 'wins': 0,
                    'losses': 0, 'cupsFor': 0, 'cupsAgainst': 0,
                }

        c1, c2 = m.cups_team1, m.cups_team2
        tables[gname][m.team1.name]['cupsFor'] += c1
        tables[gname][m.team1.name]['cupsAgainst'] += c2
        tables[gname][m.team2.name]['cupsFor'] += c2
        tables[gname][m.team2.name]['cupsAgainst'] += c1

        if m.winner_id == m.team1_id:
            tables[gname][m.team1.name]['wins'] += 1
            tables[gname][m.team1.name]['points'] += 2
            tables[gname][m.team2.name]['losses'] += 1
        elif m.winner_id == m.team2_id:
            tables[gname][m.team2.name]['wins'] += 1
            tables[gname][m.team2.name]['points'] += 2
            tables[gname][m.team1.name]['losses'] += 1

    out: Dict[str, List] = {}
    for gname, rows in tables.items():
        lst = []
        for r in rows.values():
            r['cupsDiff'] = r['cupsFor'] - r['cupsAgainst']
            lst.append(r)
        lst.sort(key=lambda r: (-r['points'], -r['cupsDiff'], -r['cupsFor'], r['name']))
        out[gname] = lst
    return out


# ── Full state snapshot ─────────────────────────────────────────────────────

def get_full_state(tournament: Tournament) -> Dict[str, Any]:
    """Serialize the complete tournament state as a JSON-safe dict."""

    # Teams (with player info)
    teams_qs = Team.objects.filter(tournament=tournament).select_related('player1', 'player2')
    teams = [t.name for t in teams_qs]
    team_players = {
        t.name: {
            'player1': t.player1.name if t.player1 else '',
            'player2': t.player2.name if t.player2 else '',
        }
        for t in teams_qs
    }

    # Group matches
    group_matches_qs = Match.objects.filter(
        tournament=tournament, phase=Match.PHASE_GROUP
    ).select_related('team1', 'team2', 'winner', 'table').order_by('group_name', 'order_index')

    matches_by_group: Dict[str, list] = {}
    groups_teams: Dict[str, list] = {}
    for m in group_matches_qs:
        gname = m.group_name or ''
        if gname not in matches_by_group:
            matches_by_group[gname] = []
            groups_teams[gname] = []
        matches_by_group[gname].append({
            'id': m.id,
            'group_name': gname,
            'team1': m.team1.name,
            'team2': m.team2.name,
            'winner': m.winner.name if m.winner else None,
            'cups_team1': m.cups_team1,
            'cups_team2': m.cups_team2,
            'order_index': m.order_index,
            'cups_state_team1': m.cups_state_team1,
            'cups_state_team2': m.cups_state_team2,
            'hit_history_team1': m.hit_history_team1,
            'hit_history_team2': m.hit_history_team2,
            'history_team1': m.history_team1,
            'history_team2': m.history_team2,
            'team1_rerack_used': m.team1_rerack_used,
            'team2_rerack_used': m.team2_rerack_used,
            'is_overtime': m.is_overtime,
            'table_no': int(m.table.name.replace('Tisch ', '')) if m.table and str(m.table.name).startswith('Tisch ') else None,
        })
        for t in (m.team1.name, m.team2.name):
            if t not in groups_teams[gname]:
                groups_teams[gname].append(t)

    group_phase = {
        'groups': [{'name': k, 'teams': v} for k, v in groups_teams.items()],
        'matches': matches_by_group,
    }

    group_standings = compute_standings(tournament)

    # KO matches
    ko_matches = Match.objects.filter(
        tournament=tournament, phase=Match.PHASE_KO
    ).select_related('team1', 'team2', 'winner').order_by('ko_bracket_type', 'ko_round', 'ko_match_index')

    rounds_dict: Dict[str, dict] = {}
    for m in ko_matches:
        key = f'{m.ko_bracket_type}|{m.ko_round}'
        if key not in rounds_dict:
            rounds_dict[key] = {
                'bracket_type': m.ko_bracket_type,
                'round_name': m.ko_round,
                'matches': [],
            }
        rounds_dict[key]['matches'].append({
            'id': m.id,
            'team1': m.team1.name if m.team1 else None,
            'team2': m.team2.name if m.team2 else None,
            'winner': m.winner.name if m.winner else None,
            'status': m.status,
            'table_no': int(m.table.name.replace('Tisch ', '')) if m.table and str(m.table.name).startswith('Tisch ') else None,
            'cups_team1': m.cups_team1,
            'cups_team2': m.cups_team2,
            'cups_state_team1': m.cups_state_team1,
            'cups_state_team2': m.cups_state_team2,
            'is_overtime': m.is_overtime,
        })

    # Play-in matches
    playin_matches = Match.objects.filter(
        tournament=tournament, phase=Match.PHASE_PLAYIN
    ).select_related('team1', 'team2', 'winner')
    ko_preview_entry = Tiebreak.objects.filter(
        tournament=tournament, mode='ko_preview'
    ).order_by('-id').first()
    ko_preview = ko_preview_entry.payload if ko_preview_entry and isinstance(ko_preview_entry.payload, dict) else {}
    ko_rounds = sort_ko_rounds(list(rounds_dict.values()))
    ko_control = get_ko_control_payload(tournament)
    active_ko_main_round_index = derive_active_ko_main_round_index(
        ko_rounds,
        ko_control.get('active_main_round_index', ko_control.get('activeMainRoundIndex')),
    )
    active_ko_stage_kind = derive_active_ko_stage_kind(
        ko_rounds,
        active_ko_main_round_index,
        ko_control.get('active_stage_kind', ko_control.get('activeStageKind')),
    )

    # Top Players (based on hits in THIS tournament)
    from django.db.models import Count
    top_players_qs = Player.objects.filter(
        cup_hits__match__tournament=tournament
    ).annotate(
        tournament_hits=Count('cup_hits')
    ).order_by('-tournament_hits', 'name')

    top_players = [
        {'name': p.name, 'hits': p.tournament_hits}
        for p in top_players_qs
    ]

    t = tournament
    return {
        'tournament': {
            'id': t.id,
            'name': t.name,
            'mode': t.mode,
            'participant_count': t.participant_count,
            'cups_per_game': t.cups_per_game,
            'finale_with_10_cups': t.finale_with_10_cups,
            'table_count': t.table_count,
            'status': t.status,
            'mobile_access_token': str(t.mobile_access_token),
            'created_at': t.created_at.isoformat(),
            # camelCase mirrors for frontend compatibility
            'currentPhase': t.status,
            'current_phase': t.status,
            'participantCount': t.participant_count,
            'cupsPerGame': t.cups_per_game,
            'finaleWith10Cups': t.finale_with_10_cups,
            'tableCount': t.table_count,
            'mobileAccessToken': str(t.mobile_access_token),
            'createdAt': t.created_at.isoformat(),
        },
        'teams': teams,
        'team_players': team_players,
        'top_players': top_players,
        'group_phase': group_phase,
        'group_standings': group_standings,
        'playin': {
            'matches': [
                {
                    'id': m.id,
                    'team1': m.team1.name,
                    'team2': m.team2.name,
                    'winner': m.winner.name if m.winner else None,
                    'cups_team1': m.cups_team1,
                    'cups_team2': m.cups_team2,
                }
                for m in playin_matches
            ]
        },
        'ko_preview': ko_preview,
        'ko_phase': {
            'rounds': ko_rounds,
            'active_main_round_index': active_ko_main_round_index,
            'activeMainRoundIndex': active_ko_main_round_index,
            'active_stage_kind': active_ko_stage_kind,
            'activeStageKind': active_ko_stage_kind,
        },
    }
