"""
Binance Data Source Plugin
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from ..base import DataSourcePlugin, DataSourceConfig


class BinancePlugin(DataSourcePlugin):
    """
    Binance data source plugin.
    
    Provides high-frequency price data and volume information.
    Can work without API key for public endpoints.
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Binance symbol mapping
        self.binance_symbol_mapping = {
            "BTC": "BTCUSDT",
            "ETH": "ETHUSDT",
            "BNB": "BNBUSDT",
            "ADA": "ADAUSDT",
            "DOT": "DOTUSDT",
            "XRP": "XRPUSDT",
            "LTC": "LTCUSDT",
            "LINK": "LINKUSDT",
            "BCH": "BCHUSDT",
            "XLM": "XLMUSDT",
            "DOGE": "DOGEUSDT",
            "UNI": "UNIUSDT",
            "THETA": "THETAUSDT",
            "VET": "VETUSDT",
            "FIL": "FILUSDT",
            "TRX": "TRXUSDT",
            "ETC": "ETCUSDT",
            "XMR": "XMRUSDT",
            "SOL": "SOLUSDT",
            "AAVE": "AAVEUSDT",
            "EOS": "EOSUSDT",
            "ATOM": "ATOMUSDT",
            "MKR": "MKRUSDT",
            "COMP": "COMPUSDT",
            "ZEC": "ZECUSDT",
            "DASH": "DASHUSDT"
        }
        
        self.base_url = "https://api.binance.com/api/v3"
        self.session = None
    
    async def _initialize(self) -> bool:
        """Initialize the Binance plugin"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test connection
            async with self.session.get(f"{self.base_url}/ping") as response:
                if response.status == 200:
                    self.logger.info("Binance plugin initialized successfully")
                    return True
                else:
                    self.logger.error(f"Binance ping failed with status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Binance plugin initialization failed: {e}")
            return False
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Internal execute method - delegates to parent execute"""
        return await self.execute(data)
    
    def _get_binance_symbol(self, symbol: str) -> str:
        """Convert crypto symbol to Binance format"""
        return self.binance_symbol_mapping.get(symbol.upper(), f"{symbol.upper()}USDT")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Binance"""
        cache_key = f"price_{symbol}"
        
        # Check cache first
        cached_price = self._get_from_cache(cache_key)
        if cached_price is not None:
            return cached_price
        
        if not self.session:
            await self._initialize()
        
        try:
            binance_symbol = self._get_binance_symbol(symbol)
            
            url = f"{self.base_url}/ticker/price"
            params = {'symbol': binance_symbol}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'price' in data:
                        price = float(data['price'])
                        self._update_cache(cache_key, price)
                        return price
                
                elif response.status == 429:
                    self.logger.warning("Binance rate limit hit")
                    await asyncio.sleep(1)
                    return await self.get_current_price(symbol)
                
                else:
                    self.logger.error(f"Binance API error: {response.status}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol} from Binance: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get historical data from Binance"""
        cache_key = f"historical_{symbol}_{period}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        if not self.session:
            await self._initialize()
        
        try:
            binance_symbol = self._get_binance_symbol(symbol)
            
            # Convert period to Binance format
            interval_map = {
                "1d": "1d",
                "7d": "1d", 
                "30d": "1d",
                "90d": "1d",
                "1y": "1d",
                "2y": "1d",
                "5y": "1w"
            }
            interval = interval_map.get(period, "1d")
            
            # Calculate limit based on period
            limit_map = {
                "1d": 24,
                "7d": 7,
                "30d": 30,
                "90d": 90,
                "1y": 365,
                "2y": 730,
                "5y": 260  # 5 years in weeks
            }
            limit = min(limit_map.get(period, 730), 1000)  # Binance max is 1000
            
            url = f"{self.base_url}/klines"
            params = {
                'symbol': binance_symbol,
                'interval': interval,
                'limit': limit
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data:
                        # Convert to DataFrame
                        df = pd.DataFrame(data, columns=[
                            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                            'close_time', 'quote_volume', 'trades', 'buy_base_volume',
                            'buy_quote_volume', 'ignore'
                        ])
                        
                        # Convert timestamp to datetime
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        
                        # Convert price columns to float
                        price_columns = ['Open', 'High', 'Low', 'Close']
                        for col in price_columns:
                            df[col] = df[col].astype(float)
                        
                        df['Volume'] = df['Volume'].astype(float)
                        
                        # Keep only relevant columns
                        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                        
                        # Cache the data
                        self._update_cache(cache_key, df)
                        return df
                
                elif response.status == 429:
                    self.logger.warning("Binance rate limit hit for historical data")
                    await asyncio.sleep(1)
                    return await self.get_historical_data(symbol, period)
                
                else:
                    self.logger.error(f"Binance historical data API error: {response.status}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol} from Binance: {e}")
            return None
    
    async def get_volume_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get volume data from Binance"""
        if not self.session:
            await self._initialize()
        
        try:
            binance_symbol = self._get_binance_symbol(symbol)
            
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': binance_symbol}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'volume_24h': float(data.get('volume', 0)),
                        'quote_volume_24h': float(data.get('quoteVolume', 0)),
                        'volume_change_24h': float(data.get('priceChangePercent', 0)),
                        'trade_count_24h': int(data.get('count', 0)),
                        'high_24h': float(data.get('highPrice', 0)),
                        'low_24h': float(data.get('lowPrice', 0))
                    }
                
                elif response.status == 429:
                    self.logger.warning("Binance rate limit hit for volume data")
                    await asyncio.sleep(1)
                    return await self.get_volume_data(symbol)
                
                else:
                    self.logger.error(f"Binance volume data API error: {response.status}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get volume data for {symbol} from Binance: {e}")
            return None
    
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """
        Binance doesn't provide market cap directly.
        This would require additional calculation with circulating supply.
        """
        self.logger.info(f"Market cap not available from Binance for {symbol}")
        return None
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        self.cache.clear()
        self.last_cache_update.clear()
        self.logger.info("Binance plugin cleaned up")