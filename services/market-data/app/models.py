from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(ge=0)


class PriceSeriesResponse(BaseModel):
    symbol: str
    source: str = Field(
        description=(
            "Origen de la serie: "
            "`tiingo` | `twelvedata` (API externa), "
            "`postgres` (cache acorde a MARKET_STALE_AFTER_SECONDS), "
            "`postgres_stale` (solo cache si la sync externa está vencida), "
            "`mock` (sin claves o tras agotar proveedores)."
        ),
    )
    points: list[PricePoint]
