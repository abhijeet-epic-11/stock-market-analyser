
import asyncio
import logging

from src.agents.market_agent import MarketAgent
from src.agents.news_agent import NewsAgent
from src.agents.planner import PlannerAgent
from src.agents.technical_agent import TechnicalAgent
from src.agents.thesis_agent import ThesisAgent
from src.schemas.planner import StockAnalysisRequest
from src.schemas.recommendation import AnalysisResponse
from src.services.llm_service import LLMService
from src.services.market_service import MarketService
from src.services.news_service import NewsService
from src.settings.config import Settings

logger = logging.getLogger(__name__)


class AnalysisWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMService(settings.openai_api_key, settings.openai_model)
        self.planner = PlannerAgent(self.llm)
        self.market_service = MarketService(
            interval=settings.yfinance_interval,
            default_exchange_suffix=settings.default_exchange_suffix,
            symbol_resolver=self.llm.resolve_symbol,
        )
        self.news_service = NewsService()
        self.market_agent = MarketAgent()
        self.technical_agent = TechnicalAgent()
        self.news_agent = NewsAgent(self.llm)
        self.thesis_agent = ThesisAgent(self.llm)

    async def execute(self, query: str | StockAnalysisRequest) -> AnalysisResponse:
        logger.info("Analysis workflow started")
        plan = await self.planner.run(query)
        market = await self.market_service.get_stock_snapshot(plan.ticker, plan.horizon)

        market_notes_task = self.market_agent.run(market)
        technical_task = self.technical_agent.run(market)
        news_task = self._analyse_news(market.ticker) if "news" in plan.tasks else self._empty_news()
        market_notes, technical, news = await asyncio.gather(market_notes_task, technical_task, news_task)

        recommendation = await self.thesis_agent.run(
            market=market,
            technical=technical,
            news=news if "news" in plan.tasks else None,
            market_notes=market_notes,
        )

        return AnalysisResponse(
            plan=plan,
            market=market,
            technical=technical,
            news=news if "news" in plan.tasks else None,
            recommendation=recommendation,
        )

    async def _empty_news(self):
        from src.schemas.analysis import NewsAnalysis

        return NewsAnalysis(sentiment="unknown", score=50, articles=[], events=[])

    async def _analyse_news(self, ticker: str):
        raw_news = await self.news_service.get_company_news(ticker, self.settings.max_news_items)
        return await self.news_agent.run(ticker, raw_news)
