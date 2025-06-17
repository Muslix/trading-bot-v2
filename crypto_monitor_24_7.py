"""
24/7 Crypto Trading Bot - Endlos-Monitoring System
Läuft dauerhaft und überwacht Arbitrage + Performance automatisch
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import eigene Module
from modules.real_price_monitor import monitor_real_exchange_prices, get_current_market_prices
from modules.arbitrage_detector import detect_arbitrage_opportunities, get_best_arbitrage_opportunity
from modules.historical_data import analyze_crypto_portfolio_enhanced, compare_timeframes
from modules.portfolio_analyzer import get_top_cryptocurrencies
from modules.telegram_bot import crypto_bot
from modules.database import db
from modules.smart_alerts import smart_alerts
from utils.decorators import async_log_performance
from config import get_config

config = get_config()


class CryptoMonitor24_7:
    """24/7 Crypto Trading Bot mit intelligentem Monitoring"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.stats = {
            'total_arbitrage_checks': 0,
            'total_performance_analyses': 0,
            'arbitrage_opportunities_found': 0,
            'alerts_sent': 0,
            'uptime_hours': 0
        }
        
        # Monitoring-Konfiguration (from .env)
        self.config = {
            'arbitrage_check_interval': config.arbitrage_check_interval,
            'performance_check_interval': config.performance_check_interval,
            'daily_summary_hour': config.daily_summary_hour,
            'watchlist_symbols': config.watchlist_symbols,
            'analysis_crypto_count': config.analysis_crypto_count,
            'exchanges': config.exchanges
        }
        
        # Letzte Checks verfolgen
        self.last_performance_check = None
        self.last_daily_summary = None
        self.performance_history = {}
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def start_monitoring(self, chat_id: str = None):
        """Starte 24/7 Monitoring"""
        self.running = True
        self.start_time = datetime.now()
        
        if chat_id:
            crypto_bot.set_chat_id(chat_id)
        
        self.logger.info("🚀 24/7 CRYPTO MONITOR GESTARTET!")
        
        # Sende Startup-Nachricht
        await crypto_bot.send_startup_message()
        
        try:
            # Haupt-Monitoring-Loop
            await self._main_monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("⏹️ Monitoring durch Benutzer gestoppt")
        except Exception as _e:
            self.logger.error(f"❌ Kritischer Fehler im Monitoring: {e}")
            await crypto_bot.send_error_alert(str(e), "Main Monitor")
        finally:
            await self._shutdown()
    
    async def _main_monitoring_loop(self):
        """Haupt-Loop für dauerhaftes Monitoring"""
        self.logger.info("🔄 Haupt-Loop gestartet...")
        
        while self.running:
            loop_start = time.time()
            
            try:
                # 1. Arbitrage Check (alle 30 Sekunden)
                await self._arbitrage_check_cycle()
                
                # 2. Performance Check (alle 10 Minuten)
                await self._performance_check_cycle()
                
                # 3. Daily Summary Check (einmal täglich um 8:00)
                await self._daily_summary_cycle()
                
                # 4. Update Statistics
                self._update_stats()
                
                # 5. Update Database Statistics
                db.update_bot_statistics(self.stats)
                
                # 5. Kurze Pause vor nächstem Cycle
                cycle_time = time.time() - loop_start
                sleep_time = max(1, self.config['arbitrage_check_interval'] - cycle_time)
                
                self.logger.info(f"🔄 Cycle abgeschlossen in {cycle_time:.1f}s - Schlafe {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                
            except Exception as _e:
                self.logger.error(f"❌ Fehler im Monitoring-Cycle: {e}")
                await crypto_bot.send_error_alert(str(e), "Monitor Cycle")
                await asyncio.sleep(30)  # Kurze Pause bei Fehlern
    
    @async_log_performance
    async def _arbitrage_check_cycle(self):
        """Arbitrage-Überwachung (alle 30 Sekunden)"""
        try:
            self.logger.info("🔍 Starte Arbitrage-Check...")
            
            arbitrage_opportunities = []
            
            for symbol in self.config['watchlist_symbols']:
                # Hole aktuelle Preise von allen Börsen
                prices = await monitor_real_exchange_prices(symbol, self.config['exchanges'])
                
                # Speichere Preis-Daten in Database
                for exchange, price in prices.items():
                    db.save_price_data(symbol, exchange, price)
                
                if prices and len(prices) >= 2:
                    # Erkenne Arbitrage-Möglichkeiten - höhere Threshold für weniger Spam
                    opportunities = detect_arbitrage_opportunities(prices, threshold=0.015)  # 1.5%
                    
                    if opportunities:
                        # Filtere nur profitable Opportunities (>= 1.5%)
                        profitable_opps = [
                            opp for opp in opportunities 
                            if opp.get('profit_percentage', 0) >= 1.5
                        ]
                        
                        if profitable_opps:
                            saved_count = 0
                            for opp in profitable_opps:
                                opp['symbol'] = symbol
                                # Speichere nur neue Arbitrage-Möglichkeiten (keine Duplikate)
                                alert_id = db.save_arbitrage_alert(opp)
                                if alert_id > 0:  # Positive ID = erfolgreich gespeichert
                                    saved_count += 1
                            
                            arbitrage_opportunities.extend(profitable_opps)
                            self.stats['arbitrage_opportunities_found'] += saved_count
                            
                            if saved_count < len(profitable_opps):
                                skipped = len(profitable_opps) - saved_count
                                self.logger.info(f"⏭️ {skipped} duplikate Alerts übersprungen für {symbol}")
                
                # Kurze Pause zwischen Symbolen
                await asyncio.sleep(1)
            
            # Nutze Smart Alert System für intelligente Alerts
            if arbitrage_opportunities:
                alert_results = await smart_alerts.process_all_alerts(
                    arbitrage_opportunities=arbitrage_opportunities
                )
                self.stats['alerts_sent'] += alert_results['arbitrage_alerts']
            
            self.stats['total_arbitrage_checks'] += 1
            self.logger.info(f"✅ Arbitrage-Check abgeschlossen - {len(arbitrage_opportunities)} Möglichkeiten gefunden")
            
        except Exception as _e:
            self.logger.error(f"❌ Fehler im Arbitrage-Check: {e}")
    
    @async_log_performance
    async def _performance_check_cycle(self):
        """Performance-Analyse (alle 10 Minuten)"""
        now = datetime.now()
        
        # Prüfe ob 10 Minuten vergangen sind
        if (self.last_performance_check and 
            now - self.last_performance_check < timedelta(minutes=10)):
            return
        
        try:
            self.logger.info("📊 Starte Performance-Analyse...")
            
            # Hole Top Cryptos für Analyse
            crypto_symbols = get_top_cryptocurrencies(self.config['analysis_crypto_count'])
            
            # Batch-Processing: Analysiere 30 Coins pro Cycle, rotiere durch die Liste
            batch_size = 30
            total_batches = (len(crypto_symbols) + batch_size - 1) // batch_size
            current_batch = getattr(self, '_current_batch', 0)
            
            start_idx = current_batch * batch_size
            end_idx = min(start_idx + batch_size, len(crypto_symbols))
            current_symbols = crypto_symbols[start_idx:end_idx]
            
            self.logger.info(f"📊 Analysiere Batch {current_batch + 1}/{total_batches}: {len(current_symbols)} Coins (Indizes {start_idx}-{end_idx-1})")
            
            # Analysiere mit historischen Daten
            results = analyze_crypto_portfolio_enhanced(current_symbols, period="1y")
            
            # Nächsten Batch für nächsten Cycle vorbereiten
            self._current_batch = (current_batch + 1) % total_batches
            
            if results:
                # Sortiere nach Sharpe Ratio
                valid_results = {k: v for k, v in results.items() if 'error' not in v}
                sorted_cryptos = sorted(valid_results.items(), 
                                      key=lambda x: x[1]['sharpe_ratio'], 
                                      reverse=True)
                
                # Speichere Performance-Daten in Database
                saved_count = db.save_performance_data(results)
                
                # Speichere Portfolio-Snapshot
                current_top_5 = sorted_cryptos[:5]
                snapshot_id = db.save_portfolio_snapshot(current_top_5, 'performance_check')
                
                # Nutze Smart Alert System für Performance-Alerts
                alert_results = await smart_alerts.process_all_alerts(
                    performance_data=current_top_5
                )
                self.stats['alerts_sent'] += alert_results['performance_alerts'] + alert_results['new_performer_alerts']
                
                # Speichere für nächsten Vergleich
                self.performance_history[now] = current_top_5
            
            self.last_performance_check = now
            self.stats['total_performance_analyses'] += 1
            self.logger.info("✅ Performance-Analyse abgeschlossen")
            
        except Exception as _e:
            self.logger.error(f"❌ Fehler in Performance-Analyse: {e}")
    
    async def _check_performance_changes(self, current_performers: List[tuple]) -> bool:
        """Prüfe ob sich Performance signifikant geändert hat"""
        if not self.performance_history:
            return True  # Erste Analyse immer senden
        
        # Hole letzte Performance
        last_time = max(self.performance_history.keys())
        last_performers = self.performance_history[last_time]
        
        # Prüfe auf große Sharpe Ratio Änderungen
        for current_symbol, current_metrics in current_performers:
            for last_symbol, last_metrics in last_performers:
                if current_symbol == last_symbol:
                    sharpe_change = abs(current_metrics['sharpe_ratio'] - last_metrics['sharpe_ratio'])
                    if sharpe_change >= crypto_bot.alert_config['sharpe_change_threshold']:
                        self.logger.info(f"📈 Signifikante Sharpe-Änderung bei {current_symbol}: {sharpe_change:.2f}")
                        return True
        
        return False
    
    async def _daily_summary_cycle(self):
        """Täglicher Summary-Report (8:00 Uhr)"""
        now = datetime.now()
        
        # Prüfe ob es 8:00 Uhr ist und noch nicht heute gesendet
        if (now.hour == self.config['daily_summary_hour'] and 
            (not self.last_daily_summary or 
             self.last_daily_summary.date() < now.date())):
            
            try:
                self.logger.info("🌅 Sende täglichen Summary...")
                
                # Erstelle Market Summary
                market_data = {
                    'total_arbitrage_opportunities': self.stats['arbitrage_opportunities_found'],
                    'avg_arbitrage_profit': 1.8,  # Wird aus echten Daten berechnet
                    'analyzed_coins': self.config['analysis_crypto_count'],
                    'uptime_hours': self._calculate_uptime_hours()
                }
                
                # Hole besten Performer für Summary
                if self.performance_history:
                    latest_performance = list(self.performance_history.values())[-1]
                    if latest_performance:
                        best_performer = latest_performance[0][1]  # Erster = Bester
                        best_performer['symbol'] = latest_performance[0][0]
                        market_data['best_performer'] = best_performer
                
                # Nutze Smart Alert System für Daily Summary
                alert_results = await smart_alerts.process_all_alerts(
                    force_daily_summary=True
                )
                self.stats['alerts_sent'] += alert_results['daily_summary_sent']
                
                self.last_daily_summary = now
                self.logger.info("✅ Täglicher Summary gesendet")
                
            except Exception as _e:
                self.logger.error(f"❌ Fehler beim täglichen Summary: {e}")
    
    def _update_stats(self):
        """Update interne Statistiken"""
        if self.start_time:
            self.stats['uptime_hours'] = self._calculate_uptime_hours()
    
    def _calculate_uptime_hours(self) -> float:
        """Berechne Uptime in Stunden"""
        if self.start_time:
            uptime = datetime.now() - self.start_time
            return round(uptime.total_seconds() / 3600, 1)
        return 0
    
    async def _shutdown(self):
        """Sauberer Shutdown"""
        self.running = False
        uptime = self._calculate_uptime_hours()
        
        self.logger.info(f"🛑 Monitor gestoppt nach {uptime} Stunden")
        self.logger.info("📊 Statistiken:")
        self.logger.info(f"   • Arbitrage Checks: {self.stats['total_arbitrage_checks']}")
        self.logger.info(f"   • Performance Analysen: {self.stats['total_performance_analyses']}")
        self.logger.info(f"   • Arbitrage gefunden: {self.stats['arbitrage_opportunities_found']}")
        self.logger.info(f"   • Alerts gesendet: {self.stats['alerts_sent']}")
        
        # Sende Shutdown-Nachricht
        shutdown_message = """
🛑 *BOT GESTOPPT*

⏱️ *Laufzeit: {uptime} Stunden*

📊 *Session-Statistiken:*
• Arbitrage Checks: {self.stats['total_arbitrage_checks']}
• Performance Analysen: {self.stats['total_performance_analyses']}  
• Arbitrage gefunden: {self.stats['arbitrage_opportunities_found']}
• Alerts gesendet: {self.stats['alerts_sent']}

🔄 Bot kann jederzeit neu gestartet werden.
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        await crypto_bot.send_message(shutdown_message)


async def main():
    """Haupt-Eingang für 24/7 Monitoring"""
    print("🚀 CRYPTO TRADING BOT - 24/7 MONITORING")
    print("=" * 60)
    
    monitor = CryptoMonitor24_7()
    
    print("⚙️ Konfiguration:")
    print(f"   • Arbitrage Check: alle {monitor.config['arbitrage_check_interval']}s")
    print(f"   • Performance Check: alle {monitor.config['performance_check_interval']//60} Minuten")
    print(f"   • Watchlist: {len(monitor.config['watchlist_symbols'])} Symbole")
    print(f"   • Analysis Cryptos: {monitor.config['analysis_crypto_count']}")
    print(f"   • Daily Summary: {monitor.config['daily_summary_hour']}:00 Uhr")
    print()
    
    # Chat ID eingeben (in Produktion automatisch)
    chat_id = input("💬 Gib deine Telegram Chat ID ein (oder Enter für Demo): ").strip()
    if not chat_id:
        chat_id = "123456789"  # Demo-Modus
        print("📱 Demo-Modus aktiviert (keine echten Telegram-Nachrichten)")
    
    print("\n🔄 Starte 24/7 Monitoring...")
    print("📱 Drücke Ctrl+C zum Stoppen")
    print("=" * 60)
    
    # Starte Monitoring
    await monitor.start_monitoring(chat_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitoring beendet!")
    except Exception as _e:
        print(f"\n❌ Kritischer Fehler: {e}")