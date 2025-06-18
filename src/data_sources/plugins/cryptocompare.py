"""
CryptoCompare Data Source Plugin - Fallback für CoinGecko
Höhere Rate Limits und andere API-Struktur
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from ..base import DataSourcePlugin, DataSourceConfig


class CryptoComparePlugin(DataSourcePlugin):
    """
    CryptoCompare data source plugin als Fallback für CoinGecko.
    
    Vorteile:
    - Höhere Rate Limits
    - Andere API-Endpunkte
    - Gute Batch-Unterstützung
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.session = None
    
    async def _initialize(self) -> bool:
        """Initialize the CryptoCompare plugin"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection
            test_url = f"{self.base_url}/price?fsym=BTC&tsyms=USD"
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    self.logger.info("CryptoCompare plugin initialized successfully")
                    return True
                else:
                    self.logger.error(f"CryptoCompare test failed with status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"CryptoCompare plugin initialization failed: {e}")
            return False
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Internal execute method - delegates to parent execute"""
        return await self.execute(data)
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get multiple prices in one API call"""
        if not symbols:
            return {}
            
        if not self.session:
            await self._initialize()
        
        # Check cache first
        results = {}
        uncached_symbols = []
        
        for symbol in symbols:
            cache_key = f"price_{symbol}"
            cached_price = self._get_from_cache(cache_key)
            if cached_price is not None:
                results[symbol] = cached_price
            else:
                uncached_symbols.append(symbol)
        
        if not uncached_symbols:
            return results
        
        try:
            # CryptoCompare batch request - up to 300 symbols!
            symbols_str = ','.join(uncached_symbols)
            url = f"{self.base_url}/pricemultifull"
            params = {
                'fsyms': symbols_str,
                'tsyms': 'USD'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'RAW' in data:
                        raw_data = data['RAW']
                        
                        for symbol in uncached_symbols:
                            if symbol in raw_data and 'USD' in raw_data[symbol]:
                                usd_data = raw_data[symbol]['USD']
                                price = float(usd_data['PRICE'])
                                results[symbol] = price
                                
                                # Cache with 10 minute duration
                                cache_key = f"price_{symbol}"
                                self._update_cache(cache_key, price)
                                
                                # Also cache market data
                                market_cap = usd_data.get('MKTCAP', 0)
                                volume_24h = usd_data.get('TOTALVOLUME24HTO', 0)
                                
                                market_cache_key = f"market_{symbol}"
                                market_data = {
                                    'market_cap': market_cap,
                                    'total_volume_24h': volume_24h,
                                    'price': price
                                }
                                self._update_cache(market_cache_key, market_data)
                
                elif response.status == 429:
                    self.logger.warning("CryptoCompare rate limit hit")
                    await asyncio.sleep(5)
                    return await self.get_multiple_prices(symbols)
                
                else:
                    self.logger.error(f"CryptoCompare API error: {response.status}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get batch prices from CryptoCompare: {e}")
            return results
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for single symbol"""
        batch_result = await self.get_multiple_prices([symbol])
        return batch_result.get(symbol)
    
    async def get_volume_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get volume data (uses cached data from batch request)"""
        market_cache_key = f"market_{symbol}"
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return {
                'total_volume_24h': cached_market_data.get('total_volume_24h'),
                'market_cap': cached_market_data.get('market_cap'),
                'volume_change_24h': 0,
                'market_cap_change_24h': 0
            }
        
        # Fallback: get fresh data
        await self.get_multiple_prices([symbol])
        
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return {
                'total_volume_24h': cached_market_data.get('total_volume_24h'),
                'market_cap': cached_market_data.get('market_cap'),
                'volume_change_24h': 0,
                'market_cap_change_24h': 0
            }
        
        return None
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get historical data (not implemented for CryptoCompare yet)"""
        self.logger.warning(f"Historical data not implemented for CryptoCompare yet for {symbol}")
        return None
    
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get market cap (uses cached data from batch request)"""
        market_cache_key = f"market_{symbol}"
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return cached_market_data.get('market_cap')
        
        # Fallback: get fresh data
        await self.get_multiple_prices([symbol])
        
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return cached_market_data.get('market_cap')
        
        return None
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.cache.clear()
        self.last_cache_update.clear()
        self.logger.info("CryptoCompare plugin cleaned up")