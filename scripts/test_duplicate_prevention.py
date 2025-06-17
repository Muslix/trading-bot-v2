#!/usr/bin/env python3
"""
Test Script für die Duplikate-Vermeidung
Testet, ob die neuen Alerts korrekt Duplikate vermeiden
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.modules.database import db

def test_duplicate_prevention():
    """Test der Duplikate-Vermeidung"""
    
    print("🧪 Teste Duplikate-Vermeidung...")
    
    # Test-Opportunity
    test_opportunity = {
        'symbol': 'TEST/USDT',
        'buy_exchange': 'binance',
        'sell_exchange': 'coinbase',
        'buy_price': 100.0,
        'sell_price': 103.0,
        'profit_percentage': 3.0,
        'profit_per_unit': 3.0
    }
    
    print("📝 Versuche ersten Alert zu speichern...")
    alert_id_1 = db.save_arbitrage_alert(test_opportunity)
    print(f"   Alert ID: {alert_id_1}")
    
    print("📝 Versuche identischen Alert zu speichern (sollte abgelehnt werden)...")
    alert_id_2 = db.save_arbitrage_alert(test_opportunity)
    print(f"   Alert ID: {alert_id_2}")
    
    print("📝 Versuche ähnlichen Alert zu speichern (3.05% statt 3.0%)...")
    similar_opportunity = test_opportunity.copy()
    similar_opportunity['profit_percentage'] = 3.05
    alert_id_3 = db.save_arbitrage_alert(similar_opportunity)
    print(f"   Alert ID: {alert_id_3}")
    
    print("📝 Versuche deutlich anderen Alert zu speichern (5.0% statt 3.0%)...")
    different_opportunity = test_opportunity.copy()
    different_opportunity['profit_percentage'] = 5.0
    alert_id_4 = db.save_arbitrage_alert(different_opportunity)
    print(f"   Alert ID: {alert_id_4}")
    
    # Auswertung
    print("\n📊 Ergebnisse:")
    if alert_id_1 > 0:
        print("✅ Erster Alert wurde korrekt gespeichert")
    else:
        print("❌ Erster Alert wurde nicht gespeichert")
    
    if alert_id_2 == -1:
        print("✅ Duplikat wurde korrekt abgelehnt")
    else:
        print("❌ Duplikat wurde fälschlicherweise gespeichert")
    
    if alert_id_3 == -1:
        print("✅ Ähnlicher Alert wurde korrekt abgelehnt")
    else:
        print("❌ Ähnlicher Alert wurde fälschlicherweise gespeichert")
    
    if alert_id_4 > 0:
        print("✅ Deutlich anderer Alert wurde korrekt gespeichert")
    else:
        print("❌ Deutlich anderer Alert wurde nicht gespeichert")
    
    # Cleanup - Lösche Test-Alerts
    print("\n🧹 Bereinige Test-Daten...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM arbitrage_alerts WHERE symbol = 'TEST/USDT'")
        deleted = cursor.rowcount
        conn.commit()
        print(f"   {deleted} Test-Alerts gelöscht")
    
    print("\n✅ Test abgeschlossen!")

if __name__ == "__main__":
    test_duplicate_prevention()
