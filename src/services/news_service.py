import asyncio
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from src.schemas.analysis import NewsAnalysis, NewsArticle
from src.services.yfinance_client import configure_yfinance_cache


class NewsService:
    POSITIVE_TERMS = {"beats", "surges", "upgrade", "growth", "record", "profit", "rally", "strong"}
    NEGATIVE_TERMS = {"misses", "falls", "downgrade", "loss", "lawsuit", "weak", "slumps", "risk"}

    async def get_company_news(self, ticker: str, limit: int) -> NewsAnalysis:
        return await asyncio.to_thread(self._get_company_news_sync, ticker, limit)

    def _get_company_news_sync(self, ticker: str, limit: int) -> NewsAnalysis:
        configure_yfinance_cache()
        articles = self._fetch_articles(ticker, limit)
        sentiment = self._classify_sentiment(articles)
        events = [article.title for article in articles[:3]]
        score = {"bullish": 75, "bearish": 25, "neutral": 50, "unknown": 50}[sentiment]
        return NewsAnalysis(sentiment=sentiment, score=score, articles=articles, events=events)

    def _fetch_articles(self, ticker: str, limit: int) -> list[NewsArticle]:
        try:
            raw_news: list[dict[str, Any]] = yf.Ticker(ticker).news or []
        except Exception:
            raw_news = []

        articles: list[NewsArticle] = []
        for item in raw_news[:limit]:
            content = item.get("content", item)
            title = content.get("title") or item.get("title")
            if not title:
                continue
            provider = content.get("provider") or {}
            published_at = self._parse_date(content.get("pubDate") or item.get("providerPublishTime"))
            articles.append(
                NewsArticle(
                    title=title,
                    publisher=provider.get("displayName") or item.get("publisher"),
                    link=content.get("canonicalUrl", {}).get("url") or item.get("link"),
                    published_at=published_at,
                    summary=content.get("summary"),
                )
            )
        return articles

    def _classify_sentiment(self, articles: list[NewsArticle]) -> str:
        if not articles:
            return "unknown"
        score = 0
        for article in articles:
            words = set(article.title.lower().split())
            score += len(words & self.POSITIVE_TERMS)
            score -= len(words & self.NEGATIVE_TERMS)
        if score > 0:
            return "bullish"
        if score < 0:
            return "bearish"
        return "neutral"

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, int):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
