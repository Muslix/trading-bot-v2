"""
Unit tests for modules/historical_data.py
Testing historical data fetching and analysis functionality
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.modules.historical_data import (
    HistoricalDataManager,
    calculate_crypto_metrics_enhanced,
    analyze_crypto_portfolio_enhanced,
    get_analysis_timeframes,
    compare_timeframes
)


class TestHistoricalDataManager(unittest.TestCase):
    """Test cases for HistoricalDataManager class"""

    def setUp(self):
        """Set up test environment"""
        self.manager = HistoricalDataManager()

    def test_init(self):
        """Test HistoricalDataManager initialization"""
        self.assertIsInstance(self.manager.crypto_symbol_mapping, dict)
        self.assertIn("BTC", self.manager.crypto_symbol_mapping)
        self.assertIn("ETH", self.manager.crypto_symbol_mapping)
        self.assertEqual(self.manager.crypto_symbol_mapping["BTC"], "BTC-USD")

    def test_crypto_symbol_mapping_completeness(self):
        """Test that symbol mapping contains expected cryptocurrencies"""
        expected_symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "XRP", "LTC", "LINK"]
        for symbol in expected_symbols:
            self.assertIn(symbol, self.manager.crypto_symbol_mapping)
            self.assertTrue(self.manager.crypto_symbol_mapping[symbol].endswith("-USD"))

    @patch('src.modules.historical_data.yf.Ticker')
    def test_fetch_historical_data_success(self, mock_ticker_class):
        """Test successful historical data fetching"""
        # Mock yfinance data
        mock_ticker = MagicMock()
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        }, index=pd.date_range('2023-01-01', periods=5))
        
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker
        
        result = self.manager.fetch_historical_data("BTC", "1y")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)
        mock_ticker_class.assert_called_once_with("BTC-USD")
        mock_ticker.history.assert_called_once_with(period="1y")

    @patch('src.modules.historical_data.yf.Ticker')
    def test_fetch_historical_data_empty_response(self, mock_ticker_class):
        """Test handling of empty historical data response"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty DataFrame
        mock_ticker_class.return_value = mock_ticker
        
        result = self.manager.fetch_historical_data("INVALID", "1y")
        
        self.assertIsNone(result)

    @patch('src.modules.historical_data.yf.Ticker')
    def test_fetch_historical_data_exception(self, mock_ticker_class):
        """Test handling of exceptions during data fetching"""
        mock_ticker_class.side_effect = Exception("API Error")
        
        result = self.manager.fetch_historical_data("BTC", "1y")
        
        self.assertIsNone(result)

    def test_fetch_historical_data_unknown_symbol(self):
        """Test fetching data for unknown symbol"""
        with patch('src.modules.historical_data.yf.Ticker') as mock_ticker_class:
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = pd.DataFrame()
            mock_ticker_class.return_value = mock_ticker
            
            result = self.manager.fetch_historical_data("UNKNOWN", "1y")
            
            # Should attempt to fetch with "UNKNOWN-USD"
            mock_ticker_class.assert_called_once_with("UNKNOWN-USD")
            self.assertIsNone(result)

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_advanced_metrics_success(self, mock_fetch):
        """Test successful advanced metrics calculation"""
        # Create mock historical data
        np.random.seed(42)  # For reproducible results
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 365)) * 100
        mock_data = pd.DataFrame({
            'Close': prices
        }, index=pd.date_range('2023-01-01', periods=365))
        
        mock_fetch.return_value = mock_data
        
        result = self.manager.calculate_advanced_metrics("BTC", "1y")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "BTC")
        self.assertEqual(result["period"], "1y")
        self.assertEqual(result["data_points"], 364)  # 365 prices -> 364 returns
        
        # Check that all required metrics are present
        required_metrics = [
            "sharpe_ratio", "sortino_ratio", "calmar_ratio", "annual_return",
            "volatility", "max_drawdown", "var_95", "var_99", "cvar_95",
            "beta_vs_btc", "win_rate", "current_price"
        ]
        for metric in required_metrics:
            self.assertIn(metric, result)
            self.assertIsInstance(result[metric], (int, float))

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_advanced_metrics_insufficient_data(self, mock_fetch):
        """Test metrics calculation with insufficient data"""
        # Create mock data with only 10 data points
        mock_data = pd.DataFrame({
            'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        }, index=pd.date_range('2023-01-01', periods=10))
        
        mock_fetch.return_value = mock_data
        
        result = self.manager.calculate_advanced_metrics("BTC", "1y")
        
        # Should return fallback metrics
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "BTC")
        self.assertIn("data_source", result)
        self.assertIn(result["data_source"], ["simulated", "simulated_with_live_price"])

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_advanced_metrics_no_data(self, mock_fetch):
        """Test metrics calculation with no data"""
        mock_fetch.return_value = None
        
        result = self.manager.calculate_advanced_metrics("BTC", "1y")
        
        # Should return fallback metrics
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "BTC")
        self.assertIn("data_source", result)
        self.assertIn(result["data_source"], ["simulated", "simulated_with_live_price"])

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_beta_vs_btc_success(self, mock_fetch):
        """Test beta calculation vs BTC"""
        # Create correlated price data
        np.random.seed(42)
        btc_returns = np.random.normal(0.001, 0.02, 365)
        eth_returns = 0.8 * btc_returns + np.random.normal(0, 0.01, 365)  # Correlated with BTC
        
        btc_prices = np.cumprod(1 + btc_returns) * 50000
        eth_prices = np.cumprod(1 + eth_returns) * 3000
        
        def side_effect(symbol, period):
            if symbol == "BTC":
                return pd.DataFrame({
                    'Close': btc_prices
                }, index=pd.date_range('2023-01-01', periods=365))
            elif symbol == "ETH":
                return pd.DataFrame({
                    'Close': eth_prices
                }, index=pd.date_range('2023-01-01', periods=365))
            return None
        
        mock_fetch.side_effect = side_effect
        
        beta = self.manager._calculate_beta_vs_btc(pd.Series(eth_returns[1:], 
                                                   index=pd.date_range('2023-01-02', periods=364)))
        
        # Beta should be close to 0.8 due to our correlation setup
        self.assertGreater(beta, 0.5)
        self.assertLess(beta, 1.2)

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_beta_vs_btc_no_btc_data(self, mock_fetch):
        """Test beta calculation when BTC data is unavailable"""
        mock_fetch.return_value = None
        
        returns = pd.Series([0.01, 0.02, -0.01, 0.005])
        beta = self.manager._calculate_beta_vs_btc(returns)
        
        self.assertEqual(beta, 1.0)  # Default value when BTC data unavailable

    def test_get_fallback_metrics(self):
        """Test fallback metrics generation"""
        result = self.manager._get_fallback_metrics("TEST")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], "TEST")
        self.assertEqual(result["period"], "2y")
        self.assertEqual(result["data_points"], 730)
        self.assertIn("data_source", result)
        self.assertEqual(result["data_source"], "simulated")
        
        # Check that all required metrics are present
        required_metrics = [
            "sharpe_ratio", "sortino_ratio", "calmar_ratio", "annual_return",
            "volatility", "max_drawdown", "var_95", "var_99", "cvar_95",
            "beta_vs_btc", "win_rate", "current_price"
        ]
        for metric in required_metrics:
            self.assertIn(metric, result)
            self.assertIsInstance(result[metric], (int, float))

    def test_get_fallback_metrics_reproducibility(self):
        """Test that fallback metrics are reproducible for same symbol"""
        result1 = self.manager._get_fallback_metrics("TEST")
        result2 = self.manager._get_fallback_metrics("TEST")
        
        # Should generate identical results for same symbol
        self.assertEqual(result1["sharpe_ratio"], result2["sharpe_ratio"])
        self.assertEqual(result1["annual_return"], result2["annual_return"])
        self.assertEqual(result1["volatility"], result2["volatility"])


