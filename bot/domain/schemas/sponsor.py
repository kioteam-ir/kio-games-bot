from pydantic import BaseModel, ConfigDict, HttpUrl


class SponsorRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    link: HttpUrl | str
