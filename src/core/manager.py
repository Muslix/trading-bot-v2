"""
Universal manager for orchestrating plugins across all modules.

This manager provides a consistent way to load, initialize, execute, and monitor
plugins for all modules (Alerts, Data Sources, Database, API, etc.).
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .base import UniversalPlugin, ModuleConfig
from .factory import UniversalFactory
from .exceptions import ManagerError, PluginNotFoundError, PluginExecutionError

logger = logging.getLogger(__name__)


class BaseManager:
    """Base class for all plugin managers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_initialized = False
        
    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize the manager"""
        self.is_initialized = True
        
    async def cleanup(self):
        """Cleanup manager resources"""
        self.is_initialized = False
        
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check"""
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "initialized": self.is_initialized
        }


class UniversalManager(BaseManager):
    """
    Universal manager for orchestrating plugins across all modules.
    
    This manager handles:
    - Plugin loading and initialization
    - Plugin execution with prioritization
    - Error handling and recovery
    - Health monitoring and metrics
    - Resource management
    """
    
    def __init__(self, module_name: str, auto_discover_path: str = None):
        super().__init__()
        self.module_name = module_name
        self.plugins: Dict[str, UniversalPlugin] = {}
        self.factory = UniversalFactory(module_name)
        self.logger = logging.getLogger(f"{__name__}.{module_name}")
        
        # Execution settings
        self.max_concurrent_executions = 10
        self.execution_timeout = 300.0  # 5 minutes default
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        
        # Statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.initialized_at = None
        
        # Auto-discovery
        if auto_discover_path:
            try:
                discovered = self.factory.auto_discover(auto_discover_path)
                self.logger.info(f"Auto-discovered {discovered} plugins for {module_name}")
            except Exception as e:
                self.logger.warning(f"Auto-discovery failed for {module_name}: {e}")
    
    async def initialize(self) -> bool:
        """
        Initialize the manager and all registered plugins.
        
        Returns:
            bool: True if initialization was successful
        """
        if self.is_initialized:
            self.logger.debug(f"Manager for {self.module_name} already initialized")
            return True
        
        try:
            self.logger.info(f"Initializing manager for {self.module_name}")
            
            # Load plugins from factory
            plugin_names = self.factory.list_available()
            self.logger.info(f"Found {len(plugin_names)} registered plugins: {plugin_names}")
            
            # Create plugin instances
            initialization_tasks = []
            for plugin_name in plugin_names:
                try:
                    # Create plugin with default config (can be overridden later)
                    config = ModuleConfig()
                    plugin = self.factory.create(plugin_name, config)
                    self.plugins[plugin_name] = plugin
                    
                    # Add initialization task
                    initialization_tasks.append(self._initialize_plugin(plugin_name, plugin))
                    
                except Exception as e:
                    self.logger.error(f"Failed to create plugin {plugin_name}: {e}")
                    continue
            
            # Initialize all plugins concurrently
            if initialization_tasks:
                results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
                
                # Check results
                successful_inits = 0
                for i, result in enumerate(results):
                    plugin_name = plugin_names[i]
                    if isinstance(result, Exception):
                        self.logger.error(f"Plugin {plugin_name} initialization failed: {result}")
                        # Remove failed plugin
                        if plugin_name in self.plugins:
                            del self.plugins[plugin_name]
                    elif result:
                        successful_inits += 1
                
                self.logger.info(f"Successfully initialized {successful_inits}/{len(plugin_names)} plugins")
            
            self.is_initialized = True
            self.initialized_at = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Manager initialization failed for {self.module_name}: {e}")
            return False
    
    async def _initialize_plugin(self, plugin_name: str, plugin: UniversalPlugin) -> bool:
        """Initialize a single plugin."""
        try:
            return await plugin.initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
            return False
    
    async def register_plugin(self, name: str, plugin_class, config: ModuleConfig = None) -> bool:
        """
        Register and initialize a new plugin.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class
            config: Plugin configuration
            
        Returns:
            bool: True if registration was successful
        """
        try:
            # Register with factory
            self.factory.register(name, plugin_class)
            
            # Create and initialize instance
            config = config or ModuleConfig()
            plugin = self.factory.create(name, config)
            
            # Initialize plugin
            if await plugin.initialize():
                self.plugins[name] = plugin
                self.logger.info(f"Successfully registered and initialized plugin {name}")
                return True
            else:
                self.logger.error(f"Failed to initialize registered plugin {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to register plugin {name}: {e}")
            return False
    
    async def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin and cleanup its resources.
        
        Args:
            name: Plugin name to unregister
            
        Returns:
            bool: True if unregistration was successful
        """
        try:
            if name in self.plugins:
                plugin = self.plugins[name]
                await plugin.cleanup()
                del self.plugins[name]
            
            self.factory.unregister(name)
            self.logger.info(f"Successfully unregistered plugin {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister plugin {name}: {e}")
            return False
    
    async def execute_plugin(self, plugin_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific plugin.
        
        Args:
            plugin_name: Name of plugin to execute
            data: Input data for plugin
            
        Returns:
            Dict containing execution results
            
        Raises:
            PluginNotFoundError: If plugin is not found
        """
        if not self.is_initialized:
            await self.initialize()
        
        if plugin_name not in self.plugins:
            available = list(self.plugins.keys())
            raise PluginNotFoundError(plugin_name, f"{self.module_name}. Available: {available}")
        
        plugin = self.plugins[plugin_name]
        
        # Check if plugin is enabled
        if not plugin.config.enabled:
            self.logger.debug(f"Plugin {plugin_name} is disabled, skipping execution")
            return {"skipped": True, "reason": "disabled", "plugin": plugin_name}
        
        try:
            self.total_executions += 1
            
            # Execute plugin
            result = await plugin.execute(data)
            
            if result.get("success", False):
                self.successful_executions += 1
            else:
                self.failed_executions += 1
            
            return result
            
        except Exception as e:
            self.failed_executions += 1
            error_msg = f"Plugin {plugin_name} execution failed: {str(e)}"
            self.logger.error(error_msg)
            raise PluginExecutionError(plugin_name, str(e), self.module_name)
    
    async def execute_all(self, data: Dict[str, Any], 
                         prioritized: bool = True,
                         max_concurrent: int = None) -> Dict[str, Any]:
        """
        Execute all enabled plugins.
        
        Args:
            data: Input data for plugins
            prioritized: Whether to execute in priority order
            max_concurrent: Maximum concurrent executions
            
        Returns:
            Dict containing results from all plugins
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not self.plugins:
            self.logger.warning(f"No plugins available for {self.module_name}")
            return {}
        
        # Filter enabled plugins
        enabled_plugins = {
            name: plugin for name, plugin in self.plugins.items()
            if plugin.config.enabled
        }
        
        if not enabled_plugins:
            self.logger.warning(f"No enabled plugins for {self.module_name}")
            return {}
        
        # Sort by priority if requested
        if prioritized:
            enabled_plugins = dict(sorted(
                enabled_plugins.items(),
                key=lambda x: x[1].config.priority,
                reverse=True
            ))
        
        max_concurrent = max_concurrent or self.max_concurrent_executions
        
        # Execute plugins with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(plugin_name: str) -> tuple:
            async with semaphore:
                try:
                    result = await self.execute_plugin(plugin_name, data)
                    return plugin_name, result
                except Exception as e:
                    return plugin_name, {"error": str(e), "success": False}
        
        # Execute all plugins
        tasks = [execute_with_semaphore(name) for name in enabled_plugins.keys()]
        
        try:
            results_list = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.execution_timeout
            )
            
            # Process results
            results = {}
            for result in results_list:
                if isinstance(result, Exception):
                    self.logger.error(f"Plugin execution exception: {result}")
                    continue
                
                plugin_name, plugin_result = result
                results[plugin_name] = plugin_result
            
            return results
            
        except asyncio.TimeoutError:
            self.logger.error(f"Plugin execution timed out after {self.execution_timeout}s")
            raise ManagerError("execute_all", f"Timeout after {self.execution_timeout}s", self.module_name)
    
    async def execute_by_type(self, plugin_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to execute
            data: Input data for plugins
            
        Returns:
            Dict containing results from matching plugins
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Filter plugins by type
        matching_plugins = {}
        for name, plugin in self.plugins.items():
            if plugin.config.enabled and plugin.plugin_type == plugin_type:
                matching_plugins[name] = plugin
        
        if not matching_plugins:
            self.logger.info(f"No enabled plugins of type '{plugin_type}' found")
            return {}
        
        # Execute matching plugins
        results = {}
        for plugin_name in matching_plugins.keys():
            try:
                result = await self.execute_plugin(plugin_name, data)
                results[plugin_name] = result
            except Exception as e:
                results[plugin_name] = {"error": str(e), "success": False}
        
        return results
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all plugins.
        
        Returns:
            Dict containing health status of all plugins
        """
        if not self.is_initialized:
            return {"initialized": False, "plugins": {}}
        
        plugin_health = {}
        
        # Check each plugin
        for name, plugin in self.plugins.items():
            try:
                health = await plugin.health_check()
                plugin_health[name] = health
            except Exception as e:
                plugin_health[name] = {
                    "plugin": name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Overall health
        healthy_count = sum(1 for h in plugin_health.values() if h.get("status") == "healthy")
        total_count = len(plugin_health)
        
        return {
            "manager": self.module_name,
            "initialized": self.is_initialized,
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "total_plugins": total_count,
            "healthy_plugins": healthy_count,
            "overall_health": "healthy" if healthy_count == total_count else "degraded",
            "plugins": plugin_health
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get manager and plugin metrics.
        
        Returns:
            Dict containing metrics
        """
        plugin_metrics = {}
        for name, plugin in self.plugins.items():
            try:
                plugin_metrics[name] = plugin.get_metrics()
            except Exception as e:
                plugin_metrics[name] = {"error": str(e)}
        
        return {
            "manager": self.module_name,
            "initialized": self.is_initialized,
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "total_plugins": len(self.plugins),
            "enabled_plugins": sum(1 for p in self.plugins.values() if p.config.enabled),
            "execution_stats": {
                "total_executions": self.total_executions,
                "successful_executions": self.successful_executions,
                "failed_executions": self.failed_executions,
                "success_rate": self.successful_executions / max(self.total_executions, 1) * 100
            },
            "plugins": plugin_metrics
        }
    
    async def cleanup(self) -> None:
        """
        Cleanup all plugins and manager resources.
        """
        self.logger.info(f"Cleaning up manager for {self.module_name}")
        
        # Cleanup all plugins
        cleanup_tasks = []
        for name, plugin in self.plugins.items():
            cleanup_tasks.append(self._cleanup_plugin(name, plugin))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Cleanup thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.plugins.clear()
        self.is_initialized = False
        
        self.logger.info(f"Manager cleanup complete for {self.module_name}")
    
    async def _cleanup_plugin(self, name: str, plugin: UniversalPlugin) -> None:
        """Cleanup a single plugin."""
        try:
            await plugin.cleanup()
            self.logger.debug(f"Cleaned up plugin {name}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup plugin {name}: {e}")
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all plugins with their status.
        
        Returns:
            List of plugin information
        """
        plugins_info = []
        for name, plugin in self.plugins.items():
            plugins_info.append({
                "name": name,
                "type": plugin.plugin_type,
                "enabled": plugin.config.enabled,
                "initialized": plugin.is_initialized,
                "priority": plugin.config.priority,
                "execution_count": plugin.execution_count,
                "last_execution": plugin.last_execution.isoformat() if plugin.last_execution else None,
                "last_error": plugin.last_error
            })
        
        return plugins_info
    
    def get_plugin(self, name: str) -> Optional[UniversalPlugin]:
        """
        Get a specific plugin instance.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def update_plugin_config(self, name: str, config: ModuleConfig) -> bool:
        """
        Update plugin configuration.
        
        Args:
            name: Plugin name
            config: New configuration
            
        Returns:
            bool: True if update was successful
        """
        if name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[name]
            plugin.config = config
            self.logger.info(f"Updated configuration for plugin {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update config for plugin {name}: {e}")
            return False
    
    def __str__(self) -> str:
        return f"UniversalManager({self.module_name}, {len(self.plugins)} plugins)"
    
    def __repr__(self) -> str:
        return f"UniversalManager(module='{self.module_name}', initialized={self.is_initialized}, plugins={list(self.plugins.keys())})"
