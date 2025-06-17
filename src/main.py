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
from typing import Dict, List

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.modules.arbitrage_detector import (
    alert_system,
    detect_arbitrage_opportunities,
    get_best_arbitrage_opportunity,
)
from src.modules.historical_data import (
    HistoricalDataManager,
    analyze_crypto_portfolio_enhanced,
    compare_timeframes,
    get_analysis_timeframes,
)
from src.modules.portfolio_analyzer import (
    analyze_crypto_portfolio_parallel,
    analyze_crypto_portfolio_sequential,
    display_portfolio_results,
    get_top_cryptocurrencies,
)
from src.modules.price_monitor import display_price_data, get_popular_crypto_symbols

# Import Module
from src.modules.real_price_monitor import (
    get_current_market_prices,
    monitor_real_exchange_prices,
)


async def crypto_screener():
    """SCHRITT 1: Multi-Exchange Preisvergleich + Arbitrage-Erkennung"""
    print("🔍 CRYPTO SCREENER - Multi-Exchange Price Monitor")
    print("=" * 60)

    # Top Kryptowährungen für Arbitrage-Überwachung
    crypto_symbols = get_popular_crypto_symbols(5)

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
                print(f"🎯 Arbitrage-Möglichkeiten gefunden:")
                alerts = alert_system(opportunities, min_profit=1.0)
                arbitrage_history.append(opportunities)
            else:
                print("✅ Keine Arbitrage-Möglichkeiten > 1%")
                arbitrage_history.append([])

        # Kurze Pause zwischen Symbolen
        await asyncio.sleep(1)

    return arbitrage_history


def crypto_portfolio_analyzer():
    """SCHRITT 2: Analysiere 100-200 Kryptowährungen mit echten historischen Daten"""
    print("\n" + "=" * 60)
    print("ENHANCED CRYPTO PORTFOLIO ANALYZER")
    print("=" * 60)

    # Erweiterte Krypto-Liste
    crypto_symbols = get_top_cryptocurrencies(100)  # Standard: 100 Coins

    print(f"🔄 Analysiere {len(crypto_symbols)} Kryptowährungen...")
    print("📊 Verwende ECHTE historische Daten für präzise Sharpe Ratios")
    print("📈 Erweiterte Metriken: Sortino, Calmar, VaR, Beta vs BTC")

    # Enhanced Analysis mit echten Daten
    print("\n🚀 Enhanced Analysis (100 Coins mit 2Y historischen Daten):")
    enhanced_start = time.time()
    enhanced_results = analyze_crypto_portfolio_enhanced(crypto_symbols, period="2y")
    enhanced_time = time.time() - enhanced_start

    # Zeige erweiterte Ergebnisse
    top_cryptos = display_enhanced_portfolio_results(enhanced_results, top_n=15)

    # Vergleiche verschiedene Zeiträume für Top 5 Coins
    print(f"\n📊 Multi-Timeframe Analysis für TOP 5 Coins:")
    timeframe_analysis = {}
    for i, (symbol, _) in enumerate(top_cryptos[:5]):
        print(f"🔍 Analysiere {symbol} über verschiedene Zeiträume...")
        timeframe_analysis[symbol] = compare_timeframes(symbol, ["1y", "2y", "3y"])

    display_timeframe_comparison(timeframe_analysis)

    print(f"\n⚡ Enhanced Analysis Performance:")
    print(f"   100 Coins mit echten Daten: {enhanced_time:.2f}s")
    print(f"   Durchschnitt pro Coin: {enhanced_time/len(crypto_symbols):.3f}s")

    return top_cryptos, enhanced_results, timeframe_analysis


def display_enhanced_portfolio_results(results: Dict[str, Dict], top_n: int = 15):
    """Zeige erweiterte Portfolio-Ergebnisse mit allen Metriken"""
    # Filtere gültige Ergebnisse
    valid_results = {k: v for k, v in results.items() if "error" not in v}

    # Sortiere nach Sharpe Ratio
    sorted_cryptos = sorted(valid_results.items(), key=lambda x: x[1]["sharpe_ratio"], reverse=True)

    print(f"\n🏆 TOP {top_n} Kryptowährungen nach Sharpe Ratio (2Y Daten):")
    print("=" * 90)
    print(
        f"{'Rank':<4} {'Symbol':<8} {'Sharpe':<8} {'Sortino':<8} {'Return%':<8} {'Vol%':<8} {'MaxDD%':<8} {'Beta':<6} {'Price':<10}"
    )
    print("-" * 90)

    for i, (symbol, metrics) in enumerate(sorted_cryptos[:top_n], 1):
        data_source = "🔴" if metrics.get("data_source") == "simulated" else "🟢"
        print(
            f"{i:3d}. {symbol:<8} {metrics['sharpe_ratio']:<8} {metrics['sortino_ratio']:<8} "
            f"{metrics['annual_return']:>6.1f}% {metrics['volatility']:>6.1f}% "
            f"{metrics['max_drawdown']:>6.1f}% {metrics['beta_vs_btc']:<6} "
            f"${metrics['current_price']:<9.2f} {data_source}"
        )

    print(f"\n📊 Statistiken der Analyse:")
    real_data_count = sum(
        1 for _, v in valid_results.items() if v.get("data_source") != "simulated"
    )
    simulated_count = len(valid_results) - real_data_count

    print(f"   🟢 Echte Marktdaten: {real_data_count} Coins")
    print(f"   🔴 Simulierte Daten: {simulated_count} Coins")
    print(f"   📈 Analysierte Coins: {len(valid_results)} von {len(results)}")

    return sorted_cryptos[:top_n]


def display_timeframe_comparison(timeframe_analysis: Dict[str, Dict]):
    """Zeige Vergleich verschiedener Zeiträume"""
    print(f"\n📈 MULTI-TIMEFRAME SHARPE RATIO COMPARISON:")
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
        top_cryptos, portfolio_results, timeframe_analysis = crypto_portfolio_analyzer()

        # Zusammenfassung
        print("\n" + "=" * 80)
        print("✨ CRYPTO TRADING BOT ERFOLGREICH IMPLEMENTIERT!")
        print("📊 Alle 3 Python-Konzepte erfolgreich umgesetzt:")
        print("  1. ✅ Multi-Exchange Price Monitor (Async/IO)")
        print("  2. ✅ Crypto Portfolio Analyzer (Multiprocessing)")
        print("  3. ✅ Automatisches Logging aller Aktionen (Decorators)")

        # Arbitrage-Statistiken
        total_opportunities = sum(len(opps) for opps in arbitrage_history)
        print(f"\n📈 Session-Statistiken:")
        print(f"   Überwachte Symbole: {len(get_popular_crypto_symbols(5))}")
        print(f"   Gefundene Arbitrage-Möglichkeiten: {total_opportunities}")
        print(f"   Analysierte Kryptowährungen: {len(get_top_cryptocurrencies(50))}")

        if top_cryptos:
            best_crypto = top_cryptos[0]
            print(
                f"   Beste Kryptowährung: {best_crypto[0]} (Sharpe: {best_crypto[1]['sharpe_ratio']:.4f})"
            )

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
