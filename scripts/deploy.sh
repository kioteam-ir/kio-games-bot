#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)/../"
REMOTE="${1:-pacman}"
REMOTE_DIR="${2:-/root/4fall-game-tgbot}"

rsync -avz --delete \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '.cursor/' \
  --exclude '.mypy_cache/' \
  --exclude '.pytest_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '*.session' \
  --exclude '*.session-shm' \
  --exclude '*.session-wal' \
  "${ROOT_DIR}/" \
  "${REMOTE}:${REMOTE_DIR}/"

ssh "${REMOTE}" "bash -s" <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"

docker compose up -d db
for i in \$(seq 1 60); do
  docker compose exec -T db pg_isready -U postgres </dev/null >/dev/null 2>&1 && break
  sleep 2
done

if ! docker compose exec -T db psql -U postgres -d 4fall_bot -tAc "SELECT 1 FROM app_user LIMIT 1" </dev/null >/dev/null 2>&1; then
  docker compose exec -T db psql -U postgres -d 4fall_bot -v ON_ERROR_STOP=1 < kio-bot.sql
fi

DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose up -d --build
docker compose up -d --force-recreate --no-deps bot
docker compose ps
EOF
