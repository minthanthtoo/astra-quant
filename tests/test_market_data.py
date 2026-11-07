from decimal import Decimal

import httpx
import pytest

from astra_quant.config import Settings
from astra_quant.exchanges.binance import BinanceSpotClient
from astra_quant.exchanges.bybit import BybitSpotClient
from astra_quant.exchanges.base import ExchangeDataError
from astra_quant.market_data.models import Candle, Interval


def test_settings_default_to_paper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASTRA_TRADING_MODE", raising=False)
    settings = Settings.from_env()
    assert settings.trading_mode == "paper"
    assert settings.default_symbol == "BTCUSDT"


def test_settings_reject_non_paper_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASTRA_TRADING_MODE", "live")
    with pytest.raises(ValueError, match="Only paper"):
        Settings.from_env()


def test_candle_rejects_inconsistent_high() -> None:
    with pytest.raises(ValueError, match="high"):
        Candle(
            exchange="test", symbol="BTCUSDT", interval=Interval.ONE_HOUR,
            open_time=0, close_time=3_599_999, open=Decimal("10"),
            high=Decimal("9"), low=Decimal("8"), close=Decimal("9"),
            volume=Decimal("1"),
        )


@pytest.mark.asyncio
async def test_binance_adapter_normalizes_kline() -> None:
    body = [[0, "10", "12", "9", "11", "5", 3_599_999, "55", 7]]
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    async with httpx.AsyncClient(transport=transport, base_url="https://test") as http:
        candles = await BinanceSpotClient(http).fetch_klines("btcusdt", Interval.ONE_HOUR)
    assert len(candles) == 1
    assert candles[0].exchange == "binance"
    assert candles[0].close == Decimal("11")
    assert candles[0].trades == 7


@pytest.mark.asyncio
async def test_bybit_adapter_sorts_and_normalizes_kline() -> None:
    body = {
        "retCode": 0,
        "result": {"list": [
            ["3600000", "11", "12", "10", "11.5", "3", "34.5"],
            ["0", "10", "12", "9", "11", "5", "55"],
        ]},
    }
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    async with httpx.AsyncClient(transport=transport, base_url="https://test") as http:
        candles = await BybitSpotClient(http).fetch_klines("BTCUSDT", Interval.ONE_HOUR)
    assert [c.open_time for c in candles] == [0, 3_600_000]
    assert candles[0].close_time == 3_599_999


@pytest.mark.asyncio
async def test_bybit_rejects_exchange_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"retCode": 10001, "result": {}})
    )
    async with httpx.AsyncClient(transport=transport, base_url="https://test") as http:
        with pytest.raises(ExchangeDataError):
            await BybitSpotClient(http).fetch_klines("BTCUSDT", Interval.ONE_HOUR)
