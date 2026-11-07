from decimal import Decimal

import pytest

from astra_quant.backtesting.engine import Backtester
from astra_quant.market_data.models import Candle, Interval
from astra_quant.strategy.baseline import Decision, DecisionAction


def candles(prices: list[int]) -> list[Candle]:
    return [Candle(
        exchange="test", symbol="BTCUSDT", interval=Interval.ONE_HOUR,
        open_time=index * 3_600_000, close_time=(index + 1) * 3_600_000 - 1,
        open=Decimal(str(price)), high=Decimal(str(price + 1)),
        low=Decimal(str(price - 1)), close=Decimal(str(price)), volume=Decimal("1"),
    ) for index, price in enumerate(prices)]


def test_backtester_executes_signal_at_next_bar_open() -> None:
    data = candles([100, 100, 120, 130])
    result = Backtester(initial_cash=1_000, fee_rate=0, slippage_rate=0).run(
        data, [Decision(DecisionAction.ENTER_LONG, data[0].close_time, data[0].close, ("test",))],
    )
    assert result.open_position_quantity == pytest.approx(10)
    assert result.final_equity == pytest.approx(1_300)
    assert result.total_return == pytest.approx(0.3)


def test_backtester_accounts_for_fees_and_slippage() -> None:
    data = candles([100, 100, 100])
    decisions = [
        Decision(DecisionAction.ENTER_LONG, data[0].close_time, data[0].close, ("entry",)),
        Decision(DecisionAction.EXIT_LONG, data[1].close_time, data[1].close, ("exit",)),
    ]
    engine = Backtester(initial_cash=1_000, fee_rate=0.001, slippage_rate=0.001)
    result = engine.run(data, decisions)
    assert len(result.completed_trades) == 1
    assert result.completed_trades[0].net_pnl < 0
    assert result.final_equity < 1_000


def test_backtester_rejects_missing_signal_timestamp() -> None:
    with pytest.raises(ValueError, match="close_time"):
        Backtester().run(candles([100, 101]), [
            Decision(DecisionAction.ENTER_LONG, 123, Decimal("100"), ("bad",)),
        ])


def test_backtester_requires_hourly_execution_bars() -> None:
    data = candles([100, 101])
    four_hour = [Candle(
        exchange="test", symbol="BTCUSDT", interval=Interval.FOUR_HOUR,
        open_time=c.open_time, close_time=c.close_time, open=c.open, high=c.high,
        low=c.low, close=c.close, volume=c.volume,
    ) for c in data]
    with pytest.raises(ValueError, match="1-hour"):
        Backtester().run(four_hour, [])
