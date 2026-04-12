#!/bin/sh
set -e

if [ "${DB_ENGINE}" = "django.db.backends.postgresql" ]; then
  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
  until nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn cipriano.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
