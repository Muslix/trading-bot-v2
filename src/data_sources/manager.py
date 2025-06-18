"""
Data Source Manager - orchestrates all data source plugins using the Universal Pattern.

This manager provides a unified interface to access data from multiple sources
like Yahoo Finance, CoinGecko, Binance, etc.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core import UniversalManager, ModuleConfig
from .base import DataSourceConfig
from .plugins import (
    YahooFinancePlugin,
    CoinGeckoPlugin,
    BinancePlugin
)


class DataSourceManager(UniversalManager):
    """
    Manager for all data source plugins.
    
    Provides unified access to multiple data sources with automatic
    fallback, caching, and load balancing.
    """
    
    def __init__(self):
        super().__init__("data_sources")
        self.logger = logging.getLogger(__name__)
        self.default_sources = ["yahoo_finance", "coingecko", "binance"]
        self.fallback_order = ["yahoo_finance", "coingecko", "binance"]
    
    async def initialize(self):
        """Initialize all data source plugins with default configurations"""
        await self._register_default_plugins()
        await super().initialize()
        self.logger.info(f"Initialized {len(self.plugins)} data source plugins")
    
    async def _register_default_plugins(self):
        """Register default data source plugins"""
        # Yahoo Finance - free, reliable for historical data
        yahoo_config = DataSourceConfig(
            enabled=True,
            priority=1,
            rate_limit_per_minute=60,
            cache_ttl_seconds=300,
            custom_settings={"use_cache": True}
        )
        self.factory.register("yahoo_finance", YahooFinancePlugin)
        
        # CoinGecko - free API with good current prices
        coingecko_config = DataSourceConfig(
            enabled=True,
            priority=2,
            rate_limit_per_minute=50,
            cache_ttl_seconds=60,
            custom_settings={"free_tier": True}
        )
        self.factory.register("coingecko", CoinGeckoPlugin)
        
        # Binance - high-frequency data, requires API key
        binance_config = DataSourceConfig(
            enabled=True,
            priority=3,
            rate_limit_per_minute=1200,
            cache_ttl_seconds=30,
            custom_settings={"requires_api_key": True}
        )
        self.factory.register("binance", BinancePlugin)
        
        # Create instances
        self.plugins["yahoo_finance"] = self.factory.create("yahoo_finance", yahoo_config)
        self.plugins["coingecko"] = self.factory.create("coingecko", coingecko_config)
        self.plugins["binance"] = self.factory.create("binance", binance_config)
    
    async def get_current_price(
        self, 
        symbol: str, 
        sources: Optional[List[str]] = None
    ) -> Optional[float]:
        """
        Get current price with automatic fallback between sources
        """
        if sources is None:
            sources = self.fallback_order
        
        for source in sources:
            if source not in self.plugins:
                continue
                
            try:
                result = await self.plugins[source].execute({
                    'operation': 'get_current_price',
                    'symbol': symbol
                })
                
                if result.get('success') and result.get('data', {}).get('price') is not None:
                    self.logger.info(f"Got price for {symbol} from {source}: ${result['data']['price']}")
                    return result['data']['price']
                    
            except Exception as e:
                self.logger.warning(f"Failed to get price from {source}: {e}")
                continue
        
        self.logger.error(f"Could not get price for {symbol} from any source")
        return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "2y",
        preferred_source: str = "yahoo_finance"
    ):
        """
        Get historical data, preferring Yahoo Finance for reliability
        """
        if preferred_source in self.plugins:
            try:
                result = await self.plugins[preferred_source].execute({
                    'operation': 'get_historical_data',
                    'symbol': symbol,
                    'period': period
                })
                
                if result.get('success'):
                    return result['data']['historical_data']
                    
            except Exception as e:
                self.logger.warning(f"Failed to get historical data from {preferred_source}: {e}")
        
        # Fallback to other sources
        for source in self.fallback_order:
            if source == preferred_source or source not in self.plugins:
                continue
                
            try:
                result = await self.plugins[source].execute({
                    'operation': 'get_historical_data',
                    'symbol': symbol,
                    'period': period
                })
                
                if result.get('success'):
                    return result['data']['historical_data']
                    
            except Exception as e:
                self.logger.warning(f"Failed to get historical data from {source}: {e}")
                continue
        
        return None
    
    async def get_multiple_prices(
        self, 
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple symbols efficiently
        """
        tasks = []
        for symbol in symbols:
            task = self.get_current_price(symbol)
            tasks.append((symbol, task))
        
        results = {}
        for symbol, task in tasks:
            try:
                price = await task
                results[symbol] = price
            except Exception as e:
                self.logger.error(f"Failed to get price for {symbol}: {e}")
                results[symbol] = None
        
        return results
    
    async def get_market_data_summary(
        self, 
        symbols: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive market data for multiple symbols
        """
        results = {}
        
        for symbol in symbols:
            try:
                # Get data from all sources concurrently
                price_task = self.get_current_price(symbol)
                
                # Try to get volume and market cap from CoinGecko
                volume_task = None
                market_cap_task = None
                
                if "coingecko" in self.plugins:
                    volume_task = self.plugins["coingecko"].execute({
                        'operation': 'get_volume_data',
                        'symbol': symbol
                    })
                    market_cap_task = self.plugins["coingecko"].execute({
                        'operation': 'get_market_cap',
                        'symbol': symbol
                    })
                
                # Await all tasks
                price = await price_task
                volume_data = await volume_task if volume_task else None
                market_cap_data = await market_cap_task if market_cap_task else None
                
                results[symbol] = {
                    'price': price,
                    'volume': volume_data.get('data', {}).get('volume_data') if volume_data and volume_data.get('success') else None,
                    'market_cap': market_cap_data.get('data', {}).get('market_cap') if market_cap_data and market_cap_data.get('success') else None,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get market data for {symbol}: {e}")
                results[symbol] = {
                    'price': None,
                    'volume': None,
                    'market_cap': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all data sources
        """
        health_status = await super().health_check_all()
        
        # Add specific data source health checks
        test_symbol = "BTC"
        source_availability = {}
        
        for source_name, plugin in self.plugins.items():
            try:
                # Test if we can get a price
                result = await plugin.execute({
                    'operation': 'get_current_price',
                    'symbol': test_symbol
                })
                
                source_availability[source_name] = {
                    'available': result.get('success', False),
                    'response_time': result.get('response_time', 'unknown'),
                    'last_error': result.get('error') if not result.get('success') else None
                }
                
            except Exception as e:
                source_availability[source_name] = {
                    'available': False,
                    'response_time': 'timeout',
                    'last_error': str(e)
                }
        
        return {
            'module_health': health_status,
            'source_availability': source_availability,
            'total_sources': len(self.plugins),
            'available_sources': sum(1 for status in source_availability.values() if status['available']),
            'timestamp': datetime.now().isoformat()
        }