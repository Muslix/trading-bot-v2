"""
Unit tests for telegram alerting functionality
Testing critical error alerts and system notifications
"""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.telegram_alerts import (
    TelegramErrorAlerter, send_critical_error_alert, 
    send_system_recovery_alert, send_health_degradation_alert
)


class TestTelegramErrorAlerter(unittest.IsolatedAsyncioTestCase):
    """Test cases for TelegramErrorAlerter class"""
    
    async def asyncSetUp(self):
        """Set up test environment"""
        self.alerter = TelegramErrorAlerter(cooldown_minutes=15)
    
    def test_init(self):
        """Test TelegramErrorAlerter initialization"""
        alerter = TelegramErrorAlerter(cooldown_minutes=30)
        
        self.assertEqual(alerter.cooldown_minutes, 30)
        self.assertEqual(alerter.last_alerts, {})
        self.assertTrue(alerter.enabled)
    
    def test_get_alert_key(self):
        """Test alert key generation"""
        key = self.alerter._get_alert_key("ValueError", "database")
        self.assertEqual(key, "ValueError_database")
        
        key2 = self.alerter._get_alert_key("ConnectionError", "api")
        self.assertEqual(key2, "ConnectionError_api")
    
    def test_should_send_alert_first_time(self):
        """Test _should_send_alert for first time alert"""
        result = self.alerter._should_send_alert("ValueError", "database")
        self.assertTrue(result)
    
    def test_should_send_alert_within_cooldown(self):
        """Test _should_send_alert within cooldown period"""
        # Record an alert
        self.alerter._record_alert("ValueError", "database")
        
        # Should not send again immediately
        result = self.alerter._should_send_alert("ValueError", "database")
        self.assertFalse(result)
    
    def test_should_send_alert_after_cooldown(self):
        """Test _should_send_alert after cooldown period"""
        # Manually set an old alert time
        past_time = datetime.now() - timedelta(minutes=20)
        self.alerter.last_alerts["ValueError_database"] = past_time
        
        result = self.alerter._should_send_alert("ValueError", "database")
        self.assertTrue(result)
    
    def test_should_send_alert_disabled(self):
        """Test _should_send_alert when alerts disabled"""
        self.alerter.disable_alerts()
        
        result = self.alerter._should_send_alert("ValueError", "database")
        self.assertFalse(result)
    
    def test_record_alert(self):
        """Test _record_alert method"""
        before_count = len(self.alerter.last_alerts)
        
        self.alerter._record_alert("ValueError", "database")
        
        after_count = len(self.alerter.last_alerts)
        self.assertEqual(after_count, before_count + 1)
        self.assertIn("ValueError_database", self.alerter.last_alerts)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_critical_error_alert_success(self, mock_crypto_bot):
        """Test successful critical error alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        result = await self.alerter.send_critical_error_alert(
            "Database connection failed",
            exception=ValueError("Connection timeout"),
            module="database",
            context={"retry_count": 3}
        )
        
        self.assertTrue(result)
        mock_crypto_bot.send_message.assert_called_once()
        
        # Check that alert was recorded
        self.assertIn("ValueError_database", self.alerter.last_alerts)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_critical_error_alert_cooldown(self, mock_crypto_bot):
        """Test critical error alert with cooldown"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        # Send first alert
        result1 = await self.alerter.send_critical_error_alert(
            "Database error", exception=ValueError("Test"), module="database"
        )
        self.assertTrue(result1)
        
        # Try to send again immediately (should be blocked)
        result2 = await self.alerter.send_critical_error_alert(
            "Database error", exception=ValueError("Test"), module="database"
        )
        self.assertFalse(result2)
        
        # Should only be called once
        self.assertEqual(mock_crypto_bot.send_message.call_count, 1)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_critical_error_alert_telegram_failure(self, mock_crypto_bot):
        """Test critical error alert when telegram fails"""
        mock_crypto_bot.send_message = AsyncMock(return_value=False)
        
        result = await self.alerter.send_critical_error_alert(
            "Test error", module="test"
        )
        
        self.assertFalse(result)
        # Alert should not be recorded if telegram fails
        self.assertNotIn("CriticalError_test", self.alerter.last_alerts)
    
    @patch('src.utils.telegram_alerts.crypto_bot', None)
    async def test_send_critical_error_alert_no_bot(self):
        """Test critical error alert when bot not available"""
        result = await self.alerter.send_critical_error_alert(
            "Test error", module="test"
        )
        
        self.assertFalse(result)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_critical_error_alert_exception(self, mock_crypto_bot):
        """Test critical error alert when exception occurs"""
        mock_crypto_bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))
        
        result = await self.alerter.send_critical_error_alert(
            "Test error", module="test"
        )
        
        self.assertFalse(result)
    
    def test_format_error_message_basic(self):
        """Test basic error message formatting"""
        message = self.alerter._format_error_message(
            "Database connection failed",
            None,
            "database",
            None
        )
        
        self.assertIn("CRITICAL ERROR ALERT", message)
        self.assertIn("Database connection failed", message)
        self.assertIn("database", message)
        self.assertIn("Bot Status", message)
    
    def test_format_error_message_with_exception(self):
        """Test error message formatting with exception"""
        exception = ValueError("Connection timeout")
        
        message = self.alerter._format_error_message(
            "Database error",
            exception,
            "database",
            None
        )
        
        self.assertIn("ValueError", message)
        self.assertIn("Connection timeout", message)
    
    def test_format_error_message_with_context(self):
        """Test error message formatting with context"""
        context = {"retry_count": 3, "timeout": 30.0, "enabled": True}
        
        message = self.alerter._format_error_message(
            "API error",
            None,
            "api",
            context
        )
        
        self.assertIn("Context", message)
        self.assertIn("retry_count", message)
        self.assertIn("timeout", message)
        self.assertIn("enabled", message)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_system_recovery_alert(self, mock_crypto_bot):
        """Test system recovery alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        result = await self.alerter.send_system_recovery_alert(
            "database", "Connection restored after restart"
        )
        
        self.assertTrue(result)
        mock_crypto_bot.send_message.assert_called_once()
        
        # Check message content
        sent_message = mock_crypto_bot.send_message.call_args[0][0]
        self.assertIn("SYSTEM RECOVERY", sent_message)
        self.assertIn("database", sent_message)
        self.assertIn("Connection restored", sent_message)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_health_degradation_alert_success(self, mock_crypto_bot):
        """Test health degradation alert"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        details = {"response_time": "5000ms", "error_rate": "15%"}
        
        result = await self.alerter.send_health_degradation_alert(
            "api_gateway", "Degraded performance", details
        )
        
        self.assertTrue(result)
        mock_crypto_bot.send_message.assert_called_once()
        
        # Check message content
        sent_message = mock_crypto_bot.send_message.call_args[0][0]
        self.assertIn("HEALTH ALERT", sent_message)
        self.assertIn("api_gateway", sent_message)
        self.assertIn("Degraded performance", sent_message)
        self.assertIn("response_time", sent_message)
        self.assertIn("error_rate", sent_message)
    
    @patch('src.utils.telegram_alerts.crypto_bot')
    async def test_send_health_degradation_alert_cooldown(self, mock_crypto_bot):
        """Test health degradation alert with cooldown"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        # Send first alert
        result1 = await self.alerter.send_health_degradation_alert(
            "database", "High latency"
        )
        self.assertTrue(result1)
        
        # Try to send again immediately
        result2 = await self.alerter.send_health_degradation_alert(
            "database", "Still high latency"
        )
        self.assertFalse(result2)
        
        # Should only be called once
        self.assertEqual(mock_crypto_bot.send_message.call_count, 1)
    
    def test_enable_disable_alerts(self):
        """Test enabling and disabling alerts"""
        # Initially enabled
        self.assertTrue(self.alerter.enabled)
        
        # Disable
        self.alerter.disable_alerts()
        self.assertFalse(self.alerter.enabled)
        
        # Enable
        self.alerter.enable_alerts()
        self.assertTrue(self.alerter.enabled)
    
    def test_get_alert_stats(self):
        """Test getting alert statistics"""
        # Add some test alerts
        self.alerter._record_alert("ValueError", "database")
        self.alerter._record_alert("ConnectionError", "api")
        
        stats = self.alerter.get_alert_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("enabled", stats)
        self.assertIn("cooldown_minutes", stats)
        self.assertIn("active_cooldowns", stats)
        self.assertIn("last_alerts", stats)
        
        self.assertTrue(stats["enabled"])
        self.assertEqual(stats["cooldown_minutes"], 15)
        self.assertEqual(stats["active_cooldowns"], 2)


class TestConvenienceFunctions(unittest.IsolatedAsyncioTestCase):
    """Test cases for convenience functions"""
    
    @patch('src.utils.telegram_alerts.telegram_alerter')
    async def test_send_critical_error_alert_function(self, mock_alerter):
        """Test send_critical_error_alert convenience function"""
        mock_alerter.send_critical_error_alert = AsyncMock(return_value=True)
        
        test_exception = ValueError("Test")
        result = await send_critical_error_alert(
            "Test error", 
            exception=test_exception, 
            module="test",
            context={"test": True}
        )
        
        self.assertTrue(result)
        mock_alerter.send_critical_error_alert.assert_called_once_with(
            "Test error", test_exception, "test", {"test": True}
        )
    
    @patch('src.utils.telegram_alerts.telegram_alerter')
    async def test_send_system_recovery_alert_function(self, mock_alerter):
        """Test send_system_recovery_alert convenience function"""
        mock_alerter.send_system_recovery_alert = AsyncMock(return_value=True)
        
        result = await send_system_recovery_alert("database", "Recovery message")
        
        self.assertTrue(result)
        mock_alerter.send_system_recovery_alert.assert_called_once_with(
            "database", "Recovery message"
        )
    
    @patch('src.utils.telegram_alerts.telegram_alerter')
    async def test_send_health_degradation_alert_function(self, mock_alerter):
        """Test send_health_degradation_alert convenience function"""
        mock_alerter.send_health_degradation_alert = AsyncMock(return_value=True)
        
        details = {"metric": "value"}
        result = await send_health_degradation_alert(
            "component", "status", details
        )
        
        self.assertTrue(result)
        mock_alerter.send_health_degradation_alert.assert_called_once_with(
            "component", "status", details
        )


class TestTelegramAlertsIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for telegram alerts"""
    
    async def test_multiple_concurrent_alerts(self):
        """Test handling multiple concurrent alerts"""
        alerter = TelegramErrorAlerter(cooldown_minutes=1)
        
        with patch('src.utils.telegram_alerts.crypto_bot') as mock_bot:
            mock_bot.send_message = AsyncMock(return_value=True)
            
            # Send multiple alerts concurrently
            tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    alerter.send_critical_error_alert(
                        f"Error {i}",
                        module=f"module_{i}",
                        exception=ValueError(f"Test error {i}")
                    )
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed since they're for different modules
            self.assertTrue(all(results))
            self.assertEqual(mock_bot.send_message.call_count, 5)
    
    async def test_alert_message_formatting_edge_cases(self):
        """Test alert message formatting with edge cases"""
        alerter = TelegramErrorAlerter()
        
        # Test with very long error message
        long_error = "A" * 1000
        message = alerter._format_error_message(long_error, None, "test", None)
        self.assertIsInstance(message, str)
        self.assertIn(long_error, message)
        
        # Test with special characters
        special_error = "Error with *markdown* and `code` and _italics_"
        message = alerter._format_error_message(special_error, None, "test", None)
        self.assertIn(special_error, message)
        
        # Test with None values in context
        context = {"valid": "value", "none_val": None, "empty": ""}
        message = alerter._format_error_message("test", None, "test", context)
        self.assertIn("valid", message)
    
    async def test_cooldown_mechanism_accuracy(self):
        """Test that cooldown mechanism works accurately"""
        alerter = TelegramErrorAlerter(cooldown_minutes=1)  # Short cooldown for testing
        
        with patch('src.utils.telegram_alerts.crypto_bot') as mock_bot:
            mock_bot.send_message = AsyncMock(return_value=True)
            
            # Send first alert
            result1 = await alerter.send_critical_error_alert("Error", module="test")
            self.assertTrue(result1)
            
            # Should be in cooldown
            result2 = await alerter.send_critical_error_alert("Error", module="test")
            self.assertFalse(result2)
            
            # Manually advance time past cooldown
            past_time = datetime.now() - timedelta(minutes=2)
            alerter.last_alerts["CriticalError_test"] = past_time
            
            # Should work again
            result3 = await alerter.send_critical_error_alert("Error", module="test")
            self.assertTrue(result3)


if __name__ == "__main__":
    unittest.main(verbosity=2)