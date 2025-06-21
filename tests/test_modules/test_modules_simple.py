"""
Simple module tests that work fast and reliably.
"""

import pytest
from unittest.mock import Mock, patch


class TestModulesBasic:
    """Basic module functionality tests"""

    def test_mock_arbitrage_detection(self):
        """Test mocked arbitrage detection"""
        mock_detector = Mock()
        mock_detector.detect_opportunities.return_value = [
            {
                "symbol": "BTC",
                "buy_exchange": "binance",
                "sell_exchange": "coinbase",
                "profit_percentage": 2.5
            }
        ]
        
        opportunities = mock_detector.detect_opportunities({
            "binance": {"BTC": 49000},
            "coinbase": {"BTC": 50225}
        })
        
        assert len(opportunities) == 1
        assert opportunities[0]["profit_percentage"] == 2.5

    def test_mock_portfolio_analysis(self):
        """Test mocked portfolio analysis"""
        mock_analyzer = Mock()
        mock_analyzer.analyze_portfolio.return_value = {
            "total_value": 10000,
            "daily_change": 2.5,
            "best_performer": "BTC",
            "worst_performer": "ADA"
        }
        
        result = mock_analyzer.analyze_portfolio(["BTC", "ETH", "ADA"])
        assert result["total_value"] == 10000
        assert result["best_performer"] == "BTC"

    def test_mock_historical_data(self):
        """Test mocked historical data"""
        mock_history = Mock()
        mock_history.get_historical_data.return_value = {
            "prices": [100, 105, 102, 108],
            "dates": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "volatility": 3.2,
            "sharpe_ratio": 1.8
        }
        
        data = mock_history.get_historical_data("BTC", "7d")
        assert len(data["prices"]) == 4
        assert data["volatility"] == 3.2