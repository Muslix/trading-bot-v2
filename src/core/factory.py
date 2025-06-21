"""
Universal factory for creating plugin instances across all modules.

This factory provides a consistent way to register and create plugin instances
for all modules (Alerts, Data Sources, Database, API, etc.).
"""

import importlib
import inspect
import pkgutil
from typing import Dict, Type, List, Optional, Any
import logging
from pathlib import Path

from .base import UniversalPlugin, ModuleConfig
from .exceptions import FactoryError, PluginNotFoundError, PluginInitializationError

logger = logging.getLogger(__name__)


class UniversalFactory:
    """
    Universal factory for creating plugin instances across all modules.
    
    This factory can:
    - Register plugin classes manually
    - Auto-discover plugins from module directories
    - Create plugin instances with configuration
    - Validate plugin implementations
    """
    
    def __init__(self, module_name: str = None):
        self.module_name = module_name
        self.registered_plugins: Dict[str, Type[UniversalPlugin]] = {}
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.{module_name}" if module_name else __name__)
    
    def register(self, name: str, plugin_class: Type[UniversalPlugin], 
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Register a plugin class with the factory.
        
        Args:
            name: Plugin name/identifier
            plugin_class: Plugin class that inherits from UniversalPlugin
            metadata: Optional plugin metadata
            
        Raises:
            FactoryError: If registration fails
        """
        try:
            # Validate plugin class
            if not issubclass(plugin_class, UniversalPlugin):
                raise FactoryError(
                    "register", 
                    name, 
                    f"Plugin class must inherit from UniversalPlugin, got {plugin_class.__name__}",
                    self.module_name
                )
            
            # Check if plugin implements required abstract methods
            if inspect.isabstract(plugin_class):
                abstract_methods = [
                    method for method in plugin_class.__abstractmethods__
                ]
                raise FactoryError(
                    "register",
                    name,
                    f"Plugin class has unimplemented abstract methods: {abstract_methods}",
                    self.module_name
                )
            
            self.registered_plugins[name] = plugin_class
            self.plugin_metadata[name] = metadata or {}
            
            self.logger.info(f"Registered plugin '{name}' from class {plugin_class.__name__}")
            
        except Exception as e:
            if isinstance(e, FactoryError):
                raise
            raise FactoryError("register", name, str(e), self.module_name)
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name to unregister
            
        Returns:
            bool: True if plugin was unregistered, False if not found
        """
        if name in self.registered_plugins:
            del self.registered_plugins[name]
            if name in self.plugin_metadata:
                del self.plugin_metadata[name]
            self.logger.info(f"Unregistered plugin '{name}'")
            return True
        return False
    
    def create(self, name: str, config: ModuleConfig) -> UniversalPlugin:
        """
        Create a plugin instance.
        
        Args:
            name: Plugin name to create
            config: Configuration for the plugin
            
        Returns:
            UniversalPlugin: Plugin instance
            
        Raises:
            PluginNotFoundError: If plugin is not registered
            PluginInitializationError: If plugin creation fails
        """
        if name not in self.registered_plugins:
            available = list(self.registered_plugins.keys())
            raise PluginNotFoundError(
                name, 
                f"{self.module_name}. Available plugins: {available}" if self.module_name else None
            )
        
        try:
            plugin_class = self.registered_plugins[name]
            plugin = plugin_class(config)
            
            self.logger.debug(f"Created plugin instance '{name}' of type {plugin_class.__name__}")
            return plugin
            
        except Exception as e:
            raise PluginInitializationError(name, str(e), self.module_name)
    
    def auto_discover(self, package_path: str, plugin_type: str = None) -> int:
        """
        Auto-discover and register plugins from a package directory.
        
        Args:
            package_path: Path to the package containing plugins (e.g., 'src.alerts.plugins')
            plugin_type: Optional filter for plugin type
            
        Returns:
            int: Number of plugins discovered and registered
            
        Raises:
            FactoryError: If discovery fails
        """
        try:
            discovered_count = 0
            
            # Import the package
            try:
                package = importlib.import_module(package_path)
            except ImportError as e:
                raise FactoryError("auto_discover", package_path, f"Failed to import package: {e}", self.module_name)
            
            # Get package directory
            if hasattr(package, '__path__'):
                package_dir = package.__path__[0]
            else:
                raise FactoryError("auto_discover", package_path, "Package has no __path__ attribute", self.module_name)
            
            # Iterate through modules in the package
            for importer, modname, ispkg in pkgutil.iter_modules([package_dir]):
                if ispkg:
                    continue  # Skip sub-packages
                
                try:
                    # Import the module
                    full_modname = f"{package_path}.{modname}"
                    module = importlib.import_module(full_modname)
                    
                    # Find plugin classes in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Skip if not a UniversalPlugin subclass
                        if not issubclass(obj, UniversalPlugin):
                            continue
                        
                        # Skip the base UniversalPlugin class itself
                        if obj is UniversalPlugin:
                            continue
                        
                        # Skip abstract classes
                        if inspect.isabstract(obj):
                            continue
                        
                        # Filter by plugin type if specified
                        if plugin_type:
                            try:
                                # Create temporary instance to check plugin_type
                                temp_config = ModuleConfig()
                                temp_instance = obj(temp_config)
                                if temp_instance.plugin_type != plugin_type:
                                    continue
                            except Exception:
                                # If we can't create instance, skip
                                continue
                        
                        # Register the plugin
                        plugin_name = name.lower().replace('plugin', '').replace('_', '')
                        if not plugin_name:
                            plugin_name = name.lower()
                        
                        # Avoid duplicate registrations
                        if plugin_name not in self.registered_plugins:
                            metadata = {
                                'module': full_modname,
                                'class_name': name,
                                'auto_discovered': True
                            }
                            self.register(plugin_name, obj, metadata)
                            discovered_count += 1
                
                except Exception as e:
                    self.logger.warning(f"Failed to process module {modname}: {e}")
                    continue
            
            self.logger.info(f"Auto-discovered {discovered_count} plugins from {package_path}")
            return discovered_count
            
        except Exception as e:
            if isinstance(e, FactoryError):
                raise
            raise FactoryError("auto_discover", package_path, str(e), self.module_name)
    
    def list_available(self) -> List[str]:
        """
        List all registered plugin names.
        
        Returns:
            List[str]: List of registered plugin names
        """
        return list(self.registered_plugins.keys())
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a registered plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            Dict with plugin information or None if not found
        """
        if name not in self.registered_plugins:
            return None
        
        plugin_class = self.registered_plugins[name]
        metadata = self.plugin_metadata.get(name, {})
        
        return {
            'name': name,
            'class': plugin_class.__name__,
            'module': plugin_class.__module__,
            'docstring': plugin_class.__doc__,
            'metadata': metadata,
            'abstract_methods': list(plugin_class.__abstractmethods__) if hasattr(plugin_class, '__abstractmethods__') else [],
        }
    
    def validate_plugin(self, name: str) -> Dict[str, Any]:
        """
        Validate a registered plugin.
        
        Args:
            name: Plugin name to validate
            
        Returns:
            Dict with validation results
        """
        if name not in self.registered_plugins:
            return {
                'valid': False,
                'errors': [f"Plugin '{name}' not registered"]
            }
        
        errors = []
        warnings = []
        
        try:
            plugin_class = self.registered_plugins[name]
            
            # Check if it's a proper subclass
            if not issubclass(plugin_class, UniversalPlugin):
                errors.append("Plugin must inherit from UniversalPlugin")
            
            # Check if abstract methods are implemented
            if inspect.isabstract(plugin_class):
                abstract_methods = list(plugin_class.__abstractmethods__)
                errors.append(f"Unimplemented abstract methods: {abstract_methods}")
            
            # Try to create instance with default config
            try:
                test_config = ModuleConfig()
                test_instance = plugin_class(test_config)
                
                # Check if plugin_type is implemented
                try:
                    plugin_type = test_instance.plugin_type
                    if not plugin_type or not isinstance(plugin_type, str):
                        errors.append("plugin_type must return a non-empty string")
                except Exception as e:
                    errors.append(f"plugin_type property error: {e}")
                
            except Exception as e:
                errors.append(f"Failed to create instance: {e}")
            
            # Check if plugin has docstring
            if not plugin_class.__doc__:
                warnings.append("Plugin class has no docstring")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get factory statistics.
        
        Returns:
            Dict with factory statistics
        """
        plugin_types = {}
        auto_discovered = 0
        manual_registered = 0
        
        for name, metadata in self.plugin_metadata.items():
            if metadata.get('auto_discovered', False):
                auto_discovered += 1
            else:
                manual_registered += 1
            
            # Try to get plugin type
            try:
                plugin_class = self.registered_plugins[name]
                temp_config = ModuleConfig()
                temp_instance = plugin_class(temp_config)
                plugin_type = temp_instance.plugin_type
                plugin_types[plugin_type] = plugin_types.get(plugin_type, 0) + 1
            except Exception:
                plugin_types['unknown'] = plugin_types.get('unknown', 0) + 1
        
        return {
            'total_plugins': len(self.registered_plugins),
            'auto_discovered': auto_discovered,
            'manually_registered': manual_registered,
            'plugin_types': plugin_types,
            'module': self.module_name
        }


# Alias for backward compatibility
PluginFactory = UniversalFactory


def create_plugin_factory(module_name: str) -> UniversalFactory:
    """Create a plugin factory for a specific module"""
    return UniversalFactory(module_name)
