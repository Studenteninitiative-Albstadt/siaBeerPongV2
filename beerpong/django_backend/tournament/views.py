from __future__ import annotations

from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Tournament, Team, Match, Player, CupHit, Table, Tiebreak
from .permissions import IsOrga, IsOrgaOrLiveview
from .serializers import TournamentSerializer, CustomTokenObtainPairSerializer
from .services import compute_structure, generate_groups, compute_standings, get_full_state


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


# ── Tournament ViewSet ───────────────────────────────────────────────────────

class TournamentViewSet(ViewSet):

    def get_permissions(self):
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
        We use the team names embedded in the payload to generate
        (or re-generate) the groups and matches in the DB.
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

        if team_names:
            generate_groups(t, team_names)

        # Also persist raw match results that came with the payload
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

        # Optional: record which player scored a cup
        event_data = body.get('event_data') or {}
        action_type = event_data.get('action_type')
        shooter_name = (body.get('shooter') or '').strip()
        shooter_team_name = (body.get('shooter_team') or '').strip()
        match_id = result.get('id')

        if action_type == 'cup_hit' and shooter_name and shooter_team_name and match_id:
            try:
                player, _ = Player.objects.get_or_create(name=shooter_name)
                team = Team.objects.get(tournament=t, name=shooter_team_name)
                match = Match.objects.get(id=match_id)
                CupHit.objects.create(match=match, player=player, team=team)
                player.total_cups_hit += 1
                player.save(update_fields=['total_cups_hit'])
            except (Team.DoesNotExist, Match.DoesNotExist):
                pass
        elif action_type == 'undo' and match_id:
            try:
                # team_key in event_data identifies whose action is undone
                # but we need to know WHICH player hit the cup we're undoing.
                # We find the last CupHit for this match and the team that hit (the shooter team).
                # team_key in event_data is the team whose cup is RESTORED (the hit was against them).
                # So the shooter was the OTHER team.
                restored_team_key = event_data.get('team_key') # 'team1' or 'team2'
                shooter_team_key = 'team2' if restored_team_key == 'team1' else 'team1'

                # Get the actual Team object for the shooter
                match = Match.objects.get(id=match_id)
                shooter_team = match.team1 if shooter_team_key == 'team1' else match.team2

                last_hit = CupHit.objects.filter(match=match, team=shooter_team).order_by('-id').first()
                if last_hit:
                    player = last_hit.player
                    player.total_cups_hit = max(0, player.total_cups_hit - 1)
                    player.save(update_fields=['total_cups_hit'])
                    last_hit.delete()
            except Exception:
                pass

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
        Match.objects.filter(tournament=t, phase=Match.PHASE_KO).delete()
        Tiebreak.objects.filter(tournament=t, mode='ko_preview').delete()

        for round_data in rounds:
            round_name = str(round_data.get('round_name') or 'Round')
            bracket_type = str(round_data.get('bracket_type') or 'main')
            for idx, m in enumerate(round_data.get('matches') or []):
                t1 = Team.objects.filter(tournament=t, name=m.get('team1')).first()
                t2 = Team.objects.filter(tournament=t, name=m.get('team2')).first()
                if not (t1 and t2):
                    continue
                winner = Team.objects.filter(tournament=t, name=m.get('winner')).first()
                Match.objects.create(
                    tournament=t, phase=Match.PHASE_KO,
                    team1=t1, team2=t2, winner=winner,
                    cups_team1=int(m.get('cups_team1') or 0),
                    cups_team2=int(m.get('cups_team2') or 0),
                    ko_round=round_name, ko_bracket_type=bracket_type, ko_match_index=idx,
                    status='done' if winner else 'pending',
                    history_team1=[], history_team2=[]
                )

        t.status = Tournament.STATUS_KO
        t.save()
        broadcast(t.id, 'ko_updated', get_full_state(t))
        return Response({'ok': True})

    @action(detail=True, methods=['get'], url_path='load-ko-bracket')
    def load_ko(self, request, pk=None):
        t = self._get_or_404(pk)
        return Response(get_full_state(t)['ko_phase'])

    @action(detail=True, methods=['post'], url_path='ko-match')
    def ko_match(self, request, pk=None):
        """Single KO match update (round_index + match_index)."""
        t = self._get_or_404(pk)
        body = request.data
        r_idx = int(body.get('round_index', -1))
        m_idx = int(body.get('match_index', -1))
        if r_idx < 0 or m_idx < 0:
            return Response({'error': 'round_index and match_index required'}, status=400)

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
        match.winner = winner
        match.cups_team1 = int(body.get('cups_team1') or 0)
        match.cups_team2 = int(body.get('cups_team2') or 0)
        match.status = 'done' if winner else 'pending'
        match.save()

        result = {
            'id': match.id, 'team1': match.team1.name, 'team2': match.team2.name,
            'winner': winner_name, 'cups_team1': match.cups_team1, 'cups_team2': match.cups_team2,
        }
        broadcast(t.id, 'ko_match_updated', result)
        return Response(result)

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


def health_check(request):
    return JsonResponse({'ok': True})
