from pydantic import BaseModel, ConfigDict, Field


class TelegramPlayer(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    first_name: str = Field(default="Player")
    username: str | None = None
    lang_code: str | None = None
