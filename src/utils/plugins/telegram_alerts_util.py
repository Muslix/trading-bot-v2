"""
Telegram Alerts Utility Plugin - telegram alert functionality
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..base import UtilPlugin, UtilConfig


class TelegramAlertsUtil(UtilPlugin):
    """
    Telegram alerts utility plugin.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.message_count = 0
        self.last_message_time = None
        self.telegram_bot = None
    
    async def _initialize_util(self) -> bool:
        """Initialize Telegram alerts utility."""
        try:
            # Import original telegram alerts functionality
            from ..telegram_alerts import (
                send_telegram_message,
                send_error_alert,
                send_info_alert,
                format_alert_message,
                get_bot_info
            )
            
            # Store functions for use
            self.send_telegram_message = send_telegram_message
            self.send_error_alert = send_error_alert
            self.send_info_alert = send_info_alert
            self.format_alert_message = format_alert_message
            self.get_bot_info = get_bot_info
            
            self.logger.info("Telegram alerts utility initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import telegram alerts: {e}")
            return False
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process telegram alert operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "send_message")
        
        if action == "send_message":
            return await self._send_message(data)
        elif action == "send_error":
            return await self._send_error_alert(data)
        elif action == "send_info":
            return await self._send_info_alert(data)
        elif action == "format_message":
            return self._format_message(data)
        elif action == "get_bot_info":
            return await self._get_bot_info()
        elif action == "get_stats":
            return self._get_telegram_stats()
        else:
            raise ValueError(f"Unknown telegram action: {action}")
    
    async def _send_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a telegram message."""
        message = data.get("message", "")
        
        if not message:
            return {"success": False, "error": "No message provided"}
        
        try:
            if hasattr(self, 'send_telegram_message'):
                result = await self.send_telegram_message(message)
                
                # Update statistics
                self.message_count += 1
                self.last_message_time = datetime.now()
                
                return {
                    "success": True,
                    "message_sent": message,
                    "result": result,
                    "total_messages": self.message_count
                }
            else:
                return {"success": False, "error": "Telegram not initialized"}
                
        except Exception as e:
            self.logger.error(f"Failed to send telegram message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_error_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an error alert via telegram."""
        message = data.get("message", "")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'send_error_alert'):
                result = await self.send_error_alert(message, context)
                
                self.message_count += 1
                self.last_message_time = datetime.now()
                
                return {
                    "success": True,
                    "alert_type": "error",
                    "message": message,
                    "result": result
                }
            else:
                return {"success": False, "error": "Telegram not initialized"}
                
        except Exception as e:
            self.logger.error(f"Failed to send error alert: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_info_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an info alert via telegram."""
        message = data.get("message", "")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'send_info_alert'):
                result = await self.send_info_alert(message, context)
                
                self.message_count += 1
                self.last_message_time = datetime.now()
                
                return {
                    "success": True,
                    "alert_type": "info", 
                    "message": message,
                    "result": result
                }
            else:
                return {"success": False, "error": "Telegram not initialized"}
                
        except Exception as e:
            self.logger.error(f"Failed to send info alert: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format a message for telegram."""
        message = data.get("message", "")
        alert_type = data.get("alert_type", "info")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'format_alert_message'):
                formatted = self.format_alert_message(message, alert_type, context)
                
                return {
                    "success": True,
                    "original_message": message,
                    "formatted_message": formatted,
                    "alert_type": alert_type
                }
            else:
                # Simple fallback formatting
                emoji = "🚨" if alert_type == "error" else "ℹ️"
                formatted = f"{emoji} {message}"
                
                return {
                    "success": True,
                    "original_message": message,
                    "formatted_message": formatted,
                    "alert_type": alert_type
                }
                
        except Exception as e:
            self.logger.error(f"Failed to format message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_bot_info(self) -> Dict[str, Any]:
        """Get telegram bot information."""
        try:
            if hasattr(self, 'get_bot_info'):
                info = await self.get_bot_info()
                
                return {
                    "success": True,
                    "bot_info": info
                }
            else:
                return {"success": False, "error": "Bot info not available"}
                
        except Exception as e:
            self.logger.error(f"Failed to get bot info: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_telegram_stats(self) -> Dict[str, Any]:
        """Get telegram statistics."""
        return {
            "total_messages_sent": self.message_count,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
            "telegram_available": hasattr(self, 'send_telegram_message'),
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }