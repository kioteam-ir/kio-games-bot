#!/bin/sh

set -e

echo "Waiting for Postgres..."
until nc -z db 5432; do
  sleep 1
done
echo "Postgres is up!"

if [ "$1" = "django" ]; then
    echo "Apply makemigrations"
    python src/manage.py makemigrations --noinput
    echo "Applying migrations..."
    python src/manage.py migrate --noinput
    echo "run collectstatic"
    python src/manage.py collectstatic --noinput
    echo "Starting Django with Gunicorn..."
    exec gunicorn --chdir src config.wsgi:application --bind 0.0.0.0:8000 --workers 3

elif [ "$1" = "bot" ]; then
    echo "Starting Bot..."
    exec poetry run bot

else
    exec "$@"
fi
