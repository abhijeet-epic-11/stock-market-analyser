from typing import Literal

from pydantic import BaseModel, Field, field_validator


Horizon = Literal["1_month", "3_months", "6_months", "1_year", "2_years", "5_years"]
TaskName = Literal["market", "technical", "news", "thesis"]


class StockAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, examples=["TCS"])
    horizon: Horizon = "6_months"

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("ticker cannot be empty")
        return cleaned


class AnalysisPlan(BaseModel):
    ticker: str
    horizon: Horizon
    tasks: list[TaskName]

    @field_validator("ticker")
    @classmethod
    def normalize_plan_ticker(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("ticker cannot be empty")
        return cleaned
