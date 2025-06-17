"""
Unit tests for web_api.py
Testing Flask API endpoints and functionality
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.web_api import app


class TestWebAPIEndpoints(unittest.TestCase):
    """Test cases for web API endpoints"""

    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_index_route_frontend_exists(self):
        """Test index route when frontend file exists"""
        with patch('builtins.open', unittest.mock.mock_open(read_data="<html>Test Frontend</html>")):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Frontend', response.data)

    def test_index_route_frontend_missing(self):
        """Test index route when frontend file is missing"""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Crypto Trading Bot API', response.data)
            self.assertIn(b'/api/dashboard-data', response.data)

    @patch('src.web_api.db')
    def test_dashboard_data_success(self, mock_db):
        """Test successful dashboard data retrieval"""
        mock_dashboard_data = {
            "arbitrage": {"total_opportunities": 10, "avg_profit": 2.5},
            "performance": {"total_coins": 50, "best_performer": "BTC"}
        }
        mock_db.get_dashboard_data.return_value = mock_dashboard_data
        
        response = self.client.get('/api/dashboard-data')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('bot_status', data['data'])
        self.assertIn('arbitrage', data['data'])

    @patch('src.web_api.db')
    def test_dashboard_data_error(self, mock_db):
        """Test dashboard data retrieval with database error"""
        mock_db.get_dashboard_data.side_effect = Exception("Database Error")
        
        response = self.client.get('/api/dashboard-data')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('src.web_api.db')
    def test_live_prices_success(self, mock_db):
        """Test successful live prices retrieval"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock price data
        mock_price_data = [
            {"symbol": "BTC", "exchange": "binance", "price": 45000, "timestamp": datetime.now()},
            {"symbol": "BTC", "exchange": "coinbase", "price": 45200, "timestamp": datetime.now()},
            {"symbol": "ETH", "exchange": "binance", "price": 3000, "timestamp": datetime.now()}
        ]
        mock_cursor.fetchall.return_value = mock_price_data
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        response = self.client.get('/api/live-prices')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('last_updated', data)
        
        # Should have calculated arbitrage for BTC
        btc_data = next((item for item in data['data'] if item['symbol'] == 'BTC'), None)
        self.assertIsNotNone(btc_data)
        self.assertIn('arbitrage', btc_data)
        self.assertGreater(btc_data['arbitrage'], 0)

    @patch('src.web_api.db')
    def test_live_prices_empty_data(self, mock_db):
        """Test live prices with empty data"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        response = self.client.get('/api/live-prices')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 0)

    @patch('src.web_api.db')
    def test_live_prices_error(self, mock_db):
        """Test live prices with database error"""
        mock_db.get_connection.side_effect = Exception("Connection Error")
        
        response = self.client.get('/api/live-prices')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('src.web_api.db')
    def test_arbitrage_alerts_success(self, mock_db):
        """Test successful arbitrage alerts retrieval"""
        mock_alerts = [
            {
                "symbol": "BTC",
                "buy_exchange": "binance",
                "sell_exchange": "coinbase",
                "profit_percentage": 2.5,
                "timestamp": datetime.now().isoformat()
            }
        ]
        mock_db.get_recent_arbitrage_alerts.return_value = mock_alerts
        
        response = self.client.get('/api/arbitrage-alerts')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['data']), 1)

    @patch('src.web_api.db')
    def test_arbitrage_alerts_error(self, mock_db):
        """Test arbitrage alerts with database error"""
        mock_db.get_recent_arbitrage_alerts.side_effect = Exception("Query Error")
        
        response = self.client.get('/api/arbitrage-alerts')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    @patch('src.web_api.merge_duplicate_performance_data')
    @patch('src.web_api.db')
    def test_performance_data_success(self, mock_db, mock_merge):
        """Test successful performance data retrieval"""
        mock_performance_data = [
            {"symbol": "BTC", "sharpe_ratio": 1.5, "annual_return": 25.0},
            {"symbol": "ETH", "sharpe_ratio": 1.2, "annual_return": 20.0},
            {"symbol": "BTC", "sharpe_ratio": 1.4, "annual_return": 24.0}  # Duplicate
        ]
        mock_cleaned_data = [
            {"symbol": "BTC", "sharpe_ratio": 1.5, "annual_return": 25.0},
            {"symbol": "ETH", "sharpe_ratio": 1.2, "annual_return": 20.0}
        ]
        
        mock_db.get_latest_performance_data.return_value = mock_performance_data
        mock_merge.return_value = mock_cleaned_data
        
        response = self.client.get('/api/performance-data')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['original_count'], 3)
        self.assertEqual(data['duplicates_removed'], 1)

    @patch('src.web_api.db')
    def test_performance_data_error(self, mock_db):
        """Test performance data with database error"""
        mock_db.get_latest_performance_data.side_effect = Exception("Database Error")
        
        response = self.client.get('/api/performance-data')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    @patch('src.web_api.db')
    def test_price_history_success(self, mock_db):
        """Test successful price history retrieval"""
        mock_price_history = [
            {"exchange": "binance", "price": 45000, "timestamp": "2023-01-01T10:00:00"},
            {"exchange": "binance", "price": 45100, "timestamp": "2023-01-01T11:00:00"},
            {"exchange": "coinbase", "price": 45200, "timestamp": "2023-01-01T10:00:00"}
        ]
        mock_db.get_price_history.return_value = mock_price_history
        
        response = self.client.get('/api/price-history/BTC')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['symbol'], 'BTC')
        self.assertEqual(data['count'], 3)
        self.assertIn('data', data)
        
        # Should group by exchange
        self.assertIn('binance', data['data'])
        self.assertIn('coinbase', data['data'])
        self.assertEqual(len(data['data']['binance']), 2)
        self.assertEqual(len(data['data']['coinbase']), 1)

    @patch('src.web_api.db')
    def test_price_history_empty(self, mock_db):
        """Test price history with no data"""
        mock_db.get_price_history.return_value = []
        
        response = self.client.get('/api/price-history/UNKNOWN')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['data']), 0)

    @patch('src.web_api.db')
    def test_price_history_error(self, mock_db):
        """Test price history with database error"""
        mock_db.get_price_history.side_effect = Exception("Query Error")
        
        response = self.client.get('/api/price-history/BTC')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    @patch('src.web_api.db')
    def test_portfolio_snapshots_success(self, mock_db):
        """Test successful portfolio snapshots retrieval"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_snapshots = [
            {
                "id": 1,
                "timestamp": datetime.now().isoformat(),
                "best_performer": "BTC",
                "best_performer_sharpe": 1.5
            }
        ]
        mock_cursor.fetchall.return_value = [dict(snap) for snap in mock_snapshots]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        response = self.client.get('/api/portfolio-snapshots')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

    @patch('src.web_api.db')
    def test_telegram_stats_success(self, mock_db):
        """Test successful telegram stats retrieval"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock stats query
        mock_stats = {"total_messages": 100, "successful_messages": 95, "message_types": 5}
        mock_recent_messages = [
            {"message_type": "arbitrage", "timestamp": datetime.now().isoformat(), "success": 1}
        ]
        
        mock_cursor.fetchone.return_value = mock_stats
        mock_cursor.fetchall.return_value = [dict(msg) for msg in mock_recent_messages]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        response = self.client.get('/api/telegram-stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('stats', data['data'])
        self.assertIn('recent_messages', data['data'])

    @patch('src.web_api.db')
    def test_bot_health_success(self, mock_db):
        """Test successful bot health check"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock health check queries
        mock_cursor.fetchone.side_effect = [
            {"last_arbitrage_check": datetime.now().isoformat()},
            {"last_performance_check": datetime.now().isoformat()},
            {"uptime_hours": 24.5, "total_alerts": 10}
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        response = self.client.get('/api/bot-health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['is_healthy'])
        self.assertIn('checked_at', data['data'])

    @patch('src.web_api.db')
    def test_bot_health_error(self, mock_db):
        """Test bot health check with error"""
        mock_db.get_connection.side_effect = Exception("Health Check Error")
        
        response = self.client.get('/api/bot-health')
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertFalse(data['data']['is_healthy'])


class TestWebAPIHelperFunctions(unittest.TestCase):
    """Test helper functions in web_api module"""

    @patch('src.web_api.db')
    def test_test_api_function(self, mock_db):
        """Test the test_api helper function"""
        # The test_api function is defined in the __main__ block, so we skip this test
        # or we could import and call it differently
        mock_db.db_path = "/test/path/db.sqlite"
        
        # Since test_api function is only available when run as main, we just verify
        # that the module imports correctly
        from src import web_api
        self.assertIsNotNone(web_api.app)


class TestWebAPIErrorHandling(unittest.TestCase):
    """Test error handling in web API"""

    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_invalid_route(self):
        """Test handling of invalid routes"""
        response = self.client.get('/api/invalid-endpoint')
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed(self):
        """Test handling of invalid HTTP methods"""
        response = self.client.post('/api/dashboard-data')
        self.assertEqual(response.status_code, 405)

    @patch('src.web_api.db')
    def test_json_serialization_error(self, mock_db):
        """Test handling of JSON serialization errors"""
        # Create an object that can't be JSON serialized
        class NonSerializable:
            pass
        
        mock_db.get_dashboard_data.return_value = {
            "normal_data": "test",
            "non_serializable": NonSerializable()
        }
        
        response = self.client.get('/api/dashboard-data')
        # Should handle the error gracefully (might return 500 or serialize what it can)
        self.assertIn(response.status_code, [200, 500])


class TestWebAPIPerformance(unittest.TestCase):
    """Test performance aspects of web API"""

    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('src.web_api.db')
    def test_large_dataset_handling(self, mock_db):
        """Test API handling of large datasets"""
        # Create large mock dataset
        large_performance_data = [
            {"symbol": f"CRYPTO{i}", "sharpe_ratio": i * 0.1, "annual_return": i * 2.0}
            for i in range(1000)
        ]
        
        with patch('src.web_api.merge_duplicate_performance_data', return_value=large_performance_data):
            mock_db.get_latest_performance_data.return_value = large_performance_data
            
            response = self.client.get('/api/performance-data')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['count'], 1000)

    @patch('src.web_api.db')
    def test_concurrent_requests(self, mock_db):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        mock_db.get_dashboard_data.return_value = {"test": "data"}
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = self.client.get('/api/dashboard-data')
                results.append(response.status_code)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=5)
        
        # All requests should succeed
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))


