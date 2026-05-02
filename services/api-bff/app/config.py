from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    service_name: str = "api-bff"
    market_data_base_url: str = "http://market-data:8000"
    signal_engine_base_url: str = "http://signal-engine:8000"
    request_timeout_seconds: float = 15.0
    # Debe ser >= al `need` de signal-engine (max(sma_long+2, pct_window+2, 60) = 60 por defecto)
    # para no pedir menos velas aquí y forzar otra petición a la API externa en el mismo flujo.
    summary_prices_limit: int = 60
