# Astra Quant

AI-assisted quantitative research and crypto spot trading platform.

## Operating principles

- **Astra is the research director**, not the trading execution authority.
- A deterministic Python engine owns signals, portfolio state, risk checks, and order execution.
- Initial scope: Binance and Bybit spot market data; BTC/USDT 4H trend with 1H confirmation.
- No leverage. Paper trading only. Live trading is disabled by design.
- No strategy is considered profitable without reproducible, cost-aware out-of-sample evidence.

## Development status

This repository is at the engineering-foundation stage. A documented architecture is not evidence of an implemented or validated trading system.

| Milestone | Scope | Status |
|---|---|---|
| M0 | Architecture and acceptance criteria | Specified; implementation review pending |
| M1 | Repository, CI, configuration, tests | In progress |
| M2 | Exchange adapters and normalized data | Not started |
| M3 | Indicators and BTC strategy | Not started |
| M4 | Backtesting and statistical validation | Not started |
| M5 | Risk engine and paper execution | Not started |
| M6 | Astra research director | Not started |
| M7 | Dashboard and monitoring | Not started |
| M8 | Security and release audit | Not started |

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
ruff check .
```

## Safety

Never commit API keys, exchange secrets, account identifiers, or production credentials. Use read-only exchange keys for data ingestion. Paper trading must remain the only enabled execution mode until the user explicitly authorizes a separately reviewed deployment after validation.

See [SECURITY.md](SECURITY.md) and [docs/architecture/overview.md](docs/architecture/overview.md).
