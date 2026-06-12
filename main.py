import argparse
import asyncio
import logging

from src.orchestrator.workflows import AnalysisWorkflow
from src.settings.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stock analysis workflow.")
    parser.add_argument(
        "query",
        nargs="?",
        default="Analyze TCS for 6 months",
        help='Natural language query, e.g. "Analyze TCS for 6 months"',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    asyncio.run(run_cli(args.query))


async def run_cli(query: str) -> None:
    workflow = AnalysisWorkflow(get_settings())
    result = await workflow.execute(query)
    recommendation = result.recommendation

    print(f"Ticker: {result.plan.ticker}")
    if result.market.ticker != result.plan.ticker:
        print(f"Resolved Market Ticker: {result.market.ticker}")
    print(f"Horizon: {result.plan.horizon}")
    print(f"Recommendation: {recommendation.recommendation}")
    print(f"Confidence: {recommendation.confidence}%")
    print()
    print("Bullish:")
    for factor in recommendation.bullish_factors:
        print(f"- {factor}")
    print()
    print("Bearish:")
    for factor in recommendation.bearish_factors:
        print(f"- {factor}")
    print()
    if result.news is not None:
        print(f"News Sentiment: {result.news.sentiment} ({result.news.score}%)")
        for event in result.news.events:
            print(f"- {event}")
        print()
    print("Risks:")
    for risk in recommendation.key_risks:
        print(f"- {risk}")
    print()
    print(recommendation.thesis)


if __name__ == "__main__":
    main()
