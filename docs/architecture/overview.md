# Architecture Overview

## Core separation

1. **Data layer** — obtains exchange data and normalizes it into canonical market records.
2. **Research layer** — creates hypotheses, factors, and candidate strategies.
3. **Validation layer** — runs reproducible backtests and statistical checks.
4. **Deterministic trading engine** — computes signals, enforces risk, tracks orders, and operates paper execution.
5. **Astra research director** — plans and reviews research tasks; it has no direct execution authority.
6. **Operations layer** — monitoring, audit logs, configuration, and dashboard.

## Initial strategy scope

- Market: BTC/USDT spot.
- Primary timeframe: 4H trend.
- Confirmation timeframe: 1H.
- Exchanges: Binance and Bybit.
- Leverage: prohibited.
- Execution: paper only.

## Non-negotiable invariants

- No look-ahead data in signal generation or backtests.
- Include fees, spread, and slippage assumptions in performance evaluation.
- Keep training, validation, and final test periods chronologically separated.
- Preserve experiment parameters, data versions, code revision, and results.
- AI cannot override risk limits or execution-mode controls.
- Fail closed when market data, state, or risk checks are uncertain.

## Build sequence

M1 establishes reproducible engineering. M2 establishes trustworthy data. M3 implements a baseline strategy. M4 tests whether it has robust evidence of incremental value. M5 adds paper execution. M6 adds AI-directed research only after the deterministic foundation exists.
