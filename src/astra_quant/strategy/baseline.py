"""Long-only 4h trend / 1h confirmation baseline; not a profitability claim."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from astra_quant.market_data.models import Candle, Interval
from astra_quant.strategy.indicators import ema, rsi


class DecisionAction(StrEnum):
    WAIT = "wait"
    HOLD = "hold"
    ENTER_LONG = "enter_long"
    EXIT_LONG = "exit_long"


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    trend_fast_ema: int = 50
    trend_slow_ema: int = 200
    confirmation_ema: int = 20
    rsi_period: int = 14
    rsi_minimum: float = 50.0

    def __post_init__(self) -> None:
        periods = (
            self.trend_fast_ema, self.trend_slow_ema,
            self.confirmation_ema, self.rsi_period,
        )
        if min(periods) < 2:
            raise ValueError("Indicator periods must be at least 2.")
        if self.trend_fast_ema >= self.trend_slow_ema:
            raise ValueError("Fast trend EMA must be shorter than slow trend EMA.")
        if not 0 <= self.rsi_minimum <= 100:
            raise ValueError("RSI minimum must be between 0 and 100.")


@dataclass(frozen=True, slots=True)
class Decision:
    action: DecisionAction
    timestamp: int | None
    reference_price: Decimal | None
    reasons: tuple[str, ...]


class BaselineTrendStrategy:
    """A transparent baseline. Inputs must contain completed candles only."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def evaluate(
        self,
        trend_candles: list[Candle],
        confirmation_candles: list[Candle],
        *,
        in_position: bool,
    ) -> Decision:
        self._validate_series(trend_candles, Interval.FOUR_HOUR)
        self._validate_series(confirmation_candles, Interval.ONE_HOUR)
        cfg = self.config
        required_trend = cfg.trend_slow_ema
        required_confirmation = max(cfg.confirmation_ema, cfg.rsi_period + 1)
        if len(trend_candles) < required_trend or len(confirmation_candles) < required_confirmation:
            return Decision(DecisionAction.WAIT, None, None, ("insufficient_warmup_data",))

        trend_closes = [float(candle.close) for candle in trend_candles]
        confirmation_closes = [float(candle.close) for candle in confirmation_candles]
        fast = ema(trend_closes, cfg.trend_fast_ema)
        slow = ema(trend_closes, cfg.trend_slow_ema)
        confirmation_ema = ema(confirmation_closes, cfg.confirmation_ema)
        current_rsi = rsi(confirmation_closes, cfg.rsi_period)
        latest = confirmation_candles[-1]
        trend_up = fast > slow
        confirmed = (
            confirmation_closes[-1] > confirmation_ema
            and current_rsi >= cfg.rsi_minimum
        )

        if in_position and (not trend_up or confirmation_closes[-1] < confirmation_ema):
            reasons = (
                ("higher_timeframe_trend_lost",)
                if not trend_up else ("price_below_confirmation_ema",)
            )
            return Decision(DecisionAction.EXIT_LONG, latest.close_time, latest.close, reasons)
        if not in_position and trend_up and confirmed:
            return Decision(
                DecisionAction.ENTER_LONG,
                latest.close_time,
                latest.close,
                ("higher_timeframe_uptrend", "one_hour_confirmation", "rsi_confirmation"),
            )
        return Decision(
            DecisionAction.HOLD if in_position else DecisionAction.WAIT,
            latest.close_time,
            latest.close,
            ("entry_conditions_not_met",),
        )

    @staticmethod
    def _validate_series(candles: list[Candle], interval: Interval) -> None:
        if not candles:
            raise ValueError("Candle series cannot be empty.")
        if any(candle.interval != interval for candle in candles):
            raise ValueError(f"Expected only {interval} candles.")
        if any(candles[i].open_time >= candles[i + 1].open_time for i in range(len(candles) - 1)):
            raise ValueError("Candles must be strictly chronological without duplicates.")
        if len({candle.symbol for candle in candles}) != 1:
            raise ValueError("Candle series must contain exactly one symbol.")
