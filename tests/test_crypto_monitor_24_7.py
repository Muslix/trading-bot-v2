"""
Unit tests for crypto_monitor_24_7.py
Comprehensive testing of the main monitoring system
"""

import asyncio
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.crypto_monitor_24_7 import CryptoMonitor24_7


class TestCryptoMonitor24_7(unittest.TestCase):
    """Test cases for CryptoMonitor24_7 class"""

    def setUp(self):
        """Set up test environment"""
        self.monitor = CryptoMonitor24_7()

    def test_init(self):
        """Test CryptoMonitor24_7 initialization"""
        self.assertFalse(self.monitor.running)
        self.assertIsNone(self.monitor.start_time)
        self.assertEqual(self.monitor.stats["total_arbitrage_checks"], 0)
        self.assertEqual(self.monitor.stats["total_performance_analyses"], 0)
        self.assertEqual(self.monitor.stats["arbitrage_opportunities_found"], 0)
        self.assertEqual(self.monitor.stats["alerts_sent"], 0)
        self.assertEqual(self.monitor.stats["uptime_hours"], 0)

    def test_config_loading(self):
        """Test configuration loading"""
        self.assertIsInstance(self.monitor.config, dict)
        self.assertIn("arbitrage_check_interval", self.monitor.config)
        self.assertIn("performance_check_interval", self.monitor.config)
        self.assertIn("daily_summary_hour", self.monitor.config)
        self.assertIn("watchlist_symbols", self.monitor.config)
        self.assertIn("analysis_crypto_count", self.monitor.config)
        self.assertIn("exchanges", self.monitor.config)

    def test_calculate_uptime_hours_no_start_time(self):
        """Test uptime calculation when not started"""
        uptime = self.monitor._calculate_uptime_hours()
        self.assertEqual(uptime, 0)

    def test_calculate_uptime_hours_with_start_time(self):
        """Test uptime calculation with start time"""
        self.monitor.start_time = datetime.now() - timedelta(hours=2)
        uptime = self.monitor._calculate_uptime_hours()
        self.assertGreater(uptime, 1.9)
        self.assertLess(uptime, 2.1)

    def test_update_stats(self):
        """Test statistics update"""
        self.monitor.start_time = datetime.now() - timedelta(hours=1)
        self.monitor._update_stats()
        self.assertGreater(self.monitor.stats["uptime_hours"], 0.9)
        self.assertLess(self.monitor.stats["uptime_hours"], 1.1)


