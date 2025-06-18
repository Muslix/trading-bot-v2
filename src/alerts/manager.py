"""
Alert Manager - orchestrates all alert plugins using the Universal Pattern.

This manager replaces the monolithic SmartAlertManager with a clean,
plugin-based architecture that's easily extensible and maintainable.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core import UniversalManager, ModuleConfig
from .base import AlertConfig
from .plugins import (
    ArbitrageAlert,
    PerformanceAlert, 
    PriceMovementAlert,
    VolumeAlert,
    DailySummaryAlert
)

# Import telegram bot for sending alerts
try:
    from src.modules.telegram_bot import crypto_bot
except ImportError:
    crypto_bot = None
    logging.warning("Telegram bot not available - alerts will be logged only")


class AlertManager(UniversalManager):
    """
    Modern alert manager using the Universal Pattern.
    
    This replaces the old SmartAlertManager with a clean, plugin-based
    architecture that supports:
    - Multiple alert types as plugins
    - Individual configuration per alert type
    - Easy addition of new alert types
    - Centralized alert sending and logging
    """
    
    def __init__(self, config_dict: Optional[Dict] = None):
        super().__init__(module_name="alerts")
        
        self.logger = logging.getLogger(__name__)
        self.config_dict = config_dict or {}
        
        # Alert sending configuration
        self.telegram_enabled = crypto_bot is not None
        self.log_all_alerts = True
        
        # Statistics
        self.alerts_sent_today = 0
        self.total_alerts_sent = 0
        self.last_reset_date = datetime.now().date()
        
        # Register default alert plugins
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Register all default alert plugins with their configurations."""
        try:
            # Arbitrage Alert
            arbitrage_config = AlertConfig(
                threshold=self.config_dict.get('arbitrage_threshold', 2.0),
                cooldown_minutes=self.config_dict.get('arbitrage_cooldown', 30),
                priority="high",
                enabled=True
            )
            self.factory.register("arbitrage", ArbitrageAlert)
            
            # Performance Alert
            performance_config = AlertConfig(
                threshold=self.config_dict.get('sharpe_change_threshold', 0.5),
                cooldown_minutes=30,
                priority="medium",
                enabled=True,
                custom_settings={"min_sharpe_for_top": 1.5}
            )
            self.factory.register("performance", PerformanceAlert)
            
            # Price Movement Alert
            price_movement_config = AlertConfig(
                threshold=self.config_dict.get('price_movement_threshold', 5.0),
                cooldown_minutes=60,
                priority="medium",
                enabled=True,
                custom_settings={"timeframe_hours": 1}
            )
            self.factory.register("price_movement", PriceMovementAlert)
            
            # Volume Alert
            volume_config = AlertConfig(
                threshold=200.0,  # 200% above normal
                cooldown_minutes=120,
                priority="low",
                enabled=False,  # Disabled by default as in original
                custom_settings={"baseline_periods": 24}
            )
            self.factory.register("volume_spike", VolumeAlert)
            
            # Daily Summary Alert
            daily_summary_config = AlertConfig(
                threshold=0,  # Not applicable for summaries
                cooldown_minutes=60,
                priority="low",
                enabled=True,
                custom_settings={"summary_hour": 8}
            )
            self.factory.register("daily_summary", DailySummaryAlert)
            
            self.logger.info("✅ Registered all default alert plugins")
            
        except Exception as e:
            self.logger.error(f"Failed to register default plugins: {e}")
    
    async def initialize_with_configs(self, plugin_configs: Optional[Dict[str, AlertConfig]] = None):
        """
        Initialize alert manager with specific plugin configurations.
        
        Args:
            plugin_configs: Dictionary mapping plugin names to their configs
        """
        try:
            self.logger.info("Initializing Alert Manager with plugin architecture")
            
            # Create plugin instances with specific configs
            plugin_configs = plugin_configs or {}
            
            for plugin_name in self.factory.list_available():
                config = plugin_configs.get(plugin_name)
                if not config:
                    # Create default config based on plugin type
                    config = self._create_default_config(plugin_name)
                
                success = await self.register_plugin(plugin_name, self.factory.registered_plugins[plugin_name], config)
                if success:
                    self.logger.info(f"✅ Initialized {plugin_name} alert plugin")
                else:
                    self.logger.error(f"❌ Failed to initialize {plugin_name} alert plugin")
            
            # Complete initialization
            await self.initialize()
            
            self.logger.info(f"✅ Alert Manager initialized with {len(self.plugins)} plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Alert Manager: {e}")
            return False
    
    def _create_default_config(self, plugin_name: str) -> AlertConfig:
        """Create default configuration for a plugin."""
        defaults = {
            "arbitrage": AlertConfig(threshold=2.0, cooldown_minutes=30, priority="high"),
            "performance": AlertConfig(threshold=0.5, cooldown_minutes=30, priority="medium"),
            "price_movement": AlertConfig(threshold=5.0, cooldown_minutes=60, priority="medium"),
            "volume_spike": AlertConfig(threshold=200.0, cooldown_minutes=120, priority="low", enabled=False),
            "daily_summary": AlertConfig(threshold=0, cooldown_minutes=60, priority="low")
        }
        
        return defaults.get(plugin_name, AlertConfig())
    
    async def process_all_alerts(self, 
                               arbitrage_opportunities: List[Dict] = None,
                               current_performers: List = None,
                               current_prices: Dict = None,
                               volume_data: Dict = None,
                               force_summary: bool = False) -> Dict[str, Any]:
        """
        Process all enabled alerts with provided data.
        
        This is the main entry point that replaces the old process_all_alerts method.
        
        Args:
            arbitrage_opportunities: List of arbitrage opportunities
            current_performers: List of current top performers
            current_prices: Dictionary of current prices
            volume_data: Dictionary of volume data
            force_summary: Force daily summary generation
            
        Returns:
            Dict containing results from all alert processing
        """
        if not self.is_initialized:
            await self.initialize_with_configs()
        
        # Reset daily counter if needed
        self._reset_daily_counter_if_needed()
        
        # Prepare consolidated data for all plugins
        consolidated_data = {
            'arbitrage_opportunities': arbitrage_opportunities or [],
            'current_performers': current_performers or [],
            'current_prices': current_prices or {},
            'volume_data': volume_data or {},
            'force_summary': force_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Processing alerts with {len(consolidated_data['arbitrage_opportunities'])} arbitrage opportunities")
        
        try:
            # Execute all alert plugins
            results = await self.execute_all(consolidated_data, prioritized=True)
            
            # Process results and send alerts
            alerts_sent = 0
            alert_summary = {
                'total_plugins_executed': len(results),
                'alerts_triggered': 0,
                'alerts_sent': 0,
                'failed_alerts': 0,
                'plugin_results': {}
            }
            
            for plugin_name, result in results.items():
                try:
                    if result.get('success', False):
                        plugin_result = result.get('result', {})
                        
                        if plugin_result.get('triggered', False):
                            alert_summary['alerts_triggered'] += 1
                            
                            # Send the alert
                            sent = await self._send_alert(
                                plugin_name,
                                plugin_result.get('message', ''),
                                plugin_result.get('priority', 'medium'),
                                plugin_result.get('data', {})
                            )
                            
                            if sent:
                                alerts_sent += 1
                                alert_summary['alerts_sent'] += 1
                        
                        alert_summary['plugin_results'][plugin_name] = {
                            'triggered': plugin_result.get('triggered', False),
                            'reason': plugin_result.get('reason', 'Success')
                        }
                    else:
                        alert_summary['failed_alerts'] += 1
                        alert_summary['plugin_results'][plugin_name] = {
                            'triggered': False,
                            'reason': result.get('error', 'Unknown error')
                        }
                        
                except Exception as e:
                    self.logger.error(f"Error processing result for {plugin_name}: {e}")
                    alert_summary['failed_alerts'] += 1
                    alert_summary['plugin_results'][plugin_name] = {
                        'triggered': False,
                        'reason': str(e)
                    }
            
            # Update statistics
            self.alerts_sent_today += alerts_sent
            self.total_alerts_sent += alerts_sent
            
            self.logger.info(f"Alert processing complete: {alerts_sent} alerts sent, {alert_summary['alerts_triggered']} triggered")
            
            return alert_summary
            
        except Exception as e:
            self.logger.error(f"Error in process_all_alerts: {e}")
            return {
                'error': str(e),
                'total_plugins_executed': 0,
                'alerts_triggered': 0,
                'alerts_sent': 0,
                'failed_alerts': 1
            }
    
    async def _send_alert(self, plugin_name: str, message: str, priority: str, data: Dict) -> bool:
        """
        Send an alert via configured channels.
        
        Args:
            plugin_name: Name of the plugin that triggered the alert
            message: Alert message to send
            priority: Alert priority level
            data: Additional alert data
            
        Returns:
            bool: True if alert was sent successfully
        """
        try:
            # Always log the alert
            if self.log_all_alerts:
                log_level = logging.WARNING if priority in ['high', 'critical'] else logging.INFO
                self.logger.log(log_level, f"ALERT [{plugin_name.upper()}]: {message}")
            
            # Send via Telegram if available
            if self.telegram_enabled and crypto_bot:
                try:
                    await crypto_bot.send_alert(message)
                    self.logger.debug(f"Alert sent via Telegram: {plugin_name}")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to send Telegram alert: {e}")
                    return False
            else:
                self.logger.debug(f"Alert logged only (Telegram not available): {plugin_name}")
                return True  # Consider logging as successful sending
                
        except Exception as e:
            self.logger.error(f"Failed to send alert for {plugin_name}: {e}")
            return False
    
    def _reset_daily_counter_if_needed(self):
        """Reset daily alert counter if it's a new day."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.alerts_sent_today = 0
            self.last_reset_date = today
            self.logger.info("Reset daily alert counter for new day")
    
    async def test_alert_plugin(self, plugin_name: str, test_data: Dict) -> Dict[str, Any]:
        """
        Test a specific alert plugin with sample data.
        
        Args:
            plugin_name: Name of plugin to test
            test_data: Test data for the plugin
            
        Returns:
            Dict containing test results
        """
        if not self.is_initialized:
            await self.initialize_with_configs()
        
        try:
            plugin = self.get_plugin(plugin_name)
            if not plugin:
                return {"error": f"Plugin {plugin_name} not found"}
            
            # Use plugin's test method to bypass cooldown
            result = await plugin.test_alert(test_data)
            
            return {
                "plugin": plugin_name,
                "test_successful": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error testing plugin {plugin_name}: {e}")
            return {
                "plugin": plugin_name,
                "test_successful": False,
                "error": str(e)
            }
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive alert statistics.
        
        Returns:
            Dict containing alert statistics
        """
        # Get base metrics from manager
        base_metrics = self.get_metrics()
        
        # Add alert-specific statistics
        plugin_stats = {}
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'get_alert_stats'):
                plugin_stats[plugin_name] = plugin.get_alert_stats()
        
        return {
            'manager_stats': base_metrics,
            'plugin_stats': plugin_stats,
            'daily_stats': {
                'alerts_sent_today': self.alerts_sent_today,
                'total_alerts_sent': self.total_alerts_sent,
                'last_reset_date': self.last_reset_date.isoformat()
            },
            'system_stats': {
                'telegram_enabled': self.telegram_enabled,
                'log_all_alerts': self.log_all_alerts,
                'total_plugins': len(self.plugins),
                'enabled_plugins': len([p for p in self.plugins.values() if p.config.enabled])
            }
        }
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a specific alert plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.config.enabled = True
            self.logger.info(f"Enabled alert plugin: {plugin_name}")
            return True
        return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a specific alert plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.config.enabled = False
            self.logger.info(f"Disabled alert plugin: {plugin_name}")
            return True
        return False
    
    async def update_plugin_threshold(self, plugin_name: str, new_threshold: float) -> bool:
        """Update threshold for a specific alert plugin."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.config.threshold = new_threshold
            self.logger.info(f"Updated {plugin_name} threshold to {new_threshold}")
            return True
        return False


# Convenience function to create and configure the alert manager
async def create_alert_manager(config_dict: Optional[Dict] = None) -> AlertManager:
    """
    Create and initialize a new AlertManager instance.
    
    Args:
        config_dict: Configuration dictionary for alert settings
        
    Returns:
        Initialized AlertManager instance
    """
    manager = AlertManager(config_dict)
    await manager.initialize_with_configs()
    return manager
