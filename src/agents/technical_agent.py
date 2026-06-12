import logging

import pandas as pd
import ta

from src.schemas.analysis import MarketSnapshot, TechnicalAnalysis

logger = logging.getLogger(__name__)


class TechnicalAgent:
    async def run(self, market: MarketSnapshot) -> TechnicalAnalysis:
        logger.info("Technical analysis started for %s", market.ticker)
        if len(market.history) < 50:
            raise ValueError("At least 50 price bars are required for technical analysis.")

        frame = pd.DataFrame([bar.model_dump() for bar in market.history])
        close = frame["close"].astype(float)

        sma20 = close.rolling(window=20).mean()
        sma50 = close.rolling(window=50).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi()
        macd_indicator = ta.trend.MACD(close=close)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()

        latest_close = float(close.iloc[-1])
        latest_sma20 = self._last(sma20)
        latest_sma50 = self._last(sma50)
        latest_ema20 = self._last(ema20)
        latest_rsi = self._last(rsi)
        latest_macd = self._last(macd_line)
        latest_signal = self._last(signal_line)

        bullish: list[str] = []
        bearish: list[str] = []
        score = 50

        if latest_close > latest_sma20:
            score += 10
            bullish.append("Price is above 20 DMA")
        else:
            score -= 10
            bearish.append("Price is below 20 DMA")

        if latest_close > latest_sma50:
            score += 15
            bullish.append("Price is above 50 DMA")
        else:
            score -= 15
            bearish.append("Price is below 50 DMA")

        if latest_ema20 > latest_sma20:
            score += 5
            bullish.append("EMA20 is above SMA20, showing near-term momentum")
        else:
            score -= 5
            bearish.append("EMA20 is below SMA20, showing weaker near-term momentum")

        if latest_rsi >= 70:
            score -= 15
            bearish.append("RSI approaching overbought")
        elif latest_rsi <= 30:
            score += 10
            bullish.append("RSI is oversold")
        else:
            bullish.append("RSI is in a healthy range")

        if latest_macd > latest_signal:
            score += 15
            macd_signal = "bullish_cross"
            bullish.append("MACD is above signal line")
        elif latest_macd < latest_signal:
            score -= 15
            macd_signal = "bearish_cross"
            bearish.append("MACD is below signal line")
        else:
            macd_signal = "neutral"

        score = max(0, min(100, score))
        trend = "bullish" if score >= 65 else "bearish" if score <= 40 else "neutral"

        return TechnicalAnalysis(
            trend=trend,
            rsi=round(latest_rsi, 2),
            sma20=round(latest_sma20, 2),
            sma50=round(latest_sma50, 2),
            ema20=round(latest_ema20, 2),
            macd=round(latest_macd, 4),
            macd_signal=macd_signal,
            score=score,
            bullish_factors=bullish,
            bearish_factors=bearish,
        )

    @staticmethod
    def _last(series: pd.Series) -> float:
        cleaned = series.dropna()
        if cleaned.empty:
            raise ValueError("Technical indicator could not be calculated from price history.")
        return float(cleaned.iloc[-1])
