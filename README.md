# Kio Games Platform

Multi-game Telegram bot and REST API, built with **aiogram 3**, **FastAPI**, **SQLAlchemy**, and **Redis**.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design, session flow, and extension points.

## Quick start

1. Copy environment files and fill in secrets (see `.env.example` and `config/.env.dev`).
2. Start the stack:

```bash
docker compose up --build
```

3. Open `http://localhost` (FastAPI admin and game API are proxied through Nginx).

## Services

| Service | Role |
|---------|------|
| `db` | PostgreSQL |
| `redis` | Game session storage |
| `api` | FastAPI — admin routes + `/games/*` REST API |
| `nginx` | Reverse proxy |
| `bot` | Telegram bot (aiogram polling) |

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_BACKEND` | `redis` | `redis` or `memory` (use `memory` for local dev without Redis) |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `GAME_SESSION_TIMEOUT` | `300` | Inactivity timeout (seconds) for active games |
| `NGINX_SERVER_NAME` | `_` | Nginx `server_name` |
| `NGINX_HTTP_PORT` | `80` | Host port mapped to Nginx |

## Development

```bash
poetry install
poetry run pytest
poetry run poe lint
poetry run poe typecheck
```

Run the bot locally (requires Postgres + Redis or `SESSION_BACKEND=memory`):

```bash
poetry run bot
```

Run the API:

```bash
poetry run api
```

## Deploy (remote server)

```bash
./scripts/deploy.sh pacman /root/4fall-game-tgbot
```

On hosts with Docker Compose \< 2.29, the script uses `DOCKER_BUILDKIT=0` automatically.

First deploy imports `kio-bot.sql` into Postgres if the database is empty.
