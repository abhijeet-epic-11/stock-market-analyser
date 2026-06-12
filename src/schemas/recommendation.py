from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.analysis import MarketSnapshot, NewsAnalysis, TechnicalAnalysis
from src.schemas.planner import AnalysisPlan


RecommendationAction = Literal["BUY", "HOLD", "SELL"]


class Recommendation(BaseModel):
    recommendation: RecommendationAction
    confidence: int = Field(..., ge=0, le=100)
    bullish_factors: list[str] = Field(default_factory=list)
    bearish_factors: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    thesis: str


class AnalysisResponse(BaseModel):
    plan: AnalysisPlan
    market: MarketSnapshot
    technical: TechnicalAnalysis
    news: NewsAnalysis | None = None
    recommendation: Recommendation
    disclaimer: str = (
        "This analysis is informational only and is not financial advice. "
        "Validate independently before making investment decisions."
    )
