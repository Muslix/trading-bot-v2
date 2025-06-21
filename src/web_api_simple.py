"""
Simple Web API Server for Crypto Trading Bot Dashboard
Simplified version that works without complex plugin architecture
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import random

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/web_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SimpleWebAPI:
    """Simple Web API without complex plugin architecture"""
    
    def __init__(self, host='0.0.0.0', port=5000, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.logger = logging.getLogger('simple_web_api')
        self.start_time = datetime.now()
        
        # State management for consistent data
        self.persistent_data = {
            'total_alerts_24h': random.randint(25, 45),
            'all_alerts': [],
            'alert_counter': 0,
            'last_update': time.time()
        }
        
        # Sample data for testing - Extended coin list for realistic analysis
        self.sample_coins = [
            'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'SOL', 'AVAX', 'MATIC', 'LINK', 'UNI',
            'LTC', 'BCH', 'XLM', 'VET', 'ICP', 'FIL', 'TRX', 'ETC', 'THETA', 'AAVE',
            'ATOM', 'XRP', 'DOGE', 'SHIB', 'APE', 'SAND', 'MANA', 'CRV', 'SUSHI', 'COMP',
            'YFI', 'MKR', 'SNX', 'BAL', 'KNC', 'ZRX', 'ALGO', 'XTZ', 'NEAR', 'LUNA',
            'FTM', 'ONE', 'HBAR', 'EOS', 'FLOW', 'ICP', 'EGLD', 'KAVA', 'ROSE', 'RUNE',
            'AXS', 'ENJ', 'CHZ', 'BAT', 'ZIL', 'IOST', 'RVN', 'WAVES', 'NEO', 'QTUM',
            'ONT', 'ZEC', 'DASH', 'DCR', 'DGB', 'SC', 'REP', 'GNT', 'STORJ', 'STEEM'
        ]
        
        self.setup_routes()
        self.setup_websocket()
        
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.route('/')
        def index():
            """Serve the frontend HTML"""
            frontend_path = os.path.join(project_root, 'frontend')
            return send_from_directory(frontend_path, 'index.html')
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': str(datetime.now() - self.start_time)
            })
        
        @self.app.route('/api/dashboard-data')
        def dashboard_data():
            """Get dashboard data"""
            try:
                data = {
                    'success': True,
                    'data': {
                        'arbitrage': {
                            'total_alerts': self.persistent_data['total_alerts_24h'],
                            'avg_profit': random.uniform(1.8, 3.2),
                            'max_profit': random.uniform(6.0, 15.0)
                        },
                        'performance': {
                            'total_coins': len(self.sample_coins),
                            'avg_sharpe': random.uniform(0.8, 1.5),
                            'max_sharpe': random.uniform(1.5, 2.5)
                        },
                        'telegram': {
                            'total_messages': random.randint(50, 150),
                            'successful_messages': random.randint(45, 145)
                        },
                        'bot_status': {
                            'is_online': True,
                            'connected_clients': random.randint(1, 5)
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(data)
            except Exception as e:
                self.logger.error(f"Error in dashboard-data: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/live-prices')
        def live_prices():
            """Get live prices with arbitrage opportunities"""
            try:
                prices = []
                exchanges = ['binance', 'coinbase', 'kraken']
                
                # Generate more realistic data for more coins
                for coin in self.sample_coins[:25]:  # Show 25 coins instead of 15
                    symbol = f"{coin}/USDT"
                    base_price = self.get_base_price(coin)
                    
                    coin_data = {'symbol': symbol}
                    exchange_prices = []
                    
                    for exchange in exchanges:
                        # Add small variations for each exchange
                        variation = random.uniform(-0.02, 0.02)  # ±2% variation
                        price = base_price * (1 + variation)
                        coin_data[exchange] = round(price, 2 if price > 1 else 6)
                        exchange_prices.append(price)
                    
                    # Calculate arbitrage opportunity
                    if len(exchange_prices) >= 2:
                        max_price = max(exchange_prices)
                        min_price = min(exchange_prices)
                        arbitrage = ((max_price - min_price) / min_price) * 100
                        coin_data['arbitrage'] = round(arbitrage, 2)
                    else:
                        coin_data['arbitrage'] = 0.0
                    
                    prices.append(coin_data)
                
                return jsonify({
                    'success': True,
                    'data': prices,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in live-prices: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/arbitrage-alerts')
        def arbitrage_alerts():
            """Get recent arbitrage alerts"""
            try:
                # Initialize alerts if empty
                if not self.persistent_data['all_alerts']:
                    alerts = []
                    for i in range(15):
                        alert = {
                            'id': int(time.time() * 1000) + i,
                            'timestamp': (datetime.now() - timedelta(hours=random.randint(0, 23))).isoformat(),
                            'symbol': f"{random.choice(self.sample_coins[:20])}/USDT",
                            'buy_exchange': random.choice(['binance', 'coinbase', 'kraken']),
                            'sell_exchange': random.choice(['binance', 'coinbase', 'kraken']),
                            'profit_percentage': random.uniform(1.0, 6.0)
                        }
                        alerts.append(alert)
                    
                    self.persistent_data['all_alerts'] = alerts
                
                alerts = self.persistent_data['all_alerts']
                
                # Sort by timestamp (newest first)
                alerts.sort(key=lambda x: x['timestamp'], reverse=True)
                
                return jsonify({
                    'success': True,
                    'data': alerts,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in arbitrage-alerts: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/performance-data')
        def performance_data():
            """Get performance data for all coins"""
            try:
                performance_data = []
                
                for coin in self.sample_coins:
                    data = {
                        'symbol': coin,
                        'sharpe_ratio': random.uniform(-0.5, 2.5),
                        'annual_return': random.uniform(-30.0, 200.0),
                        'current_price': self.get_base_price(coin),
                        'timestamp': datetime.now().isoformat()
                    }
                    performance_data.append(data)
                
                # Sort by Sharpe ratio (best first)
                performance_data.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
                
                return jsonify({
                    'success': True,
                    'data': performance_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"Error in performance-data: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Placeholder endpoints for other features
        @self.app.route('/api/defi/pools', methods=['POST'])
        def defi_pools():
            try:
                data = request.get_json()
                token_pair = data.get('token_pair', 'ETH/USDC')
                protocols = data.get('protocols', ['uniswap_v3'])
                
                pools = []
                protocol_names = {
                    'uniswap_v3': 'Uniswap V3',
                    'curve': 'Curve Finance', 
                    'sushiswap': 'SushiSwap'
                }
                
                for protocol in protocols:
                    if protocol in protocol_names:
                        pool = {
                            'protocol': protocol_names[protocol],
                            'address': '0x' + ''.join(random.choices('0123456789abcdef', k=40)),
                            'tvl': random.randint(1000000, 50000000),
                            'apy': random.uniform(5.0, 25.0),
                            'volume_24h': random.randint(100000, 5000000),
                            'fee_tier': '0.3' if protocol == 'uniswap_v3' else ('0.04' if protocol == 'curve' else '0.25')
                        }
                        pools.append(pool)
                
                return jsonify({
                    'success': True,
                    'pools': pools,
                    'token_pair': token_pair
                })
                
            except Exception as e:
                self.logger.error(f"Error in defi_pools: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/ai/sentiment', methods=['POST'])
        def ai_sentiment():
            sentiments = ['positive', 'negative', 'neutral']
            return jsonify({
                'sentiment': random.choice(sentiments),
                'confidence': random.uniform(0.6, 0.95),
                'keywords': ['crypto', 'trading', 'market']
            })
        
        @self.app.route('/api/ai/predict', methods=['POST'])
        def ai_predict():
            data = request.get_json()
            symbol = data.get('symbol', 'BTC')
            current_price = self.get_base_price(symbol.replace('/USDT', ''))
            change = random.uniform(-10.0, 10.0)
            
            return jsonify({
                'predicted_price': current_price * (1 + change/100),
                'change_percentage': change,
                'confidence': random.uniform(0.7, 0.9)
            })
        
        @self.app.route('/api/strategies/list')
        def strategies_list():
            return jsonify({'strategies': []})
        
        @self.app.route('/api/strategies/platform-stats')
        def strategies_stats():
            return jsonify({
                'total_strategies': 0,
                'active_users': 0,
                'avg_return': 0,
                'success_rate': 0
            })
        
        @self.app.route('/api/notifications/send', methods=['POST'])
        def send_notification():
            return jsonify({
                'success': True,
                'message': 'Test notification sent successfully'
            })
    
    def get_base_price(self, coin: str) -> float:
        """Get realistic base price for coin"""
        price_map = {
            'BTC': 108650.0,
            'ETH': 2658.0,
            'BNB': 658.0,
            'ADA': 0.65,
            'DOT': 3.98,
            'SOL': 157.27,
            'AVAX': 25.5,
            'MATIC': 0.85,
            'LINK': 12.4,
            'UNI': 8.2,
            'LTC': 95.0,
            'BCH': 385.0,
            'XLM': 0.12,
            'VET': 0.025,
            'ICP': 12.8,
            'FIL': 5.2,
            'TRX': 0.068,
            'ETC': 18.5,
            'THETA': 1.45,
            'AAVE': 288.0,
            'ATOM': 8.5, 'XRP': 0.52, 'DOGE': 0.08, 'SHIB': 0.000009, 'APE': 1.1,
            'SAND': 0.35, 'MANA': 0.42, 'CRV': 0.72, 'SUSHI': 0.89, 'COMP': 45.2,
            'YFI': 8650.0, 'MKR': 1450.0, 'SNX': 2.1, 'BAL': 8.4, 'KNC': 0.65,
            'ZRX': 0.38, 'ALGO': 0.15, 'XTZ': 0.75, 'NEAR': 1.85, 'LUNA': 0.45,
            'FTM': 0.22, 'ONE': 0.012, 'HBAR': 0.055, 'EOS': 0.58, 'FLOW': 0.68,
            'EGLD': 35.5, 'KAVA': 0.88, 'ROSE': 0.045, 'RUNE': 1.55, 'AXS': 5.2,
            'ENJ': 0.18, 'CHZ': 0.065, 'BAT': 0.19, 'ZIL': 0.018, 'IOST': 0.0065,
            'RVN': 0.018, 'WAVES': 1.45, 'NEO': 8.9, 'QTUM': 2.45, 'ONT': 0.15,
            'ZEC': 28.5, 'DASH': 35.2, 'DCR': 12.8, 'DGB': 0.0078, 'SC': 0.0028,
            'REP': 8.5, 'GNT': 0.12, 'STORJ': 0.32, 'STEEM': 0.18
        }
        return price_map.get(coin, random.uniform(0.01, 50.0))
    
    def get_connected_clients_count(self) -> int:
        """Get number of connected WebSocket clients"""
        try:
            if hasattr(self.socketio, 'server') and hasattr(self.socketio.server, 'manager'):
                rooms = self.socketio.server.manager.rooms
                if '/' in rooms:
                    return len(rooms['/'])
            return 0
        except Exception:
            return 0
    
    def setup_websocket(self):
        """Setup WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            self.logger.info(f"Client connected: {request.sid}")
            emit('status', {'clients': len(self.socketio.server.manager.rooms.get('/', {}).keys())})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.logger.info(f"Client disconnected: {request.sid}")
        
        # Start background task for live updates
        def background_updates():
            while True:
                try:
                    time.sleep(3)  # Update every 3 seconds
                    
                    # Generate fresh live prices
                    live_prices = []
                    exchanges = ['binance', 'coinbase', 'kraken']
                    
                    for coin in self.sample_coins[:8]:  # Update top 8 coins
                        symbol = f"{coin}/USDT"
                        base_price = self.get_base_price(coin)
                        
                        coin_data = {'symbol': symbol}
                        exchange_prices = []
                        
                        for exchange in exchanges:
                            variation = random.uniform(-0.015, 0.015)  # ±1.5% variation
                            price = base_price * (1 + variation)
                            coin_data[exchange] = round(price, 2 if price > 1 else 6)
                            exchange_prices.append(price)
                        
                        # Calculate arbitrage
                        if len(exchange_prices) >= 2:
                            max_price = max(exchange_prices)
                            min_price = min(exchange_prices)
                            arbitrage = ((max_price - min_price) / min_price) * 100
                            coin_data['arbitrage'] = round(arbitrage, 2)
                        else:
                            coin_data['arbitrage'] = 0.0
                        
                        live_prices.append(coin_data)
                    
                    # Only update alerts every 4th cycle (every 12 seconds) to avoid spam
                    alerts = None
                    if not hasattr(self, '_alert_counter'):
                        self._alert_counter = 0
                    
                    self._alert_counter += 1
                    if self._alert_counter % 4 == 0:  # Only every 12 seconds
                        alerts = []
                        
                        # Add 1-2 new alerts and increment total count slowly
                        num_new_alerts = random.choice([1, 2])
                        for i in range(num_new_alerts):
                            alert = {
                                'id': int(time.time() * 1000) + i,
                                'timestamp': datetime.now().isoformat(),
                                'symbol': f"{random.choice(self.sample_coins[:15])}/USDT",
                                'buy_exchange': random.choice(exchanges),
                                'sell_exchange': random.choice(exchanges),
                                'profit_percentage': random.uniform(1.2, 4.5)
                            }
                            alerts.append(alert)
                            
                            # Add to persistent storage and limit to 20
                            self.persistent_data['all_alerts'].insert(0, alert)
                            self.persistent_data['all_alerts'] = self.persistent_data['all_alerts'][:20]
                        
                        # Slowly increment total alerts count (simulate gradual growth)
                        if random.random() < 0.6:  # 60% chance to increment
                            self.persistent_data['total_alerts_24h'] += num_new_alerts
                    
                    # Send comprehensive live update
                    live_data = {
                        'timestamp': datetime.now().isoformat(),
                        'data': {
                            'dashboard': {
                                'arbitrage': {
                                    'total_alerts': self.persistent_data['total_alerts_24h'],
                                    'avg_profit': random.uniform(1.8, 3.2),
                                    'max_profit': random.uniform(6.0, 12.0)
                                },
                                'performance': {
                                    'total_coins': len(self.sample_coins),
                                    'avg_sharpe': random.uniform(0.9, 1.6),
                                    'max_sharpe': random.uniform(1.8, 2.8)
                                },
                                'bot_status': {
                                    'is_online': True,
                                    'connected_clients': self.get_connected_clients_count()
                                }
                            },
                            'live_prices': live_prices
                        }
                    }
                    
                    # Add alerts only when they exist
                    if alerts is not None:
                        live_data['data']['alerts'] = alerts
                    
                    self.socketio.emit('live_update', live_data)
                    self.logger.debug(f"Live update sent at {live_data['timestamp']}")
                    
                except Exception as e:
                    self.logger.error(f"Error in background updates: {e}")
        
        # Start background thread
        bg_thread = threading.Thread(target=background_updates, daemon=True)
        bg_thread.start()
        self.logger.info("🔄 Background live updates started")
    
    def run(self):
        """Run the web API server"""
        try:
            self.logger.info(f"🌐 Starting Simple Web API server on {self.host}:{self.port}")
            
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error running Web API server: {e}")


if __name__ == "__main__":
    try:
        web_api = SimpleWebAPI(
            host='0.0.0.0',
            port=5000,
            debug=False
        )
        web_api.run()
    except KeyboardInterrupt:
        logger.info("👋 Web API stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")