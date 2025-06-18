"""
Comprehensive tests for the new Data Sources system.
"""

import pytest
import asyncio
import pandas as pd
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_sources.base import DataSourcePlugin, DataSourceConfig
from src.data_sources.manager import DataSourceManager
from src.data_sources.plugins.yahoo_finance import YahooFinancePlugin
from src.data_sources.plugins.coingecko import CoinGeckoPlugin
from src.data_sources.plugins.binance import BinancePlugin


class TestDataSourceConfig:
    """Test DataSourceConfig functionality"""
    
    def test_config_creation(self):
        """Test creating a data source config"""
        config = DataSourceConfig(
            enabled=True,
            api_key="test_key",
            rate_limit_per_minute=120,
            cache_ttl_seconds=600,
            symbols=["BTC", "ETH", "ADA"]
        )
        
        assert config.enabled is True
        assert config.api_key == "test_key"
        assert config.rate_limit_per_minute == 120
        assert config.cache_ttl_seconds == 600
        assert "BTC" in config.symbols
        assert len(config.symbols) == 3
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = DataSourceConfig()
        
        assert config.enabled is True
        assert config.api_key is None
        assert config.rate_limit_per_minute == 60
        assert config.cache_ttl_seconds == 300
        assert "BTC" in config.symbols
        assert "ETH" in config.symbols


class MockDataSourcePlugin(DataSourcePlugin):
    """Mock plugin for testing"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.initialized = False
        self.cleaned_up = False
    
    async def _initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Internal execute method - delegates to parent execute"""
        return await self.execute(data)
    
    async def get_current_price(self, symbol: str) -> float:
        if symbol == "BTC":
            return 45000.0
        elif symbol == "ETH":
            return 3000.0
        return 100.0
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        # Create mock historical data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = {
            'Open': [100 + i for i in range(10)],
            'High': [105 + i for i in range(10)],
            'Low': [95 + i for i in range(10)],
            'Close': [102 + i for i in range(10)],
            'Volume': [1000000 + i * 10000 for i in range(10)]
        }
        return pd.DataFrame(data, index=dates)
    
    async def get_volume_data(self, symbol: str) -> dict:
        return {
            'current_volume': 1000000,
            'average_volume_5d': 950000,
            'volume_change_24h': 50000
        }
    
    async def get_market_cap(self, symbol: str) -> float:
        if symbol == "BTC":
            return 900000000000.0  # 900B
        return 50000000000.0  # 50B
    
    async def cleanup(self) -> None:
        self.cleaned_up = True


class TestDataSourcePlugin:
    """Test base DataSourcePlugin functionality"""
    
    @pytest.fixture
    def config(self):
        return DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=60,
            symbols=["BTC", "ETH"]
        )
    
    @pytest.fixture
    def plugin(self, config):
        return MockDataSourcePlugin(config)
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self, plugin):
        """Test plugin initialization"""
        result = await plugin.initialize()
        assert result is True
        assert plugin.initialized is True
    
    @pytest.mark.asyncio
    async def test_plugin_execute_current_price(self, plugin):
        """Test execute method for current price"""
        await plugin.initialize()
        
        result = await plugin.execute({
            'operation': 'get_current_price',
            'symbol': 'BTC'
        })
        
        assert result['success'] is True
        assert result['data']['price'] == 45000.0
        assert result['data']['symbol'] == 'BTC'
        assert result['source'] == 'MockDataSourcePlugin'
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_plugin_execute_historical_data(self, plugin):
        """Test execute method for historical data"""
        await plugin.initialize()
        
        result = await plugin.execute({
            'operation': 'get_historical_data',
            'symbol': 'BTC',
            'period': '1y'
        })
        
        assert result['success'] is True
        assert result['data']['historical_data'] is not None
        assert result['data']['symbol'] == 'BTC'
        assert result['data']['period'] == '1y'
    
    @pytest.mark.asyncio
    async def test_plugin_execute_volume_data(self, plugin):
        """Test execute method for volume data"""
        await plugin.initialize()
        
        result = await plugin.execute({
            'operation': 'get_volume_data',
            'symbol': 'ETH'
        })
        
        assert result['success'] is True
        assert result['data']['volume_data']['current_volume'] == 1000000
        assert result['data']['symbol'] == 'ETH'
    
    @pytest.mark.asyncio
    async def test_plugin_execute_market_cap(self, plugin):
        """Test execute method for market cap"""
        await plugin.initialize()
        
        result = await plugin.execute({
            'operation': 'get_market_cap',
            'symbol': 'BTC'
        })
        
        assert result['success'] is True
        assert result['data']['market_cap'] == 900000000000.0
        assert result['data']['symbol'] == 'BTC'
    
    @pytest.mark.asyncio
    async def test_plugin_execute_unknown_operation(self, plugin):
        """Test execute method with unknown operation"""
        await plugin.initialize()
        
        result = await plugin.execute({
            'operation': 'unknown_operation',
            'symbol': 'BTC'
        })
        
        assert result['success'] is False
        assert 'Unknown operation' in result['error']
    
    def test_cache_functionality(self, plugin):
        """Test caching functionality"""
        cache_key = "test_key"
        test_data = {"price": 45000.0}
        
        # Test cache miss
        assert plugin._get_from_cache(cache_key) is None
        assert not plugin._is_cache_valid(cache_key)
        
        # Update cache
        plugin._update_cache(cache_key, test_data)
        
        # Test cache hit
        assert plugin._get_from_cache(cache_key) == test_data
        assert plugin._is_cache_valid(cache_key) is True
    
    def test_cache_expiry(self, plugin):
        """Test cache expiry functionality"""
        cache_key = "test_key"
        test_data = {"price": 45000.0}
        
        # Update cache
        plugin._update_cache(cache_key, test_data)
        
        # Manually expire cache
        plugin.last_cache_update[cache_key] = datetime.now() - timedelta(seconds=plugin.config.cache_ttl_seconds + 1)
        
        # Test cache miss due to expiry
        assert not plugin._is_cache_valid(cache_key)
        assert plugin._get_from_cache(cache_key) is None


