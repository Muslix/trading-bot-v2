"""
Yahoo Finance Data Source Plugin
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import yfinance as yf
import warnings

from ..base import DataSourcePlugin, DataSourceConfig

warnings.filterwarnings("ignore")


class YahooFinancePlugin(DataSourcePlugin):
    """
    Yahoo Finance data source plugin.
    
    Provides reliable historical data and current prices for major cryptocurrencies.
    Free service with reasonable rate limits.
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Symbol mapping for Yahoo Finance
        self.symbol_mapping = {
            "BTC": "BTC-USD",
            "ETH": "ETH-USD", 
            "BNB": "BNB-USD",
            "ADA": "ADA-USD",
            "DOT": "DOT-USD",
            "XRP": "XRP-USD",
            "LTC": "LTC-USD",
            "LINK": "LINK-USD",
            "BCH": "BCH-USD",
            "XLM": "XLM-USD",
            "DOGE": "DOGE-USD",
            "UNI": "UNI-USD",
            "THETA": "THETA-USD",
            "VET": "VET-USD",
            "FIL": "FIL-USD",
            "TRX": "TRX-USD",
            "ETC": "ETC-USD",
            "XMR": "XMR-USD",
            "SOL": "SOL-USD",
            "AAVE": "AAVE-USD",
            "EOS": "EOS-USD",
            "ATOM": "ATOM-USD",
            "MKR": "MKR-USD",
            "COMP": "COMP-USD",
            "ZEC": "ZEC-USD",
            "DASH": "DASH-USD"
        }
    
    async def _initialize(self) -> bool:
        """Initialize the Yahoo Finance plugin"""
        try:
            # Test connection with a simple request
            test_ticker = yf.Ticker("BTC-USD")
            info = test_ticker.info
            
            if info:
                self.logger.info("Yahoo Finance plugin initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize Yahoo Finance plugin")
                return False
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance plugin initialization failed: {e}")
            return False
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Internal execute method - delegates to parent execute"""
        return await self.execute(data)
    
    def _get_yahoo_symbol(self, symbol: str) -> str:
        """Convert crypto symbol to Yahoo Finance format"""
        return self.symbol_mapping.get(symbol.upper(), f"{symbol.upper()}-USD")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Yahoo Finance"""
        cache_key = f"price_{symbol}"
        
        # Check cache first
        cached_price = self._get_from_cache(cache_key)
        if cached_price is not None:
            return cached_price
        
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yahoo_symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            current_price = info.get('regularMarketPrice') or info.get('currentPrice')
            
            if current_price:
                self._update_cache(cache_key, current_price)
                return float(current_price)
            
            # Fallback: try getting from recent history
            hist = await loop.run_in_executor(None, lambda: ticker.history(period="1d"))
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                self._update_cache(cache_key, current_price)
                return current_price
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol} from Yahoo Finance: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get historical data from Yahoo Finance"""
        cache_key = f"historical_{symbol}_{period}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yahoo_symbol)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period))
            
            if hist.empty:
                self.logger.warning(f"No historical data for {symbol} from Yahoo Finance")
                return None
            
            # Clean up the data
            hist = hist.dropna()
            hist.index = pd.to_datetime(hist.index)
            
            # Cache the data (longer TTL for historical data)
            cache_key_long = f"historical_{symbol}_{period}_long"
            self.cache[cache_key_long] = hist
            self.last_cache_update[cache_key_long] = datetime.now()
            
            return hist
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol} from Yahoo Finance: {e}")
            return None
    
    async def get_volume_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get volume data from Yahoo Finance"""
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yahoo_symbol)
            
            # Get recent data for volume
            hist = await loop.run_in_executor(None, lambda: ticker.history(period="5d"))
            
            if hist.empty or 'Volume' not in hist.columns:
                return None
            
            current_volume = float(hist['Volume'].iloc[-1])
            avg_volume_5d = float(hist['Volume'].mean())
            
            return {
                'current_volume': current_volume,
                'average_volume_5d': avg_volume_5d,
                'volume_change_24h': current_volume - float(hist['Volume'].iloc[-2]) if len(hist) > 1 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get volume data for {symbol} from Yahoo Finance: {e}")
            return None
    
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get market cap from Yahoo Finance"""
        try:
            yahoo_symbol = self._get_yahoo_symbol(symbol)
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, yahoo_symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            market_cap = info.get('marketCap')
            if market_cap:
                return float(market_cap)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get market cap for {symbol} from Yahoo Finance: {e}")
            return None
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.cache.clear()
        self.last_cache_update.clear()
        self.logger.info("Yahoo Finance plugin cleaned up")