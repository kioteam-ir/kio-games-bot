# 4fall-game-tgbot

Telegram bot and Django admin stack, orchestrated with Docker Compose.

## Quick start

1. Copy environment files and fill in secrets (see `.env.example` and `src/.env.dev`).
2. Start the stack:

```bash
docker compose up --build
```

3. Open `http://localhost` (Django admin is proxied through Nginx).

## Nginx (reverse proxy)

Configuration lives under `docker/nginx/`:

- `templates/default.conf.template` — rendered at container start via the official Nginx image (`envsubst`).
- `snippets/proxy_params.conf` — shared proxy headers for Django.

Only the `nginx` service publishes port 80 to the host. Django, Postgres, and the bot run on the internal `backend` network.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NGINX_SERVER_NAME` | `_` | `server_name` directive (use your domain or IP in production) |
| `NGINX_HTTP_PORT` | `80` | Host port mapped to Nginx |

Example for production:

```bash
NGINX_SERVER_NAME=example.com NGINX_HTTP_PORT=80 docker compose up -d
```

Static and media files are served by Nginx from shared volumes mounted at `/bot/src/static` and `/bot/src/media` (same paths as Django `STATIC_ROOT` / `MEDIA_ROOT`).

## Services

| Service | Role |
|---------|------|
| `db` | PostgreSQL |
| `django` | Gunicorn + Django admin |
| `nginx` | Reverse proxy and static/media |
| `bot` | Telegram bot process |
