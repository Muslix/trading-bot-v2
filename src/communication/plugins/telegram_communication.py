"""
Telegram Communication Plugin - Enhanced Telegram messaging
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from telegram import Bot
from telegram.constants import ParseMode

from ..base import BaseCommunication
from src.utils.decorators import async_log_performance


class TelegramCommunication(BaseCommunication):
    """Telegram communication plugin with advanced features"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Access custom settings from ModuleConfig
        settings = self.config.custom_settings if hasattr(self.config, 'custom_settings') else config
        self.bot_token = settings.get("bot_token")
        self.default_chat_id = settings.get("chat_id")
        self.parse_mode = settings.get("parse_mode", ParseMode.MARKDOWN)
        
        # Alert configuration
        self.alert_config = {
            "arbitrage_threshold": settings.get("arbitrage_threshold", 1.5),
            "sharpe_change_threshold": settings.get("sharpe_change_threshold", 0.5),
            "cooldown_minutes": settings.get("cooldown_minutes", 15),
            "daily_summary_hour": settings.get("daily_summary_hour", 8),
        }
        
        # Spam protection
        self.alert_cooldowns = {}
        self.last_alerts = {}
        
        self.bot = None
        self.current_chat_id = self.default_chat_id
        
    def get_communication_type(self) -> str:
        return "telegram"
        
    async def initialize(self):
        """Initialize the Telegram communication plugin"""
        if not self.bot_token:
            raise ValueError("Telegram bot token is required")
            
        self.bot = Bot(token=self.bot_token)
        self.logger.info("Telegram communication plugin initialized")
        
    async def connect(self) -> bool:
        """Establish connection to Telegram"""
        try:
            if not self.bot:
                await self.initialize()
                
            # Test the connection
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            self.is_connected = True
            
            # Auto-detect chat ID if not provided
            if not self.current_chat_id:
                self.current_chat_id = await self._get_chat_id_from_updates()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            self.is_connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from Telegram"""
        self.is_connected = False
        self.logger.info("Disconnected from Telegram")
        
    @async_log_performance
    async def send_message(self, message: str, **kwargs) -> bool:
        """Send message to Telegram"""
        if not self.is_connected:
            self.logger.error("Not connected to Telegram")
            return False
            
        chat_id = kwargs.get("chat_id", kwargs.get("recipient", self.current_chat_id))
        parse_mode = kwargs.get("parse_mode", self.parse_mode)
        test_mode = kwargs.get("test", False)
        
        if not chat_id and not test_mode:
            self.logger.warning("No chat ID available - message not sent")
            return False
            
        if test_mode:
            self.logger.info(f"Test mode: Would send message: {message[:50]}...")
            return True
            
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            self.logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
            
    async def _get_chat_id_from_updates(self) -> Optional[str]:
        """Get chat ID from recent updates"""
        try:
            updates = await self.bot.get_updates()
            if updates:
                return str(updates[-1].message.chat.id)
            return None
        except Exception as e:
            self.logger.error(f"Error getting chat ID: {e}")
            return None
            
    def set_chat_id(self, chat_id: str):
        """Set the chat ID for messages"""
        self.current_chat_id = chat_id
        self.logger.info(f"Chat ID set: {chat_id}")
        
    def _should_send_alert(self, alert_type: str, key: str = "") -> bool:
        """Check if alert should be sent (spam protection)"""
        alert_key = f"{alert_type}_{key}"
        now = datetime.now()
        
        if alert_key in self.alert_cooldowns:
            last_sent = self.alert_cooldowns[alert_key]
            cooldown_time = timedelta(minutes=self.alert_config["cooldown_minutes"])
            
            if now - last_sent < cooldown_time:
                return False
                
        self.alert_cooldowns[alert_key] = now
        return True
        
    async def send_arbitrage_alert(self, opportunities: List[Dict], **kwargs) -> bool:
        """Send arbitrage alert"""
        if not opportunities:
            return False
            
        # Filter significant opportunities
        significant_opportunities = [
            opp for opp in opportunities 
            if opp.get("profit_percentage", 0) >= self.alert_config["arbitrage_threshold"]
        ]
        
        if not significant_opportunities:
            return False
            
        # Spam protection per symbol
        symbol = significant_opportunities[0].get("symbol", "UNKNOWN")
        if not self._should_send_alert("arbitrage", symbol):
            return False
            
        # Create alert message
        best_opp = max(significant_opportunities, key=lambda x: x.get("profit_percentage", 0))
        
        message = f"""🚨 *ARBITRAGE ALERT!* 🚨

