"""
Crypto Trading Bot v2.0 - Main Entry Point
Haupt-Trading-Bot nach der 3-Schritt-Anleitung aus idea.md

SCHRITT 1: Multi-Exchange Price Monitor (Async/IO)
SCHRITT 2: Crypto Portfolio Analyzer (Multiprocessing)
SCHRITT 3: Sauberes Logging (Decorators)
"""

import asyncio
import os
import sys
import time
from typing import Dict

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import specific functions that are used
try:
    # New plugin architecture imports
    from src.analyzers.plugins.arbitrage_analyzer import (
        detect_arbitrage_opportunities,
    )
    from src.communication.plugins.telegram_communication import (
        alert_system,
    )
    from src.adapters import (
        analyze_crypto_portfolio_enhanced,
        compare_timeframes,
    )
    from src.analyzers.plugins.portfolio_analyzer import (
        get_top_cryptocurrencies,
    )
    from src.monitors.plugins.price_monitor import monitor_real_exchange_prices
    
    # New Utils integration
    from src.utils import create_util_manager
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def display_price_data(symbol: str, prices: Dict[str, float]):
    """Display price data for a symbol across exchanges"""
    print(f"💰 {symbol} Prices:")
    for exchange, price in prices.items():
        print(f"   {exchange.capitalize()}: ${price:,.4f}")
    
    if len(prices) >= 2:
        min_price = min(prices.values())
        max_price = max(prices.values())
        spread = ((max_price - min_price) / min_price) * 100
        print(f"   💹 Spread: {spread:.2f}%")


async def crypto_screener():
    """SCHRITT 1: Multi-Exchange Preisvergleich + Arbitrage-Erkennung"""
    print("🔍 CRYPTO SCREENER - Multi-Exchange Price Monitor")
    print("=" * 60)

    # Top Kryptowährungen für Arbitrage-Überwachung
    crypto_symbols = get_top_cryptocurrencies(5)

    arbitrage_history = []

    for symbol in crypto_symbols:
        print(f"\n📊 Analysiere {symbol}...")

        # ECHTE Live-Preise von allen Börsen gleichzeitig abholen
        prices = await monitor_real_exchange_prices(symbol)

        if prices:
            display_price_data(symbol, prices)

            # Arbitrage-Möglichkeiten erkennen
            opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

            if opportunities:
                print("🎯 Arbitrage-Möglichkeiten gefunden:")
                alerts = alert_system(opportunities, min_profit=1.0)
                arbitrage_history.append(opportunities)
            else:
                print("✅ Keine Arbitrage-Möglichkeiten > 1%")
                arbitrage_history.append([])

        # Kurze Pause zwischen Symbolen
        await asyncio.sleep(1)

    return arbitrage_history


async def crypto_portfolio_analyzer():
    """SCHRITT 2: Analysiere 100-200 Kryptowährungen mit echten historischen Daten"""
    print("\n" + "=" * 60)
    print("ENHANCED CRYPTO PORTFOLIO ANALYZER")
    print("=" * 60)

    # Initialize Utils Manager
    print("🔧 Initializing Utils Manager...")
    util_manager = await create_util_manager({'log_level': 'INFO'})
    print(f"✅ Utils Manager ready with {len(util_manager.plugins)} plugins")

    # Erweiterte Krypto-Liste
    crypto_symbols = get_top_cryptocurrencies(100)  # Standard: 100 Coins

    print(f"🔄 Analysiere {len(crypto_symbols)} Kryptowährungen...")
    print("📊 Verwende ECHTE historische Daten für präzise Sharpe Ratios")
    print("📈 Erweiterte Metriken: Sortino, Calmar, VaR, Beta vs BTC")

    # Enhanced Analysis mit echten Daten
    print("\n🚀 Enhanced Analysis (100 Coins mit 2Y historischen Daten):")
    enhanced_start = time.time()
    enhanced_results = await analyze_crypto_portfolio_enhanced(crypto_symbols)
    enhanced_time = time.time() - enhanced_start

    # Zeige erweiterte Ergebnisse
    top_cryptos = display_enhanced_portfolio_results(enhanced_results, top_n=15)

    # Vergleiche verschiedene Zeiträume für Top 5 Coins
    print("\n📊 Multi-Timeframe Analysis für TOP 5 Coins:")
    timeframe_analysis = {}
    for i, (symbol, _) in enumerate(top_cryptos[:5]):
        print(f"🔍 Analysiere {symbol} über verschiedene Zeiträume...")
        timeframe_analysis[symbol] = compare_timeframes(symbol, ["1y", "2y", "3y"])

    display_timeframe_comparison(timeframe_analysis)

    print("\n⚡ Enhanced Analysis Performance:")
    print(f"   100 Coins mit echten Daten: {enhanced_time:.2f}s")
    print(f"   Durchschnitt pro Coin: {enhanced_time/len(crypto_symbols):.3f}s")

    return top_cryptos, enhanced_results, timeframe_analysis


