import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_orga = models.BooleanField(default=False)
    is_liveview = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Benutzer'
        verbose_name_plural = 'Benutzer'


class Tournament(models.Model):
    STATUS_GROUP = 'group'
    STATUS_PLAYIN = 'playin'
    STATUS_KO = 'ko'
    STATUS_FINISHED = 'finished'

    name = models.CharField(max_length=100, default='Neues Turnier')
    mode = models.CharField(max_length=20, default='groups')
    participant_count = models.IntegerField(default=8)
    cups_per_game = models.IntegerField(default=6)
    finale_with_10_cups = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default=STATUS_GROUP)
    mobile_access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} (#{self.id})'


class Player(models.Model):
    name = models.CharField(max_length=100)
    total_cups_hit = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Team(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    player1 = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams_p1'
    )
    player2 = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams_p2'
    )
    group_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = [['tournament', 'name']]

    def __str__(self):
        return f'{self.name} ({self.tournament.name})'


class Table(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    PHASE_GROUP = 'group'
    PHASE_PLAYIN = 'playin'
    PHASE_KO = 'ko'

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    phase = models.CharField(max_length=20, default=PHASE_GROUP)
    group_name = models.CharField(max_length=50, blank=True, null=True)

    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_t1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_t2')
    winner = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won'
    )

    cups_team1 = models.IntegerField(default=0)
    cups_team2 = models.IntegerField(default=0)

    # Per-cup state: list of booleans (True = standing, False = hit)
    cups_state_team1 = models.JSONField(default=list)
    cups_state_team2 = models.JSONField(default=list)

    # Hit history for undo (ordered list of cup indices)
    hit_history_team1 = models.JSONField(default=list)
    hit_history_team2 = models.JSONField(default=list)

    # Re-rack tracking
    team1_rerack_used = models.BooleanField(default=False)
    team2_rerack_used = models.BooleanField(default=False)

    table = models.ForeignKey(
        Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches'
    )
    status = models.CharField(max_length=20, default='pending')
    order_index = models.IntegerField(default=0)

    # KO-specific fields
    ko_round = models.CharField(max_length=50, blank=True, null=True)
    ko_bracket_type = models.CharField(max_length=20, blank=True, null=True)
    ko_match_index = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['phase', 'group_name', 'order_index']

    def __str__(self):
        return f'{self.team1} vs {self.team2} ({self.phase})'


class Tiebreak(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='tiebreaks')
    group_name = models.CharField(max_length=50)
    mode = models.CharField(max_length=20)  # cups, rage, rage4
    payload = models.JSONField(default=dict)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f'Tiebreak {self.group_name} ({self.mode})'


class CupHit(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='cup_hits')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cup_hits')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='cup_hits')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.player.name} → {self.match}'
