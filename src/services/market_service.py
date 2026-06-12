import asyncio
import logging
from datetime import datetime
from typing import Any, Callable

import pandas as pd
import yfinance as yf

from src.schemas.analysis import MarketSnapshot, PriceBar
from src.services.yfinance_client import configure_yfinance_cache

logger = logging.getLogger(__name__)

SymbolResolver = Callable[[str, str | None], str | None]


class MarketDataError(RuntimeError):
    """Raised when market data cannot be loaded for a ticker."""


class MarketService:
    HORIZON_TO_PERIOD = {
        "1_month": "1mo",
        "3_months": "3mo",
        "6_months": "6mo",
        "1_year": "1y",
        "2_years": "2y",
        "5_years": "5y",
    }

    def __init__(
        self,
        interval: str = "1d",
        default_exchange_suffix: str | None = ".NS",
        symbol_resolver: SymbolResolver | None = None,
    ) -> None:
        self.interval = interval
        self.default_exchange_suffix = default_exchange_suffix
        self.symbol_resolver = symbol_resolver

    async def get_stock_snapshot(self, ticker: str, horizon: str) -> MarketSnapshot:
        return await asyncio.to_thread(self._get_stock_snapshot_sync, ticker, horizon)

    def _get_stock_snapshot_sync(self, ticker: str, horizon: str) -> MarketSnapshot:
        configure_yfinance_cache()
        period = self.HORIZON_TO_PERIOD.get(horizon, "6mo")
        yahoo_ticker, resolved_ticker, history = self._load_history(ticker, period)
        history = history.dropna(how="all")

        info: dict[str, Any] = {}
        try:
            info = yahoo_ticker.get_info()
        except Exception:
            info = {}

        last = history.iloc[-1]
        previous_close = self._float(info.get("previousClose"))
        price = self._float(info.get("currentPrice")) or self._float(last.get("Close"))
        day_change = None
        day_change_percent = None
        if price is not None and previous_close:
            day_change = round(price - previous_close, 4)
            day_change_percent = round((day_change / previous_close) * 100, 2)

        return MarketSnapshot(
            ticker=resolved_ticker,
            company_name=info.get("longName") or info.get("shortName"),
            currency=info.get("currency"),
            exchange=info.get("exchange"),
            price=price or 0,
            volume=self._int(last.get("Volume")) or 0,
            market_cap=self._int(info.get("marketCap")),
            high_52w=self._float(info.get("fiftyTwoWeekHigh")),
            low_52w=self._float(info.get("fiftyTwoWeekLow")),
            day_change=day_change,
            day_change_percent=day_change_percent,
            history=self._to_price_bars(history),
        )

    def _load_history(self, ticker: str, period: str):
        errors: list[str] = []

        def attempt(candidates):
            for candidate in candidates:
                if not candidate or candidate in errors:
                    continue
                yahoo_ticker = yf.Ticker(candidate)
                history = yahoo_ticker.history(period=period, interval=self.interval, auto_adjust=False)
                if not history.empty:
                    return yahoo_ticker, candidate, history
                errors.append(candidate)
            return None

        # 1. Try the literal input and its exchange-suffix variants (fast, no API call).
        result = attempt(self._ticker_candidates(ticker))
        if result:
            return result

        # 2. The input may be a company name (e.g. "INFOSYS"). Ask the LLM to resolve it
        #    to a proper Yahoo symbol, then validate that symbol against live data.
        result = attempt(self._llm_candidates(ticker))
        if result:
            return result

        # 3. Last resort: Yahoo's own search endpoint.
        result = attempt(self._search_candidates(ticker))
        if result:
            return result

        attempted = ", ".join(errors)
        raise MarketDataError(f"No market data found for ticker '{ticker}'. Tried: {attempted}.")

    def _llm_candidates(self, ticker: str) -> list[str]:
        if self.symbol_resolver is None:
            return []
        try:
            symbol = self.symbol_resolver(ticker, self.default_exchange_suffix)
        except Exception as exc:
            logger.warning("LLM symbol resolution failed for '%s': %s", ticker, exc)
            return []
        if not symbol:
            return []
        logger.info("LLM resolved '%s' -> '%s'", ticker, symbol)
        return [symbol.strip().upper()]

    def _search_candidates(self, ticker: str) -> list[str]:
        try:
            quotes = yf.Search(ticker.strip(), max_results=8).quotes
        except Exception:
            return []
        symbols = [q.get("symbol") for q in quotes if q.get("symbol")]
        suffix = (self.default_exchange_suffix or "").upper()
        # Prefer symbols on the configured default exchange (e.g. .NS for NSE).
        preferred = [s for s in symbols if suffix and s.upper().endswith(suffix)]
        ordered = preferred + [s for s in symbols if s not in preferred]
        return list(dict.fromkeys(ordered))

    def _ticker_candidates(self, ticker: str) -> list[str]:
        normalized = ticker.strip().upper()
        candidates = []
        if "." not in normalized:
            if self.default_exchange_suffix:
                candidates.append(f"{normalized}{self.default_exchange_suffix.upper()}")
            candidates.extend([normalized, f"{normalized}.NS", f"{normalized}.BO"])
        else:
            candidates.append(normalized)
        return list(dict.fromkeys(candidates))

    def _to_price_bars(self, history: pd.DataFrame) -> list[PriceBar]:
        bars: list[PriceBar] = []
        for index, row in history.iterrows():
            timestamp = index.to_pydatetime() if hasattr(index, "to_pydatetime") else datetime.utcnow()
            bars.append(
                PriceBar(
                    date=timestamp,
                    open=round(float(row["Open"]), 4),
                    high=round(float(row["High"]), 4),
                    low=round(float(row["Low"]), 4),
                    close=round(float(row["Close"]), 4),
                    volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                )
            )
        return bars

    @staticmethod
    def _float(value: Any) -> float | None:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int(value: Any) -> int | None:
        try:
            if value is None or pd.isna(value):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None
