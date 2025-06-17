"""
Integration Tests für main.py
Teste das Zusammenspiel aller Module
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

import src.main as main


class TestCryptoScreener:
    """Integration Tests für crypto_screener Funktion"""

    @pytest.mark.asyncio
    async def test_crypto_screener_execution(self, capsys):
        """Test vollständige Ausführung des Crypto Screeners"""
        # Mocke get_popular_crypto_symbols um weniger Symbole zu verwenden
        with patch("src.main.get_popular_crypto_symbols") as mock_symbols:
            mock_symbols.return_value = ["BTC/USDT", "ETH/USDT"]

            arbitrage_history = await main.crypto_screener()

            captured = capsys.readouterr()

            # Prüfe dass die Funktion ausgeführt wurde
            assert isinstance(arbitrage_history, list)
            assert len(arbitrage_history) == 2  # 2 Symbole

            # Prüfe Output
            assert "CRYPTO SCREENER" in captured.out
            assert "BTC/USDT" in captured.out
            assert "ETH/USDT" in captured.out

    @pytest.mark.asyncio
    async def test_crypto_screener_with_arbitrage(self, capsys):
        """Test Crypto Screener mit Arbitrage-Möglichkeiten"""
        # Mocke nur ein Symbol für predictable results
        with patch("src.main.get_popular_crypto_symbols") as mock_symbols:
            mock_symbols.return_value = ["DOT/USDT"]  # Dieses Symbol hat oft Arbitrage

            arbitrage_history = await main.crypto_screener()
            captured = capsys.readouterr()

            # Sollte mindestens ein Element haben
            assert len(arbitrage_history) == 1

            # Könnte Arbitrage-Möglichkeiten enthalten
            if arbitrage_history[0]:  # Wenn Arbitrage gefunden
                assert "ARBITRAGE ALERT" in captured.out


class TestCryptoPortfolioAnalyzer:
    """Integration Tests für crypto_portfolio_analyzer Funktion"""

    def test_portfolio_analyzer_execution(self, capsys):
        """Test vollständige Ausführung des Portfolio Analyzers"""
        # Mocke get_top_cryptocurrencies für kleinere Anzahl
        with patch("src.main.get_top_cryptocurrencies") as mock_cryptos:
            mock_cryptos.return_value = ["BTC", "ETH", "ADA", "DOT", "LINK"]

            top_cryptos, portfolio_results, timeframe_analysis = main.crypto_portfolio_analyzer()

            captured = capsys.readouterr()

            # Prüfe Rückgabewerte
            assert isinstance(top_cryptos, list)
            assert isinstance(portfolio_results, dict)
            assert len(portfolio_results) == 5  # 5 Symbole

            # Prüfe Output
            assert "CRYPTO PORTFOLIO ANALYZER" in captured.out
            assert "TOP 15 Kryptowährungen" in captured.out
            assert "Multi-Timeframe Analysis" in captured.out

    def test_portfolio_analyzer_results_structure(self):
        """Test Struktur der Portfolio Analyzer Ergebnisse"""
        with patch("src.main.get_top_cryptocurrencies") as mock_cryptos:
            mock_cryptos.return_value = ["BTC", "ETH"]

            top_cryptos, portfolio_results, timeframe_analysis = main.crypto_portfolio_analyzer()

            # Prüfe top_cryptos Struktur
            assert len(top_cryptos) <= 10  # Maximal 10
            for crypto_data in top_cryptos:
                assert len(crypto_data) == 2  # (symbol, metrics)
                symbol, metrics = crypto_data
                assert isinstance(symbol, str)
                assert isinstance(metrics, dict)
                assert "sharpe_ratio" in metrics

            # Prüfe portfolio_results Struktur
            for symbol, metrics in portfolio_results.items():
                assert symbol in ["BTC", "ETH"]
                assert "sharpe_ratio" in metrics
                assert "volatility" in metrics


class TestMainFunction:
    """Integration Tests für main Funktion"""

    @pytest.mark.asyncio
    async def test_main_function_complete_execution(self, capsys):
        """Test vollständige Ausführung der main Funktion"""
        # Mocke beide get functions für kleinere Datenmengen
        with patch("src.main.get_popular_crypto_symbols") as mock_symbols, patch(
            "src.main.get_top_cryptocurrencies"
        ) as mock_cryptos:

            mock_symbols.return_value = ["BTC/USDT"]
            mock_cryptos.return_value = ["BTC", "ETH"]

            # Führe main aus
            await main.main()

            captured = capsys.readouterr()

            # Prüfe dass alle Hauptabschnitte ausgeführt wurden
            assert "CRYPTO TRADING BOT v2.0" in captured.out
            assert "CRYPTO SCREENER" in captured.out
            assert "CRYPTO PORTFOLIO ANALYZER" in captured.out
            assert "ERFOLGREICH IMPLEMENTIERT" in captured.out
            assert "Session-Statistiken" in captured.out

    @pytest.mark.asyncio
    async def test_main_function_error_handling(self, capsys):
        """Test Error-Handling in main Funktion"""
        # Mocke eine Funktion um Fehler zu werfen
        with patch("src.main.crypto_screener") as mock_screener:
            mock_screener.side_effect = Exception("Test error")

            # main sollte Exception re-raisen
            with pytest.raises(Exception, match="Test error"):
                await main.main()

            captured = capsys.readouterr()
            assert "Fehler im Trading Bot" in captured.out

    @pytest.mark.asyncio
    async def test_main_statistics_calculation(self, capsys):
        """Test Statistik-Berechnung in main"""
        with patch("src.main.get_popular_crypto_symbols") as mock_symbols, patch(
            "src.main.get_top_cryptocurrencies"
        ) as mock_cryptos:

            mock_symbols.return_value = ["BTC/USDT", "ETH/USDT"]
            mock_cryptos.return_value = ["BTC", "ETH", "ADA"]

            await main.main()
            captured = capsys.readouterr()

            # Prüfe Statistiken
            assert "Überwachte Symbole: 2" in captured.out
            assert "Analysierte Kryptowährungen: 3" in captured.out
            assert "Gefundene Arbitrage-Möglichkeiten:" in captured.out


class TestModuleIntegration:
    """Tests für Integration zwischen verschiedenen Modulen"""

    @pytest.mark.asyncio
    async def test_price_monitor_arbitrage_integration(self):
        """Test Integration zwischen Price Monitor und Arbitrage Detector"""
        from src.modules.arbitrage_detector import detect_arbitrage_opportunities
        from src.modules.real_price_monitor import monitor_real_exchange_prices

        # Hole Preise
        prices = await monitor_real_exchange_prices("BTC/USDT")

        # Erkenne Arbitrage
        opportunities = detect_arbitrage_opportunities(prices, threshold=0.005)

        # Prüfe Kompatibilität
        assert isinstance(prices, dict)
        assert isinstance(opportunities, list)

        # Wenn Arbitrage gefunden, prüfe Struktur
        for opp in opportunities:
            assert opp["buy_exchange"] in prices
            assert opp["sell_exchange"] in prices
            assert opp["buy_price"] == prices[opp["buy_exchange"]]
            assert opp["sell_price"] == prices[opp["sell_exchange"]]

    def test_portfolio_analyzer_display_integration(self):
        """Test Integration zwischen Portfolio Analyzer und Display"""
        from src.modules.portfolio_analyzer import (
            analyze_crypto_portfolio_parallel,
            display_portfolio_results,
        )

        # Analysiere Portfolio
        symbols = ["BTC", "ETH", "ADA"]
        results = analyze_crypto_portfolio_parallel(symbols)

        # Zeige Ergebnisse an
        top_cryptos = display_portfolio_results(results, top_n=2)

        # Prüfe Integration
        assert len(top_cryptos) <= 2
        assert all(symbol in results for symbol, _ in top_cryptos)


class TestPerformanceIntegration:
    """Tests für Performance-Integration"""

    @pytest.mark.asyncio
    async def test_async_performance_timing(self):
        """Test dass async Operationen parallel laufen"""
        import time

        start_time = time.time()

        # Führe mehrere async Operationen parallel aus
        from src.modules.real_price_monitor import monitor_real_exchange_prices

        tasks = [monitor_real_exchange_prices("BTC/USDT"), monitor_real_exchange_prices("ETH/USDT")]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Parallel sollte schneller sein als sequential
        assert (end_time - start_time) < 1.5  # Weniger als 3 * 0.5s
        assert len(results) == 2

    def test_multiprocessing_performance(self):
        """Test Multiprocessing Performance"""
        import time

        from src.modules.portfolio_analyzer import (
            analyze_crypto_portfolio_parallel,
            analyze_crypto_portfolio_sequential,
        )

        symbols = ["BTC", "ETH", "ADA", "DOT", "LINK"]

        # Sequential
        start_seq = time.time()
        seq_results = analyze_crypto_portfolio_sequential(symbols)
        seq_time = time.time() - start_seq

        # Parallel
        start_par = time.time()
        par_results = analyze_crypto_portfolio_parallel(symbols)
        par_time = time.time() - start_par

        # Ergebnisse sollten identisch sein
        assert seq_results == par_results

        # Parallel sollte nicht langsamer sein (kann auf kleinen Sets gleich sein)
        assert par_time <= seq_time + 0.1  # Kleine Toleranz für Overhead


class TestErrorHandlingIntegration:
    """Tests für Error-Handling zwischen Modulen"""

    @pytest.mark.asyncio
    async def test_price_monitor_error_propagation(self):
        """Test Error-Handling im Price Monitor"""
        from src.modules.real_price_monitor import monitor_real_exchange_prices

        # Sollte auch bei "Fehlern" ein dict zurückgeben
        prices = await monitor_real_exchange_prices("INVALID/SYMBOL")

        assert isinstance(prices, dict)
        # Simulierte Preise sollten trotzdem funktionieren

    def test_portfolio_analyzer_error_handling(self):
        """Test Error-Handling im Portfolio Analyzer"""
        from src.modules.portfolio_analyzer import analyze_crypto_portfolio_parallel

        # Auch mit invalid symbols sollte es funktionieren
        results = analyze_crypto_portfolio_parallel(["INVALID_SYMBOL"])

        assert isinstance(results, dict)
        assert "INVALID_SYMBOL" in results
