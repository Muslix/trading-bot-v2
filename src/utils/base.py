"""
Utils module base classes and interfaces.

This module provides the foundation for all utility plugins using the Universal Pattern.
All utility types (logging, monitoring, formatting, etc.) inherit from these base classes.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from src.core import UniversalPlugin, ModuleConfig


@dataclass 
class UtilConfig(ModuleConfig):
    """Configuration for utility plugins."""
    
    # Performance settings
    timeout_seconds: int = 30
    retry_attempts: int = 3
    cache_enabled: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    max_log_size_mb: int = 10
    
    # Resource settings
    max_memory_mb: int = 100
    cleanup_interval_minutes: int = 60
    
    def validate(self) -> bool:
        """Validate utility configuration."""
        super().validate()
        
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be non-negative")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        if self.max_memory_mb <= 0:
            raise ValueError("Max memory must be positive")
            
        return True


class UtilPlugin(UniversalPlugin):
    """
    Base class for all utility plugins.
    
    This provides the standard interface that all utilities must implement:
    - setup(): Initialize utility resources
    - cleanup(): Clean up resources
    - health_check(): Check utility health
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
    
    @property
    def plugin_type(self) -> str:
        return "util"
    
    async def _initialize(self) -> bool:
        """Initialize the utility plugin."""
        self.logger.info(f"Initializing utility plugin: {self.name}")
        
        # Validate configuration
        try:
            self.config.validate()
        except Exception as e:
            self.logger.error(f"Invalid configuration for {self.name}: {e}")
            return False
        
        # Initialize utility-specific resources
        return await self._initialize_util()
    
    @abstractmethod
    async def _initialize_util(self) -> bool:
        """Utility-specific initialization logic."""
        pass
    
    async def _execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the utility function.
        
        Args:
            data: Input data for utility processing
            
        Returns:
            Dict with utility results
        """
        try:
            result = await self.process_data(data)
            
            return {
                "success": True,
                "result": result,
                "util_type": self.get_util_type(),
                "plugin_name": self.name
            }
            
        except Exception as e:
            self.logger.error(f"Utility execution failed for {self.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "util_type": self.get_util_type(),
                "plugin_name": self.name
            }
    
    @abstractmethod
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process input data.
        
        Args:
            data: Input data for processing
            
        Returns:
            Any: Processed result
        """
        pass
    
    def get_util_type(self) -> str:
        """
        Get the utility type identifier.
        
        Returns:
            str: Utility type name
        """
        # Default: use class name without 'Util' suffix
        class_name = self.__class__.__name__
        if class_name.endswith('Util'):
            return class_name[:-4].lower()
        return class_name.lower()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check utility health status.
        
        Returns:
            Dict with health information
        """
        try:
            # Basic health check - can be overridden
            is_healthy = await self._check_health()
            
            return {
                "healthy": is_healthy,
                "plugin_name": self.name,
                "util_type": self.get_util_type(),
                "last_check": self._get_current_timestamp()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "plugin_name": self.name,
                "util_type": self.get_util_type(),
                "error": str(e),
                "last_check": self._get_current_timestamp()
            }
    
    async def _check_health(self) -> bool:
        """Override this for specific health checks."""
        return self.is_initialized
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def cleanup(self) -> bool:
        """
        Clean up utility resources.
        
        Returns:
            bool: True if cleanup was successful
        """
        try:
            await self._cleanup_util()
            self.logger.info(f"Cleaned up utility plugin: {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Cleanup failed for {self.name}: {e}")
            return False
    
    async def _cleanup_util(self) -> None:
        """Override this for specific cleanup logic."""
        pass
    
    def get_util_stats(self) -> Dict[str, Any]:
        """Get utility statistics."""
        return {
            "util_type": self.get_util_type(),
            "plugin_name": self.name,
            "initialized": self.is_initialized,
            "enabled": self.config.enabled,
            "config": {
                "timeout_seconds": getattr(self.config, 'timeout_seconds', 30),
                "retry_attempts": getattr(self.config, 'retry_attempts', 3),
                "cache_enabled": getattr(self.config, 'cache_enabled', True),
                "log_level": getattr(self.config, 'log_level', 'INFO')
            }
        }