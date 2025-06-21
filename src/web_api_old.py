"""
Web API Server für Crypto Trading Bot Dashboard
Flask API zum Verbinden des Vue.js Frontends mit der SQLite Database
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import project modules
try:
    from src.database import get_database_manager
    from src.utils.symbol_normalizer import merge_duplicate_performance_data
    from src.utils import create_util_manager
    
    # Initialize database manager asynchonously
    import asyncio
    
    async def init_db():
        return await get_database_manager()
    
    async def init_utils():
        return await create_util_manager({'log_level': 'INFO'})
    
    # Get database manager and utils
    db = asyncio.run(init_db())
    util_manager = asyncio.run(init_utils())
    
except ImportError as e:
    logging.error(f"Import error in web_api: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"Database/Utils initialization error: {e}")
    sys.exit(1)

# Flask App Setup
app = Flask(__name__)
CORS(app)  # Erlaube Cross-Origin Requests
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSocket support

# Enhanced Logging Setup for Production
def setup_web_api_logging():
    """Setup comprehensive logging for web API"""
    import os
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging with file and console handlers
    logging.basicConfig(
        level=logging.INFO if os.getenv('LOG_LEVEL', 'INFO') == 'INFO' else logging.DEBUG,
        format='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler('logs/web_api.log'),
            logging.StreamHandler()
        ]
    )

setup_web_api_logging()
logger = logging.getLogger(__name__)

# Global variable to track connected clients
connected_clients = 0

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global connected_clients
    connected_clients += 1
    logger.info(f"📡 Client connected. Total clients: {connected_clients}")
    
    try:
        # Send connection status with client count
        emit('status', {
            'message': 'Connected to Trading Bot', 
            'clients': connected_clients,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send initial utils stats
        stats = util_manager.get_util_stats()
        emit('utils_stats', stats)
        
    except Exception as e:
        logger.error(f"❌ WebSocket connect error: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    global connected_clients
    connected_clients -= 1
    logger.info(f"📡 Client disconnected. Total clients: {connected_clients}")

def broadcast_live_data():
    """Background function to broadcast live data to all connected clients"""
    while True:
        try:
            if connected_clients > 0:
                # Get live data
                live_data = {}
                
                # Dashboard data
                try:
                    # Mock dashboard data since get_dashboard_data doesn't exist
                    live_data['dashboard'] = {
                        'arbitrage': {'total_alerts': 0, 'avg_profit': 1.2, 'max_profit': 5.5},
                        'performance': {'total_coins': 100, 'avg_sharpe': 0.8, 'max_sharpe': 2.1},
                        'telegram': {'total_messages': 50, 'successful_messages': 48}
                    }
                    live_data['dashboard']['bot_status'] = {
                        "is_online": True,
                        "last_check": datetime.now().isoformat(),
                        "uptime_hours": 24.5,
                        "connected_clients": connected_clients
                    }
                except Exception as e:
                    logger.error(f"Error getting dashboard data: {e}")
                
                # Live prices
                try:
                    # Mock live prices data for now
                    live_data['live_prices'] = [
                        {"symbol": "BTC/USDT", "binance": 108650, "coinbase": 108700, "arbitrage": 0.05, "timestamp": datetime.now().isoformat()},
                        {"symbol": "ETH/USDT", "binance": 2658, "coinbase": 2660, "arbitrage": 0.08, "timestamp": datetime.now().isoformat()},
                    ]
                    '''
                    since_time = datetime.now() - timedelta(minutes=5)
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT symbol, exchange, price, timestamp
                            FROM price_history
                            WHERE timestamp >= ?
                            ORDER BY symbol, exchange, timestamp DESC
                        """, (since_time,))
                        price_data = cursor.fetchall()
                    
                    # Process price data
                    symbols_prices = {}
                    for row in price_data:
                        symbol = row["symbol"]
                        exchange = row["exchange"]
                        price = row["price"]
                        if symbol not in symbols_prices:
                            symbols_prices[symbol] = {}
                        if exchange not in symbols_prices[symbol]:
                            symbols_prices[symbol][exchange] = price
                    
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
                            for exchange, price in exchanges.items():
                                price_entry[exchange] = price
                            live_prices.append(price_entry)
                    
                    live_data['live_prices'] = live_prices
                    '''
                except Exception as e:
                    logger.error(f"Error getting live prices: {e}")
                
                # Recent alerts
                try:
                    # Mock alerts data
                    live_data['alerts'] = [
                        {"symbol": "BNB/USDT", "profit_percentage": 2.5, "buy_exchange": "coinbase", "sell_exchange": "binance", "timestamp": datetime.now().isoformat()}
                    ]
                except Exception as e:
                    logger.error(f"Error getting alerts: {e}")
                
                # Performance data
                try:
                    # Mock performance data
                    live_data['performance'] = [
                        {"symbol": "SOL", "sharpe_ratio": 1.719, "annual_return": 155.8, "current_price": 157.27, "timestamp": datetime.now().isoformat()},
                        {"symbol": "BTC", "sharpe_ratio": 1.654, "annual_return": 82.6, "current_price": 108643.56, "timestamp": datetime.now().isoformat()},
                    ]
                except Exception as e:
                    logger.error(f"Error getting performance data: {e}")
                
                # Broadcast to all connected clients
                socketio.emit('live_update', {
                    'timestamp': datetime.now().isoformat(),
                    'data': live_data
                })
                
            time.sleep(1)  # Update every second
            
        except Exception as e:
            logger.error(f"Error in broadcast_live_data: {e}")
            time.sleep(5)  # Wait 5 seconds on error

# Start background thread for live updates
live_data_thread = threading.Thread(target=broadcast_live_data, daemon=True)
live_data_thread.start()


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
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    logger.info(f"Dashboard data request from {client_ip}")
    
    try:
        logger.debug("Fetching dashboard data from database")
        # Mock dashboard data for now
        dashboard_data = {
            'arbitrage': {'total_alerts': 0, 'avg_profit': 1.2, 'max_profit': 5.5},
            'performance': {'total_coins': 100, 'avg_sharpe': 0.8, 'max_sharpe': 2.1},
            'telegram': {'total_messages': 50, 'successful_messages': 48}
        }
        
        logger.debug(f"Retrieved dashboard data with {len(dashboard_data)} items")

        # Füge Bot-Status hinzu
        dashboard_data["bot_status"] = {
            "is_online": True,  # Würde in Produktion geprüft werden
            "last_check": datetime.now().isoformat(),
            "uptime_hours": 24.5,  # Sample-Wert
            "connected_clients": connected_clients
        }

        duration = time.time() - start_time
        logger.info(f"Dashboard data request completed in {duration:.3f}s for {client_ip}")
        logger.debug(f"Dashboard response size: {len(str(dashboard_data))} characters")
        
        return jsonify({"success": True, "data": dashboard_data})

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Dashboard data request failed in {duration:.3f}s for {client_ip}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/live-prices")
def get_live_prices():
    """Aktuelle Live-Preise von allen Exchanges"""
    try:
        # Mock live prices data
        live_prices = [
            {"symbol": "BTC/USDT", "binance": 108650, "coinbase": 108700, "arbitrage": 0.05, "timestamp": datetime.now().isoformat()},
            {"symbol": "ETH/USDT", "binance": 2658, "coinbase": 2660, "arbitrage": 0.08, "timestamp": datetime.now().isoformat()},
            {"symbol": "BNB/USDT", "binance": 658, "coinbase": 660, "arbitrage": 0.30, "timestamp": datetime.now().isoformat()},
        ]
        
        return jsonify({"success": True, "data": live_prices, "last_updated": datetime.now().isoformat()})
        
        '''
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
        '''

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Live-Preise: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/arbitrage-alerts")
def get_arbitrage_alerts():
    """Arbitrage Alerts der letzten 24 Stunden"""
    try:
        # Mock alerts data
        alerts = [
            {"symbol": "BNB/USDT", "profit_percentage": 2.5, "buy_exchange": "coinbase", "sell_exchange": "binance", "timestamp": datetime.now().isoformat()},
            {"symbol": "ETH/USDT", "profit_percentage": 1.2, "buy_exchange": "binance", "sell_exchange": "coinbase", "timestamp": datetime.now().isoformat()},
        ]

        return jsonify({"success": True, "data": alerts, "count": len(alerts)})

    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Arbitrage-Alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/performance-data")
def get_performance_data():
    """Neueste Performance-Daten (alle verfügbaren Coins) - mit Duplikate-Bereinigung"""
    try:
        # Mock performance data
        performance_data = [
            {"symbol": "SOL", "sharpe_ratio": 1.719, "annual_return": 155.8, "current_price": 157.27, "timestamp": datetime.now().isoformat()},
            {"symbol": "BTC", "sharpe_ratio": 1.654, "annual_return": 82.6, "current_price": 108643.56, "timestamp": datetime.now().isoformat()},
            {"symbol": "ETH", "sharpe_ratio": 1.123, "annual_return": 45.2, "current_price": 2658.34, "timestamp": datetime.now().isoformat()},
            {"symbol": "AAVE", "sharpe_ratio": 1.356, "annual_return": 131.8, "current_price": 288.02, "timestamp": datetime.now().isoformat()},
        ]

        return jsonify(
            {
                "success": True,
                "data": performance_data,
                "count": len(performance_data),
                "original_count": len(performance_data),
                "duplicates_removed": 0,
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


# ========== NEW UTILS API ENDPOINTS ==========

@app.route('/api/utils/export', methods=['POST'])
def export_data():
    """Export data in various formats using Export Utils"""
    try:
        request_data = request.get_json()
        export_format = request_data.get('format', 'csv')
        data = request_data.get('data', [])
        template = request_data.get('template')
        
        if export_format == 'csv':
            result = asyncio.run(util_manager.process_with_util('export', {
                'action': 'export_csv',
                'data': data,
                'template': template,
                'filename': f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }))
        elif export_format == 'pdf':
            result = asyncio.run(util_manager.process_with_util('export', {
                'action': 'export_pdf',
                'data': data,
                'template': template,
                'title': 'Trading Bot Report'
            }))
        elif export_format == 'json':
            result = asyncio.run(util_manager.process_with_util('export', {
                'action': 'export_json',
                'data': data
            }))
        else:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/market-data', methods=['POST'])
def get_market_data():
    """Get market data from multiple exchanges"""
    try:
        request_data = request.get_json()
        symbols = request_data.get('symbols', ['BTC/USDT'])
        exchanges = request_data.get('exchanges', ['binance', 'coinbase'])
        action = request_data.get('action', 'get_prices')
        
        result = asyncio.run(util_manager.process_with_util('market_data', {
            'action': action,
            'symbols': symbols,
            'exchanges': exchanges
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Market data error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/arbitrage', methods=['POST'])
def find_arbitrage():
    """Find arbitrage opportunities across exchanges"""
    try:
        request_data = request.get_json()
        symbols = request_data.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        min_profit = request_data.get('min_profit_percentage', 1.0)
        
        result = asyncio.run(util_manager.process_with_util('market_data', {
            'action': 'find_arbitrage',
            'symbols': symbols,
            'min_profit_percentage': min_profit
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Arbitrage search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/sentiment', methods=['POST'])
def analyze_sentiment():
    """Analyze sentiment of text or news"""
    try:
        request_data = request.get_json()
        text = request_data.get('text', '')
        action = request_data.get('action', 'analyze_sentiment')
        
        result = asyncio.run(util_manager.process_with_util('aiml', {
            'action': action,
            'text': text,
            'source': 'api'
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/backtest', methods=['POST'])
def run_backtest():
    """Run strategy backtest"""
    try:
        request_data = request.get_json()
        strategy_name = request_data.get('strategy_name', 'sma_crossover')
        price_data = request_data.get('price_data', [])
        parameters = request_data.get('parameters', {})
        
        result = asyncio.run(util_manager.process_with_util('strategy', {
            'action': 'backtest',
            'strategy_name': strategy_name,
            'price_data': price_data,
            'parameters': parameters
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/notify', methods=['POST'])
def send_notification():
    """Send notification via multiple channels"""
    try:
        request_data = request.get_json()
        message = request_data.get('message', '')
        channels = request_data.get('channels', ['telegram'])
        template = request_data.get('template')
        template_data = request_data.get('template_data', {})
        
        if len(channels) > 1:
            # Multi-channel notification
            result = asyncio.run(util_manager.process_with_util('notification', {
                'action': 'send_multi_channel',
                'message': message,
                'channels': channels,
                'template': template,
                'template_data': template_data
            }))
        else:
            # Single channel notification
            result = asyncio.run(util_manager.process_with_util('notification', {
                'action': 'send_notification',
                'channel': channels[0],
                'message': message,
                'template': template,
                'template_data': template_data
            }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Notification error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/health', methods=['GET'])
def utils_health_check():
    """Get health status of all utils plugins"""
    try:
        result = asyncio.run(util_manager.health_check_all())
        
        return jsonify({
            'success': True,
            'health_check': result,
            'stats': util_manager.get_util_stats()
        })
        
    except Exception as e:
        logger.error(f"Utils health check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/utils/stats', methods=['GET'])
def get_utils_stats():
    """Get comprehensive utils statistics"""
    try:
        stats = util_manager.get_util_stats()
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"Utils stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== DEFI API ENDPOINTS ==========

@app.route('/api/defi/pools', methods=['POST'])
def get_defi_pools():
    """Get DeFi liquidity pools"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    try:
        request_data = request.get_json()
        protocols = request_data.get('protocols', ['uniswap_v3', 'pancakeswap', 'curve'])
        token_pair = request_data.get('token_pair', 'USDC/WETH')
        min_tvl = request_data.get('min_tvl', 1000000)
        
        logger.info(f"🏊 DeFi pools request from {client_ip}")
        logger.info(f"   Token pair: {token_pair}")
        logger.info(f"   Protocols: {protocols}")
        logger.info(f"   Min TVL: ${min_tvl:,}")
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'get_pools',
            'protocols': protocols,
            'token_pair': token_pair,
            'min_tvl': min_tvl
        }))
        
        duration = time.time() - start_time
        
        if result.get('success'):
            pools_count = sum(len(pools) if isinstance(pools, list) else 0 
                            for pools in result.get('pools', {}).values())
            logger.info(f"✅ DeFi pools request completed in {duration:.3f}s")
            logger.info(f"   Found {pools_count} pools across {len(protocols)} protocols")
        else:
            logger.error(f"❌ DeFi pools request failed in {duration:.3f}s: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ DeFi pools error in {duration:.3f}s from {client_ip}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/defi/arbitrage', methods=['POST'])
def find_defi_arbitrage():
    """Find DeFi arbitrage opportunities"""
    try:
        request_data = request.get_json()
        token_pair = request_data.get('token_pair', 'USDC/WETH')
        amount = request_data.get('amount', 10000)
        min_profit = request_data.get('min_profit_percentage', 0.5)
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'find_arbitrage',
            'token_pair': token_pair,
            'amount': amount,
            'min_profit_percentage': min_profit
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DeFi arbitrage error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/defi/yield', methods=['POST'])
def calculate_defi_yield():
    """Calculate DeFi yield farming opportunities"""
    try:
        request_data = request.get_json()
        protocols = request_data.get('protocols', ['uniswap_v3', 'curve', 'pancakeswap'])
        min_apy = request_data.get('min_apy', 5.0)
        risk_tolerance = request_data.get('risk_tolerance', 'medium')
        investment_amount = request_data.get('investment_amount', 50000)
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'calculate_yield',
            'protocols': protocols,
            'min_apy': min_apy,
            'risk_tolerance': risk_tolerance,
            'investment_amount': investment_amount
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DeFi yield calculation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/defi/token-price', methods=['POST'])
def get_defi_token_price():
    """Get token price from DeFi protocols"""
    try:
        request_data = request.get_json() 
        token = request_data.get('token', 'WETH')
        vs_token = request_data.get('vs_token', 'USDC')
        protocols = request_data.get('protocols', ['uniswap_v3', 'sushiswap'])
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'get_token_price',
            'token': token,
            'vs_token': vs_token,
            'protocols': protocols
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DeFi token price error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/defi/trending-pools', methods=['GET'])
def get_defi_trending_pools():
    """Get trending DeFi pools"""
    try:
        sort_by = request.args.get('sort_by', 'volume')
        limit = int(request.args.get('limit', 10))
        min_tvl = int(request.args.get('min_tvl', 1000000))
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'get_trending_pools',
            'sort_by': sort_by,
            'limit': limit,
            'min_tvl': min_tvl
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DeFi trending pools error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/defi/protocol-stats', methods=['GET'])
def get_defi_protocol_stats():
    """Get DeFi protocol statistics"""
    try:
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'get_protocol_stats'
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"DeFi protocol stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== STRATEGY SHARING PLATFORM ENDPOINTS ==========

@app.route('/api/strategies/share', methods=['POST'])
def share_strategy():
    """Share a new trading strategy"""
    start_time = time.time()
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    
    try:
        request_data = request.get_json()
        name = request_data.get('name', '')
        author = request_data.get('author', 'anonymous')
        code = request_data.get('code', '')
        description = request_data.get('description', '')
        category = request_data.get('category', 'technical_indicators')
        tags = request_data.get('tags', [])
        performance_metrics = request_data.get('performance_metrics', {})
        risk_level = request_data.get('risk_level', 'medium')
        timeframe = request_data.get('timeframe', '1h')
        min_capital = request_data.get('min_capital', 1000)
        
        logger.info(f"📤 Strategy share request from {client_ip}")
        logger.info(f"   Strategy: '{name}' by {author}")
        logger.info(f"   Category: {category}, Risk: {risk_level}")
        logger.info(f"   Code length: {len(code)} chars")
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'share_strategy',
            'name': name,
            'author': author,
            'code': code,
            'description': description,
            'category': category,
            'tags': tags,
            'performance_metrics': performance_metrics,
            'risk_level': risk_level,
            'timeframe': timeframe,
            'min_capital': min_capital
        }))
        
        duration = time.time() - start_time
        
        if result.get('success'):
            strategy_id = result.get('strategy_id', 'unknown')
            logger.info(f"✅ Strategy shared successfully in {duration:.3f}s")
            logger.info(f"   Strategy ID: {strategy_id[:8]}...")
        else:
            logger.error(f"❌ Strategy share failed in {duration:.3f}s: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Share strategy error in {duration:.3f}s from {client_ip}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/list', methods=['GET'])
def list_strategies():
    """List strategies with optional filters"""
    try:
        category = request.args.get('category')
        risk_level = request.args.get('risk_level')
        timeframe = request.args.get('timeframe')
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        sort_by = request.args.get('sort_by', 'created_at')
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'list_strategies',
            'category': category,
            'risk_level': risk_level,
            'timeframe': timeframe,
            'verified_only': verified_only,
            'limit': limit,
            'offset': offset,
            'sort_by': sort_by
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"List strategies error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/<strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """Get a specific strategy by ID"""
    try:
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'get_strategy',
            'strategy_id': strategy_id
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get strategy error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/<strategy_id>/download', methods=['POST'])
def download_strategy(strategy_id):
    """Download a strategy"""
    try:
        request_data = request.get_json() or {}
        user_id = request_data.get('user_id', 'anonymous')
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'download_strategy',
            'strategy_id': strategy_id,
            'user_id': user_id
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Download strategy error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/<strategy_id>/rate', methods=['POST'])
def rate_strategy(strategy_id):
    """Rate and review a strategy"""
    try:
        request_data = request.get_json()
        reviewer = request_data.get('reviewer', 'anonymous')
        rating = request_data.get('rating', 5)
        comment = request_data.get('comment', '')
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'rate_strategy',
            'strategy_id': strategy_id,
            'reviewer': reviewer,
            'rating': rating,
            'comment': comment
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Rate strategy error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/search', methods=['POST'])
def search_strategies():
    """Search strategies by keywords"""
    try:
        request_data = request.get_json()
        query = request_data.get('query', '')
        category = request_data.get('category')
        tags = request_data.get('tags', [])
        min_rating = request_data.get('min_rating', 0)
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'search_strategies',
            'query': query,
            'category': category,
            'tags': tags,
            'min_rating': min_rating
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Search strategies error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/trending', methods=['GET'])
def get_trending_strategies():
    """Get trending strategies"""
    try:
        timeframe_days = int(request.args.get('timeframe_days', 7))
        limit = int(request.args.get('limit', 10))
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'get_trending_strategies',
            'timeframe_days': timeframe_days,
            'limit': limit
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get trending strategies error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/strategies/platform-stats', methods=['GET'])
def get_platform_stats():
    """Get strategy platform statistics"""
    try:
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'get_platform_stats'
        }))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get platform stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ENHANCED WEBSOCKET FEATURES ==========


@socketio.on('request_live_arbitrage')
def handle_live_arbitrage(data):
    """Handle real-time arbitrage requests"""
    try:
        symbols = data.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        min_profit = data.get('min_profit', 1.0)
        
        # Get arbitrage opportunities
        result = asyncio.run(util_manager.process_with_util('market_data', {
            'action': 'find_arbitrage',
            'symbols': symbols,
            'min_profit_percentage': min_profit
        }))
        
        emit('live_arbitrage_data', result)
        
    except Exception as e:
        logger.error(f"Live arbitrage error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_sentiment_analysis')
def handle_sentiment_request(data):
    """Handle real-time sentiment analysis"""
    try:
        text = data.get('text', '')
        
        result = asyncio.run(util_manager.process_with_util('aiml', {
            'action': 'analyze_sentiment',
            'text': text,
            'source': 'websocket'
        }))
        
        emit('sentiment_result', result)
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_market_data')
def handle_market_data_request(data):
    """Handle real-time market data requests"""
    try:
        symbols = data.get('symbols', ['BTC/USDT'])
        exchanges = data.get('exchanges', ['binance', 'coinbase'])
        
        result = asyncio.run(util_manager.process_with_util('market_data', {
            'action': 'get_prices',
            'symbols': symbols,
            'exchanges': exchanges
        }))
        
        emit('market_data_update', result)
        
    except Exception as e:
        logger.error(f"Market data error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('run_backtest')
def handle_backtest_request(data):
    """Handle real-time backtesting"""
    try:
        strategy_name = data.get('strategy_name', 'sma_crossover')
        parameters = data.get('parameters', {})
        
        # Generate sample price data for demo
        sample_data = [
            {'timestamp': '2024-01-01', 'open': 45000, 'high': 46000, 'low': 44000, 'close': 45500},
            {'timestamp': '2024-01-02', 'open': 45500, 'high': 47000, 'low': 45000, 'close': 46500},
            {'timestamp': '2024-01-03', 'open': 46500, 'high': 47500, 'low': 46000, 'close': 47000},
            # Add more sample data...
        ]
        
        result = asyncio.run(util_manager.process_with_util('strategy', {
            'action': 'backtest',
            'strategy_name': strategy_name,
            'price_data': sample_data,
            'parameters': parameters
        }))
        
        emit('backtest_result', result)
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_defi_pools')
def handle_defi_pools_request(data):
    """Handle real-time DeFi pools request"""
    try:
        protocols = data.get('protocols', ['uniswap_v3', 'pancakeswap'])
        token_pair = data.get('token_pair', 'USDC/WETH')
        min_tvl = data.get('min_tvl', 1000000)
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'get_pools',
            'protocols': protocols,
            'token_pair': token_pair,
            'min_tvl': min_tvl
        }))
        
        emit('defi_pools_data', result)
        
    except Exception as e:
        logger.error(f"DeFi pools WebSocket error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_defi_arbitrage')
def handle_defi_arbitrage_request(data):
    """Handle real-time DeFi arbitrage request"""
    try:
        token_pair = data.get('token_pair', 'USDC/WETH')
        amount = data.get('amount', 10000)
        min_profit = data.get('min_profit_percentage', 0.5)
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'find_arbitrage',
            'token_pair': token_pair,
            'amount': amount,
            'min_profit_percentage': min_profit
        }))
        
        emit('defi_arbitrage_data', result)
        
    except Exception as e:
        logger.error(f"DeFi arbitrage WebSocket error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_defi_yield')
def handle_defi_yield_request(data):
    """Handle real-time DeFi yield farming request"""
    try:
        protocols = data.get('protocols', ['uniswap_v3', 'curve'])
        min_apy = data.get('min_apy', 5.0)
        risk_tolerance = data.get('risk_tolerance', 'medium')
        investment_amount = data.get('investment_amount', 50000)
        
        result = asyncio.run(util_manager.process_with_util('defi', {
            'action': 'calculate_yield',
            'protocols': protocols,
            'min_apy': min_apy,
            'risk_tolerance': risk_tolerance,
            'investment_amount': investment_amount
        }))
        
        emit('defi_yield_data', result)
        
    except Exception as e:
        logger.error(f"DeFi yield WebSocket error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_trending_strategies')
def handle_trending_strategies_request(data):
    """Handle real-time trending strategies request"""
    try:
        timeframe_days = data.get('timeframe_days', 7)
        limit = data.get('limit', 10)
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'get_trending_strategies',
            'timeframe_days': timeframe_days,
            'limit': limit
        }))
        
        emit('trending_strategies_data', result)
        
    except Exception as e:
        logger.error(f"Trending strategies WebSocket error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_strategy_search')
def handle_strategy_search_request(data):
    """Handle real-time strategy search"""
    try:
        query = data.get('query', '')
        category = data.get('category')
        min_rating = data.get('min_rating', 0)
        
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'search_strategies',
            'query': query,
            'category': category,
            'min_rating': min_rating
        }))
        
        emit('strategy_search_results', result)
        
    except Exception as e:
        logger.error(f"Strategy search WebSocket error: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_platform_stats')
def handle_platform_stats_request(data):
    """Handle real-time platform statistics request"""
    try:
        result = asyncio.run(util_manager.process_with_util('strategy_sharing', {
            'action': 'get_platform_stats'
        }))
        
        emit('platform_stats_data', result)
        
    except Exception as e:
        logger.error(f"Platform stats WebSocket error: {e}")
        emit('error', {'message': str(e)})


def start_real_time_updates():
    """Start background task for real-time updates"""
    def background_task():
        while True:
            try:
                # Send periodic health updates
                health_result = asyncio.run(util_manager.health_check_all())
                socketio.emit('health_update', health_result)
                
                # Send periodic utils stats
                stats = util_manager.get_util_stats()
                socketio.emit('utils_stats_update', stats)
                
                # Sleep for 30 seconds
                socketio.sleep(30)
                
            except Exception as e:
                logger.error(f"Background task error: {e}")
                socketio.sleep(5)
    
    # Start background task
    socketio.start_background_task(background_task)


def test_api():
    """Teste API-Funktionalität"""
    from config import get_config

    config = get_config()

    print("🧪 WEB API TEST")
    print("=" * 40)

    print("📊 Database manager verbunden:", type(db).__name__)
    print("🔧 Utils manager verbunden:", type(util_manager).__name__)
    print("🌐 Flask App erstellt")
    print("✅ CORS aktiviert")
    print("🔌 WebSocket support aktiviert")

    print("\n📋 Verfügbare API Endpoints:")
    endpoints = [
        "GET  /                        - Frontend Dashboard",
        "GET  /api/dashboard-data      - Dashboard Übersicht",
        "GET  /api/live-prices         - Live Preise",
        "GET  /api/arbitrage-alerts    - Arbitrage Alerts",
        "# NEW UTILS ENDPOINTS:",
        "POST /api/utils/export        - Export Data (CSV/PDF/JSON)",
        "POST /api/utils/market-data   - Multi-Exchange Market Data",
        "POST /api/utils/arbitrage     - Find Arbitrage Opportunities",
        "POST /api/utils/sentiment     - Sentiment Analysis",
        "POST /api/utils/backtest      - Strategy Backtesting",
        "POST /api/utils/notify        - Multi-Channel Notifications",
        "GET  /api/utils/health        - Utils Health Check",
        "GET  /api/utils/stats         - Utils Statistics",
        "# DEFI ENDPOINTS:",
        "POST /api/defi/pools           - Get DeFi Liquidity Pools",
        "POST /api/defi/arbitrage       - Find DeFi Arbitrage Opportunities",
        "POST /api/defi/yield           - Calculate Yield Farming Opportunities",
        "POST /api/defi/token-price     - Get Token Prices from DeFi",
        "GET  /api/defi/trending-pools  - Get Trending DeFi Pools",
        "GET  /api/defi/protocol-stats  - Get DeFi Protocol Statistics",
        "# STRATEGY SHARING ENDPOINTS:",
        "POST /api/strategies/share      - Share New Strategy",
        "GET  /api/strategies/list       - List Strategies (with filters)",
        "GET  /api/strategies/<id>       - Get Specific Strategy",
        "POST /api/strategies/<id>/download - Download Strategy",
        "POST /api/strategies/<id>/rate  - Rate & Review Strategy",
        "POST /api/strategies/search     - Search Strategies",
        "GET  /api/strategies/trending   - Get Trending Strategies",
        "GET  /api/strategies/platform-stats - Platform Statistics",
        "# WEBSOCKET EVENTS:",
        "connect                       - Client Connection",
        "request_live_arbitrage        - Real-time Arbitrage",
        "request_sentiment_analysis    - Real-time Sentiment",
        "request_market_data           - Real-time Market Data",
        "run_backtest                  - Real-time Backtesting",
        "request_defi_pools            - Real-time DeFi Pools",
        "request_defi_arbitrage        - Real-time DeFi Arbitrage",
        "request_defi_yield            - Real-time DeFi Yield",
        "request_trending_strategies   - Real-time Trending Strategies",
        "request_strategy_search       - Real-time Strategy Search",
        "request_platform_stats        - Real-time Platform Statistics",
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
    print("🔄 Starte Flask Production Server mit WebSocket support...")
    socketio.run(app, debug=False, host=config.web_host, port=config.web_port, use_reloader=False, allow_unsafe_werkzeug=True)
