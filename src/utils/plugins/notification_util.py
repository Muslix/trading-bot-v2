"""
Notification Utility Plugin - multi-channel notification system
"""

import asyncio
import aiohttp
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..base import UtilPlugin, UtilConfig


class NotificationUtil(UtilPlugin):
    """
    Notification utility plugin for multi-channel notifications.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.notifications_sent = 0
        self.failed_notifications = 0
        self.last_notification_time = None
        
        # Channel configurations
        self.channels = {
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "use_tls": True
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": "",
                "api_url": "https://api.telegram.org/bot"
            },
            "discord": {
                "enabled": False,
                "webhook_url": "",
                "username": "Trading Bot",
                "avatar_url": ""
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#trading",
                "username": "TradingBot"
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "method": "POST",
                "headers": {},
                "auth_token": ""
            }
        }
        
        # Notification templates
        self.templates = {
            "alert": {
                "subject": "🚨 Trading Alert: {alert_type}",
                "body": "Alert Type: {alert_type}\nSymbol: {symbol}\nMessage: {message}\nTime: {timestamp}"
            },
            "trade": {
                "subject": "💰 Trade Executed: {side} {symbol}",
                "body": "Trade Details:\n- Symbol: {symbol}\n- Side: {side}\n- Quantity: {quantity}\n- Price: ${price}\n- Total: ${total}\nTime: {timestamp}"
            },
            "error": {
                "subject": "❌ System Error",
                "body": "Error Details:\nModule: {module}\nError: {error}\nTime: {timestamp}"
            },
            "status": {
                "subject": "📊 System Status Update",
                "body": "Status: {status}\nUptime: {uptime}\nLast Update: {timestamp}"
            },
            "performance": {
                "subject": "📈 Performance Report",
                "body": "Performance Summary:\n- Portfolio Value: ${portfolio_value}\n- Daily P&L: ${daily_pnl}\n- Win Rate: {win_rate}%\nGenerated: {timestamp}"
            }
        }
        
        # Rate limiting
        self.rate_limits = {}
        self.rate_limit_window = 300  # 5 minutes
        self.max_notifications_per_window = 20
    
    async def _initialize_util(self) -> bool:
        """Initialize notification utility."""
        try:
            # Initialize HTTP session for webhook notifications
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
            
            self.logger.info("Notification utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification utility: {e}")
            return False
    
    async def _cleanup_util(self) -> None:
        """Clean up notification utility resources."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process notification operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "send_notification")
        
        # Rate limiting check
        if not self._check_rate_limit(action):
            return {"success": False, "error": "Rate limit exceeded"}
        
        if action == "send_notification":
            return await self._send_notification(data)
        elif action == "send_multi_channel":
            return await self._send_multi_channel_notification(data)
        elif action == "configure_channel":
            return self._configure_channel(data)
        elif action == "test_channel":
            return await self._test_channel(data)
        elif action == "get_channels":
            return self._get_channels_status()
        elif action == "add_template":
            return self._add_notification_template(data)
        elif action == "get_templates":
            return self._get_notification_templates()
        elif action == "send_bulk":
            return await self._send_bulk_notifications(data)
        elif action == "schedule_notification":
            return await self._schedule_notification(data)
        elif action == "get_stats":
            return self._get_notification_stats()
        else:
            raise ValueError(f"Unknown notification action: {action}")
    
    async def _send_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification via specified channel."""
        try:
            channel = data.get("channel", "telegram")
            message = data.get("message", "")
            subject = data.get("subject", "Notification")
            template = data.get("template")
            template_data = data.get("template_data", {})
            priority = data.get("priority", "normal")  # low, normal, high, critical
            
            if not message and not template:
                return {"success": False, "error": "No message or template provided"}
            
            # Use template if provided
            if template and template in self.templates:
                subject = self.templates[template]["subject"].format(**template_data)
                message = self.templates[template]["body"].format(**template_data)
            
            # Check if channel is enabled
            if channel not in self.channels or not self.channels[channel]["enabled"]:
                return {"success": False, "error": f"Channel {channel} not enabled"}
            
            # Send via specific channel
            if channel == "email":
                result = await self._send_email(subject, message, data.get("recipients", []))
            elif channel == "telegram":
                result = await self._send_telegram(message)
            elif channel == "discord":
                result = await self._send_discord(message)
            elif channel == "slack":
                result = await self._send_slack(message)
            elif channel == "webhook":
                result = await self._send_webhook({"subject": subject, "message": message, "priority": priority})
            else:
                return {"success": False, "error": f"Unsupported channel: {channel}"}
            
            if result.get("success"):
                self.notifications_sent += 1
                self.last_notification_time = datetime.now()
            else:
                self.failed_notifications += 1
            
            return {
                "success": result.get("success", False),
                "channel": channel,
                "message_sent": message[:100] + "..." if len(message) > 100 else message,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.failed_notifications += 1
            self.logger.error(f"Notification sending failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_multi_channel_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to multiple channels."""
        try:
            channels = data.get("channels", ["telegram", "email"])
            message = data.get("message", "")
            subject = data.get("subject", "Multi-Channel Notification")
            
            if not message:
                return {"success": False, "error": "No message provided"}
            
            results = {}
            tasks = []
            
            # Create tasks for each channel
            for channel in channels:
                if channel in self.channels and self.channels[channel]["enabled"]:
                    channel_data = data.copy()
                    channel_data["channel"] = channel
                    task = self._send_notification(channel_data)
                    tasks.append((channel, task))
            
            # Execute all notifications concurrently
            if tasks:
                task_results = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )
                
                # Process results
                for i, (channel, _) in enumerate(tasks):
                    result = task_results[i]
                    if isinstance(result, Exception):
                        results[channel] = {"success": False, "error": str(result)}
                    else:
                        results[channel] = result
            
            successful_channels = [ch for ch, res in results.items() if res.get("success")]
            failed_channels = [ch for ch, res in results.items() if not res.get("success")]
            
            return {
                "success": len(successful_channels) > 0,
                "results": results,
                "successful_channels": successful_channels,
                "failed_channels": failed_channels,
                "total_channels": len(channels),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Multi-channel notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_email(self, subject: str, message: str, recipients: List[str]) -> Dict[str, Any]:
        """Send email notification."""
        try:
            config = self.channels["email"]
            
            if not all([config["smtp_server"], config["username"], config["from_email"]]):
                return {"success": False, "error": "Email configuration incomplete"}
            
            if not recipients:
                return {"success": False, "error": "No recipients provided"}
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config["from_email"]
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                if config["use_tls"]:
                    server.starttls()
                
                if config["password"]:
                    server.login(config["username"], config["password"])
                
                server.send_message(msg)
            
            return {
                "success": True,
                "recipients": recipients,
                "method": "email"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Email sending failed: {e}"}
    
    async def _send_telegram(self, message: str) -> Dict[str, Any]:
        """Send Telegram notification."""
        try:
            config = self.channels["telegram"]
            
            if not all([config["bot_token"], config["chat_id"]]):
                return {"success": False, "error": "Telegram configuration incomplete"}
            
            url = f"{config['api_url']}{config['bot_token']}/sendMessage"
            payload = {
                "chat_id": config["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return {"success": True, "method": "telegram"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Telegram API error: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Telegram sending failed: {e}"}
    
    async def _send_discord(self, message: str) -> Dict[str, Any]:
        """Send Discord notification."""
        try:
            config = self.channels["discord"]
            
            if not config["webhook_url"]:
                return {"success": False, "error": "Discord webhook URL not configured"}
            
            payload = {
                "content": message,
                "username": config.get("username", "Trading Bot")
            }
            
            if config.get("avatar_url"):
                payload["avatar_url"] = config["avatar_url"]
            
            async with self.session.post(config["webhook_url"], json=payload) as response:
                if response.status in [200, 204]:
                    return {"success": True, "method": "discord"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Discord webhook error: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Discord sending failed: {e}"}
    
    async def _send_slack(self, message: str) -> Dict[str, Any]:
        """Send Slack notification."""
        try:
            config = self.channels["slack"]
            
            if not config["webhook_url"]:
                return {"success": False, "error": "Slack webhook URL not configured"}
            
            payload = {
                "text": message,
                "channel": config.get("channel", "#general"),
                "username": config.get("username", "TradingBot"),
                "icon_emoji": ":robot_face:"
            }
            
            async with self.session.post(config["webhook_url"], json=payload) as response:
                if response.status == 200:
                    return {"success": True, "method": "slack"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"Slack webhook error: {error_text}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Slack sending failed: {e}"}
    
    async def _send_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send generic webhook notification."""
        try:
            config = self.channels["webhook"]
            
            if not config["url"]:
                return {"success": False, "error": "Webhook URL not configured"}
            
            headers = config.get("headers", {}).copy()
            if config.get("auth_token"):
                headers["Authorization"] = f"Bearer {config['auth_token']}"
            
            headers["Content-Type"] = "application/json"
            
            payload = {
                "timestamp": datetime.now().isoformat(),
                "source": "trading_bot",
                **data
            }
            
            method = config.get("method", "POST").upper()
            
            if method == "POST":
                async with self.session.post(config["url"], json=payload, headers=headers) as response:
                    success = 200 <= response.status < 300
                    return {
                        "success": success,
                        "method": "webhook",
                        "status_code": response.status
                    }
            elif method == "PUT":
                async with self.session.put(config["url"], json=payload, headers=headers) as response:
                    success = 200 <= response.status < 300
                    return {
                        "success": success,
                        "method": "webhook",
                        "status_code": response.status
                    }
            else:
                return {"success": False, "error": f"Unsupported HTTP method: {method}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Webhook sending failed: {e}"}
    
    def _configure_channel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a notification channel."""
        try:
            channel = data.get("channel", "")
            configuration = data.get("configuration", {})
            
            if channel not in self.channels:
                return {"success": False, "error": f"Unknown channel: {channel}"}
            
            # Update channel configuration
            self.channels[channel].update(configuration)
            
            return {
                "success": True,
                "channel": channel,
                "updated_config": self.channels[channel],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Channel configuration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_channel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a notification channel."""
        try:
            channel = data.get("channel", "telegram")
            
            test_message = f"🧪 Test notification from Trading Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = await self._send_notification({
                "channel": channel,
                "message": test_message,
                "subject": "Test Notification"
            })
            
            return {
                "success": result.get("success", False),
                "channel": channel,
                "test_result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Channel test failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_channels_status(self) -> Dict[str, Any]:
        """Get status of all notification channels."""
        try:
            channel_status = {}
            
            for channel, config in self.channels.items():
                channel_status[channel] = {
                    "enabled": config["enabled"],
                    "configured": self._is_channel_configured(channel),
                    "last_used": "unknown"  # Would track in production
                }
            
            return {
                "success": True,
                "channels": channel_status,
                "total_channels": len(self.channels),
                "enabled_channels": len([c for c in self.channels.values() if c["enabled"]]),
                "configured_channels": len([c for c in self.channels.keys() if self._is_channel_configured(c)])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get channels status: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_channel_configured(self, channel: str) -> bool:
        """Check if a channel is properly configured."""
        config = self.channels.get(channel, {})
        
        if channel == "email":
            return all([config.get("smtp_server"), config.get("username"), config.get("from_email")])
        elif channel == "telegram":
            return all([config.get("bot_token"), config.get("chat_id")])
        elif channel == "discord":
            return bool(config.get("webhook_url"))
        elif channel == "slack":
            return bool(config.get("webhook_url"))
        elif channel == "webhook":
            return bool(config.get("url"))
        
        return False
    
    def _add_notification_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new notification template."""
        try:
            template_name = data.get("name", "")
            subject = data.get("subject", "")
            body = data.get("body", "")
            
            if not all([template_name, subject, body]):
                return {"success": False, "error": "Template name, subject, and body required"}
            
            self.templates[template_name] = {
                "subject": subject,
                "body": body
            }
            
            return {
                "success": True,
                "template_name": template_name,
                "total_templates": len(self.templates)
            }
            
        except Exception as e:
            self.logger.error(f"Template addition failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_notification_templates(self) -> Dict[str, Any]:
        """Get all notification templates."""
        return {
            "success": True,
            "templates": self.templates,
            "total_templates": len(self.templates)
        }
    
    async def _send_bulk_notifications(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send bulk notifications."""
        try:
            notifications = data.get("notifications", [])
            
            if not notifications:
                return {"success": False, "error": "No notifications provided"}
            
            results = []
            successful = 0
            failed = 0
            
            # Process notifications in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(notifications), batch_size):
                batch = notifications[i:i + batch_size]
                
                # Send batch concurrently
                tasks = [self._send_notification(notif) for notif in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results.append({"success": False, "error": str(result), "index": i + j})
                        failed += 1
                    else:
                        results.append({"success": result.get("success", False), "index": i + j})
                        if result.get("success"):
                            successful += 1
                        else:
                            failed += 1
                
                # Small delay between batches
                if i + batch_size < len(notifications):
                    await asyncio.sleep(1)
            
            return {
                "success": True,
                "total_notifications": len(notifications),
                "successful": successful,
                "failed": failed,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Bulk notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_rate_limit(self, action: str) -> bool:
        """Check if action is within rate limits."""
        now = datetime.now()
        
        # Clean old entries
        self.rate_limits = {
            k: v for k, v in self.rate_limits.items()
            if (now - v['last_request']).total_seconds() < self.rate_limit_window
        }
        
        # Check current action
        if action not in self.rate_limits:
            self.rate_limits[action] = {'count': 1, 'last_request': now}
            return True
        
        rate_data = self.rate_limits[action]
        time_diff = (now - rate_data['last_request']).total_seconds()
        
        if time_diff >= self.rate_limit_window:
            # Reset counter
            self.rate_limits[action] = {'count': 1, 'last_request': now}
            return True
        
        if rate_data['count'] >= self.max_notifications_per_window:
            return False
        
        # Increment counter
        self.rate_limits[action]['count'] += 1
        self.rate_limits[action]['last_request'] = now
        return True
    
    def _get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        success_rate = 0
        if self.notifications_sent + self.failed_notifications > 0:
            success_rate = (self.notifications_sent / (self.notifications_sent + self.failed_notifications)) * 100
        
        return {
            "notifications_sent": self.notifications_sent,
            "failed_notifications": self.failed_notifications,
            "success_rate": success_rate,
            "last_notification_time": self.last_notification_time.isoformat() if self.last_notification_time else None,
            "configured_channels": {
                channel: self._is_channel_configured(channel)
                for channel in self.channels.keys()
            },
            "enabled_channels": [
                channel for channel, config in self.channels.items()
                if config["enabled"]
            ],
            "available_templates": list(self.templates.keys()),
            "rate_limit_stats": {
                "window_seconds": self.rate_limit_window,
                "max_per_window": self.max_notifications_per_window,
                "active_limits": len(self.rate_limits)
            },
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }