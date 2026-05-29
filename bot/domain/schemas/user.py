from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    is_banned: bool
    is_superuser: bool
    lang_code: str
    joined_time: datetime | None = None
    username: str | None = None
    name: str | None = None
