from functools import lru_cache

from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings

    SettingsConfigDict = dict


class Settings(BaseSettings):
    app_name: str = "Stock Market Analyser"
    environment: str = Field(default="development")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    default_horizon: str = "6_months"
    yfinance_interval: str = "1d"
    default_exchange_suffix: str | None = ".NS"
    max_news_items: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
