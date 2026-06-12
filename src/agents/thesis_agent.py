import logging

from src.schemas.analysis import MarketSnapshot, NewsAnalysis, TechnicalAnalysis
from src.schemas.recommendation import Recommendation
from src.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ThesisAgent:
    def __init__(self, gemini: GeminiService) -> None:
        self.gemini = gemini

    async def run(
        self,
        market: MarketSnapshot,
        technical: TechnicalAnalysis,
        news: NewsAnalysis | None = None,
        market_notes: list[str] | None = None,
    ) -> Recommendation:
        logger.info("Thesis generation started for %s", market.ticker)
        gemini_recommendation = await self.gemini.generate_recommendation(market, technical, news)
        if gemini_recommendation is not None:
            return gemini_recommendation

        score = technical.score
        bullish = list(technical.bullish_factors)
        bearish = list(technical.bearish_factors)
        risks = ["Market volatility can invalidate short-term signals."]
        notes = market_notes or []
        bullish.extend(note for note in notes if "higher" in note.lower())
        bearish.extend(note for note in notes if "lower" in note.lower())

        if news is not None:
            if news.sentiment == "bullish":
                score += 10
                bullish.extend(news.events)
            elif news.sentiment == "bearish":
                score -= 10
                bearish.extend(news.events)

        score = max(0, min(100, score))
        if score >= 65:
            action = "BUY"
        elif score <= 40:
            action = "SELL"
        else:
            action = "HOLD"

        thesis = (
            f"{market.ticker} has a {technical.trend} technical structure with a "
            f"technical score of {technical.score}/100. The current setup supports "
            f"a {action} stance for the selected horizon, subject to risk controls."
        )

        return Recommendation(
            recommendation=action,
            confidence=score,
            bullish_factors=bullish,
            bearish_factors=bearish,
            key_risks=risks,
            thesis=thesis,
        )
