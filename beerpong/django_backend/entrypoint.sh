#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating default users..."
python - <<'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from tournament.models import User
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@localhost', 'admin')
    u.is_orga = True
    u.save()
    print('Created admin user (pw: admin, role: orga)')
if not User.objects.filter(username='live').exists():
    u = User.objects.create_user('live', 'live@localhost', 'live')
    u.is_liveview = True
    u.save()
    print('Created live user (pw: live, role: liveview)')
PYEOF

echo "Starting Daphne ASGI server..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
