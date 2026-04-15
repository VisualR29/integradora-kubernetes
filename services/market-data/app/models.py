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
    source: str
    points: list[PricePoint]
