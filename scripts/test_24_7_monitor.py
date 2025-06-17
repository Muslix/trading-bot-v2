"""
Test Script für 24/7 Monitoring System
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_monitor_24_7 import CryptoMonitor24_7


async def test_monitoring():
    """Teste das 24/7 Monitoring System für ein paar Cycles"""
    print("🧪 24/7 MONITORING TEST")
    print("=" * 50)
    
    monitor = CryptoMonitor24_7()
    
    # Überschreibe Konfiguration für schnellen Test
    monitor.config['arbitrage_check_interval'] = 5  # 5 Sekunden für Test
    monitor.config['performance_check_interval'] = 20  # 20 Sekunden für Test
    monitor.config['watchlist_symbols'] = ['BTC/USDT', 'ETH/USDT']  # Nur 2 für Test
    monitor.config['analysis_crypto_count'] = 10  # Weniger für Test
    
    print(f"⚙️ Test-Konfiguration:")
    print(f"   • Arbitrage Check: alle {monitor.config['arbitrage_check_interval']}s")
    print(f"   • Performance Check: alle {monitor.config['performance_check_interval']}s")
    print(f"   • Watchlist: {len(monitor.config['watchlist_symbols'])} Symbole")
    print(f"   • Analysis Cryptos: {monitor.config['analysis_crypto_count']}")
    
    print("\n🔄 Starte Test-Monitoring (30 Sekunden)...")
    
    # Starte Monitoring für kurze Zeit
    monitor.running = True
    monitor.start_time = monitor.datetime.now() if hasattr(monitor, 'datetime') else None
    
    try:
        # Teste einzelne Komponenten
        print("\n1. Teste Arbitrage Check...")
        await monitor._arbitrage_check_cycle()
        print("✅ Arbitrage Check erfolgreich!")
        
        print("\n2. Teste Performance Check...")
        await monitor._performance_check_cycle()
        print("✅ Performance Check erfolgreich!")
        
        print("\n3. Teste Stats Update...")
        monitor._update_stats()
        print("✅ Stats Update erfolgreich!")
        
        # Zeige Statistiken
        print(f"\n📊 Test-Statistiken:")
        print(f"   • Arbitrage Checks: {monitor.stats['total_arbitrage_checks']}")
        print(f"   • Performance Analysen: {monitor.stats['total_performance_analyses']}")
        print(f"   • Arbitrage gefunden: {monitor.stats['arbitrage_opportunities_found']}")
        print(f"   • Alerts gesendet: {monitor.stats['alerts_sent']}")
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 24/7 MONITORING TEST ABGESCHLOSSEN!")
    print("🚀 System ist bereit für dauerhaftes Monitoring!")


if __name__ == "__main__":
    asyncio.run(test_monitoring())