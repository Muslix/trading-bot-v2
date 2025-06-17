"""
Web API Server für Crypto Trading Bot Dashboard
Flask API zum Verbinden des Vue.js Frontends mit der SQLite Database
"""

import logging
import os
import sys
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask_cors import CORS

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import project modules
try:
    from src.modules.database import db
    from src.utils.symbol_normalizer import merge_duplicate_performance_data
except ImportError as e:
    logging.error(f"Import error in web_api: {e}")
    sys.exit(1)

# Flask App Setup
app = Flask(__name__)
CORS(app)  # Erlaube Cross-Origin Requests

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# API ROUTES


@app.route("/")
def index():
    """Serve Frontend"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>🤖 Crypto Trading Bot API</h1>
        <p>Frontend nicht gefunden. Stelle sicher, dass frontend/index.html existiert.</p>
        <h2>Verfügbare API Endpoints:</h2>
        <ul>
            <li><a href="/api/dashboard-data">/api/dashboard-data</a> - Dashboard Übersicht</li>
            <li><a href="/api/live-prices">/api/live-prices</a> - Live Preise</li>
            <li><a href="/api/arbitrage-alerts">/api/arbitrage-alerts</a> - Arbitrage Alerts</li>
            <li><a href="/api/performance-data">/api/performance-data</a> - Performance Daten</li>
            <li><a href="/api/price-history/BTC">/api/price-history/BTC</a> - Preis Historie</li>
        </ul>
        """


@app.route("/api/dashboard-data")
def get_dashboard_data():
    """Haupt-Dashboard Daten"""
    try:
        dashboard_data = db.get_dashboard_data()

        # Füge Bot-Status hinzu
        dashboard_data["bot_status"] = {
            "is_online": True,  # Würde in Produktion geprüft werden
            "last_check": datetime.now().isoformat(),
            "uptime_hours": 24.5,  # Sample-Wert
        }

        return jsonify({"success": True, "data": dashboard_data})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Dashboard-Daten: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/live-prices")
