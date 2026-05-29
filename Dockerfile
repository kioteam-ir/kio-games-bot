# syntax=docker/dockerfile:1

FROM python:3.13-alpine AS builder

ENV POETRY_VERSION=2.3.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache build-base libffi-dev openssl-dev postgresql-dev \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /bot
COPY pyproject.toml poetry.lock README.md ./
COPY bot ./bot
COPY api ./api
RUN poetry install --only main

FROM python:3.13-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN apk add --no-cache netcat-openbsd libpq \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /bot

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY pyproject.toml poetry.lock README.md ./
COPY bot ./bot
COPY api ./api
COPY entrypoint.sh /bot/entrypoint.sh
COPY . /bot/

RUN chmod +x /bot/entrypoint.sh \
    && sed -i 's/\r$//g' /bot/entrypoint.sh

ENTRYPOINT ["/bot/entrypoint.sh"]
