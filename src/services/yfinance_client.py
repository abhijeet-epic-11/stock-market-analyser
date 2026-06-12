from pathlib import Path

import yfinance as yf


def configure_yfinance_cache() -> None:
    cache_dir = Path(".cache/yfinance").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except Exception:
        # Cache configuration should never block the analysis workflow.
        pass


configure_yfinance_cache()
