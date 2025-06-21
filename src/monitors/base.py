"""
Base Monitor Plugin Class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

from src.core.base import BasePlugin, UniversalPlugin, ModuleConfig


class BaseMonitor(UniversalPlugin):
    """Base class for all monitor plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        # Convert dict config to ModuleConfig if needed
        if isinstance(config, dict):
            module_config = ModuleConfig()
            module_config.custom_settings = config
            config = module_config
        
        super().__init__(config)
        self.logger = logging.getLogger(f"monitor.{self.__class__.__name__}")
        self.is_running = False
        
    @abstractmethod
    async def monitor(self, target: Any, **kwargs) -> Dict[str, Any]:
        """Monitor the specified target"""
        pass
    
    @abstractmethod
    def get_monitor_type(self) -> str:
        """Return the type of monitor (e.g. 'price', 'volume', 'network')"""
        pass
        
    # Implement UniversalPlugin abstract methods
    async def _initialize(self) -> bool:
        """Initialize the monitor"""
        return True
        
    @property
    def plugin_type(self) -> str:
        """Plugin type identifier"""
        return "monitor"
        
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Execute monitoring"""
        target = data.get("target")
        kwargs = data.get("kwargs", {})
        return await self.monitor(target, **kwargs)
        
    async def start_monitoring(self, target: Any, **kwargs):
        """Start continuous monitoring"""
        self.is_running = True
        self.logger.info(f"Starting {self.get_monitor_type()} monitoring")
        
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_running = False
        self.logger.info(f"Stopping {self.get_monitor_type()} monitoring")
        
    async def batch_monitor(self, targets: List[Any], **kwargs) -> List[Dict[str, Any]]:
        """Monitor multiple targets in batch"""
        results = []
        for target in targets:
            try:
                result = await self.monitor(target, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error monitoring target {target}: {e}")
                results.append({"target": target, "error": str(e)})
        return results