class TestHistoricalDataFunctions(unittest.TestCase):
    """Test standalone functions in historical_data module"""

    @patch.object(HistoricalDataManager, 'calculate_advanced_metrics')
    def test_calculate_crypto_metrics_enhanced(self, mock_calculate):
        """Test calculate_crypto_metrics_enhanced function"""
        mock_metrics = {
            "symbol": "BTC",
            "sharpe_ratio": 1.5,
            "annual_return": 25.0
        }
        mock_calculate.return_value = mock_metrics
        
        result = calculate_crypto_metrics_enhanced("BTC", "1y")
        
        self.assertEqual(result[0], "BTC")
        self.assertEqual(result[1], mock_metrics)
        mock_calculate.assert_called_once_with("BTC", "1y")

    def test_get_analysis_timeframes(self):
        """Test get_analysis_timeframes function"""
        timeframes = get_analysis_timeframes()
        
        self.assertIsInstance(timeframes, list)
        self.assertIn("1y", timeframes)
        self.assertIn("2y", timeframes)
        self.assertIn("3y", timeframes)
        self.assertIn("5y", timeframes)
        self.assertIn("max", timeframes)

    @patch.object(HistoricalDataManager, 'calculate_advanced_metrics')
    def test_compare_timeframes(self, mock_calculate):
        """Test compare_timeframes function"""
        def side_effect(symbol, period):
            return {
                "symbol": symbol,
                "period": period,
                "sharpe_ratio": 1.0 if period == "1y" else 1.5
            }
        
        mock_calculate.side_effect = side_effect
        
        result = compare_timeframes("BTC", ["1y", "2y"])
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("1y", result)
        self.assertIn("2y", result)
        self.assertEqual(result["1y"]["sharpe_ratio"], 1.0)
        self.assertEqual(result["2y"]["sharpe_ratio"], 1.5)

    @patch.object(HistoricalDataManager, 'calculate_advanced_metrics')
    def test_compare_timeframes_default_periods(self, mock_calculate):
        """Test compare_timeframes with default periods"""
        mock_calculate.return_value = {"symbol": "BTC", "sharpe_ratio": 1.5}
        
        result = compare_timeframes("BTC")
        
        # Should use default timeframes ["1y", "2y", "3y"]
        self.assertEqual(len(result), 3)
        self.assertIn("1y", result)
        self.assertIn("2y", result)
        self.assertIn("3y", result)