class TestCryptoMonitorAsyncMethods(unittest.IsolatedAsyncioTestCase):
    """Test async methods of CryptoMonitor24_7"""

    async def asyncSetUp(self):
        """Set up async test environment"""
        self.monitor = CryptoMonitor24_7()

    @patch('src.crypto_monitor_24_7.crypto_bot')
    @patch('src.crypto_monitor_24_7.db')
    async def test_shutdown(self, mock_db, mock_crypto_bot):
        """Test shutdown process"""
        mock_crypto_bot.send_message = AsyncMock(return_value=True)
        
        self.monitor.start_time = datetime.now() - timedelta(hours=1)
        self.monitor.running = True
        self.monitor.stats["total_arbitrage_checks"] = 10
        self.monitor.stats["total_performance_analyses"] = 5
        
        await self.monitor._shutdown()
        
        self.assertFalse(self.monitor.running)
        mock_crypto_bot.send_message.assert_called_once()

    @patch('src.crypto_monitor_24_7.monitor_real_exchange_prices')
    @patch('src.crypto_monitor_24_7.detect_arbitrage_opportunities')
    @patch('src.crypto_monitor_24_7.db')
    @patch('src.crypto_monitor_24_7.smart_alerts')
    async def test_arbitrage_check_cycle_no_opportunities(self, mock_smart_alerts, mock_db, mock_detect_arb, mock_monitor_prices):
        """Test arbitrage check cycle with no opportunities"""
        # Mock dependencies
        mock_monitor_prices.return_value = {"binance": 45000, "coinbase": 45100}
        mock_detect_arb.return_value = []
        mock_smart_alerts.process_all_alerts = AsyncMock(return_value={"arbitrage_alerts": 0})
        mock_db.save_price_data = MagicMock()
        
        await self.monitor._arbitrage_check_cycle()
        
        self.assertEqual(self.monitor.stats["total_arbitrage_checks"], 1)
        self.assertEqual(self.monitor.stats["arbitrage_opportunities_found"], 0)

    @patch('src.crypto_monitor_24_7.monitor_real_exchange_prices')
    @patch('src.crypto_monitor_24_7.detect_arbitrage_opportunities')
    @patch('src.crypto_monitor_24_7.db')
    @patch('src.crypto_monitor_24_7.smart_alerts')
    async def test_arbitrage_check_cycle_with_opportunities(self, mock_smart_alerts, mock_db, mock_detect_arb, mock_monitor_prices):
        """Test arbitrage check cycle with opportunities found"""
        # Mock dependencies
        mock_monitor_prices.return_value = {"binance": 45000, "coinbase": 46000}
        mock_detect_arb.return_value = [
            {
                "buy_exchange": "binance", 
                "sell_exchange": "coinbase",
                "profit_percentage": 2.2
            }
        ]
        mock_db.save_price_data = MagicMock()
        mock_db.save_arbitrage_alert = MagicMock(return_value=1)
        mock_smart_alerts.process_all_alerts = AsyncMock(return_value={"arbitrage_alerts": 1})
        
        # Reduce watchlist for predictable testing
        original_watchlist = self.monitor.config["watchlist_symbols"]
        self.monitor.config["watchlist_symbols"] = ["BTC"]
        
        await self.monitor._arbitrage_check_cycle()
        
        self.assertEqual(self.monitor.stats["total_arbitrage_checks"], 1)
        self.assertEqual(self.monitor.stats["arbitrage_opportunities_found"], 1)
        self.assertEqual(self.monitor.stats["alerts_sent"], 1)
        
        # Restore original watchlist
        self.monitor.config["watchlist_symbols"] = original_watchlist

    @patch('src.crypto_monitor_24_7.get_top_cryptocurrencies')
    @patch('src.crypto_monitor_24_7.analyze_crypto_portfolio_enhanced')
    @patch('src.crypto_monitor_24_7.db')
    @patch('src.crypto_monitor_24_7.smart_alerts')
    async def test_performance_check_cycle_first_run(self, mock_smart_alerts, mock_db, mock_analyze, mock_get_top):
        """Test performance check cycle first run"""
        # Mock dependencies
        mock_get_top.return_value = ["BTC", "ETH", "ADA"]
        mock_analyze.return_value = {
            "BTC": {"sharpe_ratio": 1.5, "annual_return": 25.0},
            "ETH": {"sharpe_ratio": 1.2, "annual_return": 20.0}
        }
        mock_db.save_performance_data = MagicMock(return_value=2)
        mock_db.save_portfolio_snapshot = MagicMock(return_value=1)
        mock_smart_alerts.process_all_alerts = AsyncMock(return_value={"performance_alerts": 0, "new_performer_alerts": 0})
        
        await self.monitor._performance_check_cycle()
        
        self.assertEqual(self.monitor.stats["total_performance_analyses"], 1)
        self.assertIsNotNone(self.monitor.last_performance_check)

    @patch('src.crypto_monitor_24_7.db')
    @patch('src.crypto_monitor_24_7.smart_alerts')
    async def test_daily_summary_cycle_wrong_hour(self, mock_smart_alerts, mock_db):
        """Test daily summary cycle when it's not the right hour"""
        # Set monitor to wrong hour
        original_hour = self.monitor.config["daily_summary_hour"]
        current_hour = datetime.now().hour
        wrong_hour = (current_hour + 1) % 24
        self.monitor.config["daily_summary_hour"] = wrong_hour
        
        await self.monitor._daily_summary_cycle()
        
        # Should not have sent summary
        self.assertIsNone(self.monitor.last_daily_summary)
        
        # Restore original hour
        self.monitor.config["daily_summary_hour"] = original_hour

    def test_check_performance_changes_no_history(self):
        """Test performance change check with no history"""
        current_performers = [("BTC", {"sharpe_ratio": 1.5})]
        result = asyncio.run(self.monitor._check_performance_changes(current_performers))
        self.assertTrue(result)  # First analysis always returns True

    def test_check_performance_changes_with_history(self):
        """Test performance change check with existing history"""
        # Set up history
        past_time = datetime.now() - timedelta(minutes=15)
        self.monitor.performance_history[past_time] = [("BTC", {"sharpe_ratio": 1.0})]
        
        # Small change - should not trigger
        current_performers = [("BTC", {"sharpe_ratio": 1.1})]
        result = asyncio.run(self.monitor._check_performance_changes(current_performers))
        self.assertFalse(result)


class TestCryptoMonitorErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test error handling in CryptoMonitor24_7"""

    async def asyncSetUp(self):
        """Set up async test environment"""
        self.monitor = CryptoMonitor24_7()

    @patch('src.crypto_monitor_24_7.monitor_real_exchange_prices')
    async def test_arbitrage_check_cycle_with_exception(self, mock_monitor_prices):
        """Test arbitrage check cycle handles exceptions gracefully"""
        mock_monitor_prices.side_effect = Exception("API Error")
        
        # Should not raise exception
        await self.monitor._arbitrage_check_cycle()
        
        # Stats should still be updated
        self.assertEqual(self.monitor.stats["total_arbitrage_checks"], 1)

    @patch('src.crypto_monitor_24_7.get_top_cryptocurrencies')
    async def test_performance_check_cycle_with_exception(self, mock_get_top):
        """Test performance check cycle handles exceptions gracefully"""
        mock_get_top.side_effect = Exception("Data Error")
        
        # Should not raise exception
        await self.monitor._performance_check_cycle()
        
        # Should not increment performance analyses due to error
        self.assertEqual(self.monitor.stats["total_performance_analyses"], 0)

    @patch('src.crypto_monitor_24_7.smart_alerts')
    async def test_daily_summary_cycle_with_exception(self, mock_smart_alerts):
        """Test daily summary cycle handles exceptions gracefully"""
        mock_smart_alerts.process_all_alerts.side_effect = Exception("Smart Alerts Error")
        
        # Set to correct hour to trigger summary
        self.monitor.config["daily_summary_hour"] = datetime.now().hour
        
        # Should not raise exception
        await self.monitor._daily_summary_cycle()
        
        # Should not have set last_daily_summary due to error
        self.assertIsNone(self.monitor.last_daily_summary)


class TestCryptoMonitorIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CryptoMonitor24_7"""

    async def asyncSetUp(self):
        """Set up integration test environment"""
        self.monitor = CryptoMonitor24_7()

    @patch('src.crypto_monitor_24_7.crypto_bot')
    async def test_start_monitoring_initialization(self, mock_crypto_bot):
        """Test start_monitoring initialization without running full loop"""
        mock_crypto_bot.set_chat_id = MagicMock()
        mock_crypto_bot.send_startup_message = AsyncMock()
        mock_crypto_bot.send_message = AsyncMock()
        
        # Mock the main loop to avoid infinite execution
        with patch.object(self.monitor, '_main_monitoring_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = KeyboardInterrupt()  # Simulate user stopping
            
            await self.monitor.start_monitoring("test_chat_id")
            
            self.assertIsNotNone(self.monitor.start_time)
            mock_crypto_bot.set_chat_id.assert_called_once_with("test_chat_id")
            mock_crypto_bot.send_startup_message.assert_called_once()


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)