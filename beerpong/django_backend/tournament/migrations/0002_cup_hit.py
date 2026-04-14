import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CupHit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cup_hits', to='tournament.match')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cup_hits', to='tournament.player')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cup_hits', to='tournament.team')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
