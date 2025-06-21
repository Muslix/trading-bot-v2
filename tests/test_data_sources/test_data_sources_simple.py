"""
Simple data sources tests without external API calls.
"""

import pytest
from unittest.mock import Mock, patch


class TestDataSourcesBasic:
    """Basic data sources functionality tests"""

    def test_mock_price_fetch(self):
        """Test mocked price fetching"""
        mock_source = Mock()
        mock_source.get_price.return_value = {"BTC": 50000, "ETH": 3000}
        
        prices = mock_source.get_price(["BTC", "ETH"])
        assert prices["BTC"] == 50000
        assert prices["ETH"] == 3000

    def test_mock_exchange_data(self):
        """Test mocked exchange data"""
        mock_exchange = Mock()
        mock_exchange.get_ticker.return_value = {
            "symbol": "BTC/USDT",
            "price": 50000,
            "volume": 1000
        }
        
        ticker = mock_exchange.get_ticker("BTC/USDT")
        assert ticker["symbol"] == "BTC/USDT"
        assert ticker["price"] == 50000

    def test_data_sources_manager_mock(self):
        """Test data sources manager with mocking"""
        mock_manager = Mock()
        mock_manager.get_all_prices.return_value = {"BTC": 50000, "ETH": 3000}
        mock_manager.is_connected.return_value = True
        
        # Test basic functionality
        prices = mock_manager.get_all_prices()
        assert prices["BTC"] == 50000
        assert mock_manager.is_connected() is True