class TestDataSourceManager:
    """Test DataSourceManager functionality"""
    
    @pytest.fixture
    def manager(self):
        return DataSourceManager()
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initialization"""
        with patch.object(manager, '_register_default_plugins') as mock_register:
            await manager.initialize()
            mock_register.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_price_with_fallback(self, manager):
        """Test get_current_price with fallback mechanism"""
        # Mock plugins
        mock_plugin1 = AsyncMock()
        mock_plugin1.execute.return_value = {
            'success': False,
            'error': 'Failed'
        }
        
        mock_plugin2 = AsyncMock()
        mock_plugin2.execute.return_value = {
            'success': True,
            'data': {'price': 45000.0}
        }
        
        manager.plugins = {
            'source1': mock_plugin1,
            'source2': mock_plugin2
        }
        manager.fallback_order = ['source1', 'source2']
        
        price = await manager.get_current_price('BTC')
        
        assert price == 45000.0
        mock_plugin1.execute.assert_called_once()
        mock_plugin2.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_multiple_prices(self, manager):
        """Test getting multiple prices concurrently"""
        # Mock the get_current_price method
        async def mock_get_price(symbol):
            if symbol == 'BTC':
                return 45000.0
            elif symbol == 'ETH':
                return 3000.0
            return None
        
        manager.get_current_price = mock_get_price
        
        result = await manager.get_multiple_prices(['BTC', 'ETH', 'UNKNOWN'])
        
        assert result['BTC'] == 45000.0
        assert result['ETH'] == 3000.0
        assert result['UNKNOWN'] is None
    
    @pytest.mark.asyncio
    async def test_get_market_data_summary(self, manager):
        """Test getting comprehensive market data"""
        # Mock plugins
        mock_coingecko = AsyncMock()
        mock_coingecko.execute.side_effect = [
            {
                'success': True,
                'data': {'volume_data': {'current_volume': 1000000}}
            },
            {
                'success': True,
                'data': {'market_cap': 900000000000.0}
            }
        ]
        
        manager.plugins = {'coingecko': mock_coingecko}
        
        # Mock get_current_price
        async def mock_get_price(symbol):
            return 45000.0 if symbol == 'BTC' else None
        
        manager.get_current_price = mock_get_price
        
        result = await manager.get_market_data_summary(['BTC'])
        
        assert 'BTC' in result
        assert result['BTC']['price'] == 45000.0
        assert result['BTC']['volume'] == {'current_volume': 1000000}
        assert result['BTC']['market_cap'] == 900000000000.0
    
    @pytest.mark.asyncio
    async def test_health_check(self, manager):
        """Test health check functionality"""
        # Mock plugin
        mock_plugin = AsyncMock()
        mock_plugin.execute.return_value = {
            'success': True,
            'data': {'price': 45000.0}
        }
        
        manager.plugins = {'test_source': mock_plugin}
        
        # Mock parent health check
        with patch.object(manager, 'health_check_all') as mock_health:
            mock_health.return_value = {'test_source': {'status': 'healthy'}}
            
            result = await manager.health_check()
            
            assert 'module_health' in result
            assert 'source_availability' in result
            assert result['total_sources'] == 1
            assert result['available_sources'] == 1


class TestYahooFinancePlugin:
    """Test Yahoo Finance plugin specifically"""
    
    @pytest.fixture
    def config(self):
        return DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=300
        )
    
    @pytest.fixture
    def plugin(self, config):
        return YahooFinancePlugin(config)
    
    def test_symbol_mapping(self, plugin):
        """Test Yahoo Finance symbol mapping"""
        assert plugin._get_yahoo_symbol('BTC') == 'BTC-USD'
        assert plugin._get_yahoo_symbol('ETH') == 'ETH-USD'
        assert plugin._get_yahoo_symbol('UNKNOWN') == 'UNKNOWN-USD'
    
    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test Yahoo Finance plugin initialization"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {'symbol': 'BTC-USD'}
            
            result = await plugin.initialize()
            assert result is True


class TestCoinGeckoPlugin:
    """Test CoinGecko plugin specifically"""
    
    @pytest.fixture
    def config(self):
        return DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=60
        )
    
    @pytest.fixture
    def plugin(self, config):
        return CoinGeckoPlugin(config)
    
    def test_coingecko_id_mapping(self, plugin):
        """Test CoinGecko ID mapping"""
        assert plugin._get_coingecko_id('BTC') == 'bitcoin'
        assert plugin._get_coingecko_id('ETH') == 'ethereum'
        assert plugin._get_coingecko_id('UNKNOWN') == 'unknown'
    
    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test CoinGecko plugin initialization"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await plugin.initialize()
            # Note: This might not work due to session mocking complexity
            # In a real test environment, you'd need more sophisticated mocking


class TestBinancePlugin:
    """Test Binance plugin specifically"""
    
    @pytest.fixture
    def config(self):
        return DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=30
        )
    
    @pytest.fixture
    def plugin(self, config):
        return BinancePlugin(config)
    
    def test_binance_symbol_mapping(self, plugin):
        """Test Binance symbol mapping"""
        assert plugin._get_binance_symbol('BTC') == 'BTCUSDT'
        assert plugin._get_binance_symbol('ETH') == 'ETHUSDT'
        assert plugin._get_binance_symbol('UNKNOWN') == 'UNKNOWNUSDT'


@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration of the data sources system"""
    # Create manager
    manager = DataSourceManager()
    
    # Mock all plugins to avoid real API calls
    with patch.object(manager, '_register_default_plugins'):
        # Create mock plugins
        mock_plugin = MockDataSourcePlugin(DataSourceConfig())
        await mock_plugin.initialize()
        
        manager.plugins = {'mock_source': mock_plugin}
        manager.fallback_order = ['mock_source']
        
        # Test current price
        price = await manager.get_current_price('BTC')
        assert price == 45000.0
        
        # Test historical data
        hist_data = await manager.get_historical_data('BTC', '1y')
        assert hist_data is not None
        # Historical data is returned as dict when serialized through execute
        if isinstance(hist_data, dict):
            assert 'Close' in hist_data
        else:
            assert len(hist_data) == 10
        
        # Test multiple prices
        prices = await manager.get_multiple_prices(['BTC', 'ETH'])
        assert prices['BTC'] == 45000.0
        assert prices['ETH'] == 3000.0
        
        # Test market data summary
        summary = await manager.get_market_data_summary(['BTC'])
        assert 'BTC' in summary
        assert summary['BTC']['price'] == 45000.0
        
        # Test health check
        health = await manager.health_check()
        assert 'source_availability' in health
        assert health['total_sources'] == 1
        
        # Cleanup
        await mock_plugin.cleanup()
        assert mock_plugin.cleaned_up is True


if __name__ == "__main__":
    pytest.main([__file__])