from pydantic import Field

from bot.config.base import BaseConfig


class DatabaseConfigClass(BaseConfig):
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="4fall_bot", alias="POSTGRES_DB")
    postgres_host: str = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    django_secret_key: str = Field(
        default="change-me-in-production",
        alias="SECRET_KEY",
    )
    django_debug: bool = Field(default=False, alias="DEBUG")
    django_allowed_hosts: str = Field(default="*", alias="ALLOWED_HOST")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


DatabaseConfig = DatabaseConfigClass()

__all__ = ("DatabaseConfig", "DatabaseConfigClass")
