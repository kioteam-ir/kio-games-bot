from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from bot.config.i18n import I18nConfigClass
from bot.domain.schemas.user import UserRecord
from bot.infrastructure.i18n.texts import TextsService


@pytest.fixture
def texts_service() -> TextsService:
    config = I18nConfigClass(texts_path=Path("src/texts.json"))
    return TextsService(config)


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
