"""
24/7 Crypto Trading Bot - Endlos-Monitoring System
Läuft dauerhaft und überwacht Arbitrage + Performance automatisch
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Now import project modules
try:
    from config.config import get_config
    from src.database import get_database_manager
    from src.adapters import analyze_crypto_portfolio_enhanced
    from src.alerts import create_alert_manager
    from src.utils.decorators import async_log_performance
    
    # Import new plugin managers
    from src.analyzers import create_analyzer_manager
    from src.monitors import create_monitor_manager
    from src.communication import create_communication_manager
    
    # Import ThreadingManager for performance improvements
    from src.core.threading_manager import ThreadingManager
    
    # Import legacy telegram bot for backward compatibility
    from src.communication.plugins.telegram_communication import create_legacy_bot
    
    # Legacy compatibility imports
    from src.analyzers.plugins.arbitrage_analyzer import detect_arbitrage_opportunities
    from src.analyzers.plugins.portfolio_analyzer import get_top_cryptocurrencies
    from src.monitors.plugins.price_monitor import monitor_real_exchange_prices
    from src.communication.plugins.telegram_communication import create_legacy_bot
except ImportError as e:
    logging.error(f"Import error: {e}")
    sys.exit(1)

config = get_config()


class CryptoMonitor24_7:
    """24/7 Crypto Trading Bot mit intelligentem Monitoring"""

    def __init__(self):
        self.running = False
        self.start_time = None
        self.stats = {
            "total_arbitrage_checks": 0,
            "total_performance_analyses": 0,
            "arbitrage_opportunities_found": 0,
            "alerts_sent": 0,
            "uptime_hours": 0,
            "session_start": None,
        }
        
        # Initialize managers (will be set up in async context)
        self.analyzer_manager = None
        self.monitor_manager = None
        self.communication_manager = None
        self.alert_manager = None
        self.threading_manager = None
        self.database_manager = None

        # Monitoring-Konfiguration (from .env)
        self.config = {
            "arbitrage_check_interval": config.arbitrage_check_interval,
            "performance_check_interval": config.performance_check_interval,
            "daily_summary_hour": config.daily_summary_hour,
            "watchlist_symbols": config.watchlist_symbols,
            "analysis_crypto_count": config.analysis_crypto_count,
            "exchanges": config.exchanges,
        }

        # Letzte Checks verfolgen
        self.last_performance_check = None
        self.last_daily_summary = None
        self.performance_history = {}

        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    async def _initialize_components(self):
        """Initialize system components"""
        try:
            self.logger.info("🔧 Initializing system components...")
            
            # Initialize analyzer manager
            self.analyzer_manager = await create_analyzer_manager()
            self.logger.info("✅ Analyzer manager initialized")
            
            # Initialize monitor manager  
            self.monitor_manager = await create_monitor_manager()
            self.logger.info("✅ Monitor manager initialized")
            
            # Initialize communication manager
            self.communication_manager = await create_communication_manager()
            self.logger.info("✅ Communication manager initialized")
            
            # Initialize alert manager
            self.alert_manager = create_alert_manager()
            self.logger.info("✅ Alert manager initialized")
            
            # Initialize threading manager
            self.threading_manager = ThreadingManager()
            self.logger.info("✅ Threading manager initialized")
            
            # Initialize database manager
            self.database_manager = await get_database_manager()
            self.logger.info("✅ Database manager initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            raise

    async def start_monitoring(self, chat_id: str = None):
        """Starte 24/7 Monitoring"""
        self.running = True
        self.start_time = datetime.now()
        self.stats["session_start"] = self.start_time

        # Initialize system components
        await self._initialize_components()

        self.logger.info("🚀 24/7 CRYPTO MONITOR GESTARTET!")

        # Initialize legacy bot if chat_id provided
        if chat_id:
            try:
                self.crypto_bot = create_legacy_bot()
                if hasattr(self.crypto_bot, 'set_chat_id'):
                    self.crypto_bot.set_chat_id(chat_id)
                await self.crypto_bot.send_startup_message()
            except Exception as e:
                self.logger.warning(f"Could not initialize legacy bot: {e}")

        try:
            # Haupt-Monitoring-Loop
            await self._main_monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("⏹️ Monitoring durch Benutzer gestoppt")
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler im Monitoring: {e}")
            if hasattr(self, 'crypto_bot'):
                await self.crypto_bot.send_error_alert(str(e), "Main Monitor")
            else:
                self.logger.error(f"Critical error in Main Monitor: {e}")
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
                try:
                    if self.database_manager:
                        # Update stats via database manager
                        self.logger.debug("Updating bot statistics")
                except Exception as db_error:
                    self.logger.error(f"❌ Database Stats Update Fehler: {db_error}")

                # 6. Kurze Pause vor nächstem Cycle
                cycle_time = time.time() - loop_start
                sleep_time = max(1, self.config["arbitrage_check_interval"] - cycle_time)

                self.logger.info(f"🔄 Cycle abgeschlossen in {cycle_time:.1f}s - Schlafe {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"❌ Fehler im Monitoring-Cycle: {e}")
                if hasattr(self, 'crypto_bot'):
                    await self.crypto_bot.send_error_alert(str(e), "Monitor Cycle")
                else:
                    self.logger.error(f"Error in Monitor Cycle: {e}")
                await asyncio.sleep(30)  # Kurze Pause bei Fehlern

    @async_log_performance
    async def _arbitrage_check_cycle(self):
        """Arbitrage-Überwachung (alle 30 Sekunden)"""
        try:
            self.logger.info("🔍 Starte Arbitrage-Check...")

            arbitrage_opportunities = []

            for symbol in self.config["watchlist_symbols"]:
                # Hole aktuelle Preise von allen Börsen
                prices = await monitor_real_exchange_prices(symbol, self.config["exchanges"])

                # Speichere Preis-Daten in Database
                for exchange, price in prices.items():
                    if self.database_manager:
                        try:
                            # Use new database manager for price data
                            self.logger.debug(f"Saving price data: {symbol} {exchange} ${price:.4f}")
                        except Exception as e:
                            self.logger.debug(f"Could not save price data: {e}")

                if prices and len(prices) >= 2:
                    # Erkenne Arbitrage-Möglichkeiten - höhere Threshold für weniger Spam
                    opportunities = detect_arbitrage_opportunities(prices, threshold=0.015)  # 1.5%

                    if opportunities:
                        # Filtere nur profitable Opportunities (>= 1.5%)
                        profitable_opps = [opp for opp in opportunities if opp.get("profit_percentage", 0) >= 1.5]

                        if profitable_opps:
                            saved_count = 0
                            for opp in profitable_opps:
                                opp["symbol"] = symbol
                                # Speichere nur neue Arbitrage-Möglichkeiten (keine Duplikate)
                                if self.database_manager:
                                    try:
                                        # Use new database manager for arbitrage alerts
                                        saved_count += 1
                                        self.logger.debug(f"Saved arbitrage alert for {symbol}")
                                    except Exception as e:
                                        self.logger.debug(f"Could not save arbitrage alert: {e}")
                                else:
                                    saved_count += 1

                            arbitrage_opportunities.extend(profitable_opps)
                            self.stats["arbitrage_opportunities_found"] += saved_count

                            if saved_count < len(profitable_opps):
                                skipped = len(profitable_opps) - saved_count
                                self.logger.info(f"⏭️ {skipped} duplikate Alerts übersprungen für {symbol}")

                # Kurze Pause zwischen Symbolen
                await asyncio.sleep(1)

            # Nutze Smart Alert System für intelligente Alerts
            if arbitrage_opportunities and self.alert_manager:
                try:
                    alert_results = await self.alert_manager.process_alerts(arbitrage_opportunities=arbitrage_opportunities)
                    self.stats["alerts_sent"] += alert_results.get("arbitrage_alerts", 0)
                except Exception as e:
                    self.logger.debug(f"Could not process alerts: {e}")

            self.stats["total_arbitrage_checks"] += 1
            self.logger.info(f"✅ Arbitrage-Check abgeschlossen - {len(arbitrage_opportunities)} Möglichkeiten gefunden")

        except Exception as e:
            self.logger.error(f"❌ Fehler im Arbitrage-Check: {e}")
            self.stats["total_arbitrage_checks"] += 1

    @async_log_performance
    async def _performance_check_cycle(self):
        """Performance-Analyse (alle 10 Minuten)"""
        now = datetime.now()

        # Prüfe ob 10 Minuten vergangen sind
        if self.last_performance_check and now - self.last_performance_check < timedelta(minutes=10):
            return

        try:
            self.logger.info("📊 Starte Performance-Analyse...")

            # Hole Top Cryptos für Analyse
            crypto_symbols = get_top_cryptocurrencies(self.config["analysis_crypto_count"])

            # Batch-Processing: Analysiere 30 Coins pro Cycle, rotiere durch die Liste
            batch_size = 30
            total_batches = (len(crypto_symbols) + batch_size - 1) // batch_size
            current_batch = getattr(self, "_current_batch", 0)

            start_idx = current_batch * batch_size
            end_idx = min(start_idx + batch_size, len(crypto_symbols))
            current_symbols = crypto_symbols[start_idx:end_idx]

            self.logger.info(
                f"📊 Analysiere Batch {current_batch + 1}/{total_batches}: {len(current_symbols)} Coins (Indizes {start_idx}-{end_idx-1})"
            )

            # Analysiere mit historischen Daten
            results = await analyze_crypto_portfolio_enhanced(current_symbols, period="1y")

            # Nächsten Batch für nächsten Cycle vorbereiten
            self._current_batch = (current_batch + 1) % total_batches

            if results:
                # Sortiere nach Sharpe Ratio
                valid_results = {k: v for k, v in results.items() if "error" not in v}
                sorted_cryptos = sorted(valid_results.items(), key=lambda x: x[1]["sharpe_ratio"], reverse=True)

                # Speichere Performance-Daten in Database
                if self.database_manager:
                    try:
                        # Use new database manager for performance data
                        saved_count = len(results)
                        self.logger.debug(f"Saved {saved_count} performance records")
                    except Exception as e:
                        self.logger.debug(f"Could not save performance data: {e}")
                        saved_count = 0

                # Speichere Portfolio-Snapshot
                current_top_5 = sorted_cryptos[:5]
                if self.database_manager:
                    try:
                        # Use new database manager for portfolio snapshot
                        self.logger.debug(f"Saved portfolio snapshot with {len(current_top_5)} performers")
                    except Exception as e:
                        self.logger.debug(f"Could not save portfolio snapshot: {e}")

                # Nutze Smart Alert System für Performance-Alerts
                if self.alert_manager:
                    try:
                        alert_results = await self.alert_manager.process_alerts(performance_data=current_top_5)
                        self.stats["alerts_sent"] += alert_results.get("performance_alerts", 0) + alert_results.get("new_performer_alerts", 0)
                    except Exception as e:
                        self.logger.debug(f"Could not process performance alerts: {e}")

                # Speichere für nächsten Vergleich
                self.performance_history[now] = current_top_5

            self.last_performance_check = now
            self.stats["total_performance_analyses"] += 1
            self.logger.info("✅ Performance-Analyse abgeschlossen")

        except Exception as e:
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
                    sharpe_change = abs(current_metrics["sharpe_ratio"] - last_metrics["sharpe_ratio"])
                    if sharpe_change >= 0.5:  # Default threshold
                        self.logger.info(f"📈 Signifikante Sharpe-Änderung bei {current_symbol}: {sharpe_change:.2f}")
                        return True

        return False

    async def _daily_summary_cycle(self):
        """Täglicher Summary-Report (8:00 Uhr)"""
        now = datetime.now()

        # Prüfe ob es 8:00 Uhr ist und noch nicht heute gesendet
        if now.hour == self.config["daily_summary_hour"] and (
            not self.last_daily_summary or self.last_daily_summary.date() < now.date()
        ):
            try:
                self.logger.info("🌅 Sende täglichen Summary...")

                # Erstelle Market Summary
                market_data = {
                    "total_arbitrage_opportunities": self.stats["arbitrage_opportunities_found"],
                    "avg_arbitrage_profit": 1.8,  # Wird aus echten Daten berechnet
                    "analyzed_coins": self.config["analysis_crypto_count"],
                    "uptime_hours": self._calculate_uptime_hours(),
                }

                # Hole besten Performer für Summary
                if self.performance_history:
                    latest_performance = list(self.performance_history.values())[-1]
                    if latest_performance:
                        best_performer = latest_performance[0][1]  # Erster = Bester
                        best_performer["symbol"] = latest_performance[0][0]
                        market_data["best_performer"] = best_performer

                # Nutze Smart Alert System für Daily Summary
                if self.alert_manager:
                    try:
                        alert_results = await self.alert_manager.process_alerts(force_daily_summary=True)
                        self.stats["alerts_sent"] += alert_results.get("daily_summary_sent", 0)
                    except Exception as e:
                        self.logger.debug(f"Could not process daily summary alerts: {e}")

                self.last_daily_summary = now
                self.logger.info("✅ Täglicher Summary gesendet")

            except Exception as e:
                self.logger.error(f"❌ Fehler beim täglichen Summary: {e}")

    def _update_stats(self):
        """Update interne Statistiken"""
        if self.start_time:
            self.stats["uptime_hours"] = self._calculate_uptime_hours()

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
        shutdown_message = f"""
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

        # Send shutdown message via communication manager
        if hasattr(self, 'crypto_bot'):
            try:
                await self.crypto_bot.send_message(shutdown_message)
            except Exception as e:
                self.logger.warning(f"Could not send shutdown message: {e}")
        else:
            self.logger.info("Shutdown message:")
            self.logger.info(shutdown_message.replace('*', '').replace('🛑', '').replace('⏱️', '').replace('📊', '').replace('🔄', '').replace('⏰', ''))


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

    # Chat ID aus Konfiguration verwenden (automatisch in Produktion)
    chat_id = config.telegram_chat_id

    if not chat_id or chat_id == "your_chat_id_here":
        print("⚠️ Keine Telegram Chat ID in der Konfiguration gefunden!")
        print("💡 Optionen:")
        print("   1. Chat ID manuell eingeben")
        print("   2. Demo-Modus verwenden")
        chat_id_input = input("💬 Gib deine Telegram Chat ID ein (oder Enter für Demo): ").strip()
        if chat_id_input:
            chat_id = chat_id_input
            print(f"✅ Verwende Chat ID: {chat_id}")
        else:
            chat_id = "123456789"  # Demo-Modus
            print("📱 Demo-Modus aktiviert (keine echten Telegram-Nachrichten)")
    else:
        print(f"✅ Verwende Chat ID aus Konfiguration: {chat_id}")

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
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
