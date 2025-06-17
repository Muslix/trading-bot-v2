"""
SQLite Database Module - Crypto Trading Bot Database
Einfache SQLite statt PostgreSQL für alle Bot-Daten
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Database Configuration
# Database-Pfad mit relativer Pfadauflösung
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "database", "crypto_trading_bot.db")
DB_VERSION = "1.0"


class CryptoDatabaseManager:
    """SQLite Database Manager für Crypto Trading Bot"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_db_exists()
        self._create_tables()

    def _ensure_db_exists(self):
        """Stelle sicher dass Database-Datei existiert"""
        if not os.path.exists(self.db_path):
            self.logger.info(f"📊 Erstelle neue SQLite Datenbank: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context Manager für Database-Verbindungen"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Für dict-like access
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            self.logger.error("Database Fehler: {e}")
            raise
        finally:
            conn.close()

    def _create_tables(self):
        """Erstelle alle benötigten Tabellen"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Arbitrage Alerts Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS arbitrage_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    buy_exchange TEXT NOT NULL,
                    sell_exchange TEXT NOT NULL,
                    buy_price REAL NOT NULL,
                    sell_price REAL NOT NULL,
                    profit_percentage REAL NOT NULL,
                    profit_per_unit REAL NOT NULL,
                    alert_sent BOOLEAN DEFAULT 0,
                    telegram_message_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 2. Price History Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL DEFAULT 0,
                    bid REAL DEFAULT 0,
                    ask REAL DEFAULT 0,
                    data_source TEXT DEFAULT 'api',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 3. Performance Data Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    sortino_ratio REAL DEFAULT 0,
                    annual_return REAL NOT NULL,
                    volatility REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    var_95 REAL DEFAULT 0,
                    beta_vs_btc REAL DEFAULT 1,
                    current_price REAL NOT NULL,
                    data_source TEXT DEFAULT 'yahoo_finance',
                    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 4. Bot Statistics Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_arbitrage_checks INTEGER DEFAULT 0,
                    total_performance_analyses INTEGER DEFAULT 0,
                    arbitrage_opportunities_found INTEGER DEFAULT 0,
                    alerts_sent INTEGER DEFAULT 0,
                    uptime_hours REAL DEFAULT 0,
                    session_start DATETIME,
                    session_end DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 5. Telegram Messages Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    chat_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    message_text TEXT,
                    telegram_message_id TEXT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 6. Portfolio Snapshots Tabelle
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    snapshot_type TEXT DEFAULT 'performance_check',
                    top_performers TEXT,  -- JSON string
                    total_coins_analyzed INTEGER DEFAULT 0,
                    avg_sharpe_ratio REAL DEFAULT 0,
                    best_performer_symbol TEXT,
                    best_performer_sharpe REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Erstelle Indizes für bessere Performance
            self._create_indexes(cursor)

            conn.commit()
            self.logger.info("✅ Alle Database-Tabellen erfolgreich erstellt/überprüft")

    def _create_indexes(self, cursor):
        """Erstelle Indizes für bessere Query-Performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp ON arbitrage_alerts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_arbitrage_symbol ON arbitrage_alerts(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_price_timestamp ON price_history(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_price_symbol_exchange ON price_history(symbol, exchange)",
            "CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_performance_symbol ON performance_data(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_telegram_timestamp ON telegram_messages(timestamp)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

    # ARBITRAGE ALERTS METHODS
    def check_recent_arbitrage_alert(self, opportunity: Dict, hours: int = 1) -> bool:
        """Prüfe ob ähnlicher Arbitrage Alert bereits in den letzten X Stunden existiert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            since_time = datetime.now() - timedelta(hours=hours)

            # Erste Prüfung: Exakte Kombination von Symbol, Exchanges und ähnlichem Profit
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM arbitrage_alerts
                WHERE symbol = ?
                AND buy_exchange = ?
                AND sell_exchange = ?
                AND ABS(profit_percentage - ?) < 0.1  -- Sehr ähnlicher Profit (±0.1%)
                AND timestamp >= ?
            """,
                (
                    opportunity.get("symbol", ""),
                    opportunity.get("buy_exchange", ""),
                    opportunity.get("sell_exchange", ""),
                    opportunity.get("profit_percentage", 0),
                    since_time,
                ),
            )

            result = cursor.fetchone()
            exists = result["count"] > 0

            if exists:
                self.logger.debug(
                    "🔄 Ähnlicher Alert bereits vorhanden für {opportunity.get('symbol', 'UNKNOWN')} ({opportunity.get('profit_percentage', 0):.1f}%)"
                )

            return exists

    def save_arbitrage_alert(self, opportunity: Dict) -> int:
        """Speichere Arbitrage Alert in Database - mit Duplikate-Prüfung"""

        # Prüfe zuerst, ob ähnlicher Alert bereits existiert
        if self.check_recent_arbitrage_alert(opportunity, hours=6):
            self.logger.debug("⏭️ Überspringe duplizierten Alert für {opportunity.get('symbol', 'UNKNOWN')}")
            return -1  # Negative ID zeigt an, dass nicht gespeichert wurde

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO arbitrage_alerts
                (symbol, buy_exchange, sell_exchange, buy_price, sell_price,
                 profit_percentage, profit_per_unit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    opportunity.get("symbol", ""),
                    opportunity.get("buy_exchange", ""),
                    opportunity.get("sell_exchange", ""),
                    opportunity.get("buy_price", 0),
                    opportunity.get("sell_price", 0),
                    opportunity.get("profit_percentage", 0),
                    opportunity.get("profit_per_unit", 0),
                ),
            )

            conn.commit()
            alert_id = cursor.lastrowid
            self.logger.info(
                "💾 Arbitrage Alert gespeichert: {alert_id} - {opportunity.get('symbol', 'UNKNOWN')} ({opportunity.get('profit_percentage', 0):.1f}%)"
            )
            return alert_id

    def update_arbitrage_alert_sent(self, alert_id: int, telegram_message_id: str = None):
        """Markiere Arbitrage Alert als gesendet"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE arbitrage_alerts
                SET alert_sent = 1, telegram_message_id = ?
                WHERE id = ?
            """,
                (telegram_message_id, alert_id),
            )

            conn.commit()

    def get_recent_arbitrage_alerts(self, hours: int = 24) -> List[Dict]:
        """Hole Arbitrage Alerts der letzten X Stunden"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            since_time = datetime.now() - timedelta(hours=hours)

            cursor.execute(
                """
                SELECT * FROM arbitrage_alerts
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since_time,),
            )

            return [dict(row) for row in cursor.fetchall()]

    # PRICE HISTORY METHODS
    def save_price_data(
        self,
        symbol: str,
        exchange: str,
        price: float,
        volume: float = 0,
        bid: float = 0,
        ask: float = 0,
    ):
        """Speichere Preis-Daten"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO price_history
                (symbol, exchange, price, volume, bid, ask)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (symbol, exchange, price, volume, bid, ask),
            )

            conn.commit()

    def get_price_history(self, symbol: str, exchange: str = None, hours: int = 24) -> List[Dict]:
        """Hole Preis-Historie"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            since_time = datetime.now() - timedelta(hours=hours)

            if exchange:
                cursor.execute(
                    """
                    SELECT * FROM price_history
                    WHERE symbol = ? AND exchange = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (symbol, exchange, since_time),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM price_history
                    WHERE symbol = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (symbol, since_time),
                )

            return [dict(row) for row in cursor.fetchall()]

    # PERFORMANCE DATA METHODS
    def save_performance_data(self, performance_results: Dict[str, Dict]):
        """Speichere Performance-Analyse-Ergebnisse"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            saved_count = 0
            for symbol, metrics in performance_results.items():
                if "error" in metrics:
                    continue

                cursor.execute(
                    """
                    INSERT INTO performance_data
                    (symbol, timeframe, sharpe_ratio, sortino_ratio, annual_return,
                     volatility, max_drawdown, var_95, beta_vs_btc, current_price,
                     data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        symbol,
                        metrics.get("period", "2y"),
                        metrics.get("sharpe_ratio", 0),
                        metrics.get("sortino_ratio", 0),
                        metrics.get("annual_return", 0),
                        metrics.get("volatility", 0),
                        metrics.get("max_drawdown", 0),
                        metrics.get("var_95", 0),
                        metrics.get("beta_vs_btc", 1),
                        metrics.get("current_price", 0),
                        metrics.get("data_source", "yahoo_finance"),
                    ),
                )
                saved_count += 1

            conn.commit()
            self.logger.info(f"💾 Performance-Daten gespeichert: {saved_count} Einträge")
            return saved_count

    def get_latest_performance_data(self, limit: int = 20) -> List[Dict]:
        """Hole neueste Performance-Daten"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT symbol, sharpe_ratio, annual_return, current_price,
                       timestamp, timeframe
                FROM performance_data
                WHERE timestamp >= date('now', '-1 day')
                ORDER BY sharpe_ratio DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    # PORTFOLIO SNAPSHOTS METHODS
    def save_portfolio_snapshot(self, top_performers: List[Tuple], snapshot_type: str = "performance_check"):
        """Speichere Portfolio-Snapshot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Konvertiere zu JSON
            performers_json = json.dumps([{"symbol": symbol, "metrics": metrics} for symbol, metrics in top_performers])

            # Berechne Statistiken
            total_coins = len(top_performers)
            avg_sharpe = (
                sum(metrics["sharpe_ratio"] for _, metrics in top_performers) / total_coins if total_coins > 0 else 0
            )
            best_performer = top_performers[0] if top_performers else ("", {"sharpe_ratio": 0})

            cursor.execute(
                """
                INSERT INTO portfolio_snapshots
                (snapshot_type, top_performers, total_coins_analyzed,
                 avg_sharpe_ratio, best_performer_symbol, best_performer_sharpe)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    snapshot_type,
                    performers_json,
                    total_coins,
                    avg_sharpe,
                    best_performer[0],
                    best_performer[1]["sharpe_ratio"],
                ),
            )

            conn.commit()
            snapshot_id = cursor.lastrowid
            self.logger.info(f"💾 Portfolio-Snapshot gespeichert: {snapshot_id}")
            return snapshot_id

    # BOT STATISTICS METHODS
    def update_bot_statistics(self, stats: Dict):
        """Update Bot-Statistiken"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO bot_statistics
                (total_arbitrage_checks, total_performance_analyses,
                 arbitrage_opportunities_found, alerts_sent, uptime_hours,
                 session_start)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    stats.get("total_arbitrage_checks", 0),
                    stats.get("total_performance_analyses", 0),
                    stats.get("arbitrage_opportunities_found", 0),
                    stats.get("alerts_sent", 0),
                    stats.get("uptime_hours", 0),
                    stats.get("session_start", datetime.now()),
                ),
            )

            conn.commit()

    # TELEGRAM MESSAGES METHODS
    def log_telegram_message(
        self,
        chat_id: str,
        message_type: str,
        message_text: str,
        success: bool = True,
        telegram_message_id: str = None,
        error_message: str = None,
    ):
        """Logge Telegram-Nachricht"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO telegram_messages
                (chat_id, message_type, message_text, success,
                 telegram_message_id, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    chat_id,
                    message_type,
                    message_text[:500],
                    success,
                    telegram_message_id,
                    error_message,
                ),
            )

            conn.commit()

    # ANALYTICS METHODS
    def get_dashboard_data(self) -> Dict:
        """Hole Daten für Frontend Dashboard"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Arbitrage Statistiken (letzte 24h)
            cursor.execute(
                """
                SELECT COUNT(*) as total_alerts,
                       AVG(profit_percentage) as avg_profit,
                       MAX(profit_percentage) as max_profit
                FROM arbitrage_alerts
                WHERE timestamp >= datetime('now', '-1 day')
            """
            )
            arbitrage_stats = dict(cursor.fetchone())

            # Performance Statistiken
            cursor.execute(
                """
                SELECT COUNT(DISTINCT symbol) as total_coins,
                       AVG(sharpe_ratio) as avg_sharpe,
                       MAX(sharpe_ratio) as max_sharpe
                FROM performance_data
                WHERE timestamp >= datetime('now', '-1 day')
            """
            )
            performance_stats = dict(cursor.fetchone())

            # Telegram Statistiken
            cursor.execute(
                """
                SELECT COUNT(*) as total_messages,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_messages
                FROM telegram_messages
                WHERE timestamp >= datetime('now', '-1 day')
            """
            )
            telegram_stats = dict(cursor.fetchone())

            return {
                "arbitrage": arbitrage_stats,
                "performance": performance_stats,
                "telegram": telegram_stats,
                "last_updated": datetime.now().isoformat(),
            }

    def cleanup_old_data(self, days: int = 30):
        """Lösche alte Daten (älter als X Tage)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            # Lösche alte Einträge
            tables_to_clean = ["price_history", "telegram_messages", "bot_statistics"]

            for table in tables_to_clean:
                cursor.execute(
                    """
                    DELETE FROM {table}
                    WHERE timestamp < ?
                """,
                    (cutoff_date,),
                )

            conn.commit()
            self.logger.info(f"🧹 Alte Daten bereinigt (älter als {days} Tage)")


