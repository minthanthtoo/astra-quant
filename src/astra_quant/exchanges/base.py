"""Shared exchange adapter protocol and errors."""
from __future__ import annotations

from typing import Protocol

from astra_quant.market_data.models import Candle, Interval


class ExchangeDataError(RuntimeError):
    """Raised when an exchange response cannot be used safely."""


class SpotMarketDataClient(Protocol):
    async def fetch_klines(
        self,
        symbol: str,
        interval: Interval,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[Candle]: ...
