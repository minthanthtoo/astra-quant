from decimal import Decimal

import pytest

from astra_quant.market_data.models import Candle, Interval
from astra_quant.strategy.baseline import BaselineTrendStrategy, DecisionAction, StrategyConfig
from astra_quant.strategy.indicators import atr, ema, rsi


def make_candles(interval: Interval, count: int, *, rising: bool = True) -> list[Candle]:
    step = 3_600_000 if interval == Interval.ONE_HOUR else 14_400_000
    result = []
    for index in range(count):
        price = Decimal(str(100 + index if rising else 100 - index * 0.1))
        result.append(Candle(
            exchange="test", symbol="BTCUSDT", interval=interval,
            open_time=index * step, close_time=(index + 1) * step - 1,
            open=price, high=price + Decimal("1"), low=price - Decimal("1"),
            close=price, volume=Decimal("10"),
        ))
    return result


def test_ema_returns_seeded_latest_value() -> None:
    assert ema([1.0, 2.0, 3.0, 4.0], 3) == pytest.approx(3.0)


def test_rsi_handles_gain_only_and_flat_series() -> None:
    assert rsi([float(i) for i in range(16)], 14) == pytest.approx(100.0)
    assert rsi([5.0] * 15, 14) == pytest.approx(50.0)


def test_atr_uses_previous_close() -> None:
    assert atr([11, 12, 13], [9, 10, 11], [10, 11, 12], 2) == pytest.approx(2.0)


def test_indicator_rejects_insufficient_data() -> None:
    with pytest.raises(ValueError, match="observations"):
        ema([1.0], 2)


def test_strategy_waits_for_warmup() -> None:
    strategy = BaselineTrendStrategy(StrategyConfig(trend_fast_ema=3, trend_slow_ema=5))
    decision = strategy.evaluate(
        make_candles(Interval.FOUR_HOUR, 4), make_candles(Interval.ONE_HOUR, 20),
        in_position=False,
    )
    assert decision.action == DecisionAction.WAIT
    assert decision.reasons == ("insufficient_warmup_data",)


def test_strategy_enters_only_when_trend_and_confirmation_align() -> None:
    strategy = BaselineTrendStrategy(StrategyConfig(trend_fast_ema=3, trend_slow_ema=5))
    decision = strategy.evaluate(
        make_candles(Interval.FOUR_HOUR, 10), make_candles(Interval.ONE_HOUR, 20),
        in_position=False,
    )
    assert decision.action == DecisionAction.ENTER_LONG
    assert decision.reference_price is not None


def test_strategy_exits_when_higher_timeframe_trend_fails() -> None:
    strategy = BaselineTrendStrategy(StrategyConfig(trend_fast_ema=3, trend_slow_ema=5))
    decision = strategy.evaluate(
        make_candles(Interval.FOUR_HOUR, 10, rising=False),
        make_candles(Interval.ONE_HOUR, 20), in_position=True,
    )
    assert decision.action == DecisionAction.EXIT_LONG
    assert "higher_timeframe_trend_lost" in decision.reasons


def test_strategy_rejects_mixed_intervals() -> None:
    with pytest.raises(ValueError, match="Expected only"):
        BaselineTrendStrategy().evaluate(
            make_candles(Interval.ONE_HOUR, 200), make_candles(Interval.ONE_HOUR, 20),
            in_position=False,
        )
