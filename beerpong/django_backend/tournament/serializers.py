from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Tournament, Team, Match


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Embed role flags into the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_orga'] = user.is_orga or user.is_staff
        token['is_liveview'] = user.is_liveview
        token['is_root'] = user.is_root or user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['is_orga'] = self.user.is_orga or self.user.is_staff
        data['is_liveview'] = self.user.is_liveview
        data['is_root'] = self.user.is_root or self.user.is_staff
        return data


class TournamentSerializer(serializers.ModelSerializer):
    # camelCase aliases for frontend compatibility
    currentPhase = serializers.CharField(source='status', read_only=True)
    current_phase = serializers.CharField(source='status', read_only=True)
    participantCount = serializers.IntegerField(source='participant_count', read_only=True)
    cupsPerGame = serializers.IntegerField(source='cups_per_game', read_only=True)
    finaleWith10Cups = serializers.BooleanField(source='finale_with_10_cups', read_only=True)
    tableCount = serializers.IntegerField(source='table_count', required=False)
    mobileAccessToken = serializers.UUIDField(source='mobile_access_token', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'mode', 'participant_count', 'cups_per_game',
            'finale_with_10_cups', 'table_count', 'tableCount', 'status', 'mobile_access_token', 'created_at',
            'currentPhase', 'current_phase', 'participantCount', 'cupsPerGame',
            'finaleWith10Cups', 'mobileAccessToken', 'createdAt',
        ]
        read_only_fields = ['id', 'created_at', 'mobile_access_token']
