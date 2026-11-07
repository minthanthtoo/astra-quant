"""Binance public spot klines adapter; no authenticated endpoints."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

import httpx

from astra_quant.exchanges.base import ExchangeDataError
from astra_quant.market_data.models import Candle, Interval


class BinanceSpotClient:
    BASE_URL = "https://api.binance.com"

    def __init__(self, client: httpx.AsyncClient | None = None, timeout: float = 10.0):
        self._client = client or httpx.AsyncClient(base_url=self.BASE_URL, timeout=timeout)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_klines(
        self,
        symbol: str,
        interval: Interval,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> list[Candle]:
        if not 1 <= limit <= 1000:
            raise ValueError("Binance kline limit must be between 1 and 1000.")
        params: dict[str, str | int] = {
            "symbol": symbol.upper(),
            "interval": interval.value,
            "limit": limit,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        try:
            response = await self._client.get("/api/v3/klines", params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ExchangeDataError("Unexpected Binance kline response.")
            candles = [
                Candle(
                    exchange="binance",
                    symbol=symbol.upper(),
                    interval=interval,
                    open_time=int(row[0]),
                    close_time=int(row[6]),
                    open=Decimal(row[1]),
                    high=Decimal(row[2]),
                    low=Decimal(row[3]),
                    close=Decimal(row[4]),
                    volume=Decimal(row[5]),
                    quote_volume=Decimal(row[7]),
                    trades=int(row[8]),
                )
                for row in payload
                if isinstance(row, list) and len(row) >= 9
            ]
            if len(candles) != len(payload):
                raise ExchangeDataError("Malformed Binance kline row.")
            return candles
        except (httpx.HTTPError, ValueError, InvalidOperation, IndexError, TypeError) as exc:
            raise ExchangeDataError(f"Binance market-data request failed: {exc}") from exc
