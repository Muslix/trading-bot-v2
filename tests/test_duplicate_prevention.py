#!/usr/bin/env python3
"""
Test für Duplikate-Vermeidung bei Arbitrage Alerts
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


class DuplicatePreventionTest:
    """Test-Klasse für Duplikate-Vermeidung"""
    
    def __init__(self):
        self.test_results = {
            'duplicate_prevention_works': False,
            'similar_alert_blocked': False,
            'different_alert_allowed': False,
            'time_window_test': False,
            'database_consistency': False,
            'errors': []
        }
        self.test_prefix = 'DUPE_TEST_'
    
    def cleanup_test_data(self):
        """Bereinige alle Test-Daten"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM arbitrage_alerts WHERE symbol LIKE ?", (f"{self.test_prefix}%",))
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    print(f"   🧹 {deleted} Test-Alerts bereinigt")
                return True
        except Exception as e:
            print(f"   ❌ Cleanup fehlgeschlagen: {e}")
            return False
    
    def test_exact_duplicate_prevention(self):
        """Teste, ob exakte Duplikate verhindert werden"""
        print("🧪 Teste exakte Duplikate-Vermeidung...")
        
        try:
            self.cleanup_test_data()
            
            # Test-Alert
            test_alert = {
                'symbol': f'{self.test_prefix}BTC/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'coinbase',
                'buy_price': 50000.0,
                'sell_price': 51000.0,
                'profit_percentage': 2.0,
                'profit_per_unit': 1000.0
            }
            
            # Erster Alert sollte gespeichert werden
            id1 = db.save_arbitrage_alert(test_alert)
            print(f"      Erster Alert: ID={id1}")
            
            # Identischer Alert sollte blockiert werden
            id2 = db.save_arbitrage_alert(test_alert)
            print(f"      Duplikat Alert: ID={id2}")
            
            if id1 > 0 and id2 == -1:
                print("   ✅ Exakte Duplikate werden korrekt verhindert")
                self.test_results['duplicate_prevention_works'] = True
                return True
            else:
                error = f"Duplikate-Vermeidung fehlgeschlagen: ID1={id1}, ID2={id2}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
                return False
                
        except Exception as e:
            error = f"Duplikate-Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def test_similar_alert_blocking(self):
        """Teste, ob ähnliche Alerts (kleiner Profit-Unterschied) blockiert werden"""
        print("🧪 Teste ähnliche Alert-Blockierung...")
        
        try:
            # Base Alert
            base_alert = {
                'symbol': f'{self.test_prefix}ETH/USDT',
                'buy_exchange': 'kraken',
                'sell_exchange': 'binance',
                'buy_price': 2500.0,
                'sell_price': 2550.0,
                'profit_percentage': 2.0,
                'profit_per_unit': 50.0
            }
            
            # Erster Alert
            id1 = db.save_arbitrage_alert(base_alert)
            print(f"      Base Alert: ID={id1}, Profit={base_alert['profit_percentage']}%")
            
            # Ähnlicher Alert (2.05% statt 2.0% - sollte blockiert werden)
            similar_alert = base_alert.copy()
            similar_alert['profit_percentage'] = 2.05
            similar_alert['profit_per_unit'] = 51.25
            
            id2 = db.save_arbitrage_alert(similar_alert)
            print(f"      Ähnlicher Alert: ID={id2}, Profit={similar_alert['profit_percentage']}%")
            
            if id1 > 0 and id2 == -1:
                print("   ✅ Ähnliche Alerts werden korrekt blockiert")
                self.test_results['similar_alert_blocked'] = True
                return True
            else:
                error = f"Ähnliche Alert-Blockierung fehlgeschlagen: ID1={id1}, ID2={id2}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
                return False
                
        except Exception as e:
            error = f"Ähnliche Alert-Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def test_different_alert_allowed(self):
        """Teste, ob deutlich unterschiedliche Alerts erlaubt werden"""
        print("🧪 Teste unterschiedliche Alert-Erlaubnis...")
        
        try:
            # Base Alert
            base_alert = {
                'symbol': f'{self.test_prefix}ADA/USDT',
                'buy_exchange': 'coinbase',
                'sell_exchange': 'kraken',
                'buy_price': 1.0,
                'sell_price': 1.02,
                'profit_percentage': 2.0,
                'profit_per_unit': 0.02
            }
            
            id1 = db.save_arbitrage_alert(base_alert)
            print(f"      Base Alert: ID={id1}, Profit={base_alert['profit_percentage']}%")
            
            # Deutlich unterschiedlicher Alert - andere Exchanges verwenden
            different_alert = {
                'symbol': f'{self.test_prefix}ADA/USDT',
                'buy_exchange': 'binance',  # Unterschiedliche Exchange
                'sell_exchange': 'coinbase',  # Unterschiedliche Exchange
                'buy_price': 1.0,
                'sell_price': 1.05,
                'profit_percentage': 5.0,
                'profit_per_unit': 0.05
            }
            
            id2 = db.save_arbitrage_alert(different_alert)
            print(f"      Unterschiedlicher Alert: ID={id2}, Profit={different_alert['profit_percentage']}%")
            
            if id1 > 0 and id2 > 0:
                print("   ✅ Unterschiedliche Alerts werden korrekt erlaubt")
                self.test_results['different_alert_allowed'] = True
                return True
            else:
                error = f"Unterschiedliche Alert-Erlaubnis fehlgeschlagen: ID1={id1}, ID2={id2}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
                return False
                
        except Exception as e:
            error = f"Unterschiedliche Alert-Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def test_time_window(self):
        """Teste das Zeitfenster für Duplikate-Vermeidung"""
        print("🧪 Teste Zeitfenster für Duplikate...")
        
        try:
            # Alert erstellen
            test_alert = {
                'symbol': f'{self.test_prefix}DOT/USDT',
                'buy_exchange': 'binance',
                'sell_exchange': 'coinbase',
                'buy_price': 10.0,
                'sell_price': 10.3,
                'profit_percentage': 3.0,
                'profit_per_unit': 0.3
            }
            
            id1 = db.save_arbitrage_alert(test_alert)
            print(f"      Alert erstellt: ID={id1}")
            
            # Prüfe, ob Duplikate-Check funktioniert
            is_duplicate = db.check_recent_arbitrage_alert(test_alert, hours=6)
            print(f"      Duplikate-Check (6h): {is_duplicate}")
            
            # Prüfe mit sehr kurzem Zeitfenster
            is_duplicate_short = db.check_recent_arbitrage_alert(test_alert, hours=0.001)  # ~3.6 Sekunden
            print(f"      Duplikate-Check (0.001h): {is_duplicate_short}")
            
            if id1 > 0 and is_duplicate and not is_duplicate_short:
                print("   ✅ Zeitfenster funktioniert korrekt")
                self.test_results['time_window_test'] = True
                return True
            else:
                error = f"Zeitfenster-Test fehlgeschlagen: ID={id1}, dup_6h={is_duplicate}, dup_short={is_duplicate_short}"
                self.test_results['errors'].append(error)
                print(f"   ❌ {error}")
                return False
                
        except Exception as e:
            error = f"Zeitfenster-Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def test_database_consistency(self):
        """Teste die Datenbank-Konsistenz nach Tests"""
        print("🧪 Teste Datenbank-Konsistenz...")
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Zähle Test-Alerts
                cursor.execute("SELECT COUNT(*) as count FROM arbitrage_alerts WHERE symbol LIKE ?", (f"{self.test_prefix}%",))
                test_count = cursor.fetchone()['count']
                print(f"      Test-Alerts in DB: {test_count}")
                
                # Überprüfe auf Duplikate in Test-Daten
                cursor.execute("""
                    SELECT symbol, buy_exchange, sell_exchange, COUNT(*) as count
                    FROM arbitrage_alerts 
                    WHERE symbol LIKE ?
                    GROUP BY symbol, buy_exchange, sell_exchange
                    HAVING count > 1
                """, (f"{self.test_prefix}%",))
                
                duplicates = cursor.fetchall()
                if duplicates:
                    print("      ⚠️ Gefundene Duplikate in Test-Daten:")
                    for dup in duplicates:
                        print(f"         {dup['symbol']} ({dup['buy_exchange']}->{dup['sell_exchange']}): {dup['count']}x")
                    
                    error = f"Duplikate in Test-Daten gefunden: {len(duplicates)} Gruppen"
                    self.test_results['errors'].append(error)
                    return False
                else:
                    print("      ✅ Keine Duplikate in Test-Daten")
                    self.test_results['database_consistency'] = True
                    return True
                
        except Exception as e:
            error = f"Konsistenz-Test fehlgeschlagen: {e}"
            self.test_results['errors'].append(error)
            print(f"   ❌ {error}")
            return False
    
    def run_all_tests(self):
        """Führe alle Duplikate-Tests aus"""
        print("🚀 DUPLICATE PREVENTION TEST SUITE")
        print("=" * 50)
        
        test_methods = [
            self.test_exact_duplicate_prevention,
            self.test_similar_alert_blocking,
            self.test_different_alert_allowed,
            self.test_time_window,
            self.test_database_consistency
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
        
        # Cleanup nach allen Tests
        self.cleanup_test_data()
        
        self.print_summary(passed_tests, total_tests)
        return passed_tests == total_tests
    
    def print_summary(self, passed_tests, total_tests):
        """Drucke Test-Zusammenfassung"""
        print("📊 DUPLICATE PREVENTION SUMMARY")
        print("=" * 50)
        print(f"✅ Tests bestanden: {passed_tests}/{total_tests}")
        
        results = self.test_results
        print(f"🔄 Exakte Duplikate verhindert: {'✅' if results['duplicate_prevention_works'] else '❌'}")
        print(f"🎯 Ähnliche Alerts blockiert: {'✅' if results['similar_alert_blocked'] else '❌'}")
        print(f"🚀 Unterschiedliche Alerts erlaubt: {'✅' if results['different_alert_allowed'] else '❌'}")
        print(f"⏰ Zeitfenster funktioniert: {'✅' if results['time_window_test'] else '❌'}")
        print(f"💾 DB-Konsistenz: {'✅' if results['database_consistency'] else '❌'}")
        
        if self.test_results['errors']:
            print("\n❌ FEHLER:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 Alle Duplikate-Tests erfolgreich!")


def main():
    """Hauptfunktion"""
    tester = DuplicatePreventionTest()
    success = tester.run_all_tests()
    
    # Exit code für CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
