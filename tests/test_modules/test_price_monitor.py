"""
Tests für modules/price_monitor.py
Teste Async/IO Price Monitoring
"""

import asyncio

import pytest

from src.modules.price_monitor import (
    display_price_data,
    fetch_crypto_price,
    get_popular_crypto_symbols,
    monitor_multi_exchange_prices,
    monitor_multiple_symbols,
)


class TestFetchCryptoPrice:
    """Tests für fetch_crypto_price Funktion"""

    @pytest.mark.asyncio
    async def test_fetch_price_success(self):
        """Test erfolgreiche Preis-Abfrage"""
        exchange = "binance"
        symbol = "BTC/USDT"

        result_exchange, price, result_symbol = await fetch_crypto_price(exchange, symbol)

        assert result_exchange == exchange
        assert result_symbol == symbol
        assert isinstance(price, float)
        assert price > 0

    @pytest.mark.asyncio
    async def test_fetch_price_different_exchanges(self):
        """Test verschiedene Exchanges liefern unterschiedliche Preise"""
        symbol = "BTC/USDT"

        binance_result = await fetch_crypto_price("binance", symbol)
        coinbase_result = await fetch_crypto_price("coinbase", symbol)
        kraken_result = await fetch_crypto_price("kraken", symbol)

        # Preise sollten unterschiedlich sein (simulierte Spreads)
        binance_price = binance_result[1]
        coinbase_price = coinbase_result[1]
        kraken_price = kraken_result[1]

        assert binance_price != coinbase_price
        assert binance_price != kraken_price
        assert coinbase_price != kraken_price

    @pytest.mark.asyncio
    async def test_fetch_price_reproducible(self):
        """Test dass gleiche Parameter reproduzierbare Ergebnisse liefern"""
        exchange = "binance"
        symbol = "ETH/USDT"

        result1 = await fetch_crypto_price(exchange, symbol)
        result2 = await fetch_crypto_price(exchange, symbol)

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_fetch_price_timing(self):
        """Test dass Funktion async sleep verwendet"""
        import time

        start_time = time.time()
        await fetch_crypto_price("binance", "BTC/USDT")
        end_time = time.time()

        # Sollte mindestens 0.5 Sekunden dauern (simulierte Latenz)
        assert (end_time - start_time) >= 0.4

    @pytest.mark.asyncio
    async def test_fetch_price_known_symbols(self):
        """Test bekannte Symbole haben erwartete Preise"""
        btc_result = await fetch_crypto_price("binance", "BTC/USDT")
        eth_result = await fetch_crypto_price("binance", "ETH/USDT")

        btc_price = btc_result[1]
        eth_price = eth_result[1]

        # BTC sollte teurer als ETH sein
        assert btc_price > eth_result[1]

        # Preise sollten in realistischen Bereichen sein
        assert 40000 <= btc_price <= 50000
        assert 2500 <= eth_price <= 3500


class TestMonitorMultiExchangePrices:
    """Tests für monitor_multi_exchange_prices Funktion"""

    @pytest.mark.asyncio
    async def test_monitor_default_exchanges(self):
        """Test Überwachung mit Standard-Exchanges"""
        symbol = "BTC/USDT"

        prices = await monitor_multi_exchange_prices(symbol)

        assert isinstance(prices, dict)
        assert len(prices) == 3  # binance, coinbase, kraken
        assert "binance" in prices
        assert "coinbase" in prices
        assert "kraken" in prices

        for exchange, price in prices.items():
            assert isinstance(price, float)
            assert price > 0

    @pytest.mark.asyncio
    async def test_monitor_custom_exchanges(self):
        """Test Überwachung mit benutzerdefinierten Exchanges"""
        symbol = "ETH/USDT"
        exchanges = ["binance", "coinbase"]

        prices = await monitor_multi_exchange_prices(symbol, exchanges)

        assert len(prices) == 2
        assert "binance" in prices
        assert "coinbase" in prices
        assert "kraken" not in prices

    @pytest.mark.asyncio
    async def test_monitor_timing_performance(self):
        """Test dass monitoring parallel ausgeführt wird"""
        import time

        symbol = "BTC/USDT"

        start_time = time.time()
        prices = await monitor_multi_exchange_prices(symbol)
        end_time = time.time()

        # Parallel sollte nicht länger als 1 Sekunde dauern
        # (3 * 0.5s sequentiell wären 1.5s)
        assert (end_time - start_time) < 1.0
        assert len(prices) == 3

    @pytest.mark.asyncio
    async def test_monitor_with_single_exchange(self):
        """Test Überwachung mit nur einem Exchange"""
        symbol = "BTC/USDT"
        exchanges = ["binance"]

        prices = await monitor_multi_exchange_prices(symbol, exchanges)

        assert len(prices) == 1
        assert "binance" in prices


