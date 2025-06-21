"""
Analyzer Manager - Manages all analyzer plugins
"""

import logging
from typing import Dict, List, Any, Optional

from src.core.manager import BaseManager
from src.core.factory import PluginFactory
from .base import BaseAnalyzer


class AnalyzerManager(BaseManager):
    """Manager for analyzer plugins"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.factory = PluginFactory("analyzers")
        self.plugins: Dict[str, BaseAnalyzer] = {}
        
    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize analyzer plugins"""
        self.logger.info("Initializing Analyzer Manager")
        
        # Register default analyzer plugins
        await self._register_default_plugins()
        
        # Initialize plugins from config
        if config:
            await self._initialize_plugins_from_config(config)
            
    async def _register_default_plugins(self):
        """Register default analyzer plugins"""
        try:
            # Register arbitrage analyzer
            from .plugins.arbitrage_analyzer import ArbitrageAnalyzer
            self.factory.register("arbitrage", ArbitrageAnalyzer)
            
            # Register portfolio analyzer
            from .plugins.portfolio_analyzer import PortfolioAnalyzer
            self.factory.register("portfolio", PortfolioAnalyzer)
            
            # Register technical analyzer
            from .plugins.technical_analyzer import TechnicalAnalyzer
            self.factory.register("technical", TechnicalAnalyzer)
            
            # Register historical analyzer
            from .plugins.historical_analyzer import HistoricalAnalyzer
            self.factory.register("historical", HistoricalAnalyzer)
            
            self.logger.info("✅ Registered all default analyzer plugins")
            
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
                    self.logger.info(f"✅ Initialized {plugin_name} analyzer")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {plugin_name} analyzer: {e}")
                    
    async def analyze(self, analyzer_type: str, data: Any, **kwargs) -> Optional[Dict[str, Any]]:
        """Perform analysis using specific analyzer"""
        if analyzer_type not in self.plugins:
            self.logger.error(f"Analyzer {analyzer_type} not found")
            return None
            
        try:
            return await self.plugins[analyzer_type].analyze(data, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {analyzer_type} analysis: {e}")
            return {"error": str(e)}
            
    async def batch_analyze(self, analyzer_type: str, data_list: List[Any], **kwargs) -> List[Dict[str, Any]]:
        """Perform batch analysis using specific analyzer"""
        if analyzer_type not in self.plugins:
            self.logger.error(f"Analyzer {analyzer_type} not found")
            return []
            
        try:
            return await self.plugins[analyzer_type].batch_analyze(data_list, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {analyzer_type} batch analysis: {e}")
            return []
            
    async def get_available_analyzers(self) -> List[str]:
        """Get list of available analyzers"""
        return list(self.plugins.keys())
        
    async def cleanup(self):
        """Cleanup all analyzer plugins"""
        for plugin in self.plugins.values():
            await plugin.cleanup()
        self.plugins.clear()


async def create_analyzer_manager(config: Dict[str, Any] = None) -> AnalyzerManager:
    """Create and initialize analyzer manager"""
    manager = AnalyzerManager()
    await manager.initialize(config)
    return manager