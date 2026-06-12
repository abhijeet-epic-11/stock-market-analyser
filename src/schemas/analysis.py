from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TrendDirection = Literal["bullish", "bearish", "neutral"]
MacdSignal = Literal["bullish_cross", "bearish_cross", "neutral"]
NewsSentiment = Literal["bullish", "bearish", "neutral", "unknown"]


class PriceBar(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketSnapshot(BaseModel):
    ticker: str
    company_name: str | None = None
    currency: str | None = None
    exchange: str | None = None
    price: float
    volume: int
    market_cap: int | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    day_change: float | None = None
    day_change_percent: float | None = None
    history: list[PriceBar] = Field(default_factory=list)


class TechnicalAnalysis(BaseModel):
    trend: TrendDirection
    rsi: float
    sma20: float
    sma50: float
    ema20: float
    macd: float
    macd_signal: MacdSignal
    score: int = Field(..., ge=0, le=100)
    bullish_factors: list[str] = Field(default_factory=list)
    bearish_factors: list[str] = Field(default_factory=list)


class NewsArticle(BaseModel):
    title: str
    publisher: str | None = None
    link: str | None = None
    published_at: datetime | None = None
    summary: str | None = None


class NewsAnalysis(BaseModel):
    sentiment: NewsSentiment
    score: int = Field(..., ge=0, le=100)
    articles: list[NewsArticle] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
