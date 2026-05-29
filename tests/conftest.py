from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime

import pytest
from aiogram.utils.i18n import I18n

# BotConfig loads at import time; tests must not require a real .env or secrets.
os.environ.setdefault("TOKEN", "ci-test-token")

import bot.i18n_bootstrap  # noqa: F401
from bot.config.i18n import I18nConfigClass
from bot.domain.schemas.user import UserRecord
from bot.infrastructure.i18n.translator import Translator


@pytest.fixture(scope="session", autouse=True)
def compiled_locales() -> None:
    subprocess.run(["poetry", "run", "poe", "compile"], check=True)


@pytest.fixture
def translator() -> Translator:
    i18n = I18n.get_current()
    assert i18n is not None
    return Translator(I18nConfigClass(), i18n)


@pytest.fixture
def user_record() -> UserRecord:
    return UserRecord(
        id=1,
        is_banned=False,
        is_superuser=False,
        lang_code="en",
        joined_time=datetime.now(tz=UTC),
        username="alice",
        name="Alice",
    )
