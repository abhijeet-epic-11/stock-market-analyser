import asyncio
import json
import logging
import re

from pydantic import ValidationError

from src.schemas.analysis import MarketSnapshot, NewsAnalysis, TechnicalAnalysis
from src.schemas.planner import AnalysisPlan, TickerResolution
from src.schemas.recommendation import Recommendation

logger = logging.getLogger(__name__)


class LLMService:
    """OpenAI-backed LLM service for planning, resolution, and synthesis.

    All prompts ask for strict JSON and the responses are validated against the
    relevant Pydantic schema. Any failure (missing key, API error, invalid payload)
    degrades gracefully to ``None`` so callers can fall back to deterministic logic.
    """

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None
        if api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=api_key)
            except Exception:
                self._client = None

    async def generate_plan(self, query: str) -> AnalysisPlan | None:
        prompt = (
            "You are a stock analysis planner. Convert the user query into strict JSON "
            "matching this schema: ticker string, horizon one of "
            "1_month|3_months|6_months|1_year|2_years|5_years, tasks array containing "
            "market, technical, news, thesis when useful. Do not recommend.\n"
            "The ticker MUST be the exact Yahoo Finance symbol including the correct exchange "
            "suffix, not the company name. Examples: Infosys -> INFY.NS, Reliance -> RELIANCE.NS, "
            "Apple -> AAPL, Toyota -> 7203.T, HSBC -> HSBA.L. Use no suffix for US listings.\n"
            f"User query: {query}"
        )
        return await asyncio.to_thread(self._generate_model, prompt, AnalysisPlan)

    def resolve_symbol(self, query: str, default_exchange_suffix: str | None = None) -> str | None:
        """Resolve a fuzzy company name or ticker into a Yahoo Finance symbol.

        Synchronous so it can be called from within MarketService's worker thread.
        Returns None when the LLM is unavailable or cannot produce a valid symbol;
        callers should validate the symbol against live market data.
        """
        if self._client is None:
            return None
        suffix_hint = ""
        if default_exchange_suffix:
            suffix_hint = (
                f"If the company is listed on the exchange for the '{default_exchange_suffix}' "
                f"suffix, prefer that listing.\n"
            )
        prompt = (
            "You map a company name or ticker to its exact Yahoo Finance symbol, including "
            "the correct exchange suffix. Examples: Infosys -> INFY.NS, Reliance -> RELIANCE.NS, "
            "Apple -> AAPL, Toyota -> 7203.T, HSBC -> HSBA.L. Use no suffix for US listings.\n"
            f"{suffix_hint}"
            'Return strict JSON: {"symbol": "<yahoo_symbol>"}.\n'
            f"Input: {query}"
        )
        resolution = self._generate_model(prompt, TickerResolution)
        return resolution.symbol if resolution else None

    async def generate_news_analysis(self, ticker: str, raw_news: NewsAnalysis) -> NewsAnalysis | None:
        prompt = (
            "You are a news analysis agent. Interpret the headlines as strict JSON matching "
            "this schema: sentiment bullish|bearish|neutral|unknown, score 0-100, "
            "articles as provided, events as the key market-moving events. "
            "Do not make a stock recommendation.\n"
            f"Ticker: {ticker}\n"
            f"News: {raw_news.model_dump_json()}"
        )
        return await asyncio.to_thread(self._generate_model, prompt, NewsAnalysis)

    async def generate_recommendation(
        self,
        market: MarketSnapshot,
        technical: TechnicalAnalysis,
        news: NewsAnalysis | None,
    ) -> Recommendation | None:
        prompt = (
            "You are a thesis and synthesizer agent. Create a final report as strict JSON "
            "matching this schema: recommendation BUY|HOLD|SELL, confidence 0-100, "
            "bullish_factors string array, bearish_factors string array, key_risks string array, "
            "thesis string. Use the market, technical, and news inputs only.\n"
            f"Market: {market.model_dump_json()}\n"
            f"Technical: {technical.model_dump_json()}\n"
            f"News: {news.model_dump_json() if news else None}\n"
        )
        return await asyncio.to_thread(self._generate_model, prompt, Recommendation)

    def _generate_model(self, prompt: str, model_type):
        if self._client is None:
            return None
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            if not text:
                return None
            payload = self._extract_json(text)
            return model_type.model_validate(payload)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            logger.warning("LLM returned invalid %s payload: %s", model_type.__name__, exc)
            return None
        except Exception as exc:
            logger.warning("LLM request failed: %s", exc)
            return None

    @staticmethod
    def _extract_json(text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        if not cleaned.startswith("{"):
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in LLM response.")
            cleaned = match.group(0)
        return json.loads(cleaned)
