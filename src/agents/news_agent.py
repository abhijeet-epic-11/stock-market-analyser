import logging

from src.schemas.analysis import NewsAnalysis
from src.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class NewsAgent:
    def __init__(self, gemini: GeminiService) -> None:
        self.gemini = gemini

    async def run(self, ticker: str, raw_news: NewsAnalysis) -> NewsAnalysis:
        logger.info("News reasoning started for %s", ticker)
        gemini_news = await self.gemini.generate_news_analysis(ticker, raw_news)
        if gemini_news is not None:
            return gemini_news
        return raw_news
