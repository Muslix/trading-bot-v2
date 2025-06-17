"""
Multi-Exchange Price Monitor - Async/IO Module
Live-Preise von Binance, Coinbase, Kraken gleichzeitig abholen
Async/IO für extreme Geschwindigkeitsvorteile
"""

import asyncio
import random
from typing import Dict, List, Tuple

from src.utils.decorators import async_log_performance


@async_log_performance
async def fetch_crypto_price(exchange_name: str, symbol: str) -> Tuple[str, float, str]:
    """Live-Preise von Exchange abholen (Simuliert für Demo)"""
    try:
        # Simuliere API-Call mit realistischen Preisen
        await asyncio.sleep(0.5)  # Simuliere API-Latenz

        # Simuliere realistische Preise basierend auf Exchange und Symbol
        base_prices = {
            "BTC/USDT": 45000,
            "ETH/USDT": 3000,
            "BNB/USDT": 300,
            "ADA/USDT": 0.5,
            "DOT/USDT": 25,
            "XRP/USDT": 0.6,
            "LTC/USDT": 150,
            "LINK/USDT": 15,
            "DOGE/USDT": 0.08,
            "MATIC/USDT": 1.2,
        }

        # Kleine Preisunterschiede zwischen Exchanges simulieren
        price_multipliers = {
            "binance": 1.0,
            "coinbase": 1.002,  # 0.2% höher
            "kraken": 0.998,  # 0.2% niedriger
        }

        base_price = base_prices.get(symbol, 100)
        multiplier = price_multipliers.get(exchange_name.lower(), 1.0)

        # Kleine zufällige Variation
        random.seed(hash(exchange_name + symbol) % 1000)
        variation = random.uniform(0.995, 1.005)

        final_price = base_price * multiplier * variation

        return (exchange_name, round(final_price, 2), symbol)

    except Exception as e:
        print(f"⚠️ {exchange_name} API Fehler für {symbol}: {e}")
        return (exchange_name, 0.0, symbol)


@async_log_performance
async def monitor_multi_exchange_prices(symbol: str, exchanges: List[str] = None) -> Dict[str, float]:
    """Live-Preise von mehreren Börsen gleichzeitig abholen"""

    if exchanges is None:
        exchanges = ["binance", "coinbase", "kraken"]

    print(f"🔍 Überwache {symbol} auf {len(exchanges)} Börsen gleichzeitig...")

    # Alle API-Calls parallel starten
    tasks = [fetch_crypto_price(exchange, symbol) for exchange in exchanges]

    # Warten auf alle Antworten
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Ergebnisse verarbeiten
    prices = {}
    for result in results:
        if isinstance(result, Exception):
            continue

        exchange_name, price, _ = result
        if price > 0:
            prices[exchange_name] = price

    return prices


async def monitor_multiple_symbols(symbols: List[str], exchanges: List[str] = None) -> Dict[str, Dict[str, float]]:
    """Überwache mehrere Symbole gleichzeitig auf allen Börsen"""

    if exchanges is None:
        exchanges = ["binance", "coinbase", "kraken"]

    print(f"🔍 Überwache {len(symbols)} Symbole auf {len(exchanges)} Börsen...")

    # Alle Symbol-Überwachungen parallel starten
    tasks = [monitor_multi_exchange_prices(symbol, exchanges) for symbol in symbols]

    # Warten auf alle Ergebnisse
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Ergebnisse strukturieren
    symbol_prices = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        symbol_prices[symbols[i]] = result

    return symbol_prices


def display_price_data(symbol: str, prices: Dict[str, float]):
    """Zeige Preis-Daten für ein Symbol"""
    if prices:
        print(f"💰 Aktuelle Preise für {symbol}:")
        for exchange, price in prices.items():
            print(f"   {exchange.upper()}: ${price:,.2f}")
    else:
        print(f"⚠️ Keine Preisdaten für {symbol} verfügbar")


def get_popular_crypto_symbols(n: int = 10) -> List[str]:
    """Hole die beliebtesten Krypto-Symbole für Überwachung"""
    symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "ADA/USDT",
        "DOT/USDT",
        "XRP/USDT",
        "LTC/USDT",
        "LINK/USDT",
        "DOGE/USDT",
        "MATIC/USDT",
    ]
    return symbols[:n]