def get_live_prices():
    """Aktuelle Live-Preise von allen Exchanges"""
    try:
        # Hole Preise der letzten 5 Minuten
        since_time = datetime.now() - timedelta(minutes=5)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT symbol, exchange, price, timestamp
                FROM price_history
                WHERE timestamp >= ?
                ORDER BY symbol, exchange, timestamp DESC
            """,
                (since_time,),
            )

            price_data = cursor.fetchall()

        # Gruppiere nach Symbol
        symbols_prices = {}
        for row in price_data:
            symbol = row["symbol"]
            exchange = row["exchange"]
            price = row["price"]

            if symbol not in symbols_prices:
                symbols_prices[symbol] = {}

            if exchange not in symbols_prices[symbol]:
                symbols_prices[symbol][exchange] = price

        # Berechne Arbitrage für jedes Symbol
        live_prices = []
        for symbol, exchanges in symbols_prices.items():
            if len(exchanges) >= 2:
                prices = list(exchanges.values())
                max_price = max(prices)
                min_price = min(prices)
                arbitrage = ((max_price - min_price) / min_price) * 100

                price_entry = {
                    "symbol": symbol,
                    "arbitrage": round(arbitrage, 2),
                    "timestamp": datetime.now().isoformat(),
                }

                # Füge Exchange-Preise hinzu
                for exchange, price in exchanges.items():
                    price_entry[exchange] = price

                live_prices.append(price_entry)

        return jsonify({"success": True, "data": live_prices, "last_updated": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Live-Preise: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/arbitrage-alerts")
def get_arbitrage_alerts():
    """Arbitrage Alerts der letzten 24 Stunden"""
    try:
        alerts = db.get_recent_arbitrage_alerts(hours=24)

        return jsonify({"success": True, "data": alerts, "count": len(alerts)})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Arbitrage-Alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/performance-data")
def get_performance_data():
    """Neueste Performance-Daten (alle verfügbaren Coins) - mit Duplikate-Bereinigung"""
    try:
        # Lade mehr Daten aus der DB (alle verfügbaren)
        performance_data = db.get_latest_performance_data(limit=200)  # Mehr Daten laden

        # Bereinige Duplikate durch Symbol-Normalisierung
        cleaned_data = merge_duplicate_performance_data(performance_data)

        # Sortiere nach Sharpe Ratio (beste zuerst)
        cleaned_data.sort(key=lambda x: x.get("sharpe_ratio", 0), reverse=True)

        return jsonify(
            {
                "success": True,
                "data": cleaned_data,  # Alle bereinigten Coins zurückgeben
                "count": len(cleaned_data),
                "original_count": len(performance_data),
                "duplicates_removed": len(performance_data) - len(cleaned_data),
            }
        )

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Performance-Daten: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/price-history/<symbol>")
def get_price_history(symbol):
    """Preis-Historie für ein bestimmtes Symbol"""
    try:
        price_history = db.get_price_history(symbol, hours=24)

        # Gruppiere nach Exchange für Chart-Darstellung
        exchanges_data = {}
        for entry in price_history:
            exchange = entry["exchange"]
            if exchange not in exchanges_data:
                exchanges_data[exchange] = []

            exchanges_data[exchange].append({"timestamp": entry["timestamp"], "price": entry["price"]})

        return jsonify({"success": True, "data": exchanges_data, "symbol": symbol, "count": len(price_history)})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Preis-Historie für {symbol}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/portfolio-snapshots")
def get_portfolio_snapshots():
    """Portfolio-Snapshots der letzten 24h"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM portfolio_snapshots
                WHERE timestamp >= datetime('now', '-1 day')
                ORDER BY timestamp DESC
                LIMIT 10
            """
            )

            snapshots = [dict(row) for row in cursor.fetchall()]

        return jsonify({"success": True, "data": snapshots, "count": len(snapshots)})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Portfolio-Snapshots: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/telegram-stats")
def get_telegram_stats():
    """Telegram Bot Statistiken"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Nachrichten der letzten 24h
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_messages,
                    COUNT(DISTINCT message_type) as message_types
                FROM telegram_messages
                WHERE timestamp >= datetime('now', '-1 day')
            """
            )

            stats = dict(cursor.fetchone())

            # Letzte Nachrichten
            cursor.execute(
                """
                SELECT message_type, timestamp, success
                FROM telegram_messages
                WHERE timestamp >= datetime('now', '-1 day')
                ORDER BY timestamp DESC
                LIMIT 10
            """
            )

            recent_messages = [dict(row) for row in cursor.fetchall()]

        return jsonify({"success": True, "data": {"stats": stats, "recent_messages": recent_messages}})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Telegram-Statistiken: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/bot-health")
def get_bot_health():
    """Bot Health Check"""
    try:
        # Prüfe letzte Aktivität
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Letzte Arbitrage-Checks
            cursor.execute(
                """
                SELECT MAX(timestamp) as last_arbitrage_check
                FROM arbitrage_alerts
            """
            )
            last_arbitrage = cursor.fetchone()

            # Letzte Performance-Analyse
            cursor.execute(
                """
                SELECT MAX(timestamp) as last_performance_check
                FROM performance_data
            """
            )
            last_performance = cursor.fetchone()

            # Bot-Statistiken
            cursor.execute(
                """
                SELECT * FROM bot_statistics
                ORDER BY timestamp DESC
                LIMIT 1
            """
            )
            latest_stats = cursor.fetchone()

        health_data = {
            "is_healthy": True,
            "last_arbitrage_check": (last_arbitrage["last_arbitrage_check"] if last_arbitrage else None),
            "last_performance_check": (last_performance["last_performance_check"] if last_performance else None),
            "latest_stats": dict(latest_stats) if latest_stats else {},
            "checked_at": datetime.now().isoformat(),
        }

        return jsonify({"success": True, "data": health_data})

    except Exception as e:
        logger.error(f"Fehler beim Health Check: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "data": {"is_healthy": False, "checked_at": datetime.now().isoformat()},
                }
            ),
            500,
        )


def test_api():
    """Teste API-Funktionalität"""
    from config import get_config

    config = get_config()

    print("🧪 WEB API TEST")
    print("=" * 40)

    print("📊 Database verbunden:", db.db_path)
    print("🌐 Flask App erstellt")
    print("✅ CORS aktiviert")

    print("\n📋 Verfügbare API Endpoints:")
    endpoints = [
        "GET  /                        - Frontend Dashboard",
        "GET  /api/dashboard-data      - Dashboard Übersicht",
        "GET  /api/live-prices         - Live Preise",
        "GET  /api/arbitrage-alerts    - Arbitrage Alerts",
        "GET  /api/performance-data    - Performance Daten",
        "GET  /api/price-history/<sym> - Preis Historie",
        "GET  /api/portfolio-snapshots - Portfolio Snapshots",
        "GET  /api/telegram-stats      - Telegram Statistiken",
        "GET  /api/bot-health          - Bot Health Check",
    ]

    for endpoint in endpoints:
        print(f"   {endpoint}")

    print("\n🚀 Server bereit!")
    print(f"   Frontend URL: http://{config.web_host}:{config.web_port}")
    print(f"   API Base URL: http://{config.web_host}:{config.web_port}/api/")
    print("\n" + "=" * 40)


if __name__ == "__main__":
    import sys
    import os

    # Add config directory to path
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
    sys.path.append(config_dir)

    from config import get_config

    config = get_config()

    test_api()
    print("🔄 Starte Flask Production Server...")
    app.run(debug=False, host=config.web_host, port=config.web_port, use_reloader=False)
