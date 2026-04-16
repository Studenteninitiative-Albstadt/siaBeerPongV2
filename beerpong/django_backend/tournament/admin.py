from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Tournament, Team, Match, Player, Table, Tiebreak


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Bier Pong Rollen', {'fields': ('is_orga', 'is_liveview')}),
    )
    list_display = ['username', 'email', 'is_orga', 'is_liveview', 'is_staff']


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode', 'participant_count', 'status', 'mobile_access_token', 'created_at']
    readonly_fields = ['mobile_access_token', 'created_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament', 'group_name']
    list_filter = ['tournament']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'tournament', 'phase', 'group_name', 'team1', 'team2', 'winner', 'status']
    list_filter = ['tournament', 'phase']


admin.site.register(Player)
admin.site.register(Table)
admin.site.register(Tiebreak)
