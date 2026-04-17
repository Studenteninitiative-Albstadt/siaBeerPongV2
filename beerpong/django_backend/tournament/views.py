from __future__ import annotations

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Tournament, Team, Match, Player, CupHit, Table, Tiebreak, MatchAssignment, AdminAction, User
from .permissions import IsOrga, IsOrgaOrLiveview, IsRoot
from .serializers import TournamentSerializer, CustomTokenObtainPairSerializer
from .services import (
    compute_structure,
    generate_groups,
    compute_standings,
    get_full_state,
    sort_ko_rounds,
    derive_active_ko_main_round_index,
    derive_active_ko_stage_kind,
    get_ko_control_payload,
    is_ko_round_complete,
    set_ko_control_payload,
)


# ── Auth ────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ── WebSocket broadcast helper ───────────────────────────────────────────────

def broadcast(tournament_id: int, event: str, data: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'tournament_{tournament_id}',
        {'type': 'tournament.update', 'event': event, 'data': data},
    )


def broadcast_personal(user_id: int, data):
    """Push a message to the personal channel of a specific user."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {'type': 'assignment.update', 'data': data},
    )


def _serialize_assignment(assignment):
    if not assignment or not assignment.match:
        return None
    m = assignment.match
    return {
        'assignment_id': assignment.id,
        'match_id': m.id,
        'phase': m.phase,
        'group_name': m.group_name,
        'team1': m.team1.name if m.team1 else None,
        'team2': m.team2.name if m.team2 else None,
        'table_no': m.table.name if m.table else None,
        'status': m.status,
        'ko_round': m.ko_round,
        'ko_bracket_type': m.ko_bracket_type,
        'ko_match_index': m.ko_match_index,
    }


# ── Tournament ViewSet ───────────────────────────────────────────────────────

class TournamentViewSet(ViewSet):

    def get_permissions(self):
        if self.action == 'mobile_state':
            return [AllowAny()]
        read_actions = {'list', 'retrieve', 'load_all_data', 'group_standings',
                        'load_ko', 'load_playin', 'load_teams'}
        if self.action in read_actions:
            return [IsOrgaOrLiveview()]
        return [IsOrga()]

    # ── CRUD ────────────────────────────────────────────────────────────────

    def list(self, request):
        qs = Tournament.objects.all()
        return Response(TournamentSerializer(qs, many=True).data)

    def create(self, request):
        d = request.data
        t = Tournament.objects.create(
            name=d.get('name', 'Neues Turnier'),
            mode=d.get('mode', 'groups'),
            participant_count=int(d.get('participantCount', d.get('participant_count', 8))),
            cups_per_game=int(d.get('cupsPerGame', d.get('cups_per_game', 6))),
            finale_with_10_cups=bool(d.get('finaleWith10Cups', d.get('finale_with_10_cups', False))),
            table_count=int(d.get('tableCount', d.get('table_count', 2))),
        )
        return Response(TournamentSerializer(t).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        t = self._get_or_404(pk)
        return Response(TournamentSerializer(t).data)

    def destroy(self, request, pk=None):
        t = self._get_or_404(pk)
        t.delete()
        return Response({'ok': True})

    # ── Update ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='update')
    def update_tournament(self, request, pk=None):
        t = self._get_or_404(pk)
        d = request.data
        if 'name' in d: t.name = str(d['name'])
        if 'mode' in d: t.mode = str(d['mode'])
        for key in ('participantCount', 'participant_count'):
            if key in d: t.participant_count = int(d[key])
        for key in ('cupsPerGame', 'cups_per_game'):
            if key in d: t.cups_per_game = int(d[key])
        for key in ('finaleWith10Cups', 'finale_with_10_cups'):
            if key in d: t.finale_with_10_cups = bool(d[key])
        for key in ('tableCount', 'table_count'):
            if key in d: t.table_count = int(d[key])
        for key in ('currentPhase', 'current_phase'):
            if key in d: t.status = str(d[key])
        t.save()
        broadcast(t.id, 'tournament_updated', {'tournament': TournamentSerializer(t).data})
        return Response({'ok': True})

    # ── Structure ────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='compute-plan')
    def compute_plan(self, request, pk=None):
        t = self._get_or_404(pk)
        n = int(request.data.get('participantCount') or t.participant_count)
        return Response(compute_structure(n))

    # ── Teams ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='save-teams')
    def save_teams(self, request, pk=None):
        t = self._get_or_404(pk)
        teams_data = request.data.get('teams', [])
        if not isinstance(teams_data, list):
            return Response({'error': 'teams must be a list'}, status=400)

        # 1. Identify valid team names from payload
        new_names = []
        for item in teams_data:
            name = (item if isinstance(item, str) else item.get('name', '')).strip()
            if name:
                new_names.append(name)

        # 2. Delete teams that are NO LONGER in the tournament
        Team.objects.filter(tournament=t).exclude(name__in=new_names).delete()

        # 3. Create or Update teams and players
        for item in teams_data:
            name = (item if isinstance(item, str) else item.get('name', '')).strip()
            if not name:
                continue

            team, _ = Team.objects.get_or_create(tournament=t, name=name)

            # Update players if provided
            if isinstance(item, dict):
                p1_name = (item.get('player1') or '').strip()
                p2_name = (item.get('player2') or '').strip()
                changed = False
                if p1_name:
                    p1, _ = Player.objects.get_or_create(name=p1_name)
                    if team.player1 != p1:
                        team.player1 = p1
                        changed = True
                if p2_name:
                    p2, _ = Player.objects.get_or_create(name=p2_name)
                    if team.player2 != p2:
                        team.player2 = p2
                        changed = True
                if changed:
                    team.save()

        # 4. AUTOMATICALLY GENERATE PLAN
        # This fulfills the request to generate the plan immediately
        generate_groups(t, new_names)

        broadcast(t.id, 'group_phase_updated', get_full_state(t))
        return Response({'ok': True, 'count': len(new_names)})

    @action(detail=True, methods=['get'], url_path='load-teams')
    def load_teams(self, request, pk=None):
        t = self._get_or_404(pk)
        teams_qs = Team.objects.filter(tournament=t).select_related('player1', 'player2')
        return Response({
            'teams': [
                {
                    'name': team.name,
                    'player1': team.player1.name if team.player1 else '',
                    'player2': team.player2.name if team.player2 else '',
                }
                for team in teams_qs
            ]
        })

    @action(detail=True, methods=['post'], url_path='save-team-players')
    def save_team_players(self, request, pk=None):
        t = self._get_or_404(pk)
        teams_data = request.data.get('teams') or []
        if not isinstance(teams_data, list):
            return Response({'error': 'teams must be a list'}, status=400)

        for item in teams_data:
            if not isinstance(item, dict):
                continue
            name = (item.get('name') or '').strip()
            if not name:
                continue

            team = Team.objects.filter(tournament=t, name=name).first()
            if not team:
                continue

            p1_name = (item.get('player1') or '').strip()
            p2_name = (item.get('player2') or '').strip()
            p1 = Player.objects.get_or_create(name=p1_name)[0] if p1_name else None
            p2 = Player.objects.get_or_create(name=p2_name)[0] if p2_name else None

            changed = False
            if team.player1 != p1:
                team.player1 = p1
                changed = True
            if team.player2 != p2:
                team.player2 = p2
                changed = True
            if changed:
                team.save(update_fields=['player1', 'player2'])

        full_state = get_full_state(t)
        broadcast(t.id, 'team_players_updated', full_state)
        return Response({
            'ok': True,
            'team_players': full_state.get('team_players') or {},
        })

    # ── Group phase ──────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='generate-groups')
    def generate_groups_action(self, request, pk=None):
        t = self._get_or_404(pk)
        team_names = request.data.get('teams') or list(
            Team.objects.filter(tournament=t).values_list('name', flat=True)
        )
        result = generate_groups(t, team_names)
        if 'error' in result:
            return Response(result, status=400)
        broadcast(t.id, 'group_phase_updated', get_full_state(t))
        return Response(result)

    @action(detail=True, methods=['post'], url_path='save-group-phase')
    def save_group_phase(self, request, pk=None):
        """
        Called by GroupsView with the full group_phase payload.
        During initial setup (no matches yet) we call generate_groups to create the
        Match objects.  During live play the auto-save calls this endpoint every few
        hundred ms – in that case we must NOT call generate_groups because it deletes
        and recreates all matches (changing their PKs), which causes LiveTable3D to
        remount and breaks real-time cup-state sync.
        """
        t = self._get_or_404(pk)
        payload = request.data

        # Extract team names from the nested payload
        groups_data = payload.get('group_phase', payload).get('groups', payload.get('groups', []))
        if isinstance(groups_data, list):
            team_names = []
            for g in groups_data:
                if isinstance(g, dict):
                    team_names.extend(g.get('teams', []))
        else:
            team_names = list(Team.objects.filter(tournament=t).values_list('name', flat=True))

        # Only regenerate the full group structure when no group matches exist yet.
        # If matches are already present, just update them in-place to preserve PKs.
        existing_match_count = Match.objects.filter(
            tournament=t, phase=Match.PHASE_GROUP
        ).count()

        if team_names and existing_match_count == 0:
            generate_groups(t, team_names)

        # Persist raw match results that came with the payload
        matches_data = payload.get('group_phase', payload).get('matches', payload.get('matches', {}))
        if isinstance(matches_data, dict):
            for gname, match_list in matches_data.items():
                for m in (match_list or []):
                    _update_group_match_from_dict(t, gname, m)

        broadcast(t.id, 'group_phase_updated', get_full_state(t))
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='group-match')
    def group_match(self, request, pk=None):
        """Single match result update — called on every cup increment."""
        t = self._get_or_404(pk)
        body = request.data
        gname = (body.get('group_name') or '').strip()

        result = _update_group_match_from_dict(t, gname, body)
        if result is None:
            return Response({'error': 'Team not found'}, status=404)

        match_id = result.get('id')
        if match_id:
            match = Match.objects.filter(id=match_id).first()
            _apply_match_event(t, match, body, user=request.user)

        standings = compute_standings(t)
        full_state = get_full_state(t)
        broadcast(t.id, 'match_updated', {
            'match': result,
            'group_standings': standings,
            'top_players': full_state['top_players'],
            'tournament': full_state['tournament']
        })
        return Response(result)
    @action(detail=True, methods=['get'], url_path='group-standings')
    def group_standings(self, request, pk=None):
        t = self._get_or_404(pk)
        return Response(compute_standings(t))

    @action(detail=True, methods=['get'], url_path='load-all-data')
    def load_all_data(self, request, pk=None):
        t = self._get_or_404(pk)
        return Response(get_full_state(t))

    # ── Play-in ──────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='save-playin')
    def save_playin(self, request, pk=None):
        t = self._get_or_404(pk)
        payload = request.data
        Match.objects.filter(tournament=t, phase=Match.PHASE_PLAYIN).delete()
        Tiebreak.objects.filter(tournament=t, mode='ko_preview').delete()

        for m in (payload.get('playin_matches') or payload.get('matches') or []):
            t1 = Team.objects.filter(tournament=t, name=m.get('team1')).first()
            t2 = Team.objects.filter(tournament=t, name=m.get('team2')).first()
            if t1 and t2:
                Match.objects.create(
                    tournament=t, phase=Match.PHASE_PLAYIN, team1=t1, team2=t2,
                    history_team1=[], history_team2=[]
                )

        t.status = Tournament.STATUS_PLAYIN
        t.save()
        broadcast(t.id, 'phase_changed', get_full_state(t))
        return Response({'ok': True})

    @action(detail=True, methods=['post'], url_path='save-ko-preview')
    def save_ko_preview(self, request, pk=None):
        t = self._get_or_404(pk)
        payload = request.data if isinstance(request.data, dict) else {}
        slots = payload.get('slots') or []
        ko_size = payload.get('ko_size', payload.get('koSize'))
        teams = payload.get('teams') or []
        source = payload.get('source') or 'groups'
        phase = payload.get('phase')

        Tiebreak.objects.filter(tournament=t, mode='ko_preview').delete()

        if slots:
            Tiebreak.objects.create(
                tournament=t,
                group_name='__ko_preview__',
                mode='ko_preview',
                payload={
                    'slots': slots,
                    'ko_size': ko_size,
                    'teams': teams,
                    'source': source,
                },
                resolved=False,
            )

        if phase is not None:
            t.status = str(phase)
            t.save(update_fields=['status'])

        broadcast(t.id, 'ko_preview_updated', get_full_state(t))
        return Response({'ok': True})

    @action(detail=True, methods=['get'], url_path='load-playin')
    def load_playin(self, request, pk=None):
        t = self._get_or_404(pk)
        matches = Match.objects.filter(
            tournament=t, phase=Match.PHASE_PLAYIN
        ).select_related('team1', 'team2', 'winner')
        return Response({'matches': [
            {
                'id': m.id, 'team1': m.team1.name, 'team2': m.team2.name,
                'winner': m.winner.name if m.winner else None,
                'cups_team1': m.cups_team1, 'cups_team2': m.cups_team2,
            }
            for m in matches
        ]})

    # ── KO bracket ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'], url_path='save-ko-bracket')
    def save_ko(self, request, pk=None):
        t = self._get_or_404(pk)
        rounds = request.data.get('rounds') or []
        incoming_active_round_index = request.data.get(
            'active_main_round_index',
            request.data.get('activeMainRoundIndex'),
        )
        incoming_active_stage_kind = request.data.get(
            'active_stage_kind',
            request.data.get('activeStageKind'),
        )
        Tiebreak.objects.filter(tournament=t, mode='ko_preview').delete()

        existing_matches = list(
            Match.objects.filter(tournament=t, phase=Match.PHASE_KO)
            .select_related('team1', 'team2', 'winner', 'table')
        )
        existing_by_id = {match.id: match for match in existing_matches}
        existing_by_key = {
            (match.ko_bracket_type or 'main', match.ko_round or '', match.ko_match_index): match
            for match in existing_matches
        }
        seen_match_ids = set()
        affected_player_ids = set()

        for round_data in rounds:
            round_name = str(round_data.get('round_name') or 'Round')
            bracket_type = str(round_data.get('bracket_type') or 'main')
            for idx, m in enumerate(round_data.get('matches') or []):
                t1 = Team.objects.filter(tournament=t, name=m.get('team1')).first()
                t2 = Team.objects.filter(tournament=t, name=m.get('team2')).first()
                if not (t1 and t2):
                    continue
                winner = Team.objects.filter(tournament=t, name=m.get('winner')).first()
                raw_table_no = m.get('table_no', m.get('tableNo', m.get('table_number', m.get('tableNumber'))))
                try:
                    table_no = int(raw_table_no) if raw_table_no is not None else None
                except (TypeError, ValueError):
                    table_no = None
                table = None
                if table_no and table_no > 0:
                    table, _ = Table.objects.get_or_create(
                        tournament=t,
                        name=f'Tisch {table_no}',
                        defaults={'is_active': True},
                    )
                raw_match_id = m.get('id')
                try:
                    match_id = int(raw_match_id) if raw_match_id is not None else None
                except (TypeError, ValueError):
                    match_id = None

                ko_match_index = m.get('ko_match_index', idx)
                try:
                    ko_match_index = int(ko_match_index)
                except (TypeError, ValueError):
                    ko_match_index = idx

                cups_team1 = int(m.get('cups_team1') or 0)
                cups_team2 = int(m.get('cups_team2') or 0)
                cups_state_team1 = m.get('cups_state_team1') if isinstance(m.get('cups_state_team1'), list) else []
                cups_state_team2 = m.get('cups_state_team2') if isinstance(m.get('cups_state_team2'), list) else []
                team1_rerack_used = bool(m.get('rerack_used_team1', False))
                team2_rerack_used = bool(m.get('rerack_used_team2', False))
                is_overtime = bool(m.get('is_overtime', False))

                match_key = (bracket_type, round_name, ko_match_index)
                match_obj = existing_by_id.get(match_id) if match_id is not None else None
                if not match_obj:
                    match_obj = existing_by_key.get(match_key)

                if match_obj:
                    teams_changed = match_obj.team1_id != t1.id or match_obj.team2_id != t2.id
                    if teams_changed and not _ko_match_has_started_db(match_obj):
                        player_ids = list(match_obj.cup_hits.values_list('player_id', flat=True))
                        if player_ids:
                            affected_player_ids.update(player_ids)
                            match_obj.cup_hits.all().delete()
                        match_obj.history_team1 = []
                        match_obj.history_team2 = []
                        match_obj.hit_history_team1 = []
                        match_obj.hit_history_team2 = []

                    if not teams_changed or not _ko_match_has_started_db(match_obj):
                        match_obj.team1 = t1
                        match_obj.team2 = t2
                        match_obj.winner = winner
                        match_obj.cups_team1 = cups_team1
                        match_obj.cups_team2 = cups_team2
                        match_obj.cups_state_team1 = cups_state_team1
                        match_obj.cups_state_team2 = cups_state_team2
                        match_obj.team1_rerack_used = team1_rerack_used
                        match_obj.team2_rerack_used = team2_rerack_used
                        match_obj.is_overtime = is_overtime
                        match_obj.ko_round = round_name
                        match_obj.ko_bracket_type = bracket_type
                        match_obj.ko_match_index = ko_match_index
                        match_obj.table = table
                        match_obj.status = 'done' if winner else 'pending'
                        match_obj.save()

                    seen_match_ids.add(match_obj.id)
                    continue

                match_obj = Match.objects.create(
                    tournament=t, phase=Match.PHASE_KO,
                    team1=t1, team2=t2, winner=winner,
                    cups_team1=cups_team1,
                    cups_team2=cups_team2,
                    cups_state_team1=cups_state_team1,
                    cups_state_team2=cups_state_team2,
                    team1_rerack_used=team1_rerack_used,
                    team2_rerack_used=team2_rerack_used,
                    is_overtime=is_overtime,
                    ko_round=round_name, ko_bracket_type=bracket_type, ko_match_index=ko_match_index,
                    table=table,
                    status='done' if winner else 'pending',
                    history_team1=[], history_team2=[]
                )
                seen_match_ids.add(match_obj.id)

        stale_matches = [
            match for match in existing_matches
            if match.id not in seen_match_ids and not _ko_match_has_started_db(match)
        ]
        for stale_match in stale_matches:
            player_ids = list(stale_match.cup_hits.values_list('player_id', flat=True))
            if player_ids:
                affected_player_ids.update(player_ids)
            stale_match.delete()

        if affected_player_ids:
            _sync_player_hit_totals(affected_player_ids)

        sorted_rounds = sort_ko_rounds(rounds)
        existing_control = get_ko_control_payload(t)
        active_main_round_index = derive_active_ko_main_round_index(
            sorted_rounds,
            incoming_active_round_index
            if incoming_active_round_index is not None
            else existing_control.get('active_main_round_index', existing_control.get('activeMainRoundIndex')),
        )
        active_stage_kind = derive_active_ko_stage_kind(
            sorted_rounds,
            active_main_round_index,
            incoming_active_stage_kind
            if incoming_active_stage_kind is not None
            else existing_control.get('active_stage_kind', existing_control.get('activeStageKind')),
        )
        set_ko_control_payload(
            t,
            {
                'active_main_round_index': active_main_round_index,
                'active_stage_kind': active_stage_kind,
            },
        )

        t.status = Tournament.STATUS_KO
        t.save()
        broadcast(t.id, 'ko_updated', get_full_state(t))
        return Response({'ok': True})

    @action(detail=True, methods=['get'], url_path='load-ko-bracket')
    def load_ko(self, request, pk=None):
        t = self._get_or_404(pk)
        return Response(get_full_state(t)['ko_phase'])

    @action(detail=True, methods=['post'], url_path='start-ko-next-round')
    def start_ko_next_round(self, request, pk=None):
        t = self._get_or_404(pk)
        next_main_round = request.data.get('next_main_round') or request.data.get('nextMainRound') or {}
        placement_round = request.data.get('placement_round') or request.data.get('placementRound') or {}
        rounds_to_materialize = []
        if isinstance(next_main_round, dict):
            rounds_to_materialize.append(next_main_round)
        if isinstance(placement_round, dict):
            rounds_to_materialize.append(placement_round)

        for round_payload in rounds_to_materialize:
            round_name = str(round_payload.get('round_name') or '')
            bracket_type = str(round_payload.get('bracket_type') or 'main')
            for idx, match_payload in enumerate(round_payload.get('matches') or []):
                team1_name = match_payload.get('team1')
                team2_name = match_payload.get('team2')
                if not team1_name or not team2_name:
                    continue
                team1 = Team.objects.filter(tournament=t, name=team1_name).first()
                team2 = Team.objects.filter(tournament=t, name=team2_name).first()
                if not (team1 and team2):
                    continue
                ko_match_index = match_payload.get('ko_match_index', idx)
                try:
                    ko_match_index = int(ko_match_index)
                except (TypeError, ValueError):
                    ko_match_index = idx

                match_obj, created = Match.objects.get_or_create(
                    tournament=t,
                    phase=Match.PHASE_KO,
                    ko_bracket_type=bracket_type,
                    ko_round=round_name,
                    ko_match_index=ko_match_index,
                    defaults={
                        'team1': team1,
                        'team2': team2,
                        'winner': None,
                        'cups_team1': 0,
                        'cups_team2': 0,
                        'cups_state_team1': [],
                        'cups_state_team2': [],
                        'team1_rerack_used': False,
                        'team2_rerack_used': False,
                        'is_overtime': False,
                        'status': 'pending',
                        'history_team1': [],
                        'history_team2': [],
                        'hit_history_team1': [],
                        'hit_history_team2': [],
                        'table': None,
                    },
                )
                if not created:
                    # Only remap unreleased matches that have not started yet.
                    if match_obj.winner or match_obj.status == 'done':
                        continue
                    if match_obj.cups_team1 or match_obj.cups_team2 or match_obj.is_overtime:
                        continue
                    match_obj.team1 = team1
                    match_obj.team2 = team2
                    match_obj.winner = None
                    match_obj.cups_team1 = 0
                    match_obj.cups_team2 = 0
                    match_obj.cups_state_team1 = []
                    match_obj.cups_state_team2 = []
                    match_obj.hit_history_team1 = []
                    match_obj.hit_history_team2 = []
                    match_obj.history_team1 = []
                    match_obj.history_team2 = []
                    match_obj.team1_rerack_used = False
                    match_obj.team2_rerack_used = False
                    match_obj.table = None
                    match_obj.status = 'pending'
                    match_obj.save(update_fields=[
                        'team1', 'team2', 'winner',
                        'cups_team1', 'cups_team2',
                        'cups_state_team1', 'cups_state_team2',
                        'hit_history_team1', 'hit_history_team2',
                        'history_team1', 'history_team2',
                        'team1_rerack_used', 'team2_rerack_used',
                        'table', 'status',
                    ])

        ko_state = get_full_state(t).get('ko_phase') or {}
        rounds = sort_ko_rounds(ko_state.get('rounds') or [])
        main_rounds = [r for r in rounds if (r.get('bracket_type') or 'main') != 'placement']
        placement_round_state = next(
            (r for r in rounds if (r.get('bracket_type') or 'main') == 'placement'),
            None,
        )
        if not main_rounds:
            return Response({'error': 'no ko rounds available'}, status=400)

        request_active_round_index = request.data.get(
            'active_main_round_index',
            request.data.get('activeMainRoundIndex'),
        )
        request_active_stage_kind = request.data.get(
            'active_stage_kind',
            request.data.get('activeStageKind'),
        )
        active_main_round_index = derive_active_ko_main_round_index(
            rounds,
            request_active_round_index
            if request_active_round_index is not None
            else ko_state.get('active_main_round_index', ko_state.get('activeMainRoundIndex')),
        )
        active_stage_kind = derive_active_ko_stage_kind(
            rounds,
            active_main_round_index,
            request_active_stage_kind
            if request_active_stage_kind is not None
            else ko_state.get('active_stage_kind', ko_state.get('activeStageKind')),
        )
        if active_main_round_index >= len(main_rounds):
            return Response({'error': 'active round out of range'}, status=400)

        if active_stage_kind == 'placement':
            if not placement_round_state:
                return Response({'error': 'placement round not available'}, status=400)
            if not is_ko_round_complete(placement_round_state):
                return Response({'error': 'current round is not complete'}, status=400)
            final_round = main_rounds[active_main_round_index]
            final_available = any(
                m.get('team1') and m.get('team2') and not m.get('winner')
                for m in (final_round.get('matches') or [])
            )
            if not final_available:
                return Response({'error': 'final not available'}, status=400)
            next_index = active_main_round_index
            next_stage_kind = 'main'
        else:
            current_round = main_rounds[active_main_round_index]
            if not is_ko_round_complete(current_round):
                return Response({'error': 'current round is not complete'}, status=400)

            if active_main_round_index >= len(main_rounds) - 1:
                return Response({'error': 'no next round available'}, status=400)

            next_index = active_main_round_index + 1
            next_stage_kind = 'main'
            if next_index == len(main_rounds) - 1 and placement_round_state:
                placement_available = any(
                    m.get('team1') and m.get('team2') and not m.get('winner')
                    for m in (placement_round_state.get('matches') or [])
                )
                if placement_available:
                    next_stage_kind = 'placement'

        set_ko_control_payload(
            t,
            {
                'active_main_round_index': next_index,
                'active_stage_kind': next_stage_kind,
            },
        )
        full_state = get_full_state(t)
        broadcast(t.id, 'ko_updated', full_state)
        return Response(full_state.get('ko_phase') or {})

    @action(detail=True, methods=['post'], url_path='ko-match')
    def ko_match(self, request, pk=None):
        """Single KO match update (round_index + match_index)."""
        t = self._get_or_404(pk)
        body = request.data
        raw_match_id = body.get('match_id')
        try:
            match_id = int(raw_match_id) if raw_match_id is not None else None
        except (TypeError, ValueError):
            match_id = None
        r_idx = int(body.get('round_index', -1))
        m_idx = int(body.get('match_index', -1))
        if match_id is None and (r_idx < 0 or m_idx < 0):
            return Response({'error': 'round_index and match_index required'}, status=400)

        match = None
        if match_id is not None:
            match = Match.objects.filter(
                tournament=t,
                phase=Match.PHASE_KO,
                id=match_id,
            ).first()

        if match is None:
            # Get distinct round keys in creation order
            rounds = list(
                Match.objects.filter(tournament=t, phase=Match.PHASE_KO)
                .values('ko_bracket_type', 'ko_round')
                .distinct()
                .order_by('id')
            )
            if r_idx >= len(rounds):
                return Response({'error': 'round index out of range'}, status=404)

            ri = rounds[r_idx]
            match = Match.objects.filter(
                tournament=t, phase=Match.PHASE_KO,
                ko_bracket_type=ri['ko_bracket_type'],
                ko_round=ri['ko_round'],
                ko_match_index=m_idx,
            ).first()
        if not match:
            return Response({'error': 'match not found'}, status=404)

        winner_name = body.get('winner')
        winner = Team.objects.filter(tournament=t, name=winner_name).first() if winner_name else None
        if winner and winner.id not in {match.team1_id, match.team2_id}:
            winner = None
            winner_name = None
        table_no_provided = any(
            key in body
            for key in ('table_no', 'tableNo', 'table_number', 'tableNumber')
        )
        raw_table_no = body.get('table_no', body.get('tableNo', body.get('table_number', body.get('tableNumber'))))
        try:
            table_no = int(raw_table_no) if raw_table_no is not None else None
        except (TypeError, ValueError):
            table_no = None
        table = match.table
        if table_no and table_no > 0:
            table, _ = Table.objects.get_or_create(
                tournament=t,
                name=f'Tisch {table_no}',
                defaults={'is_active': True},
            )
        elif table_no_provided:
            table = None
        match.winner = winner
        match.cups_team1 = int(body.get('cups_team1') or 0)
        match.cups_team2 = int(body.get('cups_team2') or 0)
        match.table = table
        match.status = 'done' if winner else 'pending'
        match.is_overtime = bool(body.get('is_overtime', match.is_overtime))
        cups_state1 = body.get('cups_state_team1')
        cups_state2 = body.get('cups_state_team2')
        if isinstance(cups_state1, list):
            match.cups_state_team1 = cups_state1
        if isinstance(cups_state2, list):
            match.cups_state_team2 = cups_state2
        match.save()

        _apply_match_event(t, match, body)

        full_state = get_full_state(t)

        result = {
            'id': match.id, 'team1': match.team1.name, 'team2': match.team2.name,
            'winner': winner_name, 'status': match.status,
            'ko_round': match.ko_round,
            'ko_bracket_type': match.ko_bracket_type,
            'ko_match_index': match.ko_match_index,
            'table_no': int(match.table.name.replace('Tisch ', '')) if match.table and str(match.table.name).startswith('Tisch ') else None,
            'cups_team1': match.cups_team1, 'cups_team2': match.cups_team2,
            'cups_state_team1': match.cups_state_team1, 'cups_state_team2': match.cups_state_team2,
            'is_overtime': match.is_overtime,
            'top_players': full_state['top_players'],
        }
        broadcast(t.id, 'ko_match_updated', result)
        broadcast(t.id, 'ko_updated', full_state)
        return Response(result)

    # ── Referee assignment ────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='referees', permission_classes=[IsOrga])
    def list_referees(self, request, pk=None):
        """Return all orga users that are NOT root — available as referees."""
        t = self._get_or_404(pk)
        referees = User.objects.filter(is_orga=True, is_root=False, is_staff=False).values(
            'id', 'username'
        )
        # Annotate with current active assignment for this tournament
        assignments = {
            a.referee_id: a
            for a in MatchAssignment.objects.filter(tournament=t, active=True)
                                            .select_related('match__team1', 'match__team2', 'match__table')
        }
        result = []
        for r in referees:
            a = assignments.get(r['id'])
            result.append({
                'id': r['id'],
                'username': r['username'],
                'assignment': _serialize_assignment(a) if a else None,
            })
        return Response(result)

    @action(detail=True, methods=['get'], url_path='my-assignment', permission_classes=[IsOrga])
    def my_assignment(self, request, pk=None):
        """Referee polls their own current assignment."""
        t = self._get_or_404(pk)
        a = MatchAssignment.objects.filter(
            tournament=t, referee=request.user, active=True
        ).select_related('match__team1', 'match__team2', 'match__table').first()
        return Response({'assignment': _serialize_assignment(a)})

    @action(detail=True, methods=['post'], url_path='assign-referee', permission_classes=[IsRoot])
    def assign_referee(self, request, pk=None):
        """
        Root assigns or unassigns a referee to a match.
        Body: { referee_id, match_id }   (match_id=null → unassign)
        """
        t = self._get_or_404(pk)
        referee_id = request.data.get('referee_id')
        match_id   = request.data.get('match_id')

        try:
            referee = User.objects.get(id=referee_id, is_orga=True)
        except User.DoesNotExist:
            return Response({'error': 'Referee not found'}, status=404)

        match = None
        if match_id:
            try:
                match = Match.objects.get(id=match_id, tournament=t)
            except Match.DoesNotExist:
                return Response({'error': 'Match not found'}, status=404)

        # Deactivate all previous assignments for this referee in this tournament
        MatchAssignment.objects.filter(tournament=t, referee=referee, active=True).update(active=False)

        assignment = None
        if match:
            assignment = MatchAssignment.objects.create(
                tournament=t,
                referee=referee,
                assigned_by=request.user,
                match=match,
                active=True,
            )

        # Log the action
        AdminAction.objects.create(
            tournament=t,
            match=match,
            user=request.user,
            action_type='assign_referee',
            payload={
                'referee_id': referee.id,
                'referee_username': referee.username,
                'match_id': match.id if match else None,
            },
        )

        # Push assignment update to referee's personal channel
        data = _serialize_assignment(assignment) if assignment else None
        broadcast_personal(referee.id, data)

        return Response({'ok': True, 'assignment': data})

    # ── Mobile access ─────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='mobile-state', permission_classes=[])
    def mobile_state(self, request, pk=None):
        """Public endpoint for mobile view — validates via ?token= query param."""
        mobile_token = request.query_params.get('token') or request.query_params.get('mobile_token')
        try:
            t = Tournament.objects.get(id=pk, mobile_access_token=mobile_token)
        except (Tournament.DoesNotExist, Exception):
            return Response({'error': 'Invalid token'}, status=403)
        return Response(get_full_state(t))

    # ── Health ────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_or_404(pk):
        try:
            return Tournament.objects.get(pk=pk)
        except Tournament.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Tournament not found')


# ── Private helpers ──────────────────────────────────────────────────────────

def _update_group_match_from_dict(tournament, gname: str, body: dict):
    """Find/create a group match and update its result. Returns serialized dict or None."""
    t1_name = body.get('team1')
    t2_name = body.get('team2')
    winner_name = body.get('winner')
    cups1 = int(body.get('cups_team1') or 0)
    cups2 = int(body.get('cups_team2') or 0)
    order_index = int(body.get('order_index') or 0)
    raw_id = body.get('id')
    try:
        match_id = int(raw_id) if raw_id is not None else None
    except (ValueError, TypeError):
        match_id = None

    cups_state1 = body.get('cups_state_team1')
    cups_state2 = body.get('cups_state_team2')
    hit_history1 = body.get('hit_history_team1')
    hit_history2 = body.get('hit_history_team2')
    history1 = body.get('history_team1')
    history2 = body.get('history_team2')
    rerack1 = bool(body.get('team1_rerack_used', False))
    rerack2 = bool(body.get('team2_rerack_used', False))
    is_overtime = bool(body.get('is_overtime', False))
    table_no_provided = any(
        key in body
        for key in ('table_no', 'tableNo', 'table_number', 'tableNumber')
    )
    raw_table_no = body.get('table_no', body.get('tableNo', body.get('table_number', body.get('tableNumber'))))
    try:
        table_no = int(raw_table_no) if raw_table_no is not None else None
    except (ValueError, TypeError):
        table_no = None

    try:
        t1 = Team.objects.get(tournament=tournament, name=t1_name)
        t2 = Team.objects.get(tournament=tournament, name=t2_name)
    except Team.DoesNotExist:
        return None

    winner = Team.objects.filter(tournament=tournament, name=winner_name).first() if winner_name else None
    match = None
    if match_id:
        try:
            match = Match.objects.get(id=match_id, tournament=tournament, phase=Match.PHASE_GROUP)
        except Match.DoesNotExist:
            pass

    if match is None:
        match = Match.objects.filter(
            tournament=tournament, phase=Match.PHASE_GROUP,
            group_name=gname, team1=t1, team2=t2,
        ).first()

    table = None
    if table_no and table_no > 0:
        table, _ = Table.objects.get_or_create(
            tournament=tournament,
            name=f'Tisch {table_no}',
            defaults={'is_active': True},
        )
    elif match and not winner and not table_no_provided:
        table = match.table

    if match:
        match.cups_team1 = cups1
        match.cups_team2 = cups2
        match.winner = winner
        match.status = 'done' if winner else 'pending'
        if isinstance(cups_state1, list):
            match.cups_state_team1 = cups_state1
        if isinstance(cups_state2, list):
            match.cups_state_team2 = cups_state2
        if isinstance(hit_history1, list):
            match.hit_history_team1 = hit_history1
        if isinstance(hit_history2, list):
            match.hit_history_team2 = hit_history2

        # New history fields
        match.history_team1 = history1 if isinstance(history1, list) else (match.history_team1 or [])
        match.history_team2 = history2 if isinstance(history2, list) else (match.history_team2 or [])

        match.team1_rerack_used = rerack1
        match.team2_rerack_used = rerack2
        match.is_overtime = is_overtime
        match.table = None if winner else table
        match.save()
    else:
        match = Match.objects.create(
            tournament=tournament, phase=Match.PHASE_GROUP, group_name=gname,
            team1=t1, team2=t2, winner=winner,
            cups_team1=cups1, cups_team2=cups2, order_index=order_index,
            cups_state_team1=cups_state1 if isinstance(cups_state1, list) else [],
            cups_state_team2=cups_state2 if isinstance(cups_state2, list) else [],
            hit_history_team1=hit_history1 if isinstance(hit_history1, list) else [],
            hit_history_team2=hit_history2 if isinstance(hit_history2, list) else [],
            history_team1=history1 if isinstance(history1, list) else [],
            history_team2=history2 if isinstance(history2, list) else [],
            team1_rerack_used=rerack1,
            team2_rerack_used=rerack2,
            is_overtime=is_overtime,
            table=None if winner else table,
            status='done' if winner else 'pending',
        )

    return {
        'id': match.id, 'group_name': gname,
        'team1': t1_name, 'team2': t2_name, 'winner': winner_name,
        'cups_team1': cups1, 'cups_team2': cups2, 'order_index': order_index,
        'cups_state_team1': match.cups_state_team1,
        'cups_state_team2': match.cups_state_team2,
        'hit_history_team1': match.hit_history_team1,
        'hit_history_team2': match.hit_history_team2,
        'history_team1': match.history_team1,
        'history_team2': match.history_team2,
        'team1_rerack_used': match.team1_rerack_used,
        'team2_rerack_used': match.team2_rerack_used,
        'is_overtime': match.is_overtime,
        'table_no': int(match.table.name.replace('Tisch ', '')) if match.table and str(match.table.name).startswith('Tisch ') else None,
    }

def _parse_positive_int(value, default=0):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _record_cup_hits(tournament, match, shooter_name: str, shooter_team_name: str, hit_count: int = 1):
    if not match or not shooter_name or not shooter_team_name:
        return

    hit_count = _parse_positive_int(hit_count, default=1)
    if hit_count <= 0:
        return

    try:
        player, _ = Player.objects.get_or_create(name=shooter_name)
        team = Team.objects.get(tournament=tournament, name=shooter_team_name)
    except Team.DoesNotExist:
        return

    CupHit.objects.bulk_create([
        CupHit(match=match, player=player, team=team)
        for _ in range(hit_count)
    ])
    player.total_cups_hit = CupHit.objects.filter(player=player).count()
    player.save(update_fields=['total_cups_hit'])


def _undo_cup_hits(match, restored_team_key: str, undo_count: int = 1):
    if not match:
        return

    undo_count = _parse_positive_int(undo_count, default=1)
    if undo_count <= 0:
        return

    shooter_team_key = 'team2' if restored_team_key == 'team1' else 'team1'
    shooter_team = match.team1 if shooter_team_key == 'team1' else match.team2
    if not shooter_team:
        return

    hits = list(CupHit.objects.filter(match=match, team=shooter_team).order_by('-id')[:undo_count])
    for hit in hits:
        player = hit.player
        hit.delete()
        player.total_cups_hit = CupHit.objects.filter(player=player).count()
        player.save(update_fields=['total_cups_hit'])


def _normalize_credit_allocations(raw_allocations):
    if not isinstance(raw_allocations, list):
        return []

    allocations = []
    for entry in raw_allocations:
        if not isinstance(entry, dict):
            continue
        player_name = str(entry.get('player_name') or entry.get('player') or '').strip()
        count = _parse_positive_int(entry.get('count'), default=0)
        if player_name and count > 0:
            allocations.append((player_name, count))
    return allocations


def _ko_match_has_started_db(match):
    if not match:
        return False
    if match.winner_id or match.status == 'done':
        return True
    if match.cups_team1 or match.cups_team2 or match.is_overtime:
        return True
    if match.table_id:
        return True
    return match.cup_hits.exists()


def _sync_player_hit_totals(player_ids):
    if not player_ids:
        return
    for player in Player.objects.filter(id__in=set(player_ids)):
        player.total_cups_hit = CupHit.objects.filter(player=player).count()
        player.save(update_fields=['total_cups_hit'])


def _log_action(tournament, match, user, action_type: str, payload: dict):
    """Write a server-side AdminAction log entry (best-effort, never raises)."""
    try:
        AdminAction.objects.create(
            tournament=tournament,
            match=match,
            user=user,
            action_type=action_type,
            payload=payload,
        )
    except Exception:
        pass


def _apply_match_event(tournament, match, body: dict, user=None):
    event_data = body.get('event_data') or {}
    action_type = str(event_data.get('action_type') or '').strip()
    if not action_type or not match:
        return

    # Log every action server-side
    if user and action_type:
        _log_action(tournament, match, user, action_type, {
            'event_data': event_data,
            'match_id': match.id,
        })

    shooter_name = (body.get('shooter') or event_data.get('player_name') or '').strip()
    shooter_team_name = (body.get('shooter_team') or event_data.get('team_name') or '').strip()

    if action_type == 'overtime_credit':
        allocations = _normalize_credit_allocations(event_data.get('credit_allocations'))
        if allocations and shooter_team_name:
            for player_name, hit_count in allocations:
                _record_cup_hits(tournament, match, player_name, shooter_team_name, hit_count)
            return

    if action_type in {'cup_hit', 'overtime_credit'}:
        hit_count = _parse_positive_int(event_data.get('credit_count'), default=1)
        _record_cup_hits(tournament, match, shooter_name, shooter_team_name, hit_count)
        return

    if action_type == 'undo':
        restored_team_key = str(event_data.get('team_key') or '').strip()
        if restored_team_key in {'team1', 'team2'}:
            undo_count = _parse_positive_int(event_data.get('undo_count'), default=1)
            _undo_cup_hits(match, restored_team_key, undo_count)


def health_check(request):
    return JsonResponse({'ok': True})
