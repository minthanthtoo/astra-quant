"""Runtime configuration with safe, paper-first defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Non-secret application settings loaded from environment variables."""

    environment: str = "development"
    trading_mode: str = "paper"
    default_symbol: str = "BTCUSDT"
    request_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> Settings:
        environment = os.getenv("ASTRA_ENV", "development").strip().lower()
        trading_mode = os.getenv("ASTRA_TRADING_MODE", "paper").strip().lower()
        symbol = os.getenv("ASTRA_DEFAULT_SYMBOL", "BTCUSDT").strip().upper()
        timeout = float(os.getenv("ASTRA_REQUEST_TIMEOUT", "10"))
        if trading_mode != "paper":
            raise ValueError("Only paper trading mode is currently supported.")
        if not symbol or timeout <= 0:
            raise ValueError("A symbol and positive request timeout are required.")
        return cls(environment, trading_mode, symbol, timeout)
