"""
Monitor Manager - Manages all monitor plugins
"""

import logging
from typing import Dict, List, Any, Optional

from src.core.manager import BaseManager
from src.core.factory import PluginFactory
from .base import BaseMonitor


class MonitorManager(BaseManager):
    """Manager for monitor plugins"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.factory = PluginFactory("monitors")  
        self.plugins: Dict[str, BaseMonitor] = {}
        
    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize monitor plugins"""
        self.logger.info("Initializing Monitor Manager")
        
        # Register default monitor plugins
        await self._register_default_plugins()
        
        # Initialize plugins from config
        if config:
            await self._initialize_plugins_from_config(config)
            
    async def _register_default_plugins(self):
        """Register default monitor plugins"""
        try:
            # Register price monitor
            from .plugins.price_monitor import PriceMonitor
            self.factory.register("price", PriceMonitor)
            
            # Register volume monitor
            from .plugins.volume_monitor import VolumeMonitor
            self.factory.register("volume", VolumeMonitor)
            
            # Register network monitor
            from .plugins.network_monitor import NetworkMonitor
            self.factory.register("network", NetworkMonitor)
            
            self.logger.info("✅ Registered all default monitor plugins")
            
        except ImportError as e:
            self.logger.error(f"Failed to register default plugins: {e}")
            
    async def _initialize_plugins_from_config(self, config: Dict[str, Any]):
        """Initialize plugins from configuration"""
        for plugin_name, plugin_config in config.items():
            if plugin_config.get("enabled", True):
                try:
                    plugin = self.factory.create(plugin_name, plugin_config)
                    await plugin.initialize()
                    self.plugins[plugin_name] = plugin
                    self.logger.info(f"✅ Initialized {plugin_name} monitor")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {plugin_name} monitor: {e}")
                    
    async def monitor(self, monitor_type: str, target: Any, **kwargs) -> Optional[Dict[str, Any]]:
        """Perform monitoring using specific monitor"""
        if monitor_type not in self.plugins:
            self.logger.error(f"Monitor {monitor_type} not found")
            return None
            
        try:
            return await self.plugins[monitor_type].monitor(target, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {monitor_type} monitoring: {e}")
            return {"error": str(e)}
            
    async def batch_monitor(self, monitor_type: str, targets: List[Any], **kwargs) -> List[Dict[str, Any]]:
        """Perform batch monitoring using specific monitor"""
        if monitor_type not in self.plugins:
            self.logger.error(f"Monitor {monitor_type} not found")
            return []
            
        try:
            return await self.plugins[monitor_type].batch_monitor(targets, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {monitor_type} batch monitoring: {e}")
            return []
            
    async def start_monitoring(self, monitor_type: str, target: Any, **kwargs):
        """Start continuous monitoring"""
        if monitor_type in self.plugins:
            await self.plugins[monitor_type].start_monitoring(target, **kwargs)
            
    async def stop_monitoring(self, monitor_type: str):
        """Stop continuous monitoring"""
        if monitor_type in self.plugins:
            await self.plugins[monitor_type].stop_monitoring()
            
    async def get_available_monitors(self) -> List[str]:
        """Get list of available monitors"""
        return list(self.plugins.keys())
        
    async def cleanup(self):
        """Cleanup all monitor plugins"""
        for plugin in self.plugins.values():
            await plugin.cleanup()
        self.plugins.clear()


async def create_monitor_manager(config: Dict[str, Any] = None) -> MonitorManager:
    """Create and initialize monitor manager"""
    manager = MonitorManager()
    await manager.initialize(config)
    return manager