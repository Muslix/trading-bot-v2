#!/usr/bin/env python3
"""
Test für Coin-Coverage - Stellt sicher, dass alle konfigurierten Coins analysiert werden
"""

import sys
import os
import time
import sqlite3
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.modules.database import db
from src.modules.portfolio_analyzer import get_top_cryptocurrencies
from src.modules.historical_data import analyze_crypto_portfolio_enhanced
from config.config import get_config

config = get_config()


class CoinCoverageTest:
    """Test-Klasse für Coin-Coverage"""
    
    def __init__(self):
        self.config = config
        self.test_results = {
            'total_configured': 0,
            'total_analyzed': 0,
            'missing_coins': [],
            'database_coins': 0,
            'api_coins': 0,
            'batch_test_passed': False,
            'errors': []
        }
    
    def test_coin_configuration(self):
        """Teste die Coin-Konfiguration"""
        print("🧪 Teste Coin-Konfiguration...")
        
        try:
            # Teste verschiedene Konfigurationen
            for count in [10, 50, 100]:
                coins = get_top_cryptocurrencies(count)
                print(f"   ✅ {count} Coins angefordert: {len(coins)} erhalten")
                
                if len(coins) != count:
                    self.test_results['errors'].append(f"Konfiguration {count}: Erwartet {count}, erhalten {len(coins)}")
            
            # Teste die aktuelle Konfiguration
            configured_count = self.config.analysis_crypto_count
            configured_coins = get_top_cryptocurrencies(configured_count)
            self.test_results['total_configured'] = len(configured_coins)
            
            print(f"   📊 Aktuelle Konfiguration: {configured_count} Coins")
            print(f"   📝 Verfügbare Coins: {len(configured_coins)}")
            print(f"   🔢 Erste 10 Coins: {configured_coins[:10]}")
            
            return True
            
        except Exception as e:
            self.test_results['errors'].append(f"Konfigurationstest fehlgeschlagen: {e}")
            return False
    
    def test_batch_processing(self):
        """Teste das Batch-Processing System"""
        print("🧪 Teste Batch-Processing...")
        
        try:
            # Simuliere Batch-Processing
            total_coins = get_top_cryptocurrencies(100)
            batch_size = 30
            total_batches = (len(total_coins) + batch_size - 1) // batch_size
            
            print(f"   📊 Total Coins: {len(total_coins)}")
            print(f"   📦 Batch Size: {batch_size}")
            print(f"   🔢 Total Batches: {total_batches}")
            
            all_batched_coins = []
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(total_coins))
                batch_coins = total_coins[start_idx:end_idx]
                all_batched_coins.extend(batch_coins)
                
                print(f"   📦 Batch {batch_idx + 1}: Indizes {start_idx}-{end_idx-1}, {len(batch_coins)} Coins")
            
            # Überprüfe, ob alle Coins erfasst wurden
            if len(all_batched_coins) == len(total_coins):
                print("   ✅ Alle Coins durch Batches erfasst")
                self.test_results['batch_test_passed'] = True
            else:
                error = f"Batch-Processing unvollständig: {len(all_batched_coins)}/{len(total_coins)}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
            
            return self.test_results['batch_test_passed']
            
        except Exception as e:
            self.test_results['errors'].append(f"Batch-Processing Test fehlgeschlagen: {e}")
            return False
    
    def test_database_coverage(self):
        """Teste, wie viele Coins tatsächlich in der Datenbank sind"""
        print("🧪 Teste Database Coverage...")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Zähle einzigartige Coins
                cursor.execute("SELECT COUNT(DISTINCT symbol) as unique_coins FROM performance_data")
                result = cursor.fetchone()
                db_coin_count = result['unique_coins']
                self.test_results['database_coins'] = db_coin_count
                
                # Hole alle Coins aus der DB
                cursor.execute("SELECT DISTINCT symbol FROM performance_data ORDER BY symbol")
                db_coins = [row['symbol'] for row in cursor.fetchall()]
                
                print(f"   📊 Coins in Datenbank: {db_coin_count}")
                print(f"   📝 DB Coins: {db_coins[:20]}{'...' if len(db_coins) > 20 else ''}")
                
                # Überprüfe Aktualität der Daten
                cursor.execute("""
                    SELECT symbol, MAX(timestamp) as last_update, COUNT(*) as entries
                    FROM performance_data 
                    GROUP BY symbol 
                    ORDER BY last_update DESC 
                    LIMIT 10
                """)
                recent_coins = cursor.fetchall()
                
                print("   🕒 Neueste Updates:")
                for coin in recent_coins:
                    print(f"      {coin['symbol']}: {coin['last_update']} ({coin['entries']} Einträge)")
                
                # Überprüfe, ob genug Coins analysiert wurden
                configured_count = self.config.analysis_crypto_count
                coverage_percentage = (db_coin_count / configured_count) * 100
                
                print(f"   📈 Coverage: {coverage_percentage:.1f}% ({db_coin_count}/{configured_count})")
                
                if coverage_percentage < 20:  # Weniger als 20% ist problematisch
                    self.test_results['errors'].append(f"Zu wenig Coins analysiert: {coverage_percentage:.1f}%")
                
                return db_coin_count > 0
                
        except Exception as e:
            self.test_results['errors'].append(f"Database Coverage Test fehlgeschlagen: {e}")
            return False
    
    def test_api_coverage(self):
        """Teste, ob die API alle verfügbaren Coins zurückgibt"""
        print("🧪 Teste API Coverage...")
        
        try:
            import requests
            
            # Teste API Endpoint
            response = requests.get('http://localhost:5000/api/performance-data', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    api_coin_count = data.get('count', 0)
                    self.test_results['api_coins'] = api_coin_count
                    
                    print(f"   📊 API liefert: {api_coin_count} Coins")
                    print(f"   📈 Original Count: {data.get('original_count', 'unknown')}")
                    print(f"   🧹 Duplikate entfernt: {data.get('duplicates_removed', 'unknown')}")
                    
                    # Überprüfe, ob API-Count mit DB-Count übereinstimmt
                    if api_coin_count == self.test_results['database_coins']:
                        print("   ✅ API Count stimmt mit DB Count überein")
                    else:
                        error = f"API/DB Mismatch: API={api_coin_count}, DB={self.test_results['database_coins']}"
                        self.test_results['errors'].append(error)
                        print(f"   ⚠️ {error}")
                    
                    return True
                else:
                    error = f"API Fehler: {data.get('error', 'Unknown error')}"
                    self.test_results['errors'].append(error)
                    print(f"   ❌ {error}")
                    return False
            else:
                error = f"API nicht erreichbar: HTTP {response.status_code}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
                return False
                
        except Exception as e:
            error = f"API Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def test_analysis_performance(self):
        """Teste die Performance der Analyse mit unterschiedlichen Coin-Anzahlen"""
        print("🧪 Teste Analysis Performance...")
        
        try:
            test_sizes = [5, 10, 20]
            performance_results = {}
            
            for size in test_sizes:
                print(f"   📊 Teste Analyse mit {size} Coins...")
                
                test_coins = get_top_cryptocurrencies(size)
                start_time = time.time()
                
                # Führe die Analyse durch
                results = analyze_crypto_portfolio_enhanced(test_coins, period="30d")
                
                end_time = time.time()
                duration = end_time - start_time
                
                performance_results[size] = {
                    'duration': duration,
                    'coins_analyzed': len(results) if results else 0,
                    'success_rate': (len(results) / size * 100) if results and size > 0 else 0
                }
                
                print(f"      ⏱️ Dauer: {duration:.2f}s")
                print(f"      ✅ Erfolgreich: {len(results) if results else 0}/{size}")
                print(f"      📈 Success Rate: {performance_results[size]['success_rate']:.1f}%")
            
            # Berechne Durchschnittszeit pro Coin
            if performance_results:
                avg_time_per_coin = sum(r['duration'] / size for size, r in performance_results.items()) / len(performance_results)
                estimated_time_100 = avg_time_per_coin * 100
                
                print(f"   ⏱️ Durchschnittliche Zeit pro Coin: {avg_time_per_coin:.3f}s")
                print(f"   🕐 Geschätzte Zeit für 100 Coins: {estimated_time_100:.1f}s ({estimated_time_100/60:.1f} Minuten)")
                
                if estimated_time_100 > 300:  # Mehr als 5 Minuten
                    self.test_results['errors'].append(f"Analyse zu langsam: {estimated_time_100:.1f}s für 100 Coins")
            
            return True
            
        except Exception as e:
            self.test_results['errors'].append(f"Performance Test fehlgeschlagen: {e}")
            return False
    
    def run_all_tests(self):
        """Führe alle Tests aus"""
        print("🚀 COIN COVERAGE TEST SUITE")
        print("=" * 50)
        
        test_methods = [
            self.test_coin_configuration,
            self.test_batch_processing,
            self.test_database_coverage,
            self.test_api_coverage,
            self.test_analysis_performance
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
                print()  # Leerzeile zwischen Tests
            except Exception as e:
                self.test_results['errors'].append(f"{test_method.__name__} crashed: {e}")
                print(f"   💥 Test crashed: {e}")
        
        self.print_summary(passed_tests, total_tests)
        return passed_tests == total_tests
    
    def print_summary(self, passed_tests, total_tests):
        """Drucke Test-Zusammenfassung"""
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"✅ Tests bestanden: {passed_tests}/{total_tests}")
        print(f"📊 Konfigurierte Coins: {self.test_results['total_configured']}")
        print(f"💾 DB Coins: {self.test_results['database_coins']}")
        print(f"🌐 API Coins: {self.test_results['api_coins']}")
        print(f"📦 Batch Processing: {'✅ OK' if self.test_results['batch_test_passed'] else '❌ FAILED'}")
        
        if self.test_results['errors']:
            print("\n❌ FEHLER:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 Alle Tests erfolgreich!")
        
        # Empfehlungen
        print("\n💡 EMPFEHLUNGEN:")
        
        db_coins = self.test_results['database_coins']
        configured_coins = self.test_results['total_configured']
        
        if db_coins < configured_coins * 0.3:
            print("   • Monitor länger laufen lassen für mehr Coin-Coverage")
        
        if self.test_results['api_coins'] != db_coins:
            print("   • API-Database Synchronisation überprüfen")
        
        if not self.test_results['batch_test_passed']:
            print("   • Batch-Processing Logic überprüfen")
        
        if len(self.test_results['errors']) == 0:
            print("   • System läuft optimal! 🚀")


def main():
    """Hauptfunktion"""
    tester = CoinCoverageTest()
    success = tester.run_all_tests()
    
    # Exit code für CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
