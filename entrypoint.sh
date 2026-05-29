#!/bin/sh

set -e

echo "Waiting for Postgres..."
until nc -z db 5432; do
  sleep 1
done
echo "Postgres is up!"

compile_locales() {
    echo "Compiling locales..."
    poetry run pybabel compile -d bot/locales -D bot
}

if [ "$1" = "api" ]; then
    compile_locales
    echo "Starting API with Uvicorn..."
    exec poetry run api

elif [ "$1" = "bot" ]; then
    compile_locales
    echo "Starting Bot..."
    exec poetry run bot

else
    exec "$@"
fi
