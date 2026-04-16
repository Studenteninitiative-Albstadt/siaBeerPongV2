#!/bin/sh
set -eu

/opt/deploy-scripts/verify_required_env.sh

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Ensuring bootstrap users..."
python - <<'PYEOF'
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from tournament.models import User


def ensure_admin():
    username = os.environ["DJANGO_SUPERUSER_USERNAME"]
    email = os.environ["DJANGO_SUPERUSER_EMAIL"]
    password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

    user, _ = User.objects.get_or_create(username=username)
    user.email = email
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.is_orga = True
    user.is_liveview = False
    user.is_root = True
    user.set_password(password)
    user.save()


def ensure_liveview():
    username = os.environ["LIVEVIEW_USERNAME"]
    password = os.environ["LIVEVIEW_PASSWORD"]

    user, _ = User.objects.get_or_create(username=username)
    user.email = f"{username}@{os.environ['APP_DOMAIN']}"
    user.is_active = True
    user.is_staff = False
    user.is_superuser = False
    user.is_orga = False
    user.is_liveview = True
    user.is_root = False
    user.set_password(password)
    user.save()


ensure_admin()
ensure_liveview()
print("Bootstrap users ensured.")
PYEOF

echo "Starting Gunicorn ASGI server..."
exec gunicorn config.asgi:application \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-90}" \
  --keep-alive "${GUNICORN_KEEPALIVE:-15}" \
  --access-logfile - \
  --error-logfile -
