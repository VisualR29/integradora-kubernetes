from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    service_name: str = "signal-engine"
    market_data_base_url: str = "http://market-data:8000"
    database_url: str = "postgresql+asyncpg://signals:signals@postgres:5432/signals"
    sma_short: int = 5
    sma_long: int = 20
    pct_window: int = 24
    pct_buy_threshold: float = 1.5
    pct_sell_threshold: float = -1.5
