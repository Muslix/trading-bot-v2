"""
Base API Plugin for modular web API system
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from flask import Blueprint

class BaseAPIPlugin(ABC):
    """Base class for all API plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"api.{self.__class__.__name__}")
        self.blueprint: Optional[Blueprint] = None
        
    @abstractmethod
    def get_blueprint(self) -> Blueprint:
        """Return Flask blueprint with routes"""
        pass
    
    @abstractmethod
    def get_route_prefix(self) -> str:
        """Return URL prefix for this plugin's routes"""
        pass
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return self.__class__.__name__.replace('Plugin', '').lower()
    
    def initialize(self) -> bool:
        """Initialize plugin - override if needed"""
        try:
            self.blueprint = self.get_blueprint()
            self.logger.info(f"✅ API Plugin {self.name} initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize {self.name}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup plugin resources - override if needed"""
        self.logger.info(f"🧹 Cleaning up API Plugin {self.name}")
    
    def health_check(self) -> Dict[str, Any]:
        """Basic health check"""
        return {
            'plugin': self.name,
            'status': 'healthy',
            'initialized': self.blueprint is not None
        }