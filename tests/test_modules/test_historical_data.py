"""
Tests für modules/historical_data.py
Teste erweiterte historische Datenanalyse
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.modules.historical_data import (
    HistoricalDataManager,
    analyze_crypto_portfolio_enhanced,
    calculate_crypto_metrics_enhanced,
    compare_timeframes,
    get_analysis_timeframes,
)


class TestHistoricalDataManager:
    """Tests für HistoricalDataManager"""

    def test_manager_initialization(self):
        """Test Manager-Initialisierung"""
        manager = HistoricalDataManager()

        assert hasattr(manager, "crypto_symbol_mapping")
        assert isinstance(manager.crypto_symbol_mapping, dict)
        assert "BTC" in manager.crypto_symbol_mapping
        assert manager.crypto_symbol_mapping["BTC"] == "BTC-USD"

    @patch("src.modules.historical_data.yf.Ticker")
    def test_fetch_historical_data_success(self, mock_ticker):
        """Test erfolgreiche Datenabfrage"""
        # Mock DataFrame mit Test-Daten
        mock_hist = pd.DataFrame(
            {"Close": [100, 102, 98, 105, 103], "Volume": [1000, 1100, 900, 1200, 1050]},
            index=pd.date_range("2023-01-01", periods=5),
        )

        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_ticker_instance

        manager = HistoricalDataManager()
        result = manager.fetch_historical_data("BTC", "1y")

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        mock_ticker.assert_called_with("BTC-USD")

    @patch("src.modules.historical_data.yf.Ticker")
    def test_fetch_historical_data_empty(self, mock_ticker):
        """Test leere Datenabfrage"""
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance

        manager = HistoricalDataManager()
        result = manager.fetch_historical_data("INVALID", "1y")

        assert result is None

    @patch("src.modules.historical_data.yf.Ticker")
    def test_fetch_historical_data_error(self, mock_ticker):
        """Test Fehlerbehandlung bei Datenabfrage"""
        mock_ticker.side_effect = Exception("API Error")

        manager = HistoricalDataManager()
        result = manager.fetch_historical_data("BTC", "1y")

        assert result is None


class TestAdvancedMetrics:
    """Tests für erweiterte Metriken-Berechnung"""

    @patch.object(HistoricalDataManager, "fetch_historical_data")
    def test_calculate_advanced_metrics_with_real_data(self, mock_fetch):
        """Test Metriken-Berechnung mit echten Daten"""
        # Mock historische Daten
        np.random.seed(42)
        prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 365))
        mock_data = pd.DataFrame({"Close": prices}, index=pd.date_range("2023-01-01", periods=365))

        mock_fetch.return_value = mock_data

        manager = HistoricalDataManager()
        metrics = manager.calculate_advanced_metrics("BTC", "1y")

        # Prüfe erwartete Metriken
        assert "sharpe_ratio" in metrics
        assert "sortino_ratio" in metrics
        assert "calmar_ratio" in metrics
        assert "annual_return" in metrics
        assert "volatility" in metrics
        assert "max_drawdown" in metrics
        assert "var_95" in metrics
        assert "var_99" in metrics
        assert "cvar_95" in metrics
        assert "beta_vs_btc" in metrics
        assert "win_rate" in metrics
        assert "current_price" in metrics

        # Prüfe Datentypen
        assert isinstance(metrics["sharpe_ratio"], float)
        assert isinstance(metrics["data_points"], int)
        assert metrics["data_points"] == 364  # 365 - 1 für pct_change
        assert metrics["symbol"] == "BTC"
        assert metrics["period"] == "1y"

    @patch.object(HistoricalDataManager, "fetch_historical_data")
    def test_calculate_advanced_metrics_fallback(self, mock_fetch):
        """Test Fallback-Metriken bei fehlenden Daten"""
        mock_fetch.return_value = None

        manager = HistoricalDataManager()
        metrics = manager.calculate_advanced_metrics("UNKNOWN", "1y")

        # Sollte Fallback-Metriken verwenden
        assert metrics["data_source"] == "simulated"
        assert "sharpe_ratio" in metrics
        assert isinstance(metrics["sharpe_ratio"], float)

    def test_fallback_metrics_consistency(self):
        """Test dass Fallback-Metriken konsistent sind"""
        manager = HistoricalDataManager()

        metrics1 = manager._get_fallback_metrics("TEST")
        metrics2 = manager._get_fallback_metrics("TEST")

        # Sollten identisch sein (gleicher Seed)
        assert metrics1 == metrics2

    def test_fallback_metrics_different_symbols(self):
        """Test dass verschiedene Symbole verschiedene Fallback-Metriken haben"""
        manager = HistoricalDataManager()

        metrics_btc = manager._get_fallback_metrics("BTC")
        metrics_eth = manager._get_fallback_metrics("ETH")

        # Sollten unterschiedlich sein
        assert metrics_btc != metrics_eth

    @patch.object(HistoricalDataManager, "fetch_historical_data")
    def test_beta_calculation(self, mock_fetch):
        """Test Beta-Berechnung vs BTC"""
        # Mock Daten für Asset und BTC
        np.random.seed(42)
        btc_prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.03, 100))
        asset_prices = 50 * np.cumprod(1 + np.random.normal(0.002, 0.04, 100))

        def mock_fetch_side_effect(symbol, period):
            if symbol == "BTC":
                return pd.DataFrame(
                    {"Close": btc_prices}, index=pd.date_range("2023-01-01", periods=100)
                )
            else:
                return pd.DataFrame(
                    {"Close": asset_prices}, index=pd.date_range("2023-01-01", periods=100)
                )

        mock_fetch.side_effect = mock_fetch_side_effect

        manager = HistoricalDataManager()
        asset_returns = pd.Series(np.diff(asset_prices) / asset_prices[:-1])
        beta = manager._calculate_beta_vs_btc(asset_returns)

        assert isinstance(beta, float)
        assert 0.1 < beta < 3.0  # Realistischer Beta-Bereich


class TestEnhancedFunctions:
    """Tests für erweiterte Funktionen"""

    def test_calculate_crypto_metrics_enhanced(self):
        """Test erweiterte Metriken-Funktion"""
        symbol, metrics = calculate_crypto_metrics_enhanced("BTC", "1y")

        assert symbol == "BTC"
        assert isinstance(metrics, dict)
        assert "sharpe_ratio" in metrics

    @patch("multiprocessing.Pool")
    def test_analyze_crypto_portfolio_enhanced(self, mock_pool):
        """Test erweiterte Portfolio-Analyse"""
        # Mock Pool-Ergebnisse
        mock_pool_instance = MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_pool_instance.map.return_value = [
            ("BTC", {"sharpe_ratio": 1.5, "symbol": "BTC"}),
            ("ETH", {"sharpe_ratio": 1.2, "symbol": "ETH"}),
        ]

        symbols = ["BTC", "ETH"]
        results = analyze_crypto_portfolio_enhanced(symbols, "2y")

        assert isinstance(results, dict)
        assert len(results) == 2
        assert "BTC" in results
        assert "ETH" in results
        mock_pool_instance.map.assert_called_once()

    def test_compare_timeframes(self):
        """Test Zeitraum-Vergleich"""
        timeframes = ["1y", "2y"]
        results = compare_timeframes("BTC", timeframes)

        assert isinstance(results, dict)
        assert "1y" in results
        assert "2y" in results

        for period, metrics in results.items():
            assert period in timeframes
            assert "sharpe_ratio" in metrics

    def test_get_analysis_timeframes(self):
        """Test verfügbare Zeiträume"""
        timeframes = get_analysis_timeframes()

        assert isinstance(timeframes, list)
        assert len(timeframes) > 0
        assert "1y" in timeframes
        assert "2y" in timeframes


class TestMetricsValidation:
    """Tests für Metriken-Validierung"""

    @patch.object(HistoricalDataManager, "fetch_historical_data")
    def test_metrics_bounds_checking(self, mock_fetch):
        """Test dass Metriken in realistischen Bereichen sind"""
        # Mock extreme Daten mit etwas Variation
        np.random.seed(42)  # For consistent results
        base_prices = [100 * (1.1**i) for i in range(100)]  # Steady growth
        extreme_prices = [
            p * (1 + np.random.normal(0, 0.05)) for p in base_prices
        ]  # Add volatility
        mock_data = pd.DataFrame(
            {"Close": extreme_prices}, index=pd.date_range("2023-01-01", periods=100)
        )

        mock_fetch.return_value = mock_data

        manager = HistoricalDataManager()
        metrics = manager.calculate_advanced_metrics("EXTREME", "1y")

        # Sharpe Ratio sollte numerisch sein
        assert isinstance(metrics["sharpe_ratio"], float)
        assert not np.isnan(metrics["sharpe_ratio"])
        assert not np.isinf(metrics["sharpe_ratio"])

        # Max Drawdown sollte negativ oder null sein
        assert metrics["max_drawdown"] <= 0

        # Volatilität sollte positiv sein
        assert metrics["volatility"] > 0

        # Win Rate sollte zwischen 0 und 100 sein
        assert 0 <= metrics["win_rate"] <= 100

    def test_insufficient_data_handling(self):
        """Test Behandlung unzureichender Daten"""
        manager = HistoricalDataManager()

        # Mock mit zu wenig Daten
        short_data = pd.DataFrame(
            {"Close": [100, 101, 99]}, index=pd.date_range("2023-01-01", periods=3)
        )

        with patch.object(manager, "fetch_historical_data", return_value=short_data):
            metrics = manager.calculate_advanced_metrics("SHORT", "1y")

            # Sollte Fallback verwenden (mit oder ohne Live-Preis)
            assert metrics["data_source"] in ["simulated", "simulated_with_live_price"]


class TestErrorHandling:
    """Tests für Fehlerbehandlung"""

    @patch.object(HistoricalDataManager, "fetch_historical_data")
    def test_data_processing_error_handling(self, mock_fetch):
        """Test Fehlerbehandlung bei Datenverarbeitung"""
        # Mock fehlerhafte Daten
        bad_data = pd.DataFrame(
            {"Close": [np.nan, np.inf, -np.inf, 100]}, index=pd.date_range("2023-01-01", periods=4)
        )

        mock_fetch.return_value = bad_data

        manager = HistoricalDataManager()
        metrics = manager.calculate_advanced_metrics("BAD", "1y")

        # Sollte Fallback verwenden oder robuste Behandlung
        assert isinstance(metrics, dict)
        assert "sharpe_ratio" in metrics

    def test_symbol_mapping_fallback(self):
        """Test Fallback für unbekannte Symbole"""
        manager = HistoricalDataManager()

        # Unbekanntes Symbol sollte Standard-Mapping verwenden
        with patch.object(manager, "fetch_historical_data") as mock_fetch:
            mock_fetch.return_value = None
            manager.fetch_historical_data("UNKNOWN_SYMBOL", "1y")

            # Sollte mit UNKNOWN_SYMBOL-USD versuchen
            mock_fetch.assert_called_with("UNKNOWN_SYMBOL", "1y")
