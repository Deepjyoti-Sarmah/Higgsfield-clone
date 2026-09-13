from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_SESSION_SECRET = "local-dev-secret-not-for-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env.local", "../../.env.local"), extra="ignore")

    env: str = "local"
    app_role: str = "api"
    port: int = 8000
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/higgsfield"
    session_secret: str = LOCAL_SESSION_SECRET
    session_ttl_days: int = 30
    static_dir: str = "../web/dist"

    @property
    def is_local(self) -> bool:
        return self.env == "local"

    @property
    def async_database_url(self) -> str:
        return to_asyncpg_url(self.database_url)

    @model_validator(mode="after")
    def reject_local_secret_outside_local(self) -> "Settings":
        if not self.is_local and self.session_secret == LOCAL_SESSION_SECRET:
            raise ValueError("SESSION_SECRET must be set when ENV is not local")
        return self


def to_asyncpg_url(url: str) -> str:
    # Neon/Railway hand out libpq URLs; asyncpg needs its own scheme and `ssl` instead of `sslmode`.
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
    query = [("ssl", value) if key == "sslmode" else (key, value) for key, value in parse_qsl(parts.query)]
    query = [(key, value) for key, value in query if key != "channel_binding"]
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@lru_cache
def get_settings() -> Settings:
    return Settings()
