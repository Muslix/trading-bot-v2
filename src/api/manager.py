"""
API Manager for modular web API system
Manages and coordinates all API plugins
"""

import logging
from typing import Dict, List, Optional, Type
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from .base import BaseAPIPlugin


class APIManager:
    """Manager for API plugins"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger('api.manager')
        self.plugins: Dict[str, BaseAPIPlugin] = {}
        self.app: Optional[Flask] = None
        self.socketio: Optional[SocketIO] = None
        self.plugin_classes: Dict[str, Type[BaseAPIPlugin]] = {}
        
    def initialize_app(self) -> Flask:
        """Initialize Flask app with CORS and SocketIO"""
        if self.app is None:
            self.app = Flask(__name__)
            CORS(self.app)  # Enable Cross-Origin Requests
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self.logger.info("🌐 Flask app initialized with CORS and SocketIO")
        return self.app
    
    def register_plugin(self, plugin_name: str, plugin_class: Type[BaseAPIPlugin]):
        """Register a new API plugin"""
        try:
            self.plugin_classes[plugin_name] = plugin_class
            self.logger.info(f"📝 Registered API plugin: {plugin_name}")
        except Exception as e:
            self.logger.error(f"❌ Failed to register plugin {plugin_name}: {e}")
            
    def load_plugin(self, plugin_name: str, plugin_config: Dict = None) -> bool:
        """Load and initialize a plugin"""
        try:
            if plugin_name in self.plugins:
                self.logger.warning(f"⚠️ Plugin {plugin_name} already loaded")
                return True
                
            if plugin_name not in self.plugin_classes:
                self.logger.error(f"❌ Plugin {plugin_name} not registered")
                return False
                
            plugin_class = self.plugin_classes[plugin_name]
            plugin = plugin_class(plugin_config or {})
            
            if plugin.initialize():
                # Register blueprint with Flask app
                if self.app and plugin.blueprint:
                    self.app.register_blueprint(
                        plugin.blueprint, 
                        url_prefix=plugin.get_route_prefix()
                    )
                    self.logger.info(f"🔗 Registered blueprint for {plugin_name} at {plugin.get_route_prefix()}")
                
                self.plugins[plugin_name] = plugin
                return True
            else:
                self.logger.error(f"❌ Plugin {plugin_name} initialization failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str):
        """Unload and cleanup a plugin"""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
                self.logger.info(f"🗑️ Unloaded plugin: {plugin_name}")
            except Exception as e:
                self.logger.error(f"❌ Error unloading plugin {plugin_name}: {e}")
    
    def load_default_plugins(self):
        """Load all default API plugins"""
        default_plugins = [
            ('dashboard', {}),
            ('arbitrage', {}),
            ('performance', {}), 
            ('database', {}),
            ('utils', {}),
            ('websocket', {})
        ]
        
        loaded_count = 0
        for plugin_name, plugin_config in default_plugins:
            if self.load_plugin(plugin_name, plugin_config):
                loaded_count += 1
                
        self.logger.info(f"✅ Loaded {loaded_count}/{len(default_plugins)} default API plugins")
        return loaded_count
    
    def get_plugin(self, plugin_name: str) -> Optional[BaseAPIPlugin]:
        """Get a loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins"""
        return list(self.plugins.keys())
    
    def health_check(self) -> Dict:
        """Check health of all plugins"""
        health_data = {
            'api_manager': 'healthy',
            'total_plugins': len(self.plugins),
            'plugins': {}
        }
        
        for name, plugin in self.plugins.items():
            try:
                health_data['plugins'][name] = plugin.health_check()
            except Exception as e:
                health_data['plugins'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        return health_data
    
    def cleanup(self):
        """Cleanup all plugins"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
        self.logger.info("🧹 API Manager cleanup complete")


async def create_api_manager(config: Dict = None) -> APIManager:
    """Factory function to create and initialize API manager"""
    manager = APIManager(config)
    
    # Initialize Flask app
    app = manager.initialize_app()
    
    # Auto-register default plugins
    from .plugins.dashboard_plugin import DashboardPlugin
    from .plugins.arbitrage_plugin import ArbitragePlugin
    from .plugins.performance_plugin import PerformancePlugin
    from .plugins.database_plugin import DatabasePlugin
    from .plugins.utils_plugin import UtilsPlugin
    from .plugins.websocket_plugin import WebSocketPlugin
    
    manager.register_plugin('dashboard', DashboardPlugin)
    manager.register_plugin('arbitrage', ArbitragePlugin)
    manager.register_plugin('performance', PerformancePlugin)
    manager.register_plugin('database', DatabasePlugin)
    manager.register_plugin('utils', UtilsPlugin)
    manager.register_plugin('websocket', WebSocketPlugin)
    
    # Load default plugins
    manager.load_default_plugins()
    
    return manager