from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.api import ApiConfigClass
from api.infrastructure.database.models import AppSponser, AppUser
from api.presentation.dependencies import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    joined_time: datetime
    is_superuser: bool
    is_banned: bool
    lang_code: str


class SponsorAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    link: str
    joined_memebers: int
    is_active: bool


def verify_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
    api_config: ApiConfigClass = Depends(ApiConfigClass),
) -> None:
    if x_admin_token not in api_config.valid_admin_tokens():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    _: None = Depends(verify_admin_token),
    session: AsyncSession = Depends(get_session),
) -> list[UserAdminResponse]:
    result = await session.execute(select(AppUser).order_by(AppUser.joined_time.desc()))
    users = result.scalars().all()
    return [UserAdminResponse.model_validate(user) for user in users]


@router.get("/sponsors", response_model=list[SponsorAdminResponse])
async def list_sponsors(
    _: None = Depends(verify_admin_token),
    session: AsyncSession = Depends(get_session),
) -> list[SponsorAdminResponse]:
    result = await session.execute(select(AppSponser).order_by(AppSponser.created_time.desc()))
    sponsors = result.scalars().all()
    return [SponsorAdminResponse.model_validate(sponsor) for sponsor in sponsors]
