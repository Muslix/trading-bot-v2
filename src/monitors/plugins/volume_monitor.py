"""
Volume Monitor Plugin - Trading volume monitoring
"""

from typing import Dict, List, Any
import aiohttp
import logging

from ..base import BaseMonitor
from src.utils.decorators import async_log_performance


class VolumeMonitor(BaseMonitor):
    """Trading volume monitoring from exchanges"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.exchanges = config.get("exchanges", ["binance", "coinbase"])
        self.timeout = config.get("timeout", 10)
        self.volume_threshold = config.get("volume_threshold", 1000000)  # $1M default
        
    def get_monitor_type(self) -> str:
        return "volume"
        
    @async_log_performance
    async def monitor(self, target: Any, **kwargs) -> Dict[str, Any]:
        """
        Monitor trading volume for a specific symbol
        
        Args:
            target: str - Trading pair symbol (e.g., 'BTC/USDT')
            kwargs: Additional parameters
        """
        if not isinstance(target, str):
            return {"error": "Invalid target - expected trading pair symbol"}
            
        symbol = target
        
        try:
            volume_data = await self._get_volume_data(symbol)
            
            total_volume = sum(volume_data.values())
            avg_volume = total_volume / len(volume_data) if volume_data else 0
            
            return {
                "symbol": symbol,
                "volume_by_exchange": volume_data,
                "total_volume_24h": total_volume,
                "average_volume": avg_volume,
                "exchanges_count": len(volume_data),
                "high_volume_alert": total_volume > self.volume_threshold,
                "volume_distribution": self._calculate_volume_distribution(volume_data)
            }
            
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}
            
    async def _get_volume_data(self, symbol: str) -> Dict[str, float]:
        """Get 24h volume data from exchanges"""
        volume_data = {}
        
        for exchange in self.exchanges:
            try:
                volume = await self._fetch_exchange_volume(exchange, symbol)
                if volume > 0:
                    volume_data[exchange] = volume
            except Exception as e:
                self.logger.error(f"Error fetching volume from {exchange}: {e}")
                
        return volume_data
        
    async def _fetch_exchange_volume(self, exchange: str, symbol: str) -> float:
        """Fetch 24h volume from specific exchange"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if exchange.lower() == "binance":
                return await self._fetch_binance_volume(session, symbol)
            elif exchange.lower() == "coinbase":
                return await self._fetch_coinbase_volume(session, symbol)
            else:
                return 0.0
                
    async def _fetch_binance_volume(self, session: aiohttp.ClientSession, symbol: str) -> float:
        """Fetch volume from Binance"""
        binance_symbol = symbol.replace("/", "")
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return float(data.get("quoteVolume", 0))
        return 0.0
        
    async def _fetch_coinbase_volume(self, session: aiohttp.ClientSession, symbol: str) -> float:
        """Fetch volume from Coinbase"""
        cb_symbol = symbol.replace("/", "-")
        url = f"https://api.exchange.coinbase.com/products/{cb_symbol}/stats"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return float(data.get("volume", 0))
        return 0.0
        
    def _calculate_volume_distribution(self, volume_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate volume distribution percentages"""
        total_volume = sum(volume_data.values())
        if total_volume == 0:
            return {}
            
        return {
            exchange: round((volume / total_volume) * 100, 2)
            for exchange, volume in volume_data.items()
        }