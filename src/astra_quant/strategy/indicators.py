"""Small, deterministic technical indicators used by baseline strategies."""
from __future__ import annotations

from collections.abc import Sequence


def _validate(values: Sequence[float], minimum: int) -> None:
    if len(values) < minimum:
        raise ValueError(f"At least {minimum} observations are required.")
    if any(not isinstance(value, (int, float)) or not _is_finite(value) for value in values):
        raise ValueError("Indicator inputs must be finite numbers.")


def _is_finite(value: float) -> bool:
    return value == value and abs(value) != float("inf")


def ema(values: Sequence[float], period: int) -> float:
    """Return the latest EMA, seeded with the first period's simple average."""
    if period < 1:
        raise ValueError("EMA period must be positive.")
    _validate(values, period)
    result = sum(values[:period]) / period
    alpha = 2.0 / (period + 1.0)
    for value in values[period:]:
        result = alpha * value + (1.0 - alpha) * result
    return result


def rsi(values: Sequence[float], period: int = 14) -> float:
    """Return latest Wilder RSI; flat series return 50 and gain-only returns 100."""
    if period < 1:
        raise ValueError("RSI period must be positive.")
    _validate(values, period + 1)
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]
    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:], strict=True):
        average_gain = ((period - 1) * average_gain + gain) / period
        average_loss = ((period - 1) * average_loss + loss) / period
    if average_loss == 0:
        return 50.0 if average_gain == 0 else 100.0
    relative_strength = average_gain / average_loss
    return 100.0 - 100.0 / (1.0 + relative_strength)


def atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float:
    """Return latest Wilder ATR from equally sized high, low and close series."""
    if period < 1:
        raise ValueError("ATR period must be positive.")
    if not (len(highs) == len(lows) == len(closes)) or len(closes) < period + 1:
        raise ValueError("ATR requires equal series with at least period + 1 values.")
    _validate(highs, period + 1)
    _validate(lows, period + 1)
    _validate(closes, period + 1)
    true_ranges = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(closes))
    ]
    result = sum(true_ranges[:period]) / period
    for true_range in true_ranges[period:]:
        result = ((period - 1) * result + true_range) / period
    return result