💎 *{best_opp['symbol']}*
💰 *Profit: {best_opp['profit_percentage']:.1f}%*

📈 Buy on: *{best_opp['buy_exchange']}* (${best_opp['buy_price']:.2f})
📉 Sell on: *{best_opp['sell_exchange']}* (${best_opp['sell_price']:.2f})

💵 Profit per unit: *${best_opp.get('profit_per_unit', 0):.2f}*

⏰ {datetime.now().strftime('%H:%M:%S')}"""
        
        return await self.send_message(message, **kwargs)


# Legacy compatibility function for alert_system
def alert_system(opportunities: List[Dict], min_profit: float = 1.0) -> List[Dict]:
    """Legacy alert system compatibility function"""
    try:
        from config.config import get_config
        cfg = get_config()
        
        # Filter opportunities by minimum profit
        significant_opportunities = [
            opp for opp in opportunities 
            if opp.get("profit_percent", 0) >= min_profit
        ]
        
        # Create communication instance and send alerts asynchronously
        if significant_opportunities:
            telegram_config = {
                "bot_token": cfg.telegram_bot_token,
                "chat_id": cfg.telegram_chat_id,
                "arbitrage_threshold": min_profit,
                "cooldown_minutes": cfg.alert_cooldown_minutes,
            }
            
            comm = TelegramCommunication(telegram_config)
            
            # Create task to send alert asynchronously (don't wait)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    loop.create_task(comm.send_arbitrage_alert(significant_opportunities))
                else:
                    # If no loop, run it
                    asyncio.run(comm.send_arbitrage_alert(significant_opportunities))
            except:
                # Fallback - just log the alert
                logging.info(f"Would send arbitrage alert for {len(significant_opportunities)} opportunities")
        
        return significant_opportunities
        
    except Exception as e:
        logging.error(f"Error in alert_system: {e}")
        return []


# Legacy compatibility - create global instance
def create_legacy_bot(config: Dict[str, Any] = None) -> 'TelegramCryptoBot':
    """Create legacy TelegramCryptoBot instance for backward compatibility"""
    
    class TelegramCryptoBot:
        """Legacy wrapper for TelegramCommunication"""
        
        def __init__(self, bot_token: str = None):
            # Import config here to avoid circular imports
            try:
                from config.config import get_config
                cfg = get_config()
                
                telegram_config = {
                    "bot_token": bot_token or cfg.telegram_bot_token,
                    "chat_id": cfg.telegram_chat_id,
                    "arbitrage_threshold": cfg.arbitrage_threshold,
                    "sharpe_change_threshold": cfg.sharpe_change_threshold,
                    "cooldown_minutes": cfg.alert_cooldown_minutes,
                    "daily_summary_hour": cfg.daily_summary_hour,
                }
                
                self.comm = TelegramCommunication(telegram_config)
                self.alert_config = self.comm.alert_config
                
            except Exception as e:
                logging.error(f"Error creating legacy bot: {e}")
                self.comm = None
                
        async def __aenter__(self):
            if self.comm:
                await self.comm.initialize()
                await self.comm.connect()
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.comm:
                await self.comm.disconnect()
                
        def set_chat_id(self, chat_id: str):
            if self.comm:
                self.comm.set_chat_id(chat_id)
                
        async def send_message(self, message: str, parse_mode: str = ParseMode.MARKDOWN) -> bool:
            if self.comm:
                return await self.comm.send_message(message, parse_mode=parse_mode)
            return False
            
        async def send_alert(self, message: str, alert_type: str = "general") -> bool:
            if self.comm:
                return await self.comm.send_message(message)
            return False
            
        async def send_arbitrage_alert(self, opportunities: List[Dict]) -> bool:
            if self.comm:
                return await self.comm.send_arbitrage_alert(opportunities)
            return False
            
        async def test_connection(self) -> bool:
            if self.comm:
                try:
                    if not self.comm.bot:
                        await self.comm.initialize()
                    bot_info = await self.comm.bot.get_me()
                    self.comm.logger.info(f"Bot connected: @{bot_info.username}")
                    return True
                except Exception as e:
                    self.comm.logger.error(f"Bot connection test failed: {e}")
                    return False
            return False
            
        async def get_chat_id_from_updates(self) -> Optional[str]:
            if self.comm:
                return await self.comm._get_chat_id_from_updates()
            return None
    
    return TelegramCryptoBot()