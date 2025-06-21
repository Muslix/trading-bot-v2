"""
Universal base classes and interfaces for all trading bot modules.

This module provides the core abstractions that all modules (Alerts, Data Sources, 
Database, API, etc.) inherit from to ensure consistency across the codebase.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ModuleConfig:
    """Universal configuration base class for all modules."""
    
    # Core settings
    enabled: bool = True
    priority: int = 1
    timeout: float = 30.0
    retry_count: int = 3
    
    # Module-specific settings
    custom_settings: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
        if self.priority < 0:
            raise ValueError("Priority must be non-negative")
        return True


class UniversalPlugin(ABC):
    """
    Universal base class for ALL plugins across all modules.
    
    This provides a consistent interface for:
    - Alerts (ArbitrageAlert, PerformanceAlert, etc.)
    - Data Sources (BinanceDataSource, CoinGeckoDataSource, etc.)
    - Database Repositories (PriceRepository, AlertRepository, etc.)
    - API Routes (PriceRoutes, AlertRoutes, etc.)
    """
    
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.name = self.__class__.__name__
        self.is_initialized = False
        self.logger = logging.getLogger(f"{self.__module__}.{self.name}")
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Plugin metadata
        self.created_at = datetime.now()
        self.execution_count = 0
        self.last_execution = None
        self.last_error = None
    
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful
        """
        if self.is_initialized:
            self.logger.debug(f"Plugin {self.name} already initialized")
            return True
            
        try:
            self.logger.info(f"Initializing plugin {self.name}")
            success = await self._initialize()
            self.is_initialized = success
            
            if success:
                self.logger.info(f"Plugin {self.name} initialized successfully")
            else:
                self.logger.error(f"Plugin {self.name} initialization failed")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error initializing plugin {self.name}: {e}")
            self.last_error = str(e)
            return False
    
    @abstractmethod
    async def _initialize(self) -> bool:
        """
        Plugin-specific initialization logic.
        
        Returns:
            bool: True if initialization was successful
        """
        pass
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin with retry logic and error handling.
        
        Args:
            data: Input data for plugin execution
            
        Returns:
            Dict containing execution results
        """
        if not self.is_initialized:
            await self.initialize()
            
        if not self.is_initialized:
            return {"error": "Plugin not initialized", "success": False}
        
        for attempt in range(self.config.retry_count + 1):
            try:
                self.logger.debug(f"Executing plugin {self.name} (attempt {attempt + 1})")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._execute(data),
                    timeout=self.config.timeout
                )
                
                # Update execution stats
                self.execution_count += 1
                self.last_execution = datetime.now()
                self.last_error = None
                
                self.logger.debug(f"Plugin {self.name} executed successfully")
                return {"success": True, "result": result, "plugin": self.name}
                
            except asyncio.TimeoutError:
                error_msg = f"Plugin {self.name} execution timed out after {self.config.timeout}s"
                self.logger.warning(error_msg)
                self.last_error = error_msg
                
                if attempt < self.config.retry_count:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                return {"error": error_msg, "success": False, "plugin": self.name}
                
            except Exception as e:
                error_msg = f"Plugin {self.name} execution failed: {str(e)}"
                self.logger.error(error_msg)
                self.last_error = error_msg
                
                if attempt < self.config.retry_count:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                return {"error": error_msg, "success": False, "plugin": self.name}
        
        return {"error": "Max retries exceeded", "success": False, "plugin": self.name}
    
    @abstractmethod
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """
        Plugin-specific execution logic.
        
        Args:
            data: Input data for execution
            
        Returns:
            Plugin-specific result
        """
        pass
    
    async def cleanup(self) -> None:
        """
        Cleanup plugin resources.
        """
        try:
            self.logger.info(f"Cleaning up plugin {self.name}")
            await self._cleanup()
            self.is_initialized = False
            self.logger.info(f"Plugin {self.name} cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error cleaning up plugin {self.name}: {e}")
    
    async def _cleanup(self) -> None:
        """Plugin-specific cleanup logic."""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """
        Plugin type identifier.
        
        Returns:
            str: Plugin type (e.g., 'alert', 'data_source', 'repository')
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the plugin.
        
        Returns:
            Dict containing health status
        """
        return {
            "plugin": self.name,
            "type": self.plugin_type,
            "initialized": self.is_initialized,
            "enabled": self.config.enabled,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
            "status": "healthy" if self.is_initialized and not self.last_error else "unhealthy"
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get plugin metrics for monitoring.
        
        Returns:
            Dict containing plugin metrics
        """
        return {
            "plugin": self.name,
            "type": self.plugin_type,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution,
            "last_error": self.last_error,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
            "config": {
                "enabled": self.config.enabled,
                "priority": self.config.priority,
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count
            }
        }
    
    def __str__(self) -> str:
        return f"{self.name}(type={self.plugin_type}, initialized={self.is_initialized})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"


# Alias for backward compatibility
BasePlugin = UniversalPlugin
