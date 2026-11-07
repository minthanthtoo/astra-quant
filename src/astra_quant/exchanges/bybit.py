"""Bybit public spot klines adapter; no authenticated endpoints."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

import httpx

from astra_quant.exchanges.base import ExchangeDataError
from astra_quant.market_data.models import Candle, Interval


class BybitSpotClient:
    BASE_URL = "https://api.bybit.com"

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
        limit: int = 200,
    ) -> list[Candle]:
        if not 1 <= limit <= 1000:
            raise ValueError("Bybit kline limit must be between 1 and 1000.")
        params: dict[str, str | int] = {
            "category": "spot",
            "symbol": symbol.upper(),
            "interval": "60" if interval is Interval.ONE_HOUR else "240",
            "limit": limit,
        }
        if start_time is not None:
            params["start"] = start_time
        if end_time is not None:
            params["end"] = end_time
        try:
            response = await self._client.get("/v5/market/kline", params=params)
            response.raise_for_status()
            payload = response.json()
            result = payload.get("result", {}) if isinstance(payload, dict) else {}
            if payload.get("retCode") != 0 or not isinstance(result.get("list"), list):
                raise ExchangeDataError("Unexpected Bybit kline response.")
            rows = result["list"]
            candles = [
                Candle(
                    exchange="bybit",
                    symbol=symbol.upper(),
                    interval=interval,
                    open_time=int(row[0]),
                    close_time=int(row[0]) + (3_600_000 if interval is Interval.ONE_HOUR else 14_400_000) - 1,
                    open=Decimal(row[1]),
                    high=Decimal(row[2]),
                    low=Decimal(row[3]),
                    close=Decimal(row[4]),
                    volume=Decimal(row[5]),
                    quote_volume=Decimal(row[6]),
                )
                for row in rows
                if isinstance(row, list) and len(row) >= 7
            ]
            if len(candles) != len(rows):
                raise ExchangeDataError("Malformed Bybit kline row.")
            return sorted(candles, key=lambda candle: candle.open_time)
        except (httpx.HTTPError, ValueError, InvalidOperation, IndexError, TypeError) as exc:
            raise ExchangeDataError(f"Bybit market-data request failed: {exc}") from exc
