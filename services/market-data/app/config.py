from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MARKET_", case_sensitive=False)

    service_name: str = "market-data"
    default_price_limit: int = 60
    max_price_limit: int = 500
