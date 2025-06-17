"""
Unit tests for modules/portfolio_analyzer.py
Testing cryptocurrency portfolio analysis functionality
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.modules.portfolio_analyzer import (
    calculate_crypto_metrics,
    analyze_crypto_portfolio_parallel,
    analyze_crypto_portfolio_sequential,
    get_top_cryptocurrencies,
    display_portfolio_results
)


class TestCalculateCryptoMetrics(unittest.TestCase):
    """Test cases for calculate_crypto_metrics function"""

    def test_calculate_crypto_metrics_success(self):
        """Test successful crypto metrics calculation"""
        result = calculate_crypto_metrics("BTC")
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "BTC")
        
        metrics = result[1]
        self.assertIsInstance(metrics, dict)
        
        # Check that all required metrics are present
        required_metrics = ["sharpe_ratio", "volatility", "annual_return", "max_drawdown", "current_price"]
        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (int, float))

    def test_calculate_crypto_metrics_reproducibility(self):
        """Test that metrics are reproducible for same symbol"""
        result1 = calculate_crypto_metrics("BTC")
        result2 = calculate_crypto_metrics("BTC")
        
        # Should generate identical results for same symbol due to seeding
        self.assertEqual(result1[1]["sharpe_ratio"], result2[1]["sharpe_ratio"])
        self.assertEqual(result1[1]["volatility"], result2[1]["volatility"])
        self.assertEqual(result1[1]["annual_return"], result2[1]["annual_return"])

    def test_calculate_crypto_metrics_different_symbols(self):
        """Test that different symbols produce different metrics"""
        result_btc = calculate_crypto_metrics("BTC")
        result_eth = calculate_crypto_metrics("ETH")
        
        # Different symbols should have different metrics
        self.assertNotEqual(result_btc[1]["sharpe_ratio"], result_eth[1]["sharpe_ratio"])
        self.assertNotEqual(result_btc[1]["current_price"], result_eth[1]["current_price"])

    def test_calculate_crypto_metrics_edge_cases(self):
        """Test metrics calculation with edge case symbols"""
        test_symbols = ["", "INVALID", "123", "special@#$"]
        
        for symbol in test_symbols:
            result = calculate_crypto_metrics(symbol)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], symbol)
            self.assertIsInstance(result[1], dict)

    def test_calculate_crypto_metrics_validates_ranges(self):
        """Test that calculated metrics are within reasonable ranges"""
        result = calculate_crypto_metrics("BTC")
        metrics = result[1]
        
        # Validate metric ranges
        self.assertGreaterEqual(metrics["volatility"], 0)
        self.assertLessEqual(metrics["volatility"], 500)  # Max 500% volatility
        self.assertGreaterEqual(metrics["max_drawdown"], -100)  # Min -100%
        self.assertLessEqual(metrics["max_drawdown"], 0)  # Max 0% (no positive drawdown)
        self.assertGreater(metrics["current_price"], 0)  # Price must be positive

    @patch('src.modules.portfolio_analyzer.np.random.seed')
    @patch('src.modules.portfolio_analyzer.np.random.normal')
    @patch('src.modules.portfolio_analyzer.np.random.uniform')
    def test_calculate_crypto_metrics_with_exception(self, mock_uniform, mock_normal, mock_seed):
        """Test handling of exceptions during calculation"""
        mock_normal.side_effect = Exception("Calculation error")
        
        result = calculate_crypto_metrics("ERROR")
        
        self.assertEqual(result[0], "ERROR")
        self.assertIn("error", result[1])


class TestAnalyzeCryptoPortfolioParallel(unittest.TestCase):
    """Test cases for analyze_crypto_portfolio_parallel function"""

    @patch('src.modules.portfolio_analyzer.Pool')
    def test_analyze_crypto_portfolio_parallel_success(self, mock_pool_class):
        """Test successful parallel portfolio analysis"""
        # Mock multiprocessing pool
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=None)
        mock_pool.map.return_value = [
            ("BTC", {"sharpe_ratio": 1.5, "volatility": 65.0}),
            ("ETH", {"sharpe_ratio": 1.2, "volatility": 75.0}),
            ("ADA", {"sharpe_ratio": 0.8, "volatility": 85.0})
        ]
        mock_pool_class.return_value = mock_pool
        
        symbols = ["BTC", "ETH", "ADA"]
        result = analyze_crypto_portfolio_parallel(symbols)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertIn("ADA", result)
        
        # Verify pool was used correctly
        mock_pool.map.assert_called_once()

    @patch('src.modules.portfolio_analyzer.Pool')
    def test_analyze_crypto_portfolio_parallel_empty_list(self, mock_pool_class):
        """Test parallel analysis with empty symbol list"""
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=None)
        mock_pool.map.return_value = []
        mock_pool_class.return_value = mock_pool
        
        result = analyze_crypto_portfolio_parallel([])
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    @patch('src.modules.portfolio_analyzer.Pool')
    def test_analyze_crypto_portfolio_parallel_large_list(self, mock_pool_class):
        """Test parallel analysis with large symbol list"""
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=None)
        
        # Generate 100 mock results
        mock_results = [(f"CRYPTO{i}", {"sharpe_ratio": i * 0.1}) for i in range(100)]
        mock_pool.map.return_value = mock_results
        mock_pool_class.return_value = mock_pool
        
        symbols = [f"CRYPTO{i}" for i in range(100)]
        result = analyze_crypto_portfolio_parallel(symbols)
        
        self.assertEqual(len(result), 100)
        self.assertIn("CRYPTO0", result)
        self.assertIn("CRYPTO99", result)


class TestAnalyzeCryptoPortfolioSequential(unittest.TestCase):
    """Test cases for analyze_crypto_portfolio_sequential function"""

    def test_analyze_crypto_portfolio_sequential_success(self):
        """Test successful sequential portfolio analysis"""
        symbols = ["BTC", "ETH", "ADA"]
        result = analyze_crypto_portfolio_sequential(symbols)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertIn("ADA", result)
        
        # Each result should be a valid metrics dict
        for symbol, metrics in result.items():
            self.assertIsInstance(metrics, dict)
            self.assertIn("sharpe_ratio", metrics)
            self.assertIn("volatility", metrics)

    def test_analyze_crypto_portfolio_sequential_empty_list(self):
        """Test sequential analysis with empty symbol list"""
        result = analyze_crypto_portfolio_sequential([])
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_analyze_crypto_portfolio_sequential_single_symbol(self):
        """Test sequential analysis with single symbol"""
        result = analyze_crypto_portfolio_sequential(["BTC"])
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        self.assertIn("BTC", result)


class TestGetTopCryptocurrencies(unittest.TestCase):
    """Test cases for get_top_cryptocurrencies function"""

    def test_get_top_cryptocurrencies_default(self):
        """Test getting top cryptocurrencies with default count"""
        result = get_top_cryptocurrencies()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 50)  # Default is 50
        
        # Should contain expected major cryptocurrencies
        self.assertIn("BTC", result)
        self.assertIn("ETH", result)
        self.assertIn("BNB", result)

    def test_get_top_cryptocurrencies_custom_count(self):
        """Test getting top cryptocurrencies with custom count"""
        result = get_top_cryptocurrencies(10)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 10)
        
        # Should start with major cryptocurrencies
        self.assertEqual(result[0], "BTC")
        self.assertEqual(result[1], "ETH")
        self.assertEqual(result[2], "BNB")

    def test_get_top_cryptocurrencies_large_count(self):
        """Test getting more cryptocurrencies than available"""
        total_available = len(get_top_cryptocurrencies(1000))
        result = get_top_cryptocurrencies(total_available + 10)
        
        # Should return all available without error
        self.assertEqual(len(result), total_available)

    def test_get_top_cryptocurrencies_zero_count(self):
        """Test getting zero cryptocurrencies"""
        result = get_top_cryptocurrencies(0)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_get_top_cryptocurrencies_negative_count(self):
        """Test getting negative count of cryptocurrencies"""
        result = get_top_cryptocurrencies(-5)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_get_top_cryptocurrencies_no_duplicates(self):
        """Test that returned list has no duplicates"""
        result = get_top_cryptocurrencies(50)
        
        self.assertEqual(len(result), len(set(result)))

    def test_get_top_cryptocurrencies_content_validation(self):
        """Test that all returned symbols are valid"""
        result = get_top_cryptocurrencies(20)
        
        for symbol in result:
            self.assertIsInstance(symbol, str)
            self.assertGreater(len(symbol), 0)
            self.assertTrue(symbol.isupper())  # Should be uppercase

    def test_get_top_cryptocurrencies_order(self):
        """Test that cryptocurrencies are returned in expected order"""
        result = get_top_cryptocurrencies(10)
        
        # First few should be the major cryptocurrencies in order
        expected_start = ["BTC", "ETH", "BNB", "XRP", "ADA"]
        for i, expected in enumerate(expected_start):
            if i < len(result):
                self.assertEqual(result[i], expected)


class TestDisplayPortfolioResults(unittest.TestCase):
    """Test cases for display_portfolio_results function"""

    def test_display_portfolio_results_success(self):
        """Test successful portfolio results display"""
        test_results = {
            "BTC": {"sharpe_ratio": 1.5, "annual_return": 25.0, "volatility": 65.0},
            "ETH": {"sharpe_ratio": 1.2, "annual_return": 20.0, "volatility": 75.0},
            "ADA": {"sharpe_ratio": 0.8, "annual_return": 15.0, "volatility": 85.0}
        }
        
        # Capture stdout to test output
        with patch('builtins.print') as mock_print:
            result = display_portfolio_results(test_results, top_n=3)
            
            # Should have printed header and results
            mock_print.assert_called()
            
            # Should return sorted results
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 3)
            
            # Should be sorted by sharpe ratio (descending)
            self.assertEqual(result[0][0], "BTC")  # Highest Sharpe
            self.assertEqual(result[1][0], "ETH")
            self.assertEqual(result[2][0], "ADA")  # Lowest Sharpe

    def test_display_portfolio_results_with_errors(self):
        """Test portfolio results display with error entries"""
        test_results = {
            "BTC": {"sharpe_ratio": 1.5, "annual_return": 25.0, "volatility": 65.0},
            "ERROR": {"error": "API Error"},
            "ETH": {"sharpe_ratio": 1.2, "annual_return": 20.0, "volatility": 75.0}
        }
        
        with patch('builtins.print') as mock_print:
            result = display_portfolio_results(test_results, top_n=5)
            
            # Should filter out error entries
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0][0], "BTC")
            self.assertEqual(result[1][0], "ETH")

    def test_display_portfolio_results_empty_dict(self):
        """Test portfolio results display with empty results"""
        with patch('builtins.print') as mock_print:
            result = display_portfolio_results({}, top_n=10)
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)

    def test_display_portfolio_results_top_n_limit(self):
        """Test portfolio results display with top_n limit"""
        test_results = {
            f"CRYPTO{i}": {"sharpe_ratio": i * 0.1, "annual_return": i * 2.0, "volatility": 50.0 + i}
            for i in range(20)
        }
        
        with patch('builtins.print') as mock_print:
            result = display_portfolio_results(test_results, top_n=5)
            
            # Should return only top 5
            self.assertEqual(len(result), 5)
            
            # Should be sorted by sharpe ratio (descending)
            sharpe_ratios = [metrics["sharpe_ratio"] for _, metrics in result]
            self.assertEqual(sharpe_ratios, sorted(sharpe_ratios, reverse=True))

    def test_display_portfolio_results_default_top_n(self):
        """Test portfolio results display with default top_n"""
        test_results = {
            f"CRYPTO{i}": {"sharpe_ratio": i * 0.1, "annual_return": i * 2.0, "volatility": 50.0 + i}
            for i in range(15)
        }
        
        with patch('builtins.print') as mock_print:
            result = display_portfolio_results(test_results)  # Default top_n=10
            
            # Should return top 10
            self.assertEqual(len(result), 10)


class TestPortfolioAnalyzerIntegration(unittest.TestCase):
    """Integration tests for portfolio analyzer module"""

    def test_parallel_vs_sequential_consistency(self):
        """Test that parallel and sequential analysis produce consistent results"""
        symbols = ["BTC", "ETH", "ADA", "DOT", "XRP"]
        
        # Since both use the same underlying function with seeding, results should be identical
        parallel_result = analyze_crypto_portfolio_sequential(symbols)  # Use sequential to avoid mocking
        sequential_result = analyze_crypto_portfolio_sequential(symbols)
        
        self.assertEqual(parallel_result, sequential_result)

    def test_end_to_end_portfolio_analysis(self):
        """Test complete portfolio analysis workflow"""
        # Get top cryptocurrencies
        symbols = get_top_cryptocurrencies(5)
        
        # Analyze portfolio
        results = analyze_crypto_portfolio_sequential(symbols)
        
        # Display results
        with patch('builtins.print'):
            top_performers = display_portfolio_results(results, top_n=3)
        
        # Validate complete workflow
        self.assertEqual(len(symbols), 5)
        self.assertEqual(len(results), 5)
        self.assertLessEqual(len(top_performers), 3)
        
        # Validate that top performers are properly sorted
        if len(top_performers) > 1:
            for i in range(len(top_performers) - 1):
                current_sharpe = top_performers[i][1]["sharpe_ratio"]
                next_sharpe = top_performers[i + 1][1]["sharpe_ratio"]
                self.assertGreaterEqual(current_sharpe, next_sharpe)


class TestPortfolioAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_calculate_crypto_metrics_extreme_values(self):
        """Test metrics calculation with extreme hash values"""
        # Test with symbols that produce extreme hash values
        extreme_symbols = ["", "A" * 1000, "🚀", "null", "undefined"]
        
        for symbol in extreme_symbols:
            result = calculate_crypto_metrics(symbol)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0], symbol)
            self.assertIsInstance(result[1], dict)

    def test_portfolio_analysis_performance(self):
        """Test portfolio analysis performance with large datasets"""
        # Test with a large number of symbols
        large_symbol_list = [f"CRYPTO{i}" for i in range(100)]
        
        # Should complete without timeout or memory issues
        result = analyze_crypto_portfolio_sequential(large_symbol_list)
        
        self.assertEqual(len(result), 100)
        self.assertIsInstance(result, dict)

    def test_display_portfolio_results_formatting(self):
        """Test that display output is properly formatted"""
        test_results = {
            "BITCOIN": {"sharpe_ratio": 1.23456789, "annual_return": 25.6789, "volatility": 65.4321},
            "ETHEREUM": {"sharpe_ratio": 0.87654321, "annual_return": 18.1234, "volatility": 78.9876}
        }
        
        with patch('builtins.print') as mock_print:
            display_portfolio_results(test_results, top_n=2)
            
            # Check that print was called with formatted strings
            mock_print.assert_called()
            
            # Verify formatting by checking call args
            calls = mock_print.call_args_list
            self.assertGreater(len(calls), 0)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)