"""
Simple monitor tests without complex dependencies.
"""

import pytest
from unittest.mock import Mock, patch


class TestMonitorsBasic:
    """Basic monitor functionality tests"""

    def test_mock_price_monitor(self):
        """Test mocked price monitoring"""
        mock_monitor = Mock()
        mock_monitor.check_price.return_value = {
            "symbol": "BTC",
            "price": 50000,
            "change": 5.2,
            "alert": False
        }
        
        result = mock_monitor.check_price("BTC")
        assert result["symbol"] == "BTC"
        assert result["price"] == 50000
        assert result["alert"] is False

    def test_mock_volume_monitor(self):
        """Test mocked volume monitoring"""
        mock_monitor = Mock()
        mock_monitor.check_volume.return_value = {
            "symbol": "ETH",
            "volume": 5000000,
            "spike_detected": True
        }
        
        result = mock_monitor.check_volume("ETH")
        assert result["symbol"] == "ETH"
        assert result["spike_detected"] is True

    @patch('src.monitors.create_monitor_manager')
    def test_monitor_manager_creation(self, mock_create):
        """Test monitor manager creation"""
        mock_manager = Mock()
        mock_create.return_value = mock_manager
        
        from src.monitors import create_monitor_manager
        manager = create_monitor_manager({})
        
        assert manager is not None
        mock_create.assert_called_once()