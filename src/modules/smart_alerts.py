"""
Smart Alert System - Intelligente Alert-Regeln für den Crypto Trading Bot
Implementiert alle konfigurierten Alert-Bedingungen mit Anti-Spam-Mechanismen
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.modules.telegram_bot import crypto_bot
from src.modules.database import db
from src.utils.decorators import async_log_performance
from config.config import get_config

config = get_config()


class SmartAlertManager:
    """Intelligentes Alert-Management-System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Alert-Konfiguration (aus Environment Variables)
        self.alert_rules = {
            # Arbitrage Rules - Konfigurierbar über .env
            'arbitrage_immediate': {
                'threshold': config.arbitrage_threshold,  # Aus .env laden
                'cooldown_minutes': config.alert_cooldown_minutes,  # Aus .env laden
                'enabled': True,
                'priority': 'high'
            },
            
            # Sharpe Ratio Change Rules - Konfigurierbar über .env
            'sharpe_change': {
                'threshold': config.sharpe_change_threshold,  # Aus .env laden
                'cooldown_minutes': 30,
                'enabled': True,
                'priority': 'medium'
            },
            
            # New Top Performer Rules
            'new_top_performer': {
                'enabled': True,
                'cooldown_minutes': 60,
                'min_sharpe': 1.5,  # Mindest-Sharpe für "Top Performer"
                'priority': 'medium'
            },
            
            # Daily Summary Rules
            'daily_summary': {
                'enabled': True,
                'hour': 8,  # 8:00 Uhr
                'priority': 'low'
            },
            
            # Market Movement Rules
            'large_price_movement': {
                'threshold': 5.0,  # 5% Preisbewegung in 1h
                'cooldown_minutes': 60,
                'enabled': True,
                'priority': 'medium'
            },
            
            # Volume Spike Rules
            'volume_spike': {
                'threshold': 200.0,  # 200% über Normal-Volumen
                'cooldown_minutes': 120,
                'enabled': False,  # Erstmal deaktiviert (keine Volume-Daten)
                'priority': 'low'
            }
        }
        
        # Alert-Historie für Cooldown-Management
        self.alert_history = {}
        
        # Performance-Tracking
        self.last_performance_snapshot = {}
        self.price_history_tracker = {}
        
        self.logger.info("✅ Smart Alert Manager initialisiert")
    
    def _should_send_alert(self, alert_type: str, key: str = "") -> bool:
        """Prüfe ob Alert gesendet werden soll (Anti-Spam)"""
        if not self.alert_rules.get(alert_type, {}).get('enabled', False):
            return False
        
        alert_key = f"{alert_type}_{key}"
        now = datetime.now()
        
        if alert_key in self.alert_history:
            last_sent = self.alert_history[alert_key]
            cooldown_minutes = self.alert_rules[alert_type].get('cooldown_minutes', 60)
            cooldown_time = timedelta(minutes=cooldown_minutes)
            
            if now - last_sent < cooldown_time:
                return False
        
        self.alert_history[alert_key] = now
        return True
    
    def _filter_redundant_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Filtere redundante/ähnliche Arbitrage-Opportunities aus"""
        if not opportunities:
            return []
        
        # Gruppiere nach Symbol
        symbol_groups = {}
        for opp in opportunities:
            symbol = opp.get('symbol', 'UNKNOWN')
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(opp)
        
        # Für jedes Symbol: Nehme nur die beste Opportunity
        filtered_opportunities = []
        for symbol, opps in symbol_groups.items():
            # Sortiere nach Profit und nehme die beste
            best_opp = max(opps, key=lambda x: x.get('profit_percentage', 0))
            
            # Nur hinzufügen wenn über threshold
            if best_opp.get('profit_percentage', 0) >= self.alert_rules['arbitrage_immediate']['threshold']:
                filtered_opportunities.append(best_opp)
        
        return filtered_opportunities
    
    @async_log_performance
    async def check_arbitrage_alerts(self, arbitrage_opportunities: List[Dict]) -> int:
        """Prüfe und sende Arbitrage Alerts"""
        alerts_sent = 0
        
        # Filtere nach Threshold
        threshold = self.alert_rules['arbitrage_immediate']['threshold']
        significant_opportunities = [
            opp for opp in arbitrage_opportunities 
            if opp.get('profit_percentage', 0) >= threshold
        ]
        
        # Reduziere redundante Alerts
        significant_opportunities = self._filter_redundant_opportunities(significant_opportunities)
        
        if not significant_opportunities:
            return alerts_sent
        
        # Gruppiere nach Symbol für Spam-Protection
        symbols_checked = set()
        
        for opportunity in significant_opportunities:
            symbol = opportunity.get('symbol', 'UNKNOWN')
            
            if symbol in symbols_checked:
                continue
            symbols_checked.add(symbol)
            
            # Prüfe Cooldown
            if self._should_send_alert('arbitrage_immediate', symbol):
                
                # Speichere in Database (aber prüfe Duplikate nicht hier, da schon im Monitor gemacht)
                # alert_id = db.save_arbitrage_alert(opportunity)  # Bereits im Monitor gespeichert
                
                # Sende Telegram Alert
                if await crypto_bot.send_arbitrage_alert([opportunity]):
                    # db.update_arbitrage_alert_sent(alert_id)  # Update später wenn nötig
                    alerts_sent += 1
                    
                    self.logger.info(f"🚨 Arbitrage Alert gesendet: {symbol} ({opportunity['profit_percentage']:.1f}%)")
        
        return alerts_sent
    
    @async_log_performance
    async def check_performance_change_alerts(self, current_performers: List[Tuple]) -> int:
        """Prüfe Performance-Änderungs-Alerts"""
        alerts_sent = 0
        
        if not current_performers:
            return alerts_sent
        
        # Vergleiche mit letztem Snapshot
        if not self.last_performance_snapshot:
            self.last_performance_snapshot = dict(current_performers)
            return alerts_sent
        
        threshold = self.alert_rules['sharpe_change']['threshold']
        significant_changes = []
        
        for symbol, current_metrics in current_performers[:10]:  # Top 10 prüfen
            if symbol in self.last_performance_snapshot:
                last_metrics = self.last_performance_snapshot[symbol]
                
                current_sharpe = current_metrics.get('sharpe_ratio', 0)
                last_sharpe = last_metrics.get('sharpe_ratio', 0)
                
                change = abs(current_sharpe - last_sharpe)
                
                if change >= threshold:
                    significant_changes.append({
                        'symbol': symbol,
                        'old_sharpe': last_sharpe,
                        'new_sharpe': current_sharpe,
                        'change': change,
                        'direction': 'UP' if current_sharpe > last_sharpe else 'DOWN'
                    })
        
        # Sende Alerts für signifikante Änderungen
        for change in significant_changes:
            if self._should_send_alert('sharpe_change', change['symbol']):
                
                # Erstelle Alert-Nachricht
                direction_emoji = "📈" if change['direction'] == 'UP' else "📉"
                message = f"""
{direction_emoji} *PERFORMANCE ALERT!*

