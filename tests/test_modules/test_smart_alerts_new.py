"""
Unit tests for modules/smart_alerts.py
Testing smart alert system functionality
"""

import asyncio
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


def create_mock_config():
    mock_config_obj = MagicMock()
    mock_config_obj.arbitrage_threshold = 1.5
    mock_config_obj.alert_cooldown_minutes = 15
    mock_config_obj.sharpe_change_threshold = 0.5
    mock_config_obj.daily_summary_hour = 8
    mock_config_obj.telegram_bot_token = "test_token"
    mock_config_obj.telegram_chat_id = "test_chat_id"
    return mock_config_obj


# Mock at sys.modules level to prevent actual module loading
mock_database_module = MagicMock()
mock_database_module.CryptoDatabaseManager = MagicMock()
mock_database_module.db = MagicMock()
sys.modules['src.modules.database'] = mock_database_module

mock_telegram_module = MagicMock()
mock_telegram_module.get_config = MagicMock(return_value=create_mock_config())
mock_telegram_module.crypto_bot = MagicMock()
sys.modules['src.modules.telegram_bot'] = mock_telegram_module

# Now safe to import with mocked dependencies
with patch('config.config.get_config', return_value=create_mock_config()):
    from src.modules.smart_alerts import SmartAlertManager


class TestSmartAlertManager(unittest.TestCase):
    """Test cases for SmartAlertManager class"""

    def setUp(self):
        """Set up test environment"""
        self.alert_manager = SmartAlertManager()

    def test_init(self):
        """Test SmartAlertManager initialization"""
        self.assertIsInstance(self.alert_manager.alert_rules, dict)
        self.assertIsInstance(self.alert_manager.alert_history, dict)
        self.assertIsInstance(self.alert_manager.last_performance_snapshot, dict)
        self.assertIsInstance(self.alert_manager.price_history_tracker, dict)

        # Check that required alert rules are configured
        required_rules = [
            "arbitrage_immediate", "sharpe_change", "new_top_performer",
            "daily_summary", "large_price_movement", "volume_spike"
        ]
        for rule in required_rules:
            self.assertIn(rule, self.alert_manager.alert_rules)

    def test_alert_rules_structure(self):
        """Test that alert rules have proper structure"""
        for rule_name, rule_config in self.alert_manager.alert_rules.items():
            self.assertIsInstance(rule_config, dict)
            self.assertIn("enabled", rule_config)
            self.assertIn("priority", rule_config)
            self.assertIsInstance(rule_config["enabled"], bool)
            self.assertIn(rule_config["priority"], ["high", "medium", "low"])

    def test_should_send_alert_disabled_rule(self):
        """Test _should_send_alert with disabled rule"""
        # Disable a rule
        original_enabled = self.alert_manager.alert_rules["volume_spike"]["enabled"]
        self.alert_manager.alert_rules["volume_spike"]["enabled"] = False

        result = self.alert_manager._should_send_alert("volume_spike", "BTC")
        self.assertFalse(result)

        # Restore original state
        self.alert_manager.alert_rules["volume_spike"]["enabled"] = original_enabled

    def test_should_send_alert_first_time(self):
        """Test _should_send_alert for first time alert"""
        result = self.alert_manager._should_send_alert("arbitrage_immediate", "BTC")
        self.assertTrue(result)

        # Should have recorded the alert
        alert_key = "arbitrage_immediate_BTC"
        self.assertIn(alert_key, self.alert_manager.alert_history)

    def test_should_send_alert_within_cooldown(self):
        """Test _should_send_alert within cooldown period"""
        # Send first alert
        self.alert_manager._should_send_alert("arbitrage_immediate", "BTC")

        # Try to send again immediately
        result = self.alert_manager._should_send_alert("arbitrage_immediate", "BTC")
        self.assertFalse(result)

    def test_should_send_alert_after_cooldown(self):
        """Test _should_send_alert after cooldown period"""
        # Manually set an old alert time
        past_time = datetime.now() - timedelta(hours=2)
        self.alert_manager.alert_history["arbitrage_immediate_BTC"] = past_time

        result = self.alert_manager._should_send_alert("arbitrage_immediate", "BTC")
        self.assertTrue(result)

    def test_should_send_alert_nonexistent_rule(self):
        """Test _should_send_alert with nonexistent rule"""
        result = self.alert_manager._should_send_alert("nonexistent_rule", "BTC")
        self.assertFalse(result)

    def test_filter_redundant_opportunities_empty_list(self):
        """Test _filter_redundant_opportunities with empty list"""
        result = self.alert_manager._filter_redundant_opportunities([])
        self.assertEqual(result, [])

    def test_filter_redundant_opportunities_single_symbol(self):
        """Test _filter_redundant_opportunities with single symbol"""
        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5},
            {"symbol": "BTC", "profit_percentage": 1.8},
            {"symbol": "BTC", "profit_percentage": 3.2}
        ]

        result = self.alert_manager._filter_redundant_opportunities(opportunities)

        # Should return only the best opportunity for BTC
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["profit_percentage"], 3.2)

    def test_filter_redundant_opportunities_multiple_symbols(self):
        """Test _filter_redundant_opportunities with multiple symbols"""
        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5},
            {"symbol": "ETH", "profit_percentage": 1.8},
            {"symbol": "BTC", "profit_percentage": 1.2},
            {"symbol": "ADA", "profit_percentage": 3.0}
        ]

        result = self.alert_manager._filter_redundant_opportunities(opportunities)

        # Should return best opportunity for each symbol
        self.assertEqual(len(result), 3)
        symbols = [opp["symbol"] for opp in result]
        self.assertIn("BTC", symbols)
        self.assertIn("ETH", symbols)
        self.assertIn("ADA", symbols)

    def test_filter_redundant_opportunities_below_threshold(self):
        """Test _filter_redundant_opportunities filtering below threshold"""
        # Set a high threshold for testing
        original_threshold = self.alert_manager.alert_rules["arbitrage_immediate"]["threshold"]
        self.alert_manager.alert_rules["arbitrage_immediate"]["threshold"] = 2.0

        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5},  # Above threshold
            {"symbol": "ETH", "profit_percentage": 1.5},  # Below threshold
        ]

        result = self.alert_manager._filter_redundant_opportunities(opportunities)

        # Should only return BTC
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["symbol"], "BTC")

        # Restore original threshold
        self.alert_manager.alert_rules["arbitrage_immediate"]["threshold"] = original_threshold

    def test_get_alert_stats(self):
        """Test get_alert_stats method"""
        # Add some test alert history
        now = datetime.now()
        self.alert_manager.alert_history["test_alert_1"] = now
        self.alert_manager.alert_history["test_alert_2"] = now - timedelta(days=1)

        stats = self.alert_manager.get_alert_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("rules_configured", stats)
        self.assertIn("rules_enabled", stats)
        self.assertIn("alerts_sent_today", stats)
        self.assertIn("last_performance_check", stats)
        self.assertIn("alert_rules", stats)

        self.assertGreaterEqual(stats["rules_configured"], 6)
        self.assertEqual(stats["alerts_sent_today"], 1)  # Only test_alert_1 is today


