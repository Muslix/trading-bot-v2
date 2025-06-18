"""
Base classes for Data Source plugins using the Universal Pattern.
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from src.core import UniversalPlugin, ModuleConfig


@dataclass
class DataSourceConfig(ModuleConfig):
    """Configuration for Data Source plugins"""
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    cache_ttl_seconds: int = 300  # 5 minutes default
    symbols: Optional[List[str]] = None
    default_period: str = "2y"
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC", "ETH", "BNB", "ADA", "DOT"]


class DataSourcePlugin(UniversalPlugin):
    """
    Base class for all data source plugins.
    
    Each data source (Yahoo Finance, CoinGecko, Binance, etc.) 
    implements this interface.
    """
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.config: DataSourceConfig = config
        self.cache: Dict[str, Any] = {}
        self.last_cache_update: Dict[str, datetime] = {}
    
    @property
    def plugin_type(self) -> str:
        return "data_source"
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "2y"
    ) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol"""
        pass
    
    @abstractmethod
    async def get_volume_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get volume data for a symbol"""
        pass
    
    @abstractmethod
    async def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get market cap for a symbol"""
        pass
        
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal execute method - handles different data requests
        """
        operation = data.get('operation', 'get_current_price')
        symbol = data.get('symbol', 'BTC')
        
        try:
            if operation == 'get_current_price':
                price = await self.get_current_price(symbol)
                return {
                    'success': True,
                    'data': {'price': price, 'symbol': symbol},
                    'source': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'get_historical_data':
                period = data.get('period', self.config.default_period)
                hist_data = await self.get_historical_data(symbol, period)
                return {
                    'success': True,
                    'data': {
                        'historical_data': hist_data.to_dict() if hist_data is not None else None,
                        'symbol': symbol,
                        'period': period
                    },
                    'source': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'get_volume_data':
                volume_data = await self.get_volume_data(symbol)
                return {
                    'success': True,
                    'data': {'volume_data': volume_data, 'symbol': symbol},
                    'source': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'get_market_cap':
                market_cap = await self.get_market_cap(symbol)
                return {
                    'success': True,
                    'data': {'market_cap': market_cap, 'symbol': symbol},
                    'source': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                return {
                    'success': False,
                    'error': f"Unknown operation: {operation}",
                    'source': self.name,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'source': self.name,
                'timestamp': datetime.now().isoformat()
            }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.last_cache_update:
            return False
        
        last_update = self.last_cache_update[cache_key]
        cache_age = (datetime.now() - last_update).total_seconds()
        return cache_age < self.config.cache_ttl_seconds
    
    def _update_cache(self, cache_key: str, data: Any) -> None:
        """Update cache with new data"""
        self.cache[cache_key] = data
        self.last_cache_update[cache_key] = datetime.now()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache.get(cache_key)
        return None