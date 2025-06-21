"""
Base Analyzer Plugin Class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

from src.core.base import BasePlugin, UniversalPlugin, ModuleConfig


class BaseAnalyzer(UniversalPlugin):
    """Base class for all analyzer plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        # Convert dict config to ModuleConfig if needed
        if isinstance(config, dict):
            module_config = ModuleConfig()
            module_config.custom_settings = config
            config = module_config
        
        super().__init__(config)
        self.logger = logging.getLogger(f"analyzer.{self.__class__.__name__}")
    
    @abstractmethod
    async def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Perform analysis on the given data"""
        pass
    
    @abstractmethod
    def get_analyzer_type(self) -> str:
        """Return the type of analyzer (e.g. 'arbitrage', 'portfolio', 'technical')"""
        pass
        
    # Implement UniversalPlugin abstract methods
    async def _initialize(self) -> bool:
        """Initialize the analyzer"""
        return True
        
    @property
    def plugin_type(self) -> str:
        """Plugin type identifier"""
        return "analyzer"
        
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Execute analysis"""
        return await self.analyze(data)
    
    async def batch_analyze(self, data_list: List[Any], **kwargs) -> List[Dict[str, Any]]:
        """Analyze multiple data points in batch"""
        results = []
        for data in data_list:
            try:
                result = await self.analyze(data, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error analyzing data point: {e}")
                results.append({"error": str(e)})
        return results