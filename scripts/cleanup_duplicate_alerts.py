#!/usr/bin/env python3
"""
Cleanup Script für Duplikate Arbitrage Alerts
Entfernt alle duplizierten Alerts und behält nur den neuesten pro einzigartige Gelegenheit
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.modules.database import db


def cleanup_duplicate_alerts():
    """Entferne alle duplizierten Alerts, behalte nur den neuesten"""
    
    print("🧹 Starte Cleanup von duplizierten Arbitrage Alerts...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Finde alle duplizierten Alert-Gruppen
        cursor.execute("""
            SELECT symbol, buy_exchange, sell_exchange, COUNT(*) as count
            FROM arbitrage_alerts 
            GROUP BY symbol, buy_exchange, sell_exchange 
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        duplicate_groups = cursor.fetchall()
        
        if not duplicate_groups:
            print("✅ Keine Duplikate gefunden!")
            return
        
        print(f"📊 Gefunden: {len(duplicate_groups)} Gruppen mit Duplikaten")
        
        total_deleted = 0
        
        for group in duplicate_groups:
            symbol = group['symbol']
            buy_exchange = group['buy_exchange']
            sell_exchange = group['sell_exchange']
            count = group['count']
            
            print(f"  🔍 {symbol} ({buy_exchange} -> {sell_exchange}): {count} Duplikate")
            
            # Finde alle IDs für diese Gruppe, sortiert nach Timestamp (neueste zuerst)
            cursor.execute("""
                SELECT id, timestamp, profit_percentage
                FROM arbitrage_alerts
                WHERE symbol = ? AND buy_exchange = ? AND sell_exchange = ?
                ORDER BY timestamp DESC
            """, (symbol, buy_exchange, sell_exchange))
            
            alerts = cursor.fetchall()
            
            if len(alerts) <= 1:
                continue
                
            # Behalte den ersten (neuesten), lösche den Rest
            keep_id = alerts[0]['id']
            delete_ids = [alert['id'] for alert in alerts[1:]]
            
            print(f"    ✅ Behalte Alert ID {keep_id} ({alerts[0]['timestamp']})")
            print(f"    🗑️  Lösche {len(delete_ids)} ältere Alerts...")
            
            # Lösche die älteren Alerts
            for delete_id in delete_ids:
                cursor.execute("DELETE FROM arbitrage_alerts WHERE id = ?", (delete_id,))
                total_deleted += 1
        
        conn.commit()
        
        print(f"\n✅ Cleanup abgeschlossen!")
        print(f"📊 Insgesamt gelöschte Alerts: {total_deleted}")
        
        # Zeige finale Statistiken
        cursor.execute("SELECT COUNT(*) as total FROM arbitrage_alerts")
        remaining = cursor.fetchone()['total']
        print(f"📊 Verbleibende Alerts: {remaining}")


def show_cleanup_preview():
    """Zeige eine Vorschau der zu löschenden Duplikate"""
    
    print("👀 Vorschau der Duplikate-Cleanup-Operation:")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Aktuelle Gesamt-Anzahl
        cursor.execute("SELECT COUNT(*) as total FROM arbitrage_alerts")
        total_before = cursor.fetchone()['total']
        
        # Finde Duplikate
        cursor.execute("""
            SELECT 
                symbol, 
                buy_exchange, 
                sell_exchange, 
                COUNT(*) as count,
                MIN(timestamp) as oldest,
                MAX(timestamp) as newest
            FROM arbitrage_alerts 
            GROUP BY symbol, buy_exchange, sell_exchange 
            HAVING count > 1
            ORDER BY count DESC
        """)
        
        duplicate_groups = cursor.fetchall()
        
        if not duplicate_groups:
            print("✅ Keine Duplikate gefunden!")
            return
        
        print(f"📊 Aktuelle Alerts insgesamt: {total_before}")
        print(f"📊 Gefundene Duplikat-Gruppen: {len(duplicate_groups)}")
        print("\nDetails der Duplikate:")
        print("-" * 80)
        
        total_to_delete = 0
        
        for group in duplicate_groups:
            symbol = group['symbol']
            buy_exchange = group['buy_exchange'] 
            sell_exchange = group['sell_exchange']
            count = group['count']
            oldest = group['oldest']
            newest = group['newest']
            to_delete = count - 1
            
            print(f"  {symbol:15} {buy_exchange:10} -> {sell_exchange:10} | "
                  f"Anzahl: {count:2} | Lösche: {to_delete:2} | "
                  f"Von: {oldest} bis: {newest}")
            
            total_to_delete += to_delete
        
        print("-" * 80)
        print(f"📊 Insgesamt zu löschende Alerts: {total_to_delete}")
        print(f"📊 Verbleibende Alerts nach Cleanup: {total_before - total_to_delete}")


def main():
    """Hauptfunktion"""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        show_cleanup_preview()
    elif len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_duplicate_alerts()
    else:
        print("🧹 Duplikate Arbitrage Alerts Cleanup Tool")
        print()
        print("Verwendung:")
        print("  python3 scripts/cleanup_duplicate_alerts.py --preview   # Zeige Vorschau")
        print("  python3 scripts/cleanup_duplicate_alerts.py --cleanup   # Führe Cleanup durch")
        print()
        show_cleanup_preview()


if __name__ == "__main__":
    main()