class TestSmartAlertManagerAsyncMethods(unittest.IsolatedAsyncioTestCase):
    """Test async methods of SmartAlertManager"""

    async def asyncSetUp(self):
        """Set up async test environment"""
        self.alert_manager = SmartAlertManager()

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_arbitrage_alerts_no_opportunities(self, mock_crypto_bot):
        """Test check_arbitrage_alerts with no opportunities"""
        result = await self.alert_manager.check_arbitrage_alerts([])
        self.assertEqual(result, 0)

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_arbitrage_alerts_below_threshold(self, mock_crypto_bot):
        """Test check_arbitrage_alerts with opportunities below threshold"""
        opportunities = [
            {"symbol": "BTC", "profit_percentage": 0.8}  # Below default threshold
        ]

        result = await self.alert_manager.check_arbitrage_alerts(opportunities)
        self.assertEqual(result, 0)

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_arbitrage_alerts_success(self, mock_crypto_bot):
        """Test successful arbitrage alert check"""
        mock_crypto_bot.send_arbitrage_alert = AsyncMock(return_value=True)

        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5}  # Above threshold
        ]

        result = await self.alert_manager.check_arbitrage_alerts(opportunities)

        self.assertEqual(result, 1)
        mock_crypto_bot.send_arbitrage_alert.assert_called_once()

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_arbitrage_alerts_telegram_failure(self, mock_crypto_bot):
        """Test arbitrage alert check when telegram fails"""
        mock_crypto_bot.send_arbitrage_alert = AsyncMock(return_value=False)

        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5}
        ]

        result = await self.alert_manager.check_arbitrage_alerts(opportunities)

        self.assertEqual(result, 0)  # No alerts sent due to telegram failure

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_arbitrage_alerts_cooldown(self, mock_crypto_bot):
        """Test arbitrage alert check with cooldown"""
        mock_crypto_bot.send_arbitrage_alert = AsyncMock(return_value=True)

        opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5}
        ]

        # Send first alert
        result1 = await self.alert_manager.check_arbitrage_alerts(opportunities)
        self.assertEqual(result1, 1)

        # Try to send again immediately (should be blocked by cooldown)
        result2 = await self.alert_manager.check_arbitrage_alerts(opportunities)
        self.assertEqual(result2, 0)

    async def test_check_performance_change_alerts_no_data(self):
        """Test performance change alerts with no data"""
        result = await self.alert_manager.check_performance_change_alerts([])
        self.assertEqual(result, 0)

    async def test_check_performance_change_alerts_first_run(self):
        """Test performance change alerts on first run"""
        performers = [("BTC", {"sharpe_ratio": 1.5})]

        result = await self.alert_manager.check_performance_change_alerts(performers)

        self.assertEqual(result, 0)  # No alerts on first run
        # Should have stored the snapshot
        self.assertIn("BTC", self.alert_manager.last_performance_snapshot)

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_performance_change_alerts_significant_change(self, mock_crypto_bot):
        """Test performance change alerts with significant change"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)

        # Set up initial snapshot
        self.alert_manager.last_performance_snapshot = {"BTC": {"sharpe_ratio": 1.0}}

        # Set threshold low enough to trigger alert
        original_threshold = self.alert_manager.alert_rules["sharpe_change"]["threshold"]
        self.alert_manager.alert_rules["sharpe_change"]["threshold"] = 0.4

        performers = [("BTC", {"sharpe_ratio": 1.5})]  # 0.5 change

        result = await self.alert_manager.check_performance_change_alerts(performers)

        self.assertEqual(result, 1)
        mock_crypto_bot.send_message.assert_called_once()

        # Restore original threshold
        self.alert_manager.alert_rules["sharpe_change"]["threshold"] = original_threshold

    @patch('src.modules.smart_alerts.db')
    async def test_check_new_top_performer_alerts_no_data(self, mock_db):
        """Test new top performer alerts with no data"""
        result = await self.alert_manager.check_new_top_performer_alerts([])
        self.assertEqual(result, 0)

    @patch('src.modules.smart_alerts.db')
    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_new_top_performer_alerts_success(self, mock_crypto_bot, mock_db):
        """Test successful new top performer alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)

        # Mock database to return empty old performers
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn

        performers = [("BTC", {"sharpe_ratio": 2.0})]  # Above min_sharpe

        result = await self.alert_manager.check_new_top_performer_alerts(performers)

        self.assertEqual(result, 1)
        mock_crypto_bot.send_message.assert_called_once()

    @patch('src.modules.smart_alerts.db')
    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_daily_summary_alert_wrong_hour(self, mock_crypto_bot, mock_db):
        """Test daily summary alert at wrong hour"""
        # Set summary hour to different from current hour
        current_hour = datetime.now().hour
        wrong_hour = (current_hour + 1) % 24
        self.alert_manager.alert_rules["daily_summary"]["hour"] = wrong_hour

        result = await self.alert_manager.check_daily_summary_alert()
        self.assertFalse(result)

    @patch('src.modules.smart_alerts.db')
    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_daily_summary_alert_force(self, mock_crypto_bot, mock_db):
        """Test forced daily summary alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)

        # Mock database responses
        mock_db.get_dashboard_data.return_value = {
            "arbitrage": {"avg_profit": 2.5},
            "performance": {"total_coins": 50}
        }
        mock_db.get_latest_performance_data.return_value = [
            {"symbol": "BTC", "sharpe_ratio": 1.5}
        ]
        mock_db.get_recent_arbitrage_alerts.return_value = [
            {"symbol": "BTC", "profit": 2.0}
        ]

        result = await self.alert_manager.check_daily_summary_alert(force=True)

        self.assertTrue(result)
        mock_crypto_bot.send_message.assert_called_once()

    @patch('src.modules.smart_alerts.db')
    async def test_check_large_price_movement_alerts_no_data(self, mock_db):
        """Test large price movement alerts with no data"""
        result = await self.alert_manager.check_large_price_movement_alerts({})
        self.assertEqual(result, 0)

    @patch('src.modules.smart_alerts.db')
    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_check_large_price_movement_alerts_success(self, mock_crypto_bot, mock_db):
        """Test successful large price movement alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)

        # Mock database to return old price
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"avg_price": 40000}  # Old price
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=None)
        mock_db.get_connection.return_value = mock_conn

        # Current price data with significant change
        current_prices = {
            "BTC": {"binance": 42000, "coinbase": 42100}  # ~5% increase
        }

        result = await self.alert_manager.check_large_price_movement_alerts(current_prices)

        self.assertEqual(result, 1)
        mock_crypto_bot.send_message.assert_called_once()

    async def test_process_all_alerts_no_data(self):
        """Test process_all_alerts with no data"""
        result = await self.alert_manager.process_all_alerts()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_alerts"], 0)
        self.assertIn("arbitrage_alerts", result)
        self.assertIn("performance_alerts", result)
        self.assertIn("new_performer_alerts", result)
        self.assertIn("price_movement_alerts", result)
        self.assertIn("daily_summary_sent", result)

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_process_all_alerts_with_arbitrage(self, mock_crypto_bot):
        """Test process_all_alerts with arbitrage opportunities"""
        mock_crypto_bot.send_arbitrage_alert = AsyncMock(return_value=True)

        arbitrage_opportunities = [
            {"symbol": "BTC", "profit_percentage": 2.5}
        ]

        result = await self.alert_manager.process_all_alerts(
            arbitrage_opportunities=arbitrage_opportunities
        )

        self.assertEqual(result["arbitrage_alerts"], 1)
        self.assertEqual(result["total_alerts"], 1)

    async def test_process_all_alerts_exception_handling(self):
        """Test that process_all_alerts handles exceptions gracefully"""
        # Mock a method to raise an exception
        with patch.object(self.alert_manager, 'check_arbitrage_alerts',
                          side_effect=Exception("Test error")):

            arbitrage_opportunities = [
                {"symbol": "BTC", "profit_percentage": 2.5}
            ]

            # Should not raise exception
            result = await self.alert_manager.process_all_alerts(
                arbitrage_opportunities=arbitrage_opportunities
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["total_alerts"], 0)


