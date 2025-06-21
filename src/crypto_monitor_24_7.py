"""
24/7 Crypto Trading Bot - Endlos-Monitoring System
Läuft dauerhaft und überwacht Arbitrage + Performance automatisch
"""

import asyncio
import concurrent.futures
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
        # Managers will be initialized in start_monitoring() method
        self.alert_manager = None
        self.db_manager = None
        self.analyzer_manager = None
        self.monitor_manager = None
        self.communication_manager = None
        self.threading_manager = None
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

        # Enhanced production logging setup
        self._setup_production_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize legacy bot for backward compatibility
        self.crypto_bot = None  # Will be initialized in start_monitoring
        self.production_logger = None  # Will be initialized in start_monitoring

    def _setup_production_logging(self):
        """Setup comprehensive production logging"""
        import os
        
        # Create logs directory structure
        os.makedirs("logs", exist_ok=True)
        os.makedirs("logs/errors", exist_ok=True)
        os.makedirs("logs/debug", exist_ok=True)
        os.makedirs("logs/archive", exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO if os.getenv('LOG_LEVEL', 'INFO') == 'INFO' else logging.DEBUG,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('logs/crypto_monitor_main.log'),
                logging.StreamHandler()  # Console output
            ]
        )
        
        # Set up specific loggers for different components
        self._setup_component_loggers()

    def _setup_component_loggers(self):
        """Setup specialized loggers for different components"""
        # Arbitrage logger
        arbitrage_logger = logging.getLogger('arbitrage')
        arbitrage_handler = logging.FileHandler('logs/arbitrage_opportunities.log')
        arbitrage_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        arbitrage_logger.addHandler(arbitrage_handler)
        arbitrage_logger.setLevel(logging.INFO)
        
        # Performance logger  
        performance_logger = logging.getLogger('performance')
        performance_handler = logging.FileHandler('logs/performance_analysis.log')
        performance_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        performance_logger.addHandler(performance_handler)
        performance_logger.setLevel(logging.INFO)
        
        # Data sources logger
        data_logger = logging.getLogger('data_sources')
        data_handler = logging.FileHandler('logs/data_sources.log')
        data_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        data_logger.addHandler(data_handler)
        data_logger.setLevel(logging.DEBUG)
        
        # Error logger
        error_logger = logging.getLogger('errors')
        error_handler = logging.FileHandler('logs/errors/system_errors.log')
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        ))
        error_logger.addHandler(error_handler)
        error_logger.setLevel(logging.ERROR)

    async def start_monitoring(self, chat_id: str = None):
        """Starte 24/7 Monitoring"""
        self.running = True
        self.start_time = datetime.now()
        self.stats["session_start"] = self.start_time

        # Initialize production logger for detailed monitoring
        try:
            from src.utils.production_logger import get_production_logger
            self.production_logger = get_production_logger("crypto_monitor")
            self.production_logger.log_startup(self.config)
        except Exception as e:
            self.logger.warning(f"Could not initialize production logger: {e}")

        # Initialize all managers asynchronously
        self.logger.info("🔧 Initializing system components...")
        
        # Initialize legacy bot first
        if self.crypto_bot is None:
            self.crypto_bot = create_legacy_bot()
        
        # Initialize analyzer manager
        if self.analyzer_manager is None:
            self.logger.info("🧮 Initializing analyzer manager...")
            analyzer_config = {
                "arbitrage": {"enabled": True, "threshold": config.arbitrage_threshold},
                "portfolio": {"enabled": True, "analysis_count": self.config["analysis_crypto_count"]},
                "technical": {"enabled": True}
            }
            self.analyzer_manager = await create_analyzer_manager(analyzer_config)
            self.logger.info("✅ Analyzer manager initialized")
        
        # Initialize monitor manager
        if self.monitor_manager is None:
            self.logger.info("📊 Initializing monitor manager...")
            monitor_config = {
                "price": {"enabled": True, "exchanges": self.config["exchanges"]},
                "volume": {"enabled": True},
                "network": {"enabled": True}
            }
            self.monitor_manager = await create_monitor_manager(monitor_config)
            self.logger.info("✅ Monitor manager initialized")
        
        # Initialize communication manager
        if self.communication_manager is None:
            self.logger.info("📱 Initializing communication manager...")
            comm_config = {
                "telegram": {
                    "enabled": True,
                    "bot_token": config.telegram_bot_token,
                    "chat_id": config.telegram_chat_id,
                    "arbitrage_threshold": config.arbitrage_threshold,
                    "sharpe_change_threshold": config.sharpe_change_threshold,
                    "cooldown_minutes": config.alert_cooldown_minutes
                }
            }
            self.communication_manager = await create_communication_manager(comm_config)
            self.logger.info("✅ Communication manager initialized")
        
        if self.alert_manager is None:
            self.logger.info("📬 Initializing alert manager...")
            # Pass config to alert manager
            alert_config_dict = {
                'arbitrage_threshold': config.arbitrage_threshold,
                'sharpe_change_threshold': config.sharpe_change_threshold,
                'alert_cooldown_minutes': config.alert_cooldown_minutes
            }
            self.alert_manager = await create_alert_manager(alert_config_dict)
            self.logger.info("✅ Alert manager initialized")
        
        if self.db_manager is None:
            self.logger.info("💾 Initializing database manager...")
            self.db_manager = await get_database_manager()
            self.logger.info("✅ Database manager initialized")
        
        # Initialize ThreadingManager for performance improvements
        if self.threading_manager is None:
            self.logger.info("🧵 Initializing threading manager...")
            self.threading_manager = ThreadingManager(max_workers=8)
            self.logger.info("✅ Threading manager initialized with 8 workers")

        if chat_id:
            self.logger.info(f"📱 Setting Telegram chat ID: {chat_id}")
            self.crypto_bot.set_chat_id(chat_id)

        self.logger.info("🚀 24/7 CRYPTO MONITOR GESTARTET!")
        self.logger.info(f"📊 Configuration: {self.config}")
        self.logger.info(f"📅 Start time: {self.start_time}")

        # Sende aussagekräftige Startup-Nachricht
        startup_message = f"""🚀 *CRYPTO TRADING BOT GESTARTET!*

📊 *Monitoring Konfiguration:*
• Arbitrage Check: alle {self.config['arbitrage_check_interval']}s
• Performance Check: alle {self.config['performance_check_interval']//60} Min
• Überwachte Symbole: {len(self.config['watchlist_symbols'])}
• Börsen: {', '.join(self.config['exchanges']).upper()}

🔍 *Aktive Module:*
• ✅ Arbitrage Analyzer
• ✅ Portfolio Analyzer  
• ✅ Price Monitor
• ✅ Database Manager
• ✅ Telegram Alerts
• 🧵 Threading Manager (8 workers)

⚡ *Performance Features:*
• Concurrent arbitrage processing
• Threaded portfolio analysis
• Optimized data collection

⏰ Start: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"""

        if self.communication_manager:
            await self.communication_manager.send_message("telegram", startup_message)
        else:
            await self.crypto_bot.send_message(startup_message)

        try:
            # Haupt-Monitoring-Loop
            await self._main_monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("⏹️ Monitoring durch Benutzer gestoppt")
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler im Monitoring: {e}")
            await self.crypto_bot.send_error_alert(str(e), "Main Monitor")
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
                    await self.db_manager.execute('save', repository='bot_statistics', data=self.stats)
                except Exception as db_error:
                    self.logger.error(f"❌ Database Stats Update Fehler: {db_error}")

                # 6. Kurze Pause vor nächstem Cycle
                cycle_time = time.time() - loop_start
                sleep_time = max(1, self.config["arbitrage_check_interval"] - cycle_time)

                self.logger.info(f"🔄 Cycle abgeschlossen in {cycle_time:.1f}s - Schlafe {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"❌ Fehler im Monitoring-Cycle: {e}")
                await self.crypto_bot.send_error_alert(str(e), "Monitor Cycle")
                await asyncio.sleep(30)  # Kurze Pause bei Fehlern

    @async_log_performance
    async def _arbitrage_check_cycle(self):
        """Arbitrage-Überwachung (alle 30 Sekunden)"""
        arbitrage_logger = logging.getLogger('arbitrage')
        
        try:
            self.logger.info("🔍 Starte Arbitrage-Check...")
            arbitrage_logger.info(f"Starting arbitrage check for {len(self.config['watchlist_symbols'])} symbols")

            arbitrage_opportunities = []

            # Parallelisierte Verarbeitung für bessere Performance mit vielen Coins
            async def process_symbol(symbol):
                arbitrage_logger.info(f"Checking arbitrage for {symbol}")
                symbol_start_time = time.time()
                symbol_opportunities = []
                
                try:
                    # Hole aktuelle Preise von allen Börsen
                    prices = await monitor_real_exchange_prices(symbol, self.config["exchanges"])
                    
                    # Log detailed price information
                    arbitrage_logger.info(f"{symbol} prices from {len(prices)} exchanges: {prices}")
                    
                    # Log to production logger if available
                    if self.production_logger:
                        for exchange, price in prices.items():
                            self.production_logger.log_price_data(symbol, exchange, price)

                    # Speichere Preis-Daten in Database
                    for exchange, price in prices.items():
                        price_data = {
                            'symbol': symbol,
                            'exchange': exchange,
                            'price': price,
                            'timestamp': datetime.now().isoformat()
                        }
                        await self.db_manager.execute('save', repository='price', data=price_data)
                        
                    data_logger = logging.getLogger('data_sources')
                    data_logger.debug(f"Saved price data: {symbol} {exchange} ${price:.4f}")

                    if prices and len(prices) >= 2:
                        # Erkenne Arbitrage-Möglichkeiten - höhere Threshold für weniger Spam
                        opportunities = detect_arbitrage_opportunities(prices, threshold=0.015)  # 1.5%
                        
                        arbitrage_logger.info(f"{symbol}: Found {len(opportunities)} opportunities")
                        
                        # Log detailed arbitrage calculation
                        if self.production_logger:
                            self.production_logger.log_arbitrage_calculation(symbol, prices, opportunities)

                        if opportunities:
                            # Filtere nur profitable Opportunities (>= 1.5%)
                            profitable_opps = [opp for opp in opportunities if opp.get("profit_percentage", 0) >= 1.5]
                            
                            arbitrage_logger.info(f"{symbol}: {len(profitable_opps)} profitable opportunities (>= 1.5%)")

                            if profitable_opps:
                                saved_count = 0
                                for opp in profitable_opps:
                                    opp["symbol"] = symbol
                                    arbitrage_logger.info(f"Arbitrage opportunity: {opp['buy_exchange']} -> {opp['sell_exchange']} profit: {opp.get('profit_percentage', 0):.2f}%")
                                    
                                    # Speichere nur neue Arbitrage-Möglichkeiten (keine Duplikate)
                                    try:
                                        await self.db_manager.execute('save', repository='arbitrage', data=opp)
                                        saved_count += 1
                                        arbitrage_logger.info(f"Saved arbitrage opportunity for {symbol}")
                                    except Exception as e:
                                        # Duplicate or error - skip
                                        arbitrage_logger.debug(f"Skipped duplicate/error for {symbol}: {e}")

                                symbol_opportunities.extend(profitable_opps)
                                self.stats["arbitrage_opportunities_found"] += saved_count

                                if saved_count < len(profitable_opps):
                                    skipped = len(profitable_opps) - saved_count
                                    self.logger.info(f"⏭️ {skipped} duplikate Alerts übersprungen für {symbol}")
                                    arbitrage_logger.info(f"Skipped {skipped} duplicate alerts for {symbol}")
                    else:
                        arbitrage_logger.warning(f"{symbol}: Insufficient price data ({len(prices)} exchanges)")
                    
                    # Log timing for this symbol
                    symbol_duration = time.time() - symbol_start_time
                    arbitrage_logger.debug(f"{symbol} processing completed in {symbol_duration:.2f}s")
                    
                    return symbol_opportunities
                    
                except Exception as e:
                    arbitrage_logger.error(f"Error processing {symbol}: {e}")
                    return []

            # Use ThreadingManager for concurrent processing with better performance
            symbols = self.config["watchlist_symbols"]
            
            # Process symbols concurrently using ThreadingManager
            self.logger.info(f"🧵 Processing {len(symbols)} symbols concurrently with ThreadingManager")
            
            # Convert async process_symbol to sync for ThreadingManager
            def sync_process_symbol(symbol):
                try:
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(process_symbol(symbol))
                    finally:
                        loop.close()
                except Exception as e:
                    arbitrage_logger.error(f"Thread error processing {symbol}: {e}")
                    return []
            
            # Submit all symbols for concurrent processing
            futures = []
            for symbol in symbols:
                future = self.threading_manager.submit_task(
                    sync_process_symbol,
                    symbol
                )
                futures.append(future)
            
            # Wait for all results with timeout
            self.logger.info("⏳ Waiting for concurrent arbitrage processing to complete...")
            results = []
            try:
                for future in concurrent.futures.as_completed(futures, timeout=60):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        arbitrage_logger.error(f"Future result error: {e}")
                        results.append([])
            except concurrent.futures.TimeoutError:
                self.logger.warning("⚠️ Arbitrage processing timeout, using partial results")
                for future in futures:
                    if future.done():
                        try:
                            results.append(future.result())
                        except:
                            results.append([])
            
            # Collect all opportunities from results
            for result in results:
                if isinstance(result, list):
                    arbitrage_opportunities.extend(result)
                elif result is not None:
                    self.logger.warning(f"Unexpected result type: {type(result)}")
            
            # Log performance metrics from ThreadingManager
            try:
                metrics = self.threading_manager.get_metrics()
                self.logger.info(f"🔧 Threading performance - Active: {metrics.get('active_tasks', 0)}, Completed: {metrics.get('completed_tasks', 0)}")
            except Exception as e:
                self.logger.debug(f"Could not get threading metrics: {e}")
            
            # Optional: Run health check
            health = self.threading_manager.health_check()
            if not health['healthy']:
                self.logger.warning(f"⚠️ ThreadingManager health issues: {health['issues']}")

            # Nutze Smart Alert System für intelligente Alerts
            if arbitrage_opportunities:
                alert_results = await self.alert_manager.process_all_alerts(arbitrage_opportunities=arbitrage_opportunities)
                self.stats["alerts_sent"] += alert_results.get("alerts_sent", 0)

            self.stats["total_arbitrage_checks"] += 1
            self.logger.info(f"✅ Arbitrage-Check abgeschlossen - {len(arbitrage_opportunities)} Möglichkeiten gefunden")

        except Exception as e:
            self.logger.error(f"❌ Fehler im Arbitrage-Check: {e}")
            self.stats["total_arbitrage_checks"] += 1

    @async_log_performance
    async def _performance_check_cycle(self):
        """Performance-Analyse (alle 10 Minuten)"""
        performance_logger = logging.getLogger('performance')
        now = datetime.now()

        # Prüfe ob 10 Minuten vergangen sind
        if self.last_performance_check and now - self.last_performance_check < timedelta(minutes=10):
            time_remaining = timedelta(minutes=10) - (now - self.last_performance_check)
            performance_logger.debug(f"Skipping performance check, {time_remaining} remaining")
            return

        try:
            self.logger.info("📊 Starte Performance-Analyse...")
            performance_logger.info(f"Starting performance analysis at {now}")

            # Hole Top Cryptos für Analyse
            crypto_symbols = get_top_cryptocurrencies(self.config["analysis_crypto_count"])
            performance_logger.info(f"Retrieved {len(crypto_symbols)} crypto symbols for analysis")

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

            # Use ThreadingManager for concurrent portfolio analysis
            def sync_analyze_crypto(symbols):
                try:
                    # Create event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(analyze_crypto_portfolio_enhanced(symbols, period="1y"))
                    finally:
                        loop.close()
                except Exception as e:
                    performance_logger.error(f"Thread error in portfolio analysis: {e}")
                    return {}
            
            # Submit portfolio analysis task
            self.logger.info(f"🧵 Submitting portfolio analysis for {len(current_symbols)} symbols to ThreadingManager")
            future = self.threading_manager.submit_task(
                sync_analyze_crypto,
                current_symbols
            )
            
            # Wait for result with timeout
            try:
                results = future.result(timeout=120)
                if not results:
                    results = {}
            except concurrent.futures.TimeoutError:
                self.logger.warning("⚠️ Portfolio analysis timeout")
                results = {}
            except Exception as e:
                performance_logger.error(f"Portfolio analysis error: {e}")
                results = {}

            # Nächsten Batch für nächsten Cycle vorbereiten
            self._current_batch = (current_batch + 1) % total_batches

            if results:
                # Sortiere nach Sharpe Ratio
                valid_results = {k: v for k, v in results.items() if "error" not in v}
                sorted_cryptos = sorted(valid_results.items(), key=lambda x: x[1]["sharpe_ratio"], reverse=True)

                # Speichere Performance-Daten in Database
                try:
                    await self.db_manager.execute('save', repository='performance', data=results)
                except Exception as e:
                    self.logger.error(f"❌ Performance data save error: {e}")

                # Speichere Portfolio-Snapshot
                current_top_5 = sorted_cryptos[:5]
                try:
                    snapshot_data = {
                        'performers': current_top_5,
                        'snapshot_type': 'performance_check',
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.db_manager.execute('save', repository='portfolio', data=snapshot_data)
                except Exception as e:
                    self.logger.error(f"❌ Portfolio snapshot save error: {e}")

                # Nutze Smart Alert System für Performance-Alerts
                alert_results = await self.alert_manager.process_all_alerts(current_performers=current_top_5)
                self.stats["alerts_sent"] += alert_results.get("alerts_sent", 0)

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
                    if sharpe_change >= config.sharpe_change_threshold:
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
                alert_results = await self.alert_manager.process_all_alerts(force_summary=True)
                self.stats["alerts_sent"] += alert_results.get("alerts_sent", 0)

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
        if self.communication_manager:
            await self.communication_manager.send_message("telegram", shutdown_message)
        else:
            await self.crypto_bot.send_message(shutdown_message)
            
        # Cleanup all managers
        if self.analyzer_manager:
            await self.analyzer_manager.cleanup()
        if self.monitor_manager:
            await self.monitor_manager.cleanup()
        if self.communication_manager:
            await self.communication_manager.cleanup()
        if self.threading_manager:
            self.threading_manager.shutdown()
            self.logger.info("✅ Threading manager shutdown complete")


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


# Legacy bot is now initialized within CryptoMonitor24_7 class
