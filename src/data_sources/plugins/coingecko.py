"""
CoinGecko Data Source Plugin
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..base import DataSourcePlugin, DataSourceConfig


class CoinGeckoPlugin(DataSourcePlugin):
    """
    CoinGecko data source plugin.
    
    Provides current prices, market caps, and volume data.
    Free API with rate limits.
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # CoinGecko ID mapping
        self.coingecko_id_mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin", 
            "ADA": "cardano",
            "DOT": "polkadot",
            "XRP": "ripple",
            "LTC": "litecoin",
            "LINK": "chainlink",
            "BCH": "bitcoin-cash",
            "XLM": "stellar",
            "DOGE": "dogecoin",
            "UNI": "uniswap",
            "THETA": "theta-token",
            "VET": "vechain",
            "FIL": "filecoin",
            "TRX": "tron",
            "ETC": "ethereum-classic",
            "XMR": "monero",
            "SOL": "solana",
            "AAVE": "aave",
            "EOS": "eos",
            "ATOM": "cosmos",
            "MKR": "maker",
            "COMP": "compound-governance-token",
            "ZEC": "zcash",
            "DASH": "dash"
        }
        
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = None
    
    async def _initialize(self) -> bool:
        """Initialize the CoinGecko plugin"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection
            async with self.session.get(f"{self.base_url}/ping") as response:
                if response.status == 200:
                    self.logger.info("CoinGecko plugin initialized successfully")
                    return True
                else:
                    self.logger.error(f"CoinGecko ping failed with status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"CoinGecko plugin initialization failed: {e}")
            return False
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Internal execute method - delegates to parent execute"""
        return await self.execute(data)
    
    def _get_coingecko_id(self, symbol: str) -> str:
        """Convert crypto symbol to CoinGecko ID"""
        return self.coingecko_id_mapping.get(symbol.upper(), symbol.lower())
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from CoinGecko (single symbol - use batch for multiple)"""
        cache_key = f"price_{symbol}"
        
        # Check cache first (longer cache for rate limit relief)
        cached_price = self._get_from_cache(cache_key)
        if cached_price is not None:
            return cached_price
        
        # For single requests, use the batch method with one symbol
        batch_result = await self.get_multiple_prices([symbol])
        return batch_result.get(symbol)
    
    async def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """Get multiple prices in one API call (MUCH more efficient!)"""
        if not symbols:
            return {}
            
        if not self.session:
            await self._initialize()
        
        # Check cache first for all symbols
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
            # Convert symbols to CoinGecko IDs
            coingecko_ids = [self._get_coingecko_id(symbol) for symbol in uncached_symbols]
            
            # Batch request - up to 250 coins per request!
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coingecko_ids),
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Map results back to symbols
                    for symbol, coingecko_id in zip(uncached_symbols, coingecko_ids):
                        if coingecko_id in data and 'usd' in data[coingecko_id]:
                            price = float(data[coingecko_id]['usd'])
                            results[symbol] = price
                            
                            # Cache with longer duration (10 minutes for rate limit relief)
                            cache_key = f"price_{symbol}"
                            self._update_cache(cache_key, price)
                            
                            # Also cache market data if available
                            if 'usd_market_cap' in data[coingecko_id]:
                                market_cap = data[coingecko_id]['usd_market_cap']
                                volume_24h = data[coingecko_id].get('usd_24h_vol', 0)
                                
                                market_cache_key = f"market_{symbol}"
                                market_data = {
                                    'market_cap': market_cap,
                                    'total_volume_24h': volume_24h,
                                    'price': price
                                }
                                self._update_cache(market_cache_key, market_data)
                
                elif response.status == 429:
                    self.logger.warning("CoinGecko rate limit hit for batch request")
                    # Longer wait for batch requests
                    await asyncio.sleep(10)
                    return await self.get_multiple_prices(symbols)
                
                else:
                    self.logger.error(f"CoinGecko batch API error: {response.status}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get batch prices from CoinGecko: {e}")
            return results
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get historical data from CoinGecko"""
        cache_key = f"historical_{symbol}_{period}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        if not self.session:
            await self._initialize()
        
        try:
            coingecko_id = self._get_coingecko_id(symbol)
            
            # Convert period to days
            days_map = {
                "1d": 1,
                "7d": 7,
                "30d": 30,
                "90d": 90,
                "1y": 365,
                "2y": 730,
                "5y": 1825
            }
            days = days_map.get(period, 730)  # Default to 2 years
            
            url = f"{self.base_url}/coins/{coingecko_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily' if days > 90 else 'hourly'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'prices' in data:
                        # Convert to DataFrame
                        prices = data['prices']
                        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        df.rename(columns={'price': 'Close'}, inplace=True)
                        
                        # Add volume if available
                        if 'total_volumes' in data:
                            volumes = data['total_volumes']
                            volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                            volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
                            volume_df.set_index('timestamp', inplace=True)
                            df['Volume'] = volume_df['volume']
                        
                        # Cache the data
                        self._update_cache(cache_key, df)
                        return df
                
                elif response.status == 429:
                    self.logger.warning("CoinGecko rate limit hit for historical data")
                    await asyncio.sleep(2)
                    return await self.get_historical_data(symbol, period)
                
                else:
                    self.logger.error(f"CoinGecko historical data API error: {response.status}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol} from CoinGecko: {e}")
            return None
    
    async def get_volume_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get volume data from CoinGecko (uses cached market data from batch requests)"""
        
        # Check if we have cached market data from batch request
        market_cache_key = f"market_{symbol}"
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return {
                'total_volume_24h': cached_market_data.get('total_volume_24h'),
                'market_cap': cached_market_data.get('market_cap'),
                'volume_change_24h': 0,  # Not available in simple API
                'market_cap_change_24h': 0  # Not available in simple API
            }
        
        # Fallback: get fresh data for this symbol
        await self.get_multiple_prices([symbol])  # This will cache market data
        
        # Try cache again
        cached_market_data = self._get_from_cache(market_cache_key)
        if cached_market_data is not None:
            return {
                'total_volume_24h': cached_market_data.get('total_volume_24h'),
                'market_cap': cached_market_data.get('market_cap'),
                'volume_change_24h': 0,
                'market_cap_change_24h': 0
            }
        
        return None
    
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get market cap from CoinGecko"""
        volume_data = await self.get_volume_data(symbol)
        if volume_data and 'market_cap' in volume_data:
            return volume_data['market_cap']
        return None
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.cache.clear()
        self.last_cache_update.clear()
        self.logger.info("CoinGecko plugin cleaned up")