class TestMonitorMultipleSymbols:
    """Tests für monitor_multiple_symbols Funktion"""

    @pytest.mark.asyncio
    async def test_monitor_multiple_symbols_structure(self):
        """Test Struktur bei Überwachung mehrerer Symbole"""
        symbols = ["BTC/USDT", "ETH/USDT"]

        results = await monitor_multiple_symbols(symbols)

        assert isinstance(results, dict)
        assert len(results) == 2
        assert "BTC/USDT" in results
        assert "ETH/USDT" in results

        for symbol, prices in results.items():
            assert isinstance(prices, dict)
            assert len(prices) == 3  # Standard 3 exchanges

    @pytest.mark.asyncio
    async def test_monitor_multiple_symbols_custom_exchanges(self):
        """Test mehrere Symbole mit benutzerdefinierten Exchanges"""
        symbols = ["BTC/USDT", "ETH/USDT"]
        exchanges = ["binance", "coinbase"]

        results = await monitor_multiple_symbols(symbols, exchanges)

        for symbol, prices in results.items():
            assert len(prices) == 2
            assert "binance" in prices
            assert "coinbase" in prices

    @pytest.mark.asyncio
    async def test_monitor_empty_symbol_list(self):
        """Test leere Symbol-Liste"""
        results = await monitor_multiple_symbols([])
        assert results == {}


class TestUtilityFunctions:
    """Tests für Utility-Funktionen"""

    def test_get_popular_crypto_symbols_default(self):
        """Test Standard-Anzahl beliebter Symbole"""
        symbols = get_popular_crypto_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) == 10
        assert "BTC/USDT" in symbols
        assert "ETH/USDT" in symbols

    def test_get_popular_crypto_symbols_custom_count(self):
        """Test benutzerdefinierte Anzahl"""
        symbols = get_popular_crypto_symbols(5)

        assert len(symbols) == 5
        assert "BTC/USDT" in symbols

    def test_get_popular_crypto_symbols_no_duplicates(self):
        """Test keine Duplikate in Symbol-Liste"""
        symbols = get_popular_crypto_symbols(10)

        assert len(symbols) == len(set(symbols))

    def test_display_price_data_with_prices(self, capsys):
        """Test Anzeige von Preis-Daten"""
        symbol = "BTC/USDT"
        prices = {"binance": 45000.0, "coinbase": 45100.0, "kraken": 44900.0}

        display_price_data(symbol, prices)
        captured = capsys.readouterr()

        assert "Aktuelle Preise für {symbol}" in captured.out
        assert "BINANCE: $45,000.00" in captured.out
        assert "COINBASE: $45,100.00" in captured.out
        assert "KRAKEN: $44,900.00" in captured.out

    def test_display_price_data_empty_prices(self, capsys):
        """Test Anzeige bei leeren Preis-Daten"""
        symbol = "BTC/USDT"
        prices = {}

        display_price_data(symbol, prices)
        captured = capsys.readouterr()

        assert "Keine Preisdaten" in captured.out
        assert symbol in captured.out


class TestPriceMonitorEdgeCases:
    """Tests für Edge Cases im Price Monitoring"""

    @pytest.mark.asyncio
    async def test_fetch_price_unknown_symbol(self):
        """Test unbekanntes Symbol"""
        result = await fetch_crypto_price("binance", "UNKNOWN/USDT")

        exchange, price, symbol = result
        assert exchange == "binance"
        assert symbol == "UNKNOWN/USDT"
        assert isinstance(price, float)
        assert 99.0 <= price <= 105.0  # Default-Preis für unbekannte Symbole mit Variation

    @pytest.mark.asyncio
    async def test_monitor_with_empty_exchange_list(self):
        """Test Überwachung mit leerer Exchange-Liste"""
        symbol = "BTC/USDT"

        prices = await monitor_multi_exchange_prices(symbol, [])

        assert prices == {}

    @pytest.mark.asyncio
    async def test_concurrent_price_fetching(self):
        """Test dass mehrere Preis-Abfragen parallel laufen"""
        import time

        # Starte mehrere fetch_crypto_price Calls gleichzeitig
        tasks = [
            fetch_crypto_price("binance", "BTC/USDT"),
            fetch_crypto_price("coinbase", "ETH/USDT"),
            fetch_crypto_price("kraken", "ADA/USDT"),
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Parallel sollte schneller sein als 3 * 0.5s = 1.5s
        assert (end_time - start_time) < 1.0
        assert len(results) == 3
