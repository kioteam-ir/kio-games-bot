from __future__ import annotations

from asgiref.sync import sync_to_async

from bot.domain.repositories import SponsorRepository
from bot.domain.schemas.sponsor import SponsorRecord
from bot.infrastructure.persistence.django_setup import setup_django


class DjangoSponsorRepository(SponsorRepository):
    def __init__(self) -> None:
        setup_django()

    async def list_active(self) -> list[SponsorRecord]:
        from app.models import Sponser

        rows = await sync_to_async(Sponser.get_all)()
        return [SponsorRecord.model_validate(row) for row in rows]
