#!/bin/sh
set -eu

required_vars="
APP_DOMAIN
APP_HTTP_PORT
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS
DJANGO_CORS_ALLOWED_ORIGINS
DJANGO_CSRF_TRUSTED_ORIGINS
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_PASSWORD
LIVEVIEW_USERNAME
LIVEVIEW_PASSWORD
"

placeholder_guard_vars="
DJANGO_SECRET_KEY
POSTGRES_PASSWORD
DJANGO_SUPERUSER_PASSWORD
LIVEVIEW_PASSWORD
"

for var_name in $required_vars; do
  eval "value=\${$var_name:-}"
  if [ -z "$value" ]; then
    echo "Refusing to start: required environment variable '$var_name' is empty."
    exit 1
  fi
done

for var_name in $placeholder_guard_vars; do
  eval "value=\${$var_name:-}"
  case "$value" in
    *PLEASECHANGEME*)
      echo "Refusing to start: '$var_name' still contains PLEASECHANGEME."
      exit 1
      ;;
  esac
done

echo "Environment check passed."
