from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User, Tournament


def get_user_from_token(token_str: str):
    """Validate a JWT access token and return the User, or None."""
    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token['user_id'])
    except (TokenError, User.DoesNotExist, KeyError, Exception):
        return None


def get_tournament_for_mobile(tournament_id: int, mobile_token: str):
    """Return Tournament if mobile_token matches, else None."""
    try:
        return Tournament.objects.get(id=tournament_id, mobile_access_token=mobile_token)
    except (Tournament.DoesNotExist, Exception):
        return None