# Global Database Instance
db = CryptoDatabaseManager()


def test_database():
    """Teste Database-Funktionalität"""
    print("🧪 SQLite Database Test")
    print("=" * 40)

    # Test 1: Arbitrage Alert speichern
    print("1. Teste Arbitrage Alert...")
    test_opportunity = {
        "symbol": "BTC/USDT",
        "buy_exchange": "binance",
        "sell_exchange": "coinbase",
        "buy_price": 45000,
        "sell_price": 46000,
        "profit_percentage": 2.2,
        "profit_per_unit": 1000,
    }

    alert_id = db.save_arbitrage_alert(test_opportunity)
    print(f"✅ Alert gespeichert mit ID: {alert_id}")

    # Test 2: Price Data speichern
    print("\n2. Teste Price Data...")
    db.save_price_data("BTC/USDT", "binance", 45123.45, volume=1000)
    print("✅ Price Data gespeichert")

    # Test 3: Performance Data
    print("\n3. Teste Performance Data...")
    test_performance = {
        "BTC": {
            "sharpe_ratio": 1.65,
            "sortino_ratio": 2.1,
            "annual_return": 82.6,
            "volatility": 48.7,
            "max_drawdown": -28.1,
            "current_price": 45123.45,
            "period": "2y",
        }
    }
    saved_count = db.save_performance_data(test_performance)
    print(f"✅ Performance Data gespeichert: {saved_count} Einträge")

    # Test 4: Dashboard Data
    print("\n4. Teste Dashboard Data...")
    dashboard_data = db.get_dashboard_data()
    print(f"✅ Dashboard Data: {dashboard_data}")

    print("\n" + "=" * 40)
    print("🎉 SQLite Database Tests erfolgreich!")
    print(f"📊 Database-Datei: {db.db_path}")


if __name__ == "__main__":
    test_database()
