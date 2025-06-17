"""
Unit tests for health monitoring functionality
Testing system health and monitoring functions
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


class HealthChecker:
    """Standalone health checker for testing"""
    
    def check_bot_health(self, db_connection):
        """Bot Health Check Implementation"""
        try:
            with db_connection.get_connection() as conn:
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

            return {"success": True, "data": health_data}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {"is_healthy": False, "checked_at": datetime.now().isoformat()},
            }, 500


class TestHealthMonitoring(unittest.TestCase):
    """Test cases for health monitoring functionality"""

    def setUp(self):
        """Set up test environment"""
        self.health_checker = HealthChecker()
        
    def test_bot_health_endpoint_success(self):
        """Test successful bot health check"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock database responses
        now = datetime.now()
        mock_cursor.fetchone.side_effect = [
            {"last_arbitrage_check": (now - timedelta(minutes=5)).isoformat()},  # Recent arbitrage
            {"last_performance_check": (now - timedelta(minutes=10)).isoformat()},  # Recent performance
            {  # Bot statistics
                "total_alerts": 42,
                "total_opportunities": 123,
                "avg_profit": 2.5,
                "uptime_hours": 24.5
            }
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        # Call the function
        result = self.health_checker.check_bot_health(mock_db)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
        self.assertIn("data", result)
        
        health_data = result["data"]
        self.assertTrue(health_data.get("is_healthy", False))
        self.assertIn("last_arbitrage_check", health_data)
        self.assertIn("last_performance_check", health_data)
        self.assertIn("latest_stats", health_data)
        self.assertIn("checked_at", health_data)

    def test_bot_health_endpoint_database_error(self):
        """Test bot health check with database error"""
        # Mock database to raise exception
        mock_db = MagicMock()
        mock_db.get_connection.side_effect = Exception("Database connection failed")
        
        # Call the function
        result = self.health_checker.check_bot_health(mock_db)
        
        # Assertions
        self.assertIsInstance(result, tuple)  # Error responses are tuples (data, status_code)
        response_data, status_code = result
        self.assertEqual(status_code, 500)
        self.assertFalse(response_data.get("success", True))
        self.assertIn("error", response_data)
        self.assertFalse(response_data["data"]["is_healthy"])

    def test_bot_health_no_recent_activity(self):
        """Test bot health when no recent activity detected"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Mock database responses with no recent activity
        mock_cursor.fetchone.side_effect = [
            None,  # No arbitrage checks
            None,  # No performance checks
            None   # No bot statistics
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        # Call the function
        result = self.health_checker.check_bot_health(mock_db)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
        
        health_data = result["data"]
        self.assertTrue(health_data.get("is_healthy", False))  # Should still be healthy
        self.assertIsNone(health_data.get("last_arbitrage_check"))
        self.assertIsNone(health_data.get("last_performance_check"))
        self.assertEqual(health_data.get("latest_stats"), {})

    def test_health_data_structure(self):
        """Test that health data has correct structure"""
        # Mock successful database response
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        now = datetime.now()
        mock_cursor.fetchone.side_effect = [
            {"last_arbitrage_check": now.isoformat()},
            {"last_performance_check": now.isoformat()},
            {"total_alerts": 10, "uptime_hours": 12.5}
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        result = self.health_checker.check_bot_health(mock_db)
        
        # Check required fields
        required_fields = ["success", "data"]
        for field in required_fields:
            self.assertIn(field, result)
        
        health_data = result["data"]
        required_health_fields = ["is_healthy", "checked_at"]
        for field in required_health_fields:
            self.assertIn(field, health_data)
        
        # Check data types
        self.assertIsInstance(health_data["is_healthy"], bool)
        self.assertIsInstance(health_data["checked_at"], str)
        
        # Check datetime format
        try:
            datetime.fromisoformat(health_data["checked_at"].replace('Z', '+00:00'))
        except ValueError:
            self.fail("checked_at is not a valid ISO format datetime")

    def test_health_check_database_queries(self):
        """Test that health check executes correct database queries"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"test": "data"}
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        result = self.health_checker.check_bot_health(mock_db)
        
        # Verify that the correct SQL queries were executed
        expected_queries = [
            "SELECT MAX(timestamp) as last_arbitrage_check\n                    FROM arbitrage_alerts",
            "SELECT MAX(timestamp) as last_performance_check\n                    FROM performance_data",
            "SELECT * FROM bot_statistics\n                    ORDER BY timestamp DESC\n                    LIMIT 1"
        ]
        
        # Check that execute was called 3 times with expected queries
        self.assertEqual(mock_cursor.execute.call_count, 3)
        actual_queries = [call[0][0].strip() for call in mock_cursor.execute.call_args_list]
        
        for expected, actual in zip(expected_queries, actual_queries):
            self.assertEqual(expected.strip(), actual.strip())


class TestHealthMonitoringEdgeCases(unittest.TestCase):
    """Test edge cases for health monitoring"""

    def setUp(self):
        """Set up test environment"""
        self.health_checker = HealthChecker()

    def test_health_endpoint_response_time(self):
        """Test that health endpoint responds quickly"""
        # Mock fast database response
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"test": "data"}
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        import time
        start_time = time.time()
        result = self.health_checker.check_bot_health(mock_db)
        end_time = time.time()
        
        # Health check should be fast (< 1 second)
        self.assertLess(end_time - start_time, 1.0)
        self.assertIsNotNone(result)

    def test_health_endpoint_error_handling(self):
        """Test that health endpoint handles various error scenarios"""
        error_scenarios = [
            Exception("Database timeout"),
            ConnectionError("Database unreachable"),
            ValueError("Invalid data format"),
            RuntimeError("System overloaded")
        ]
        
        for error in error_scenarios:
            with self.subTest(error=error):
                mock_db = MagicMock()
                mock_db.get_connection.side_effect = error
                
                result = self.health_checker.check_bot_health(mock_db)
                
                # Should return error response
                self.assertIsInstance(result, tuple)
                response_data, status_code = result
                self.assertEqual(status_code, 500)
                self.assertFalse(response_data.get("success", True))

    def test_partial_database_data(self):
        """Test health check with partial database data"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Only first query returns data, others return None
        mock_cursor.fetchone.side_effect = [
            {"last_arbitrage_check": datetime.now().isoformat()},
            None,  # No performance data
            None   # No bot statistics
        ]
        
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        
        mock_db = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        
        result = self.health_checker.check_bot_health(mock_db)
        
        # Should still be successful
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
        
        health_data = result["data"]
        self.assertTrue(health_data.get("is_healthy", False))
        self.assertIsNotNone(health_data.get("last_arbitrage_check"))
        self.assertIsNone(health_data.get("last_performance_check"))
        self.assertEqual(health_data.get("latest_stats"), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)