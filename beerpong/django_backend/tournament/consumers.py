import json
from urllib.parse import parse_qs
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from .auth import get_user_from_token, get_tournament_for_mobile
from .models import Tournament
from .services import get_full_state


class TournamentConsumer(WebsocketConsumer):
    """
    WebSocket consumer for real-time tournament updates.

    Auth:
    - Admin/Liveview/Referee: ?token=<JWT>
    - Mobile:                 ?mobile_token=<UUID>

    Groups joined:
    - tournament_{id}         — broadcast channel for all tournament clients
    - user_{user_id}          — personal channel for push messages (e.g. referee assignments)
    """

    def connect(self):
        self.tournament_id = self.scope['url_route']['kwargs']['tournament_id']
        self.group_name = f'tournament_{self.tournament_id}'
        self.personal_group = None

        params = parse_qs(self.scope.get('query_string', b'').decode())
        token = (params.get('token') or [''])[0]
        mobile_token = (params.get('mobile_token') or [''])[0]

        self.authed_user = None
        self.is_mobile = False

        if token:
            self.authed_user = get_user_from_token(token)
        elif mobile_token:
            t = get_tournament_for_mobile(self.tournament_id, mobile_token)
            if t:
                self.is_mobile = True

        if not self.authed_user and not self.is_mobile:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        # Join personal channel so root can push assignment updates to this user
        if self.authed_user:
            self.personal_group = f'user_{self.authed_user.id}'
            async_to_sync(self.channel_layer.group_add)(self.personal_group, self.channel_name)

        self.accept()

        # Send full initial state on connect
        try:
            tournament = Tournament.objects.get(id=self.tournament_id)
            self.send(text_data=json.dumps({
                'type': 'state.init',
                'data': get_full_state(tournament),
            }))
        except Tournament.DoesNotExist:
            pass

        # If this is a referee (is_orga but not is_root), send their current assignment immediately
        if self.authed_user and self.authed_user.is_orga and not self.authed_user.is_root:
            self._send_assignment()

    def _send_assignment(self):
        """Push current active assignment to a referee."""
        from .models import MatchAssignment
        assignment = MatchAssignment.objects.filter(
            tournament_id=self.tournament_id,
            referee=self.authed_user,
            active=True,
        ).select_related('match__team1', 'match__team2', 'match__table').first()

        if assignment and assignment.match:
            m = assignment.match
            self.send(text_data=json.dumps({
                'type': 'assignment.updated',
                'data': _serialize_assignment(assignment),
            }))
        else:
            self.send(text_data=json.dumps({
                'type': 'assignment.updated',
                'data': None,
            }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        if self.personal_group:
            async_to_sync(self.channel_layer.group_discard)(self.personal_group, self.channel_name)

    def receive(self, text_data):
        # Only orga users may send messages; currently all mutations go through REST
        pass

    # Called by channel layer when broadcast() is triggered from a view
    def tournament_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'state.update',
            'event': event.get('event'),
            'data': event.get('data'),
        }))

    # Called when root pushes assignment update to personal channel
    def assignment_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'assignment.updated',
            'data': event.get('data'),
        }))


def _serialize_assignment(assignment):
    if not assignment:
        return None
    m = assignment.match
    if not m:
        return None
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
