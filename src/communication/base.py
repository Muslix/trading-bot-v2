"""
Base Communication Plugin Class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

from src.core.base import BasePlugin, UniversalPlugin, ModuleConfig


class BaseCommunication(UniversalPlugin):
    """Base class for all communication plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        # Convert dict config to ModuleConfig if needed
        if isinstance(config, dict):
            module_config = ModuleConfig()
            module_config.custom_settings = config
            config = module_config
        
        super().__init__(config)
        self.logger = logging.getLogger(f"communication.{self.__class__.__name__}")
        self.is_connected = False
        
    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> bool:
        """Send a message"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection"""
        pass
        
    @abstractmethod
    async def disconnect(self):
        """Close connection"""
        pass
    
    @abstractmethod
    def get_communication_type(self) -> str:
        """Return the type of communication (e.g. 'telegram', 'email', 'slack')"""
        pass
        
    # Implement UniversalPlugin abstract methods
    async def _initialize(self) -> bool:
        """Initialize the communication plugin"""
        return await self.connect()
        
    @property
    def plugin_type(self) -> str:
        """Plugin type identifier"""
        return "communication"
        
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """Execute communication"""
        message = data.get("message", "")
        kwargs = data.get("kwargs", {})
        return await self.send_message(message, **kwargs)
        
    async def send_formatted_message(self, template: str, data: Dict[str, Any], **kwargs) -> bool:
        """Send a formatted message using template"""
        try:
            formatted_message = template.format(**data)
            return await self.send_message(formatted_message, **kwargs)
        except Exception as e:
            self.logger.error(f"Error formatting message: {e}")
            return False
            
    async def broadcast_message(self, message: str, recipients: List[str], **kwargs) -> Dict[str, bool]:
        """Send message to multiple recipients"""
        results = {}
        for recipient in recipients:
            try:
                success = await self.send_message(message, recipient=recipient, **kwargs)
                results[recipient] = success
            except Exception as e:
                self.logger.error(f"Error sending to {recipient}: {e}")
                results[recipient] = False
        return results