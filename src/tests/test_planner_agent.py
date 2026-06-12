import asyncio
import unittest

from src.agents.planner import PlannerAgent
from src.schemas.planner import AnalysisPlan


class StubGemini:
    async def generate_plan(self, query: str):
        return None


class GeminiPlanStub:
    async def generate_plan(self, query: str):
        return AnalysisPlan(ticker="infy", horizon="1_year", tasks=["technical"])


class PlannerAgentTest(unittest.TestCase):
    def test_planner_creates_work_from_query(self) -> None:
        plan = asyncio.run(PlannerAgent(StubGemini()).run("Analyze TCS for 6 months"))

        self.assertEqual(plan.ticker, "TCS")
        self.assertEqual(plan.horizon, "6_months")
        self.assertEqual(plan.tasks, ["market", "technical", "news", "thesis"])

    def test_planner_prefers_gemini_plan(self) -> None:
        plan = asyncio.run(PlannerAgent(GeminiPlanStub()).run("Should be understood by Gemini"))

        self.assertEqual(plan.ticker, "INFY")
        self.assertEqual(plan.horizon, "1_year")
        self.assertEqual(plan.tasks, ["technical", "market", "news", "thesis"])


if __name__ == "__main__":
    unittest.main()
