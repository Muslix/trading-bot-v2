"""
Communication Manager - Manages all communication plugins
"""

import logging
from typing import Dict, List, Any, Optional

from src.core.manager import BaseManager
from src.core.factory import PluginFactory
from .base import BaseCommunication


class CommunicationManager(BaseManager):
    """Manager for communication plugins"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.factory = PluginFactory("communication")
        self.plugins: Dict[str, BaseCommunication] = {}
        
    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize communication plugins"""
        self.logger.info("Initializing Communication Manager")
        
        # Register default communication plugins
        await self._register_default_plugins()
        
        # Initialize plugins from config
        if config:
            await self._initialize_plugins_from_config(config)
            
    async def _register_default_plugins(self):
        """Register default communication plugins"""
        try:
            # Register telegram plugin
            from .plugins.telegram_communication import TelegramCommunication
            self.factory.register("telegram", TelegramCommunication)
            
            # Register email plugin
            from .plugins.email_communication import EmailCommunication
            self.factory.register("email", EmailCommunication)
            
            # Register webhook plugin
            from .plugins.webhook_communication import WebhookCommunication
            self.factory.register("webhook", WebhookCommunication)
            
            self.logger.info("✅ Registered all default communication plugins")
            
        except ImportError as e:
            self.logger.error(f"Failed to register default plugins: {e}")
            
    async def _initialize_plugins_from_config(self, config: Dict[str, Any]):
        """Initialize plugins from configuration"""
        for plugin_name, plugin_config in config.items():
            if plugin_config.get("enabled", True):
                try:
                    plugin = self.factory.create(plugin_name, plugin_config)
                    await plugin.initialize()
                    
                    # Try to connect
                    if await plugin.connect():
                        self.plugins[plugin_name] = plugin
                        self.logger.info(f"✅ Initialized {plugin_name} communication")
                    else:
                        self.logger.error(f"❌ Failed to connect {plugin_name} communication")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {plugin_name} communication: {e}")
                    
    async def send_message(self, comm_type: str, message: str, **kwargs) -> bool:
        """Send message using specific communication plugin"""
        if comm_type not in self.plugins:
            self.logger.error(f"Communication plugin {comm_type} not found")
            return False
            
        try:
            return await self.plugins[comm_type].send_message(message, **kwargs)
        except Exception as e:
            self.logger.error(f"Error sending message via {comm_type}: {e}")
            return False
            
    async def broadcast_message(self, message: str, comm_types: List[str] = None, **kwargs) -> Dict[str, bool]:
        """Broadcast message to multiple communication channels"""
        if comm_types is None:
            comm_types = list(self.plugins.keys())
            
        results = {}
        for comm_type in comm_types:
            if comm_type in self.plugins:
                try:
                    success = await self.plugins[comm_type].send_message(message, **kwargs)
                    results[comm_type] = success
                except Exception as e:
                    self.logger.error(f"Error broadcasting to {comm_type}: {e}")
                    results[comm_type] = False
            else:
                results[comm_type] = False
                
        return results
        
    async def send_formatted_message(self, comm_type: str, template: str, data: Dict[str, Any], **kwargs) -> bool:
        """Send formatted message using template"""
        if comm_type not in self.plugins:
            self.logger.error(f"Communication plugin {comm_type} not found")
            return False
            
        try:
            return await self.plugins[comm_type].send_formatted_message(template, data, **kwargs)
        except Exception as e:
            self.logger.error(f"Error sending formatted message via {comm_type}: {e}")
            return False
            
    async def get_available_channels(self) -> List[str]:
        """Get list of available communication channels"""
        return list(self.plugins.keys())
        
    async def test_connections(self) -> Dict[str, bool]:
        """Test all communication connections"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                # Send a test message
                test_message = f"Test connection from {name} communication plugin"
                success = await plugin.send_message(test_message, test=True)
                results[name] = success
            except Exception as e:
                self.logger.error(f"Connection test failed for {name}: {e}")
                results[name] = False
        return results
        
    async def cleanup(self):
        """Cleanup all communication plugins"""
        for plugin in self.plugins.values():
            await plugin.disconnect()
            await plugin.cleanup()
        self.plugins.clear()


async def create_communication_manager(config: Dict[str, Any] = None) -> CommunicationManager:
    """Create and initialize communication manager"""
    manager = CommunicationManager()
    await manager.initialize(config)
    return manager