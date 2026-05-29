#!/bin/sh

set -e

echo "Waiting for Postgres..."
until nc -z db 5432; do
  sleep 1
done
echo "Postgres is up!"

if [ "$1" = "api" ]; then
    echo "Compiling locales..."
    poetry run poe compile
    echo "Starting API with Uvicorn..."
    exec poetry run api

elif [ "$1" = "bot" ]; then
    echo "Compiling locales..."
    poetry run poe compile
    echo "Starting Bot..."
    exec poetry run bot

else
    exec "$@"
fi