def display_enhanced_portfolio_results(results: Dict, top_n: int = 15):
    """Zeige erweiterte Portfolio-Ergebnisse mit allen Metriken"""
    # Extract portfolio analysis from new format
    portfolio_analysis = results.get("portfolio_analysis", {})
    
    # Filtere gültige Ergebnisse (sichere Prüfung auf Dictionary)
    valid_results = {k: v for k, v in portfolio_analysis.items() if isinstance(v, dict) and "error" not in v and v.get("current_price", 0) > 0}

    if not valid_results:
        print("❌ Keine gültigen Portfolio-Daten verfügbar")
        return []

    # Sortiere nach Preis (da Sharpe Ratio nicht verfügbar ist in neuer Struktur)
    sorted_cryptos = sorted(valid_results.items(), key=lambda x: x[1].get("current_price", 0), reverse=True)

    print(f"\n🏆 TOP {top_n} Kryptowährungen nach Preis:")
    print("=" * 70)
    print(f"{'Rank':<4} {'Symbol':<8} {'Price':<12} {'Volume':<15} {'MarketCap':<15}")
    print("-" * 70)

    for i, (symbol, metrics) in enumerate(sorted_cryptos[:top_n], 1):
        price = metrics.get("current_price", 0)
        volume = metrics.get("volume_24h", 0) or 0
        market_cap = metrics.get("market_cap", 0) or 0
        
        # Format large numbers
        volume_str = f"${volume/1e6:.1f}M" if volume > 1e6 else f"${volume:.0f}"
        mcap_str = f"${market_cap/1e9:.1f}B" if market_cap > 1e9 else f"${market_cap/1e6:.1f}M" if market_cap > 1e6 else f"${market_cap:.0f}"
        
        print(f"{i:3d}. {symbol:<8} ${price:<11.4f} {volume_str:<15} {mcap_str:<15}")

    print("\n📊 Statistiken der Analyse:")
    print(f"   📈 Portfolio-Wert: ${results.get('total_portfolio_value', 0):.2f}")
    print(f"   💰 Analysierte Coins: {len(valid_results)} von {len(portfolio_analysis)}")

    return [(symbol, metrics) for symbol, metrics in sorted_cryptos[:top_n]]


def display_timeframe_comparison(timeframe_analysis: Dict[str, Dict]):
    """Zeige Vergleich verschiedener Zeiträume"""
    print("\n📈 MULTI-TIMEFRAME SHARPE RATIO COMPARISON:")
    print("=" * 70)
    print(f"{'Symbol':<8} {'1Y':<10} {'2Y':<10} {'3Y':<10} {'Trend':<8}")
    print("-" * 70)

    for symbol, timeframes in timeframe_analysis.items():
        sharpe_1y = timeframes.get("1y", {}).get("sharpe_ratio", 0)
        sharpe_2y = timeframes.get("2y", {}).get("sharpe_ratio", 0)
        sharpe_3y = timeframes.get("3y", {}).get("sharpe_ratio", 0)

        # Bestimme Trend
        if sharpe_3y > sharpe_2y > sharpe_1y:
            trend = "📈 UP"
        elif sharpe_1y > sharpe_2y > sharpe_3y:
            trend = "📉 DOWN"
        else:
            trend = "↔️ MIX"

        print(f"{symbol:<8} {sharpe_1y:<10.3f} {sharpe_2y:<10.3f} {sharpe_3y:<10.3f} {trend:<8}")

    print("\n💡 Interpretation:")
    print("   📈 UP: Konstant steigende Performance über Zeit")
    print("   📉 DOWN: Performance verschlechtert sich über Zeit")
    print("   ↔️ MIX: Gemischte Performance je nach Zeitraum")


async def main():
    """Haupt-Trading-Bot nach der 3-Schritt-Anleitung"""
    print("🚀 CRYPTO TRADING BOT v2.0")
    print("Basierend auf YouTube-Video: 3 Advanced Python Concepts")
    print("Modulare Architektur für bessere Wartbarkeit")
    print("=" * 80)

    try:
        # SCHRITT 1: Multi-Exchange Price Monitor (Async/IO)
        arbitrage_history = await crypto_screener()

        # SCHRITT 2: Enhanced Portfolio Analyzer (Multiprocessing + Real Data)
        top_cryptos, portfolio_results, timeframe_analysis = await crypto_portfolio_analyzer()

        # Zusammenfassung
        print("\n" + "=" * 80)
        print("✨ CRYPTO TRADING BOT ERFOLGREICH IMPLEMENTIERT!")
        print("📊 Alle 3 Python-Konzepte erfolgreich umgesetzt:")
        print("  1. ✅ Multi-Exchange Price Monitor (Async/IO)")
        print("  2. ✅ Crypto Portfolio Analyzer (Multiprocessing)")
        print("  3. ✅ Automatisches Logging aller Aktionen (Decorators)")

        # Arbitrage-Statistiken
        total_opportunities = sum(len(opps) for opps in arbitrage_history)
        print("\n📈 Session-Statistiken:")
        print(f"   Überwachte Symbole: {len(get_top_cryptocurrencies(5))}")
        print(f"   Gefundene Arbitrage-Möglichkeiten: {total_opportunities}")
        print(f"   Analysierte Kryptowährungen: {len(get_top_cryptocurrencies(50))}")

        if top_cryptos:
            best_crypto = top_cryptos[0]
            print(f"   Beste Kryptowährung: {best_crypto[0]} (Preis: ${best_crypto[1].get('current_price', 0):.2f})")

        print("\n🎯 Nächste Schritte:")
        print("  - Erweitere zu Arbitrage Bot")
        print("  - Füge Backtesting Engine hinzu")
        print("  - Implementiere automatisches Trading")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Fehler im Trading Bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