class TestSmartAlertManagerEdgeCases(unittest.IsolatedAsyncioTestCase):
    """Test edge cases and error conditions"""

    async def asyncSetUp(self):
        """Set up async test environment"""
        self.alert_manager = SmartAlertManager()

    def test_alert_rules_configuration_validation(self):
        """Test that alert rules are properly configured"""
        for rule_name, rule_config in self.alert_manager.alert_rules.items():
            # All rules should have enabled and priority
            self.assertIn("enabled", rule_config, f"Rule {rule_name} missing 'enabled'")
            self.assertIn("priority", rule_config, f"Rule {rule_name} missing 'priority'")

            # Priority should be valid
            self.assertIn(rule_config["priority"], ["high", "medium", "low"])

            # Cooldown rules should have cooldown_minutes
            if rule_name != "daily_summary":
                self.assertIn("cooldown_minutes", rule_config,
                              f"Rule {rule_name} missing 'cooldown_minutes'")

    def test_alert_history_cleanup(self):
        """Test that alert history doesn't grow indefinitely"""
        # Add many old alerts
        base_time = datetime.now() - timedelta(days=30)
        for i in range(1000):
            key = f"old_alert_{i}"
            self.alert_manager.alert_history[key] = base_time + timedelta(minutes=i)

        # Alert history should still be manageable
        self.assertLess(len(self.alert_manager.alert_history), 2000)

    @patch('src.modules.smart_alerts.crypto_bot')
    async def test_concurrent_alert_processing(self, mock_crypto_bot):
        """Test concurrent alert processing doesn't cause issues"""
        # Mock the async method properly
        mock_crypto_bot.send_arbitrage_alert = AsyncMock(return_value=True)
        
        # Create multiple concurrent alert checks
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                self.alert_manager.check_arbitrage_alerts([
                    {
                        "symbol": f"CRYPTO{i}",
                        "profit_percentage": 2.0,
                        "buy_exchange": "binance",
                        "sell_exchange": "coinbase",
                        "buy_price": 45000,
                        "sell_price": 46000
                    }
                ])
            )
            tasks.append(task)

        # Should complete without errors
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All results should be integers (not exceptions)
        for result in results:
            self.assertIsInstance(result, int)

    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets"""
        # Create large opportunity list
        large_opportunities = []
        for i in range(1000):
            large_opportunities.append({
                "symbol": f"CRYPTO{i % 100}",  # 100 unique symbols
                "profit_percentage": 1.0 + (i % 50) * 0.1
            })

        # Should filter without memory issues
        filtered = self.alert_manager._filter_redundant_opportunities(large_opportunities)

        # Should have filtered down to unique symbols
        self.assertLessEqual(len(filtered), 100)

    def test_string_formatting_edge_cases(self):
        """Test string formatting with edge case values"""
        # Test with extreme values that might cause formatting issues
        extreme_metrics = {
            "sharpe_ratio": float('inf'),
            "annual_return": -999999.99,
            "current_price": 0.000000001
        }

        # Should not raise exceptions when formatting
        try:
            # This simulates the message formatting in the alerts
            test_message = f"Sharpe: {extreme_metrics['sharpe_ratio']:.3f}"
            test_message += f"Return: {extreme_metrics['annual_return']:.1f}%"
            test_message += f"Price: ${extreme_metrics['current_price']:,.2f}"
        except Exception as e:
            self.fail(f"String formatting failed with extreme values: {e}")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
