from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MARKET_", case_sensitive=False)

    service_name: str = "market-data"
    default_price_limit: int = 60
    max_price_limit: int = 500

    database_url: str | None = Field(
        default=None,
        description="postgresql+asyncpg://... Si está vacío, no hay cache en Postgres.",
    )

    tiingo_token: str | None = None
    tiingo_base_url: str = "https://api.tiingo.com"

    twelvedata_api_key: str | None = None
    twelvedata_base_url: str = "https://api.twelvedata.com"

    provider_order: str = "tiingo,twelvedata,mock"
    stale_after_seconds: int = 86400
    cache_serve_min_rows: int = 26
    fetch_timeout_seconds: float = 20.0
    candle_interval: str = "1d"

    allowed_symbols: str | None = Field(
        default=None,
        description="Lista separada por comas (ej. AAPL,MSFT). Vacío = sin restricción.",
    )

    @field_validator("provider_order")
    @classmethod
    def strip_order(cls, v: str) -> str:
        return v.strip() or "mock"
