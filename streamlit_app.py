"""Streamlit UI for the stock analysis workflow."""

import asyncio

import pandas as pd
import streamlit as st

from src.orchestrator.workflows import AnalysisWorkflow
from src.schemas.planner import Horizon, StockAnalysisRequest
from src.settings.config import get_settings

HORIZONS: list[Horizon] = [
    "1_month",
    "3_months",
    "6_months",
    "1_year",
    "2_years",
    "5_years",
]

REC_COLORS = {"BUY": "#16a34a", "HOLD": "#d97706", "SELL": "#dc2626"}
SENTIMENT_EMOJI = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡", "unknown": "⚪"}


def run_analysis(request: StockAnalysisRequest):
    workflow = AnalysisWorkflow(get_settings())
    return asyncio.run(workflow.execute(request))


def render_price_chart(market) -> None:
    if not market.history:
        st.info("No price history available.")
        return
    df = pd.DataFrame(
        {
            "date": [bar.date for bar in market.history],
            "close": [bar.close for bar in market.history],
        }
    ).set_index("date")
    st.line_chart(df, y="close", height=320)


def render_factors(title: str, factors: list[str], icon: str) -> None:
    st.markdown(f"**{icon} {title}**")
    if not factors:
        st.caption("None reported.")
        return
    for factor in factors:
        st.markdown(f"- {factor}")


def main() -> None:
    st.set_page_config(page_title="Stock Market Analyser", page_icon="📈", layout="wide")
    st.title("📈 Stock Market Analyser")
    st.caption("Multi-agent analysis: planning, market data, technicals, news, and thesis.")

    with st.sidebar:
        st.header("Analysis Inputs")
        ticker = st.text_input("Ticker", value="TCS", help="e.g. TCS, INFY, AAPL").strip()
        horizon = st.selectbox(
            "Horizon",
            HORIZONS,
            index=HORIZONS.index("6_months"),
            format_func=lambda h: h.replace("_", " ").title(),
        )
        run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    if not run_clicked:
        st.info("Enter a ticker and click **Run Analysis** to start.")
        return

    if not ticker:
        st.error("Please enter a ticker.")
        return

    try:
        request = StockAnalysisRequest(ticker=ticker, horizon=horizon)
    except ValueError as exc:
        st.error(f"Invalid input: {exc}")
        return

    with st.spinner(f"Analysing {request.ticker} over {horizon.replace('_', ' ')}..."):
        try:
            result = run_analysis(request)
        except Exception as exc:  # noqa: BLE001 - surface any workflow error to the UI
            st.error(f"Analysis failed: {exc}")
            return

    market = result.market
    rec = result.recommendation
    color = REC_COLORS.get(rec.recommendation, "#475569")

    # Header summary
    name = market.company_name or result.plan.ticker
    st.subheader(f"{name} ({market.ticker})")
    st.markdown(
        f"<span style='background:{color};color:white;padding:4px 14px;"
        f"border-radius:6px;font-weight:600;font-size:1.1rem'>"
        f"{rec.recommendation} · {rec.confidence}% confidence</span>",
        unsafe_allow_html=True,
    )

    cur = market.currency or ""
    cols = st.columns(4)
    cols[0].metric(
        "Price",
        f"{market.price:,.2f} {cur}".strip(),
        delta=f"{market.day_change_percent:+.2f}%" if market.day_change_percent is not None else None,
    )
    cols[1].metric("Technical Score", f"{result.technical.score}/100")
    cols[2].metric("Trend", result.technical.trend.title())
    if result.news is not None:
        cols[3].metric(
            "News Sentiment",
            f"{SENTIMENT_EMOJI.get(result.news.sentiment, '')} {result.news.sentiment.title()}",
            delta=f"{result.news.score}%",
        )
    else:
        cols[3].metric("News", "Skipped")

    st.divider()
    render_price_chart(market)
    st.divider()

    # Thesis & recommendation
    st.markdown("### 🧭 Recommendation")
    st.write(rec.thesis)
    left, right = st.columns(2)
    with left:
        render_factors("Bullish Factors", rec.bullish_factors, "🟢")
    with right:
        render_factors("Bearish Factors", rec.bearish_factors, "🔴")
    render_factors("Key Risks", rec.key_risks, "⚠️")

    # Technical detail
    with st.expander("📊 Technical Indicators"):
        tech = result.technical
        tcols = st.columns(4)
        tcols[0].metric("RSI", f"{tech.rsi:.1f}")
        tcols[1].metric("MACD", f"{tech.macd:.3f}", delta=tech.macd_signal.replace("_", " "))
        tcols[2].metric("SMA 20 / 50", f"{tech.sma20:.2f} / {tech.sma50:.2f}")
        tcols[3].metric("EMA 20", f"{tech.ema20:.2f}")
        c1, c2 = st.columns(2)
        with c1:
            render_factors("Bullish", tech.bullish_factors, "🟢")
        with c2:
            render_factors("Bearish", tech.bearish_factors, "🔴")

    # News detail
    if result.news is not None and result.news.articles:
        with st.expander(f"📰 News ({len(result.news.articles)} articles)"):
            if result.news.events:
                st.markdown("**Key events**")
                for event in result.news.events:
                    st.markdown(f"- {event}")
                st.divider()
            for article in result.news.articles:
                if article.link:
                    st.markdown(f"**[{article.title}]({article.link})**")
                else:
                    st.markdown(f"**{article.title}**")
                meta = " · ".join(
                    part
                    for part in [
                        article.publisher,
                        article.published_at.strftime("%Y-%m-%d") if article.published_at else None,
                    ]
                    if part
                )
                if meta:
                    st.caption(meta)
                if article.summary:
                    st.write(article.summary)

    st.caption(result.disclaimer)


if __name__ == "__main__":
    main()
