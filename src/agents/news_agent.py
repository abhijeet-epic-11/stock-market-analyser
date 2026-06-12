import logging

from src.schemas.analysis import NewsAnalysis
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class NewsAgent:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def run(self, ticker: str, raw_news: NewsAnalysis) -> NewsAnalysis:
        logger.info("News reasoning started for %s", ticker)
        llm_news = await self.llm.generate_news_analysis(ticker, raw_news)
        if llm_news is not None:
            return llm_news
        return raw_news
