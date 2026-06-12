# Stock Market Analyser

A CLI-first stock analysis workflow built around Gemini-backed planning, typed domain models, and agent/service separation.

## First Principle

Agents reason. Services fetch.

The technical agent never calls Yahoo Finance. The workflow asks `MarketService` for a typed `MarketSnapshot`, then passes that model into `TechnicalAgent`.

## Target Flow

```text
User
  |
  v
Planner Agent (Gemini)
  |
  +--> Market Agent (Python)
  +--> Technical Agent (Python)
  +--> News Agent (Gemini)
  |
  v
Thesis/Synthesizer Agent (Gemini)
  |
  v
Final Report
```

If `GEMINI_API_KEY` is not present, planner/news/thesis use deterministic fallback behavior so the local workflow remains testable.

## Run Locally

```bash
uv run python main.py "Analyze TCS for 6 months"
```

Without `uv`:

```bash
.venv/bin/python main.py "Analyze TCS for 6 months"
```

Expected CLI shape:

```text
Recommendation: BUY
Confidence: 82%

Bullish:
- Price is above 50 DMA
- MACD is above signal line

Bearish:
- RSI approaching overbought
```

## Architecture

- `schemas/`: Pydantic domain models
- `services/`: external data/model integrations, including Gemini adapter
- `agents/`: reasoning units
- `orchestrator/`: workflow coordination
- `main.py`: Sprint 1 CLI

## Environment

Use `.env` for secrets:

```text
GEMINI_API_KEY=xxxx
```

Gemini is used by the planner, news agent, and thesis/synthesizer when `GEMINI_API_KEY` is configured.
