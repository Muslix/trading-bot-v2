"""
Tests für modules/portfolio_analyzer.py
Teste Multiprocessing Portfolio-Analyse
"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.portfolio_analyzer import (
    analyze_crypto_portfolio_parallel,
    analyze_crypto_portfolio_sequential,
    calculate_crypto_metrics,
    display_portfolio_results,
    get_top_cryptocurrencies,
)


class TestCalculateCryptoMetrics:
    """Tests für calculate_crypto_metrics Funktion"""

    def test_calculate_metrics_valid_symbol(self):
        """Test Metriken-Berechnung für gültiges Symbol"""
        symbol = "BTC"
        result_symbol, metrics = calculate_crypto_metrics(symbol)

        assert result_symbol == "BTC"
        assert isinstance(metrics, dict)
        assert "sharpe_ratio" in metrics
        assert "volatility" in metrics
        assert "annual_return" in metrics
        assert "max_drawdown" in metrics
        assert "current_price" in metrics

        # Werte sollten numerisch und sinnvoll sein
        assert isinstance(metrics["sharpe_ratio"], float)
        assert isinstance(metrics["volatility"], float)
        assert isinstance(metrics["annual_return"], float)
        assert isinstance(metrics["max_drawdown"], float)
        assert isinstance(metrics["current_price"], float)

        # Volatilität und Preis sollten positiv sein
        assert metrics["volatility"] > 0
        assert metrics["current_price"] > 0

    def test_calculate_metrics_reproducible(self):
        """Test dass Ergebnisse für gleiche Symbole reproduzierbar sind"""
        symbol = "ETH"

        result1 = calculate_crypto_metrics(symbol)
        result2 = calculate_crypto_metrics(symbol)

        assert result1 == result2

    def test_calculate_metrics_different_symbols(self):
        """Test dass verschiedene Symbole verschiedene Ergebnisse liefern"""
        btc_result = calculate_crypto_metrics("BTC")
        eth_result = calculate_crypto_metrics("ETH")

        assert btc_result[0] != eth_result[0]
        assert btc_result[1] != eth_result[1]


class TestPortfolioAnalysis:
    """Tests für Portfolio-Analyse Funktionen"""

    def test_analyze_portfolio_parallel_structure(self):
        """Test Struktur der parallelen Portfolio-Analyse"""
        symbols = ["BTC", "ETH", "ADA"]

        results = analyze_crypto_portfolio_parallel(symbols)

        assert isinstance(results, dict)
        assert len(results) == 3
        assert all(symbol in results for symbol in symbols)

        for symbol, metrics in results.items():
            assert isinstance(metrics, dict)
            assert "sharpe_ratio" in metrics

    def test_analyze_portfolio_sequential_structure(self):
        """Test Struktur der sequentiellen Portfolio-Analyse"""
        symbols = ["BTC", "ETH"]

        results = analyze_crypto_portfolio_sequential(symbols)

        assert isinstance(results, dict)
        assert len(results) == 2
        assert all(symbol in results for symbol in symbols)

    def test_parallel_vs_sequential_same_results(self):
        """Test dass parallel und sequential gleiche Ergebnisse liefern"""
        symbols = ["BTC", "ETH", "ADA"]

        parallel_results = analyze_crypto_portfolio_parallel(symbols)
        sequential_results = analyze_crypto_portfolio_sequential(symbols)

        assert parallel_results == sequential_results

    @patch("src.modules.portfolio_analyzer.Pool")
    def test_parallel_uses_multiprocessing(self, mock_pool):
        """Test dass parallel Version Multiprocessing verwendet"""
        mock_pool_instance = MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_pool_instance.map.return_value = [("BTC", {"sharpe_ratio": 1.5})]

        symbols = ["BTC"]
        results = analyze_crypto_portfolio_parallel(symbols)

        mock_pool.assert_called_once()
        mock_pool_instance.map.assert_called_once()


class TestUtilityFunctions:
    """Tests für Utility-Funktionen"""

    def test_get_top_cryptocurrencies_default(self):
        """Test Standard-Anzahl von Kryptowährungen"""
        cryptos = get_top_cryptocurrencies()

        assert isinstance(cryptos, list)
        assert len(cryptos) == 50  # Updated to match new default
        assert "BTC" in cryptos
        assert "ETH" in cryptos

    def test_get_top_cryptocurrencies_custom_count(self):
        """Test benutzerdefinierte Anzahl"""
        cryptos = get_top_cryptocurrencies(10)

        assert len(cryptos) == 10
        assert "BTC" in cryptos
        assert "ETH" in cryptos

    def test_get_top_cryptocurrencies_no_duplicates(self):
        """Test dass keine Duplikate existieren"""
        cryptos = get_top_cryptocurrencies(30)

        assert len(cryptos) == len(set(cryptos))

    def test_display_portfolio_results(self, capsys):
        """Test Anzeige der Portfolio-Ergebnisse"""
        mock_results = {
            "BTC": {"sharpe_ratio": 2.5, "annual_return": 150.0, "volatility": 60.0},
            "ETH": {"sharpe_ratio": 1.8, "annual_return": 120.0, "volatility": 65.0},
            "ADA": {"sharpe_ratio": 1.2, "annual_return": 80.0, "volatility": 70.0},
        }

        top_cryptos = display_portfolio_results(mock_results, top_n=2)
        captured = capsys.readouterr()

        assert len(top_cryptos) == 2
        assert top_cryptos[0][0] == "BTC"  # Höchste Sharpe Ratio
        assert top_cryptos[1][0] == "ETH"

        assert "TOP 2 Kryptowährungen" in captured.out
        assert "BTC" in captured.out
        assert "2.5" in captured.out  # Sharpe ratio

    def test_display_portfolio_results_filters_errors(self, capsys):
        """Test dass Fehler-Ergebnisse gefiltert werden"""
        mock_results = {
            "BTC": {"sharpe_ratio": 2.5, "annual_return": 150.0, "volatility": 60.0},
            "ETH": {"error": "API Error"},
            "ADA": {"sharpe_ratio": 1.2, "annual_return": 80.0, "volatility": 70.0},
        }

        top_cryptos = display_portfolio_results(mock_results)

        assert len(top_cryptos) == 2  # ETH sollte gefiltert werden
        symbols = [crypto[0] for crypto in top_cryptos]
        assert "ETH" not in symbols
        assert "BTC" in symbols
        assert "ADA" in symbols


class TestPortfolioAnalysisEdgeCases:
    """Tests für Edge Cases in der Portfolio-Analyse"""

    def test_empty_symbol_list(self):
        """Test leere Symbol-Liste"""
        results = analyze_crypto_portfolio_parallel([])
        assert results == {}

        results = analyze_crypto_portfolio_sequential([])
        assert results == {}

    def test_single_symbol(self):
        """Test einzelnes Symbol"""
        results = analyze_crypto_portfolio_parallel(["BTC"])

        assert len(results) == 1
        assert "BTC" in results
        assert isinstance(results["BTC"], dict)

    def test_large_symbol_list(self):
        """Test große Symbol-Liste (Performance)"""
        large_symbols = [f"CRYPTO{i}" for i in range(100)]

        results = analyze_crypto_portfolio_parallel(large_symbols)

        assert len(results) == 100
        assert all(f"CRYPTO{i}" in results for i in range(100))
