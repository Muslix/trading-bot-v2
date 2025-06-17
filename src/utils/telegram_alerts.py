"""
Telegram Error Alerting System
Send critical system errors via Telegram
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    from src.modules.telegram_bot import crypto_bot
    from src.utils.error_logger import log_error, log_info
except ImportError:
    # Fallback for testing
    crypto_bot = None

    def log_error(msg, exception=None, context=None):
        print(f"ERROR: {msg}")

    def log_info(msg, context=None):
        print(f"INFO: {msg}")


class TelegramErrorAlerter:
    """Telegram error alerting system"""
    
    def __init__(self, cooldown_minutes: int = 30):
        self.cooldown_minutes = cooldown_minutes
        self.last_alerts: Dict[str, datetime] = {}
        self.enabled = True
        
    def _get_alert_key(self, error_type: str, module: str) -> str:
        """Generate alert key for cooldown tracking"""
        return f"{error_type}_{module}"
    
    def _should_send_alert(self, error_type: str, module: str) -> bool:
        """Check if alert should be sent (not in cooldown)"""
        if not self.enabled:
            return False
            
        alert_key = self._get_alert_key(error_type, module)
        last_alert = self.last_alerts.get(alert_key)
        
        if last_alert is None:
            return True
            
        cooldown_period = timedelta(minutes=self.cooldown_minutes)
        return datetime.now() - last_alert > cooldown_period
    
    def _record_alert(self, error_type: str, module: str) -> None:
        """Record that alert was sent"""
        alert_key = self._get_alert_key(error_type, module)
        self.last_alerts[alert_key] = datetime.now()
    
    async def send_critical_error_alert(self, 
                                      error_message: str, 
                                      exception: Optional[Exception] = None,
                                      module: str = "system", 
                                      context: Optional[Dict] = None) -> bool:
        """Send critical error alert via Telegram"""
        
        error_type = type(exception).__name__ if exception else "CriticalError"
        
        # Check cooldown
        if not self._should_send_alert(error_type, module):
            log_info("Telegram alert skipped due to cooldown", 
                    context={"error_type": error_type, "module": module})
            return False
        
        try:
            # Format error message
            alert_message = self._format_error_message(error_message, exception, module, context)
            
            # Send telegram message
            if crypto_bot:
                success = await crypto_bot.send_message(alert_message)
                if success:
                    self._record_alert(error_type, module)
                    log_info("Critical error alert sent via Telegram", 
                            context={"error_type": error_type, "module": module})
                    return True
                else:
                    log_error("Failed to send Telegram alert", 
                             context={"error_type": error_type, "module": module})
                    return False
            else:
                log_error("Telegram bot not available for error alerts")
                return False
                
        except Exception as e:
            log_error("Exception while sending Telegram error alert", exception=e,
                     context={"original_error": error_message, "module": module})
            return False
    
    def _format_error_message(self, 
                            error_message: str, 
                            exception: Optional[Exception], 
                            module: str, 
                            context: Optional[Dict]) -> str:
        """Format error message for Telegram"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"🚨 *CRITICAL ERROR ALERT* 🚨\n\n"
        message += f"⏰ *Time:* {timestamp}\n"
        message += f"📦 *Module:* `{module}`\n\n"
        message += f"💥 *Error:* {error_message}\n\n"
        
        if exception:
            message += f"🔍 *Exception Type:* `{type(exception).__name__}`\n"
            message += f"📝 *Exception Message:* `{str(exception)}`\n\n"
        
        if context:
            message += f"🔧 *Context:*\n"
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)):
                    message += f"   • {key}: `{value}`\n"
            message += "\n"
        
        message += f"🤖 *Bot Status:* Please check system logs for details"
        
        return message
    
    async def send_system_recovery_alert(self, module: str, recovery_message: str) -> bool:
        """Send system recovery alert"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"✅ *SYSTEM RECOVERY* ✅\n\n"
            message += f"⏰ *Time:* {timestamp}\n"
            message += f"📦 *Module:* `{module}`\n\n"
            message += f"🔄 *Recovery:* {recovery_message}\n\n"
            message += f"🤖 *Bot Status:* System operational"
            
            if crypto_bot:
                success = await crypto_bot.send_message(message)
                if success:
                    log_info("System recovery alert sent via Telegram", 
                            context={"module": module})
                return success
            return False
            
        except Exception as e:
            log_error("Exception while sending recovery alert", exception=e,
                     context={"module": module})
            return False
    
    async def send_health_degradation_alert(self, 
                                          component: str, 
                                          status: str, 
                                          details: Optional[Dict] = None) -> bool:
        """Send health degradation alert"""
        
        # Use component as module for cooldown
        if not self._should_send_alert("HealthDegradation", component):
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"⚠️ *HEALTH ALERT* ⚠️\n\n"
            message += f"⏰ *Time:* {timestamp}\n"
            message += f"🏥 *Component:* `{component}`\n"
            message += f"📊 *Status:* {status}\n\n"
            
            if details:
                message += f"📋 *Details:*\n"
                for key, value in details.items():
                    message += f"   • {key}: `{value}`\n"
                message += "\n"
            
            message += f"🔍 *Action Required:* Please check system health"
            
            if crypto_bot:
                success = await crypto_bot.send_message(message)
                if success:
                    self._record_alert("HealthDegradation", component)
                    log_info("Health degradation alert sent via Telegram", 
                            context={"component": component, "status": status})
                return success
            return False
            
        except Exception as e:
            log_error("Exception while sending health alert", exception=e,
                     context={"component": component})
            return False
    
    def enable_alerts(self) -> None:
        """Enable telegram alerts"""
        self.enabled = True
        log_info("Telegram error alerts enabled")
    
    def disable_alerts(self) -> None:
        """Disable telegram alerts"""
        self.enabled = False
        log_info("Telegram error alerts disabled")
    
    def get_alert_stats(self) -> Dict:
        """Get alerting statistics"""
        return {
            "enabled": self.enabled,
            "cooldown_minutes": self.cooldown_minutes,
            "active_cooldowns": len(self.last_alerts),
            "last_alerts": dict(self.last_alerts)
        }


# Global telegram alerter instance
telegram_alerter = TelegramErrorAlerter()


async def send_critical_error_alert(error_message: str, 
                                  exception: Optional[Exception] = None,
                                  module: str = "system", 
                                  context: Optional[Dict] = None) -> bool:
    """Convenience function for sending critical error alerts"""
    return await telegram_alerter.send_critical_error_alert(
        error_message, exception, module, context
    )


async def send_system_recovery_alert(module: str, recovery_message: str) -> bool:
    """Convenience function for sending recovery alerts"""
    return await telegram_alerter.send_system_recovery_alert(module, recovery_message)


async def send_health_degradation_alert(component: str, 
                                       status: str, 
                                       details: Optional[Dict] = None) -> bool:
    """Convenience function for sending health alerts"""
    return await telegram_alerter.send_health_degradation_alert(component, status, details)