"""
Webhook Communication Plugin - HTTP webhooks for notifications
"""

import json
from typing import Dict, List, Any
import aiohttp
import logging

from ..base import BaseCommunication
from src.utils.decorators import async_log_performance


class WebhookCommunication(BaseCommunication):
    """Webhook communication plugin for HTTP notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.timeout = config.get("timeout", 10)
        self.verify_ssl = config.get("verify_ssl", True)
        
    def get_communication_type(self) -> str:
        return "webhook"
        
    async def connect(self) -> bool:
        """Test webhook connection"""
        if not self.webhook_url:
            self.logger.error("No webhook URL configured")
            return False
            
        try:
            # Test webhook with ping
            test_payload = {"type": "ping", "message": "Connection test"}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.post(
                    self.webhook_url,
                    json=test_payload,
                    headers=self.headers
                ) as response:
                    if response.status < 400:
                        self.is_connected = True
                        self.logger.info(f"Webhook connection successful: {response.status}")
                        return True
                    else:
                        self.logger.error(f"Webhook test failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to connect to webhook: {e}")
            self.is_connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from webhook"""
        self.is_connected = False
        self.logger.info("Disconnected from webhook")
        
    @async_log_performance
    async def send_message(self, message: str, **kwargs) -> bool:
        """Send message via webhook"""
        if not self.is_connected:
            self.logger.error("Not connected to webhook")
            return False
            
        message_type = kwargs.get("message_type", "notification")
        extra_data = kwargs.get("extra_data", {})
        
        # Prepare payload
        payload = {
            "type": message_type,
            "message": message,
            "timestamp": kwargs.get("timestamp", "unknown"),
            **extra_data
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status < 400:
                        self.logger.info(f"Webhook message sent successfully: {response.status}")
                        return True
                    else:
                        self.logger.error(f"Webhook send failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending webhook message: {e}")
            return False
            
    async def send_structured_alert(self, alert_data: Dict[str, Any], **kwargs) -> bool:
        """Send structured alert data"""
        payload = {
            "type": "structured_alert",
            "alert_data": alert_data,
            "timestamp": kwargs.get("timestamp", "unknown")
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status < 400:
                        self.logger.info("Structured alert sent successfully")
                        return True
                    else:
                        self.logger.error(f"Structured alert send failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending structured alert: {e}")
            return False