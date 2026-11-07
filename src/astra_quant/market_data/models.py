"""Exchange-independent market data models."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Interval(StrEnum):
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"


@dataclass(frozen=True, slots=True)
class Candle:
    """A single OHLCV candle; timestamps are UTC Unix milliseconds."""

    exchange: str
    symbol: str
    interval: Interval
    open_time: int
    close_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal | None = None
    trades: int | None = None

    def __post_init__(self) -> None:
        if self.open_time < 0 or self.close_time < self.open_time:
            raise ValueError("Invalid candle timestamps.")
        if min(self.open, self.high, self.low, self.close, self.volume) < 0:
            raise ValueError("OHLCV values cannot be negative.")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("Candle high is inconsistent with OHLC values.")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("Candle low is inconsistent with OHLC values.")
        if self.trades is not None and self.trades < 0:
            raise ValueError("Trade count cannot be negative.")
