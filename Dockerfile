# syntax=docker/dockerfile:1

FROM python:3.14-alpine AS builder

ENV POETRY_VERSION=2.3.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false

RUN apk add --no-cache build-base libffi-dev openssl-dev postgresql-dev \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /bot
COPY pyproject.toml poetry.lock README.md ./
COPY bot ./bot
COPY api ./api
COPY tools ./tools
RUN poetry install --only main \
    && poetry run pybabel compile -d bot/locales -D bot

FROM python:3.14-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false

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

# Remove the virtual environment created by Poetry in the builder stage, as we have already copied the installed packages to the runtime stage.
RUN rm -rf .venv

RUN chmod +x /bot/entrypoint.sh \
    && sed -i 's/\r$//g' /bot/entrypoint.sh

ENTRYPOINT ["/bot/entrypoint.sh"]
