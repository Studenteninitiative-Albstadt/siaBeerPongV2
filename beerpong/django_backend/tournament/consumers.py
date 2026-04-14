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
    - Admin/Liveview: ?token=<JWT>
    - Mobile:         ?mobile_token=<UUID>
    """

    def connect(self):
        self.tournament_id = self.scope['url_route']['kwargs']['tournament_id']
        self.group_name = f'tournament_{self.tournament_id}'

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

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

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
