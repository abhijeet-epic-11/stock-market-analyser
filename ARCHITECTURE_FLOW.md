# Stock Market Analyser Architecture Flow

This file shows how the current agentic architecture works end to end.

## High-Level Flow

```mermaid
flowchart TD
    U[User Query<br/>Example: Analyze TCS for 6 months] --> M[main.py CLI Runner]
    M --> W[AnalysisWorkflow]

    W --> P[Planner Agent<br/>Gemini-first]
    P --> PLAN[AnalysisPlan<br/>ticker, horizon, tasks]

    PLAN --> MS[Market Service<br/>Yahoo Finance]
    MS --> SNAP[MarketSnapshot<br/>resolved ticker, price, volume,<br/>market cap, 52W high/low, history]

    SNAP --> MA[Market Agent<br/>Python reasoning]
    SNAP --> TA[Technical Agent<br/>Python indicators]
    PLAN --> NS[News Service<br/>Yahoo Finance headlines]

    NS --> RAWNEWS[Raw NewsAnalysis]
    RAWNEWS --> NA[News Agent<br/>Gemini-first]

    MA --> MN[Market Notes]
    TA --> TECH[TechnicalAnalysis<br/>RSI, SMA20, SMA50,<br/>EMA20, MACD, score]
    NA --> NEWS[NewsAnalysis<br/>sentiment, score, events]

    MN --> TH[Thesis / Synthesizer Agent<br/>Gemini-first]
    TECH --> TH
    NEWS --> TH
    SNAP --> TH

    TH --> REC[Recommendation<br/>BUY / HOLD / SELL,<br/>confidence, factors, risks, thesis]
    REC --> OUT[CLI Final Report]
```

## Core Rule

```text
Agents reason.
Services fetch.
Schemas define what can be passed.
Workflow coordinates.
```

Agents never call Yahoo Finance directly. External data access stays inside services.

## Component Responsibilities

```mermaid
flowchart LR
    subgraph Schemas
        S1[StockAnalysisRequest]
        S2[AnalysisPlan]
        S3[MarketSnapshot]
        S4[TechnicalAnalysis]
        S5[NewsAnalysis]
        S6[Recommendation]
    end

    subgraph Services
        SV1[MarketService<br/>fetches market data]
        SV2[NewsService<br/>fetches headlines]
        SV3[GeminiService<br/>LLM adapter]
    end

    subgraph Agents
        A1[PlannerAgent<br/>creates work plan]
        A2[MarketAgent<br/>reasons on snapshot]
        A3[TechnicalAgent<br/>computes indicators]
        A4[NewsAgent<br/>summarizes news impact]
        A5[ThesisAgent<br/>synthesizes final report]
    end

    subgraph Orchestration
        O1[AnalysisWorkflow<br/>orders and fans out work]
    end

    S1 --> O1
    O1 --> A1
    A1 --> SV3
    A1 --> S2
    O1 --> SV1
    SV1 --> S3
    O1 --> SV2
    SV2 --> S5
    S3 --> A2
    S3 --> A3
    S5 --> A4
    A4 --> SV3
    A2 --> A5
    A3 --> A5
    A4 --> A5
    A5 --> SV3
    A5 --> S6
```

## Runtime Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI as main.py
    participant WF as AnalysisWorkflow
    participant Planner as PlannerAgent
    participant Gemini as GeminiService
    participant MarketSvc as MarketService
    participant NewsSvc as NewsService
    participant MarketAgent
    participant Tech as TechnicalAgent
    participant NewsAgent
    participant Thesis as ThesisAgent

    User->>CLI: Analyze TCS for 6 months
    CLI->>WF: execute(query)
    WF->>Planner: run(query)
    Planner->>Gemini: generate_plan(query)
    Gemini-->>Planner: AnalysisPlan or None
    Planner-->>WF: AnalysisPlan

    WF->>MarketSvc: get_stock_snapshot(ticker, horizon)
    MarketSvc-->>WF: MarketSnapshot with resolved ticker

    par Python market reasoning
        WF->>MarketAgent: run(MarketSnapshot)
        MarketAgent-->>WF: market notes
    and Python technical analysis
        WF->>Tech: run(MarketSnapshot)
        Tech-->>WF: TechnicalAnalysis
    and Gemini news reasoning
        WF->>NewsSvc: get_company_news(resolved ticker)
        NewsSvc-->>WF: raw NewsAnalysis
        WF->>NewsAgent: run(ticker, raw NewsAnalysis)
        NewsAgent->>Gemini: generate_news_analysis(...)
        Gemini-->>NewsAgent: NewsAnalysis or None
        NewsAgent-->>WF: NewsAnalysis
    end

    WF->>Thesis: run(market, technical, news, market notes)
    Thesis->>Gemini: generate_recommendation(...)
    Gemini-->>Thesis: Recommendation or None
    Thesis-->>WF: Recommendation
    WF-->>CLI: AnalysisResponse
    CLI-->>User: Final report
```

## Fallback Behavior

Gemini is used first for:

- planning
- news interpretation
- thesis synthesis

If Gemini is unavailable or returns invalid JSON, the app falls back to deterministic logic so the local workflow can still run and tests remain stable.

## Example CLI Output

```text
Ticker: TCS
Resolved Market Ticker: TCS.NS
Horizon: 6_months
Recommendation: SELL
Confidence: 5%

Bullish:
- RSI is in a healthy range

Bearish:
- Price is below 20 DMA
- Price is below 50 DMA
- MACD is below signal line

News Sentiment: neutral (50%)

Risks:
- Market volatility can invalidate short-term signals.
```
