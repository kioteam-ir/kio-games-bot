from pydantic import Field, computed_field

from api.config.base import BaseConfig
from bot.config.bot import parse_admin_ids


class ApiConfigClass(BaseConfig):
    api_admin_token: str | None = Field(default=None, alias="API_ADMIN_TOKEN")
    admin_ids_env: str = Field(default="", alias="ADMIN_IDS")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin_ids(self) -> list[int]:
        return parse_admin_ids(self.admin_ids_env)

    def valid_admin_tokens(self) -> set[str]:
        tokens = {str(admin_id) for admin_id in self.admin_ids}
        if self.api_admin_token:
            tokens.add(self.api_admin_token)
        return tokens


ApiConfig = ApiConfigClass()

__all__ = ("ApiConfig", "ApiConfigClass")
