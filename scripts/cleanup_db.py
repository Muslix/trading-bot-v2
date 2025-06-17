#!/usr/bin/env python3
"""
Database Cleanup Utility
Bereinigt alte/redundante Alert-Daten aus der Database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.database import db
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_old_alerts(days_to_keep: int = 7):
    """Lösche alte Arbitrage Alerts (älter als X Tage)"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count old alerts
            cursor.execute("""
                SELECT COUNT(*) as count FROM arbitrage_alerts 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            old_count = cursor.fetchone()['count']
            
            if old_count > 0:
                # Delete old alerts
                cursor.execute("""
                    DELETE FROM arbitrage_alerts 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                conn.commit()
                logger.info(f"✅ Deleted {old_count} old alerts (older than {days_to_keep} days)")
            else:
                logger.info("✅ No old alerts to delete")
                
    except Exception as e:
        logger.error(f"❌ Error cleaning up old alerts: {e}")


def cleanup_zero_profit_alerts():
    """Lösche Alerts mit 0% Profit"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count zero profit alerts
            cursor.execute("""
                SELECT COUNT(*) as count FROM arbitrage_alerts 
                WHERE profit_percentage <= 0
            """)
            
            zero_count = cursor.fetchone()['count']
            
            if zero_count > 0:
                # Delete zero profit alerts
                cursor.execute("""
                    DELETE FROM arbitrage_alerts 
                    WHERE profit_percentage <= 0
                """)
                
                conn.commit()
                logger.info(f"✅ Deleted {zero_count} zero-profit alerts")
            else:
                logger.info("✅ No zero-profit alerts to delete")
                
    except Exception as e:
        logger.error(f"❌ Error cleaning up zero-profit alerts: {e}")


def cleanup_duplicate_alerts():
    """Lösche doppelte Alerts (gleicher Symbol, Exchange, Timestamp innerhalb 1 Minute)"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find and delete duplicates - keep the one with highest profit
            cursor.execute("""
                DELETE FROM arbitrage_alerts 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM arbitrage_alerts 
                    GROUP BY symbol, buy_exchange, sell_exchange, 
                             strftime('%Y-%m-%d %H:%M', timestamp)
                )
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"✅ Deleted {deleted_count} duplicate alerts")
            else:
                logger.info("✅ No duplicate alerts found")
                
    except Exception as e:
        logger.error(f"❌ Error cleaning up duplicate alerts: {e}")


def show_alert_statistics():
    """Zeige Alert-Statistiken"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total alerts
            cursor.execute("SELECT COUNT(*) as count FROM arbitrage_alerts")
            total = cursor.fetchone()['count']
            
            # Profitable alerts
            cursor.execute("SELECT COUNT(*) as count FROM arbitrage_alerts WHERE profit_percentage > 0")
            profitable = cursor.fetchone()['count']
            
            # Recent alerts (last 24h)
            cursor.execute("""
                SELECT COUNT(*) as count FROM arbitrage_alerts 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            recent = cursor.fetchone()['count']
            
            # Average profit
            cursor.execute("""
                SELECT AVG(profit_percentage) as avg_profit 
                FROM arbitrage_alerts 
                WHERE profit_percentage > 0
            """)
            avg_profit = cursor.fetchone()['avg_profit'] or 0
            
            print("\n" + "="*50)
            print("📊 ALERT STATISTICS")
            print("="*50)
            print(f"Total Alerts: {total}")
            print(f"Profitable Alerts (>0%): {profitable}")
            print(f"Recent Alerts (24h): {recent}")
            print(f"Average Profit: {avg_profit:.2f}%")
            print("="*50)
            
    except Exception as e:
        logger.error(f"❌ Error showing statistics: {e}")


def main():
    """Hauptfunktion - Cleanup mit verschiedenen Optionen"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Cleanup Utility')
    parser.add_argument('--old-alerts', type=int, default=7, 
                       help='Delete alerts older than X days (default: 7)')
    parser.add_argument('--zero-profit', action='store_true',
                       help='Delete zero-profit alerts')
    parser.add_argument('--duplicates', action='store_true',
                       help='Delete duplicate alerts')
    parser.add_argument('--stats', action='store_true',
                       help='Show alert statistics')
    parser.add_argument('--all', action='store_true',
                       help='Run all cleanup operations')
    
    args = parser.parse_args()
    
    logger.info("🧹 Starting database cleanup...")
    
    if args.stats or args.all:
        show_alert_statistics()
    
    if args.zero_profit or args.all:
        cleanup_zero_profit_alerts()
    
    if args.duplicates or args.all:
        cleanup_duplicate_alerts()
    
    if args.old_alerts or args.all:
        cleanup_old_alerts(args.old_alerts)
    
    if args.stats or args.all:
        print("\n📊 Statistics after cleanup:")
        show_alert_statistics()
    
    logger.info("✅ Database cleanup completed!")


if __name__ == "__main__":
    main()
