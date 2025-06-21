"""
Utils Manager - orchestrates all utility plugins using the Universal Pattern.

This manager provides a centralized way to access and manage utility functions
with a clean, plugin-based architecture that's easily extensible.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core import UniversalManager, ModuleConfig
from .base import UtilConfig
from .plugins import (
    PerformanceUtil,
    LoggingUtil,
    SymbolNormalizerUtil,
    SystemHealthUtil,
    TelegramAlertsUtil,
    ExportUtil,
    MarketDataUtil,
    AIMLUtil,
    SecurityUtil,
    StrategyUtil,
    NotificationUtil,
    DeFiUtil,
    StrategySharingUtil
)


class UtilManager(UniversalManager):
    """
    Modern utility manager using the Universal Pattern.
    
    This provides centralized access to all utility functions with:
    - Multiple utility types as plugins
    - Individual configuration per utility type
    - Easy addition of new utility types
    - Centralized resource management
    """
    
    def __init__(self, config_dict: Optional[Dict] = None):
        super().__init__(module_name="utils")
        
        self.logger = logging.getLogger(__name__)
        self.config_dict = config_dict or {}
        
        # Statistics
        self.total_operations = 0
        self.failed_operations = 0
        self.start_time = datetime.now()
        
        # Register default utility plugins
        self._register_default_plugins()
    
    def _register_default_plugins(self):
        """Register all default utility plugins with their configurations."""
        try:
            # Performance Util
            self.factory.register("performance", PerformanceUtil)
            
            # Logging Util
            self.factory.register("logging", LoggingUtil)
            
            # Symbol Normalizer Util
            self.factory.register("symbol_normalizer", SymbolNormalizerUtil)
            
            # System Health Util
            self.factory.register("system_health", SystemHealthUtil)
            
            # Telegram Alerts Util
            self.factory.register("telegram_alerts", TelegramAlertsUtil)
            
            # Export Util
            self.factory.register("export", ExportUtil)
            
            # Market Data Util
            self.factory.register("market_data", MarketDataUtil)
            
            # AI/ML Util
            self.factory.register("aiml", AIMLUtil)
            
            # Security Util
            self.factory.register("security", SecurityUtil)
            
            # Strategy Util
            self.factory.register("strategy", StrategyUtil)
            
            # Notification Util
            self.factory.register("notification", NotificationUtil)
            
            # DeFi Util
            self.factory.register("defi", DeFiUtil)
            
            # Strategy Sharing Util
            self.factory.register("strategy_sharing", StrategySharingUtil)
            
            self.logger.info("✅ Registered all default utility plugins")
            
        except Exception as e:
            self.logger.error(f"Failed to register default plugins: {e}")
    
    async def initialize_with_configs(self, plugin_configs: Optional[Dict[str, UtilConfig]] = None):
        """
        Initialize utility manager with specific plugin configurations.
        
        Args:
            plugin_configs: Dictionary mapping plugin names to their configs
        """
        try:
            self.logger.info("Initializing Utils Manager with plugin architecture")
            
            # Create plugin instances with specific configs
            plugin_configs = plugin_configs or {}
            
            for plugin_name in self.factory.list_available():
                config = plugin_configs.get(plugin_name)
                if not config:
                    # Create default config based on plugin type
                    config = self._create_default_config(plugin_name)
                
                success = await self.register_plugin(plugin_name, self.factory.registered_plugins[plugin_name], config)
                if success:
                    self.logger.info(f"✅ Initialized {plugin_name} utility plugin")
                else:
                    self.logger.error(f"❌ Failed to initialize {plugin_name} utility plugin")
            
            # Complete initialization
            await self.initialize()
            
            self.logger.info(f"✅ Utils Manager initialized with {len(self.plugins)} plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Utils Manager: {e}")
            return False
    
    def _create_default_config(self, plugin_name: str) -> UtilConfig:
        """Create default configuration for a plugin."""
        defaults = {
            "performance": UtilConfig(
                timeout_seconds=30,
                retry_attempts=3,
                cache_enabled=True,
                log_level=self.config_dict.get('log_level', 'INFO')
            ),
            "logging": UtilConfig(
                log_level=self.config_dict.get('log_level', 'INFO'),
                log_to_file=True,
                max_log_size_mb=10
            ),
            "symbol_normalizer": UtilConfig(
                cache_enabled=True,
                timeout_seconds=5
            ),
            "system_health": UtilConfig(
                cleanup_interval_minutes=60,
                max_memory_mb=100,
                timeout_seconds=10
            ),
            "telegram_alerts": UtilConfig(
                timeout_seconds=10,
                retry_attempts=2
            ),
            "export": UtilConfig(
                timeout_seconds=60,
                max_memory_mb=200
            ),
            "market_data": UtilConfig(
                timeout_seconds=30,
                retry_attempts=3,
                cache_enabled=True
            ),
            "aiml": UtilConfig(
                timeout_seconds=30,
                cache_enabled=True
            ),
            "security": UtilConfig(
                timeout_seconds=10,
                retry_attempts=1
            ),
            "strategy": UtilConfig(
                timeout_seconds=120,
                max_memory_mb=500
            ),
            "notification": UtilConfig(
                timeout_seconds=30,
                retry_attempts=2
            ),
            "defi": UtilConfig(
                timeout_seconds=60,
                retry_attempts=3
            ),
            "strategy_sharing": UtilConfig(
                timeout_seconds=30,
                retry_attempts=2
            )
        }
        
        return defaults.get(plugin_name, UtilConfig())
    
    async def process_with_util(self, util_name: str, data: Any) -> Dict[str, Any]:
        """
        Process data with a specific utility plugin.
        
        Args:
            util_name: Name of utility plugin to use
            data: Data to process
            
        Returns:
            Dict containing processing results
        """
        if not self.is_initialized:
            await self.initialize_with_configs()
        
        try:
            plugin = self.get_plugin(util_name)
            if not plugin:
                return {
                    "success": False,
                    "error": f"Utility plugin {util_name} not found"
                }
            
            # Execute the utility
            result = await plugin._execute({"data": data})
            self.total_operations += 1
            
            if not result.get("success", False):
                self.failed_operations += 1
            
            return result
            
        except Exception as e:
            self.failed_operations += 1
            self.logger.error(f"Error using utility {util_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "util_name": util_name
            }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Run health checks on all utility plugins.
        
        Returns:
            Dict containing health status of all plugins
        """
        if not self.is_initialized:
            await self.initialize_with_configs()
        
        results = {}
        overall_healthy = True
        
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'health_check'):
                    health_result = await plugin.health_check()
                    results[plugin_name] = health_result
                    
                    if not health_result.get("healthy", False):
                        overall_healthy = False
                else:
                    results[plugin_name] = {
                        "healthy": plugin.is_initialized,
                        "plugin_name": plugin_name,
                        "note": "Basic health check only"
                    }
                    
            except Exception as e:
                results[plugin_name] = {
                    "healthy": False,
                    "plugin_name": plugin_name,
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "overall_healthy": overall_healthy,
            "plugin_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_all(self) -> Dict[str, Any]:
        """
        Clean up all utility plugins.
        
        Returns:
            Dict containing cleanup results
        """
        results = {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'cleanup'):
                    success = await plugin.cleanup()
                    results[plugin_name] = {
                        "cleaned": success,
                        "plugin_name": plugin_name
                    }
                else:
                    results[plugin_name] = {
                        "cleaned": True,
                        "plugin_name": plugin_name,
                        "note": "No cleanup required"
                    }
                    
            except Exception as e:
                results[plugin_name] = {
                    "cleaned": False,
                    "plugin_name": plugin_name,
                    "error": str(e)
                }
        
        return {
            "cleanup_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_util_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive utility statistics.
        
        Returns:
            Dict containing utility statistics
        """
        # Get base metrics from manager
        base_metrics = self.get_metrics()
        
        # Add util-specific statistics
        plugin_stats = {}
        for plugin_name, plugin in self.plugins.items():
            if hasattr(plugin, 'get_util_stats'):
                plugin_stats[plugin_name] = plugin.get_util_stats()
        
        runtime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'manager_stats': base_metrics,
            'plugin_stats': plugin_stats,
            'operation_stats': {
                'total_operations': self.total_operations,
                'failed_operations': self.failed_operations,
                'success_rate': (self.total_operations - self.failed_operations) / max(self.total_operations, 1) * 100,
                'runtime_seconds': runtime_seconds
            },
            'system_stats': {
                'total_plugins': len(self.plugins),
                'enabled_plugins': len([p for p in self.plugins.values() if p.config.enabled]),
                'initialized_plugins': len([p for p in self.plugins.values() if p.is_initialized])
            }
        }
    
    # Convenience methods for common utilities
    async def log_performance(self, func_name: str, duration: float, module: str = "unknown", context: dict = None) -> bool:
        """Log performance information."""
        try:
            result = await self.process_with_util("performance", {
                "action": "log_performance",
                "func_name": func_name,
                "duration": duration,
                "module": module,
                "context": context or {}
            })
            return result.get("success", False)
        except Exception:
            return False
    
    async def normalize_symbol(self, symbol: str) -> str:
        """Normalize a trading symbol."""
        try:
            result = await self.process_with_util("symbol_normalizer", {
                "action": "normalize",
                "symbol": symbol
            })
            if result.get("success", False):
                return result.get("result", {}).get("normalized_symbol", symbol)
        except Exception:
            pass
        return symbol
    
    async def send_telegram_alert(self, message: str) -> bool:
        """Send a Telegram alert."""
        try:
            result = await self.process_with_util("telegram_alerts", {
                "action": "send_message",
                "message": message
            })
            return result.get("success", False)
        except Exception:
            return False
    
    async def log_error(self, message: str, exception: Exception = None, context: dict = None) -> bool:
        """Log an error message."""
        try:
            result = await self.process_with_util("logging", {
                "action": "log_error",
                "message": message,
                "exception": exception,
                "context": context or {}
            })
            return result.get("success", False)
        except Exception:
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            result = await self.process_with_util("system_health", {
                "action": "health_check"
            })
            if result.get("success", False):
                return result.get("result", {})
        except Exception:
            pass
        return {"error": "Health check failed"}
    
    def get_performance_decorator(self, async_mode: bool = False):
        """Get a performance logging decorator."""
        try:
            plugin = self.get_plugin("performance")
            if plugin and hasattr(plugin, '_create_performance_decorator'):
                return plugin._create_performance_decorator({"async": async_mode})
        except Exception:
            pass
        return None


# Convenience function to create and configure the utility manager
async def create_util_manager(config_dict: Optional[Dict] = None) -> UtilManager:
    """
    Create and initialize a new UtilManager instance.
    
    Args:
        config_dict: Configuration dictionary for utility settings
        
    Returns:
        Initialized UtilManager instance
    """
    manager = UtilManager(config_dict)
    await manager.initialize_with_configs()
    return manager