💎 *{change['symbol']}* 
📊 Sharpe Ratio Änderung: *{change['change']:.2f}*

{change['direction']}:
• Alt: {change['old_sharpe']:.3f}
• Neu: {change['new_sharpe']:.3f}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
                
                if await crypto_bot.send_message(message):
                    alerts_sent += 1
                    self.logger.info(f"📊 Performance Alert gesendet: {change['symbol']} ({change['change']:.2f})")
        
        # Update Snapshot
        self.last_performance_snapshot = dict(current_performers)
        
        return alerts_sent
    
    @async_log_performance
    async def check_new_top_performer_alerts(self, current_performers: List[Tuple]) -> int:
        """Prüfe New Top Performer Alerts"""
        alerts_sent = 0
        
        if not current_performers:
            return alerts_sent
        
        min_sharpe = self.alert_rules['new_top_performer']['min_sharpe']
        
        # Hole alte Top 5 aus Database
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT symbol, best_performer_sharpe FROM portfolio_snapshots 
                    WHERE timestamp >= datetime('now', '-1 day')
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                
                old_top_performers = set(row['symbol'] for row in cursor.fetchall() 
                                       if row['best_performer_sharpe'] >= min_sharpe)
        except:
            old_top_performers = set()
        
        # Aktuelle Top Performer
        current_top = set(symbol for symbol, metrics in current_performers[:5] 
                         if metrics.get('sharpe_ratio', 0) >= min_sharpe)
        
        # Neue Top Performer finden
        new_performers = current_top - old_top_performers
        
        for symbol in new_performers:
            if self._should_send_alert('new_top_performer', symbol):
                
                # Finde Metriken für diesen Symbol
                symbol_metrics = next((metrics for sym, metrics in current_performers if sym == symbol), {})
                
                message = f"""
🌟 *NEUER TOP PERFORMER!*

💎 *{symbol}* ist in die Top 5 aufgestiegen!

📊 *Performance:*
• Sharpe Ratio: *{symbol_metrics.get('sharpe_ratio', 0):.3f}*
• Annual Return: *{symbol_metrics.get('annual_return', 0):.1f}%*
• Current Price: *${symbol_metrics.get('current_price', 0):,.2f}*

🚀 Genauer analysieren!
⏰ {datetime.now().strftime('%H:%M:%S')}
"""
                
                if await crypto_bot.send_message(message):
                    alerts_sent += 1
                    self.logger.info(f"🌟 New Top Performer Alert gesendet: {symbol}")
        
        return alerts_sent
    
    @async_log_performance
    async def check_daily_summary_alert(self, force: bool = False) -> bool:
        """Prüfe Daily Summary Alert (8:00 Uhr)"""
        now = datetime.now()
        summary_hour = self.alert_rules['daily_summary']['hour']
        
        # Prüfe Zeit oder Force-Flag
        if not force and now.hour != summary_hour:
            return False
        
        if not force and not self._should_send_alert('daily_summary', now.strftime('%Y-%m-%d')):
            return False
        
        try:
            # Sammle Tages-Statistiken
            dashboard_data = db.get_dashboard_data()
            
            # Hole beste Performer
            latest_performance = db.get_latest_performance_data(limit=3)
            
            # Hole Arbitrage-Statistiken
            alerts_24h = db.get_recent_arbitrage_alerts(hours=24)
            
            message = f"""
🌅 *TÄGLICHER MARKT-REPORT*

📊 *24h Übersicht:*
• Arbitrage Alerts: *{len(alerts_24h)}*
• Avg. Profit: *{dashboard_data.get('arbitrage', {}).get('avg_profit', 0):.1f}%*
• Analysierte Coins: *{dashboard_data.get('performance', {}).get('total_coins', 0)}*

🏆 *TOP 3 PERFORMER:*
"""
            
            for i, performer in enumerate(latest_performance[:3], 1):
                message += f"  {i}. *{performer['symbol']}* (Sharpe: {performer['sharpe_ratio']:.2f})\n"
            
            message += f"""
📈 *Bot Status:*
• System: Online 24/7
• Letzte Analyse: {datetime.now().strftime('%H:%M')}

💡 *Heute geplant:*
• Kontinuierliche Arbitrage-Überwachung
• Performance-Updates alle 10min
• Smart Alerts bei Marktbewegungen

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
            
            if await crypto_bot.send_message(message):
                self.logger.info("🌅 Daily Summary Alert gesendet")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Daily Summary: {e}")
        
        return False
    
    @async_log_performance
    async def check_large_price_movement_alerts(self, current_prices: Dict[str, Dict]) -> int:
        """Prüfe Large Price Movement Alerts"""
        alerts_sent = 0
        threshold = self.alert_rules['large_price_movement']['threshold']
        
        # Vergleiche mit gespeicherten Preisen von vor 1h
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        for symbol, exchanges in current_prices.items():
            try:
                # Hole Preis von vor 1 Stunde
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT AVG(price) as avg_price
                        FROM price_history 
                        WHERE symbol = ? AND timestamp <= ? AND timestamp >= ?
                    """, (symbol, one_hour_ago, one_hour_ago - timedelta(minutes=10)))
                    
                    result = cursor.fetchone()
                    old_price = result['avg_price'] if result and result['avg_price'] else None
                
                if old_price:
                    # Berechne aktuelle Durchschnittspreis
                    current_avg = sum(exchanges.values()) / len(exchanges)
                    
                    # Berechne Änderung
                    change_percent = ((current_avg - old_price) / old_price) * 100
                    
                    if abs(change_percent) >= threshold:
                        if self._should_send_alert('large_price_movement', symbol):
                            
                            direction = "🚀" if change_percent > 0 else "📉"
                            message = f"""
{direction} *GROSSE PREISBEWEGUNG!*

💎 *{symbol}*
💰 Preis-Änderung (1h): *{change_percent:+.1f}%*

📊 *Details:*
• Vorher: ${old_price:,.2f}
• Jetzt: ${current_avg:,.2f}
• Änderung: ${current_avg - old_price:+,.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
                            
                            if await crypto_bot.send_message(message):
                                alerts_sent += 1
                                self.logger.info(f"📊 Price Movement Alert gesendet: {symbol} ({change_percent:+.1f}%)")
                                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei Price Movement Check für {symbol}: {e}")
        
        return alerts_sent
    
    async def process_all_alerts(self, 
                               arbitrage_opportunities: List[Dict] = None,
                               performance_data: List[Tuple] = None,
                               price_data: Dict[str, Dict] = None,
                               force_daily_summary: bool = False) -> Dict[str, int]:
        """Verarbeite alle Alert-Typen"""
        
        results = {
            'arbitrage_alerts': 0,
            'performance_alerts': 0,
            'new_performer_alerts': 0,
            'price_movement_alerts': 0,
            'daily_summary_sent': 0,
            'total_alerts': 0
        }
        
        try:
            # 1. Arbitrage Alerts
            if arbitrage_opportunities:
                results['arbitrage_alerts'] = await self.check_arbitrage_alerts(arbitrage_opportunities)
            
            # 2. Performance Change Alerts
            if performance_data:
                results['performance_alerts'] = await self.check_performance_change_alerts(performance_data)
                results['new_performer_alerts'] = await self.check_new_top_performer_alerts(performance_data)
            
            # 3. Price Movement Alerts
            if price_data:
                results['price_movement_alerts'] = await self.check_large_price_movement_alerts(price_data)
            
            # 4. Daily Summary Alert
            if await self.check_daily_summary_alert(force=force_daily_summary):
                results['daily_summary_sent'] = 1
            
            # Gesamtsumme
            results['total_alerts'] = sum(v for k, v in results.items() if k != 'total_alerts')
            
            if results['total_alerts'] > 0:
                self.logger.info(f"📬 Smart Alerts verarbeitet: {results['total_alerts']} Alerts gesendet")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Verarbeiten der Smart Alerts: {e}")
        
        return results
    
    def get_alert_stats(self) -> Dict:
        """Hole Alert-Statistiken"""
        return {
            'rules_configured': len(self.alert_rules),
            'rules_enabled': sum(1 for rule in self.alert_rules.values() if rule.get('enabled', False)),
            'alerts_sent_today': len([t for t in self.alert_history.values() 
                                    if t.date() == datetime.now().date()]),
            'last_performance_check': bool(self.last_performance_snapshot),
            'alert_rules': self.alert_rules
        }


# Global Smart Alert Manager Instance
smart_alerts = SmartAlertManager()


async def test_smart_alerts():
    """Teste Smart Alert System"""
    print("🧪 SMART ALERTS TEST")
    print("=" * 50)
    
    # Test 1: Alert Rules
    print("1. Alert-Regeln:")
    stats = smart_alerts.get_alert_stats()
    print(f"   • Konfigurierte Regeln: {stats['rules_configured']}")
    print(f"   • Aktivierte Regeln: {stats['rules_enabled']}")
    
    # Test 2: Arbitrage Alert
    print("\n2. Teste Arbitrage Alert...")
    test_arbitrage = [{
        'symbol': 'BTC/USDT',
        'buy_exchange': 'binance',
        'sell_exchange': 'coinbase',
        'buy_price': 45000,
        'sell_price': 46200,
        'profit_percentage': 2.7,
        'profit_per_unit': 1200
    }]
    
    result = await smart_alerts.check_arbitrage_alerts(test_arbitrage)
    print(f"   ✅ Arbitrage Alerts: {result}")
    
    # Test 3: Performance Alert
    print("\n3. Teste Performance Alert...")
    test_performance = [
        ('BTC', {'sharpe_ratio': 1.8, 'annual_return': 85.0}),
        ('ETH', {'sharpe_ratio': 1.2, 'annual_return': 45.0})
    ]
    
    result = await smart_alerts.check_performance_change_alerts(test_performance)
    print(f"   ✅ Performance Alerts: {result}")
    
    # Test 4: Daily Summary (Force)
    print("\n4. Teste Daily Summary...")
    result = await smart_alerts.check_daily_summary_alert(force=True)
    print(f"   ✅ Daily Summary: {'Gesendet' if result else 'Nicht gesendet'}")
    
    print("\n" + "=" * 50)
    print("🎉 Smart Alerts Tests abgeschlossen!")


if __name__ == "__main__":
    asyncio.run(test_smart_alerts())