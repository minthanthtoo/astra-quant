"""Single-asset, long-only backtester with next-bar execution and trading costs."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, stdev

from astra_quant.market_data.models import Candle, Interval
from astra_quant.strategy.baseline import Decision, DecisionAction


@dataclass(frozen=True, slots=True)
class Trade:
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    quantity: float
    net_pnl: float
    return_fraction: float


@dataclass(frozen=True, slots=True)
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    completed_trades: tuple[Trade, ...]
    equity_curve: tuple[tuple[int, float], ...]
    open_position_quantity: float


class Backtester:
    """Backtest close-time decisions at the next candle open; never fills on signal close."""

    def __init__(
        self,
        *,
        initial_cash: float = 1_000.0,
        fee_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        bars_per_year: int = 365 * 24,
    ) -> None:
        if initial_cash <= 0 or not 0 <= fee_rate < 1 or not 0 <= slippage_rate < 0.1:
            raise ValueError("Invalid capital, fee, or slippage configuration.")
        if bars_per_year < 1:
            raise ValueError("bars_per_year must be positive.")
        self.initial_cash = initial_cash
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.bars_per_year = bars_per_year

    def run(self, candles: list[Candle], decisions: list[Decision]) -> BacktestResult:
        self._validate_candles(candles)
        decision_by_execution_index: dict[int, Decision] = {}
        close_to_index = {candle.close_time: i for i, candle in enumerate(candles)}
        for decision in decisions:
            if decision.action not in (DecisionAction.ENTER_LONG, DecisionAction.EXIT_LONG):
                continue
            if decision.timestamp not in close_to_index:
                raise ValueError("Every actionable decision must reference a candle close_time.")
            signal_index = close_to_index[decision.timestamp]
            execution_index = signal_index + 1
            if execution_index < len(candles):
                if execution_index in decision_by_execution_index:
                    raise ValueError("Only one actionable decision is allowed per execution bar.")
                decision_by_execution_index[execution_index] = decision

        cash = self.initial_cash
        quantity = 0.0
        entry_price = 0.0
        entry_time = 0
        entry_cost = 0.0
        trades: list[Trade] = []
        equity_curve: list[tuple[int, float]] = []

        for index, candle in enumerate(candles):
            decision = decision_by_execution_index.get(index)
            if decision is not None and decision.action == DecisionAction.ENTER_LONG and quantity == 0:
                fill = float(candle.open) * (1.0 + self.slippage_rate)
                quantity = cash / (fill * (1.0 + self.fee_rate))
                entry_cost = quantity * fill * (1.0 + self.fee_rate)
                cash = 0.0
                entry_price = fill
                entry_time = candle.open_time
            elif decision is not None and decision.action == DecisionAction.EXIT_LONG and quantity > 0:
                fill = float(candle.open) * (1.0 - self.slippage_rate)
                proceeds = quantity * fill * (1.0 - self.fee_rate)
                net_pnl = proceeds - entry_cost
                trades.append(Trade(
                    entry_time=entry_time, exit_time=candle.open_time,
                    entry_price=entry_price, exit_price=fill, quantity=quantity,
                    net_pnl=net_pnl, return_fraction=net_pnl / entry_cost,
                ))
                cash = proceeds
                quantity = 0.0
                entry_cost = 0.0
            equity = cash + quantity * float(candle.close)
            equity_curve.append((candle.close_time, equity))

        values = [value for _, value in equity_curve]
        peaks: list[float] = []
        peak = self.initial_cash
        for value in values:
            peak = max(peak, value)
            peaks.append(peak)
        drawdowns = [(peak_value - value) / peak_value for peak_value, value in zip(peaks, values)]
        returns = [values[i] / values[i - 1] - 1.0 for i in range(1, len(values)) if values[i - 1] > 0]
        volatility = stdev(returns) if len(returns) > 1 else 0.0
        sharpe = mean(returns) / volatility * sqrt(self.bars_per_year) if volatility > 0 else 0.0
        final_equity = values[-1]
        return BacktestResult(
            initial_cash=self.initial_cash, final_equity=final_equity,
            total_return=final_equity / self.initial_cash - 1.0,
            max_drawdown=max(drawdowns, default=0.0), sharpe_ratio=sharpe,
            completed_trades=tuple(trades), equity_curve=tuple(equity_curve),
            open_position_quantity=quantity,
        )

    @staticmethod
    def _validate_candles(candles: list[Candle]) -> None:
        if len(candles) < 2:
            raise ValueError("At least two candles are required for next-bar execution.")
        interval = candles[0].interval
        symbol = candles[0].symbol
        if interval != Interval.ONE_HOUR:
            raise ValueError("The initial backtester accepts 1-hour execution candles only.")
        if any(candle.interval != interval or candle.symbol != symbol for candle in candles):
            raise ValueError("Backtest candles must share one symbol and interval.")
        if any(candles[i].open_time >= candles[i + 1].open_time for i in range(len(candles) - 1)):
            raise ValueError("Backtest candles must be strictly chronological.")
