import logging
import re

from src.schemas.planner import AnalysisPlan, StockAnalysisRequest
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PlannerAgent:
    HORIZON_ALIASES = {
        "1 month": "1_month",
        "one month": "1_month",
        "3 months": "3_months",
        "three months": "3_months",
        "6 months": "6_months",
        "six months": "6_months",
        "1 year": "1_year",
        "one year": "1_year",
        "2 years": "2_years",
        "two years": "2_years",
        "5 years": "5_years",
        "five years": "5_years",
    }

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def run(self, query: str | StockAnalysisRequest) -> AnalysisPlan:
        logger.info("Planner analysis started")
        if isinstance(query, StockAnalysisRequest):
            request = query
        else:
            llm_plan = await self.llm.generate_plan(query)
            if llm_plan is not None:
                return self._normalize_plan(llm_plan)
            request = self._parse_query(query)

        return AnalysisPlan(
            ticker=request.ticker,
            horizon=request.horizon,
            tasks=["market", "technical", "news", "thesis"],
        )

    @staticmethod
    def _normalize_plan(plan: AnalysisPlan) -> AnalysisPlan:
        tasks = list(dict.fromkeys(plan.tasks))
        for required in ("market", "technical", "news", "thesis"):
            if required not in tasks:
                tasks.append(required)
        return AnalysisPlan(ticker=plan.ticker, horizon=plan.horizon, tasks=tasks)

    def _parse_query(self, query: str) -> StockAnalysisRequest:
        normalized = query.strip()
        ticker = self._extract_ticker(normalized)
        horizon = self._extract_horizon(normalized)
        return StockAnalysisRequest(ticker=ticker, horizon=horizon)

    def _extract_ticker(self, query: str) -> str:
        match = re.search(r"\b(?:analyze|analyse)\s+([A-Za-z0-9.\-]+)", query, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        tokens = re.findall(r"[A-Za-z0-9.\-]+", query)
        if not tokens:
            raise ValueError("Could not identify a ticker from the query.")
        return tokens[0]

    def _extract_horizon(self, query: str) -> str:
        lowered = query.lower().replace("_", " ")
        for phrase, horizon in self.HORIZON_ALIASES.items():
            if phrase in lowered:
                return horizon
        return "6_months"
