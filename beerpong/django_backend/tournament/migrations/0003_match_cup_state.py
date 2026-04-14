from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0002_cup_hit'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='cups_state_team1',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='match',
            name='cups_state_team2',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='match',
            name='hit_history_team1',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='match',
            name='hit_history_team2',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='match',
            name='team1_rerack_used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='team2_rerack_used',
            field=models.BooleanField(default=False),
        ),
    ]