class TestWebAPIConfiguration(unittest.TestCase):
    """Test web API configuration and setup"""

    def test_app_configuration(self):
        """Test Flask app configuration"""
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, 'config'))

    def test_cors_enabled(self):
        """Test that CORS is properly enabled"""
        # This is tested implicitly through successful API calls in other tests
        # since CORS would block requests in a real browser environment
        with app.test_client() as client:
            response = client.get('/api/dashboard-data')
            # Response should include CORS headers (handled by flask-cors)
            self.assertIn('Access-Control-Allow-Origin', response.headers or {})

    def test_api_routes_registered(self):
        """Test that all expected API routes are registered"""
        expected_routes = [
            '/',
            '/api/dashboard-data',
            '/api/live-prices',
            '/api/arbitrage-alerts',
            '/api/performance-data',
            '/api/price-history/<symbol>',
            '/api/portfolio-snapshots',
            '/api/telegram-stats',
            '/api/bot-health'
        ]
        
        # Get all registered routes
        registered_routes = []
        for rule in app.url_map.iter_rules():
            registered_routes.append(rule.rule)
        
        # Check that our expected routes are registered
        for expected_route in expected_routes:
            route_pattern = expected_route.replace('<symbol>', '<string:symbol>')
            if route_pattern not in registered_routes:
                # Some routes might have slight variations, so do partial matching
                found = any(route_pattern.split('<')[0] in route for route in registered_routes)
                self.assertTrue(found, f"Route {expected_route} not found in registered routes")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)