from pydantic import Field, field_validator

from api.config.base import BaseConfig


class ApiConfigClass(BaseConfig):
    api_admin_token: str | None = Field(default=None, alias="API_ADMIN_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return [262253630]
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return [int(item) for item in value]
        msg = f"Unsupported ADMIN_IDS value: {value!r}"
        raise TypeError(msg)

    def valid_admin_tokens(self) -> set[str]:
        tokens = {str(admin_id) for admin_id in self.admin_ids}
        if self.api_admin_token:
            tokens.add(self.api_admin_token)
        return tokens


ApiConfig = ApiConfigClass()

__all__ = ("ApiConfig", "ApiConfigClass")
