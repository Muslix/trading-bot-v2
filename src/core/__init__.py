"""
Core module providing universal base classes and patterns for all trading bot modules.

This module defines the universal design patterns that are used across all modules:
- Alerts, Data Sources, Database, API, etc.

The core patterns include:
- UniversalPlugin: Base class for all plugin implementations
- UniversalManager: Base manager for orchestrating plugins  
- UniversalFactory: Factory for creating plugin instances
- ModuleConfig: Type-safe configuration base class
"""

from .base import UniversalPlugin, ModuleConfig
from .manager import UniversalManager
from .factory import UniversalFactory
from .exceptions import ModuleError, PluginNotFoundError, PluginExecutionError

__all__ = [
    'UniversalPlugin',
    'ModuleConfig', 
    'UniversalManager',
    'UniversalFactory',
    'ModuleError',
    'PluginNotFoundError',
    'PluginExecutionError'
]