class TestAnalyzeCryptoPortfolioEnhanced(unittest.TestCase):
    """Test analyze_crypto_portfolio_enhanced function"""

    @patch('multiprocessing.Pool')
    def test_analyze_crypto_portfolio_enhanced_success(self, mock_pool_class):
        """Test successful portfolio analysis"""
        # Mock multiprocessing pool
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=None)
        mock_pool.map.return_value = [
            ("BTC", {"sharpe_ratio": 1.5, "annual_return": 25.0}),
            ("ETH", {"sharpe_ratio": 1.2, "annual_return": 20.0})
        ]
        mock_pool_class.return_value = mock_pool
        
        result = analyze_crypto_portfolio_enhanced(["BTC", "ETH"], "1y")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertEqual(result["BTC"]["sharpe_ratio"], 1.5)
        self.assertEqual(result["ETH"]["sharpe_ratio"], 1.2)

    @patch('multiprocessing.Pool')
    def test_analyze_crypto_portfolio_enhanced_empty_list(self, mock_pool_class):
        """Test portfolio analysis with empty symbol list"""
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=None)
        mock_pool.map.return_value = []
        mock_pool_class.return_value = mock_pool
        
        result = analyze_crypto_portfolio_enhanced([], "1y")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)


class TestHistoricalDataEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def setUp(self):
        """Set up test environment"""
        self.manager = HistoricalDataManager()

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_advanced_metrics_with_zero_volatility(self, mock_fetch):
        """Test metrics calculation with zero volatility (constant prices)"""
        # Create constant price data
        mock_data = pd.DataFrame({
            'Close': [100] * 365  # Constant price
        }, index=pd.date_range('2023-01-01', periods=365))
        
        mock_fetch.return_value = mock_data
        
        result = self.manager.calculate_advanced_metrics("STABLE", "1y")
        
        self.assertIsInstance(result, dict)
        # Should handle zero volatility gracefully
        self.assertEqual(result["volatility"], 0.0)
        self.assertEqual(result["sharpe_ratio"], 0)  # Should be 0 when volatility is 0

    @patch.object(HistoricalDataManager, 'fetch_historical_data')
    def test_calculate_advanced_metrics_with_all_negative_returns(self, mock_fetch):
        """Test metrics calculation with all negative returns"""
        # Create declining price data
        prices = [100 * (0.99 ** i) for i in range(365)]  # 1% daily decline
        mock_data = pd.DataFrame({
            'Close': prices
        }, index=pd.date_range('2023-01-01', periods=365))
        
        mock_fetch.return_value = mock_data
        
        result = self.manager.calculate_advanced_metrics("DECLINING", "1y")
        
        self.assertIsInstance(result, dict)
        self.assertLess(result["annual_return"], 0)  # Should be negative
        self.assertEqual(result["win_rate"], 0.0)  # No positive returns
        self.assertLess(result["max_drawdown"], 0)  # Should be negative

    def test_calculate_advanced_metrics_with_exception(self):
        """Test that exceptions in calculate_advanced_metrics are handled"""
        # Mock fetch_historical_data to raise an exception
        with patch.object(self.manager, 'fetch_historical_data', side_effect=Exception("Calculation Error")):
            # Should not raise exception but return fallback
            result = self.manager.calculate_advanced_metrics("ERROR", "1y")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["symbol"], "ERROR")
            self.assertIn("data_source", result)
            self.assertEqual(result["data_source"], "simulated")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)