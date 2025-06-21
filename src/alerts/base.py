"""
Alerts module base classes and interfaces.

This module provides the foundation for all alert plugins using the Universal Pattern.
All alert types (arbitrage, performance, technical, etc.) inherit from these base classes.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from src.core import UniversalPlugin, ModuleConfig


@dataclass 
class AlertConfig(ModuleConfig):
    """Configuration for alert plugins."""
    
    # Alert-specific settings
    threshold: float = 2.0
    cooldown_minutes: int = 60
    priority: str = "medium"  # low, medium, high, critical
    
    # Message formatting
    message_template: Optional[str] = None
    include_details: bool = True
    max_message_length: int = 4096
    
    # Filtering
    min_value_threshold: Optional[float] = None
    max_alerts_per_hour: int = 10
    symbols_whitelist: Optional[List[str]] = field(default_factory=list)
    symbols_blacklist: Optional[List[str]] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate alert configuration."""
        super().validate()
        
        # Convert string values to appropriate types
        try:
            threshold = float(self.threshold) if isinstance(self.threshold, str) else self.threshold
            cooldown_minutes = int(self.cooldown_minutes) if isinstance(self.cooldown_minutes, str) else self.cooldown_minutes
            max_alerts_per_hour = int(self.max_alerts_per_hour) if isinstance(self.max_alerts_per_hour, str) else self.max_alerts_per_hour
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid configuration value type: {e}")
        
        if threshold <= 0:
            raise ValueError("Alert threshold must be positive")
        if cooldown_minutes < 0:
            raise ValueError("Cooldown minutes must be non-negative")
        if self.priority not in ["low", "medium", "high", "critical"]:
            raise ValueError("Priority must be one of: low, medium, high, critical")
        if max_alerts_per_hour <= 0:
            raise ValueError("Max alerts per hour must be positive")
            
        # Update the actual values with converted types
        self.threshold = threshold
        self.cooldown_minutes = cooldown_minutes
        self.max_alerts_per_hour = max_alerts_per_hour
            
        return True


class AlertPlugin(UniversalPlugin):
    """
    Base class for all alert plugins.
    
    This provides the standard interface that all alerts must implement:
    - should_trigger(): Check if alert conditions are met
    - format_message(): Create the alert message
    - get_alert_data(): Extract relevant data for the alert
    """
    
    def __init__(self, config: AlertConfig):
        super().__init__(config)
        self.alert_history = {}
        self.alert_count = 0
        self.last_alert_time = None
    
    @property
    def plugin_type(self) -> str:
        return "alert"
    
    async def _initialize(self) -> bool:
        """Initialize the alert plugin."""
        self.logger.info(f"Initializing alert plugin: {self.name}")
        
        # Validate configuration
        try:
            self.config.validate()
        except Exception as e:
            self.logger.error(f"Invalid configuration for {self.name}: {e}")
            return False
        
        # Initialize alert-specific resources
        return await self._initialize_alert()
    
    @abstractmethod
    async def _initialize_alert(self) -> bool:
        """Alert-specific initialization logic."""
        pass
    
    async def _execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the alert check.
        
        Args:
            data: Market data or other input for alert checking
            
        Returns:
            Dict with alert results
        """
        try:
            # Check if alert should trigger
            should_trigger = await self.should_trigger(data)
            
            if not should_trigger:
                return {
                    "triggered": False,
                    "reason": "Conditions not met",
                    "alert_type": self.get_alert_type()
                }
            
            # Check cooldown
            if not self._check_cooldown():
                return {
                    "triggered": False,
                    "reason": "Still in cooldown period",
                    "alert_type": self.get_alert_type()
                }
            
            # Get alert data
            alert_data = await self.get_alert_data(data)
            
            # Format message
            message = await self.format_message(alert_data)
            
            # Update tracking
            self._update_alert_tracking()
            
            return {
                "triggered": True,
                "message": message,
                "alert_type": self.get_alert_type(),
                "priority": self.config.priority,
                "data": alert_data,
                "timestamp": self.last_alert_time.isoformat() if self.last_alert_time else None
            }
            
        except Exception as e:
            self.logger.error(f"Alert execution failed for {self.name}: {e}")
            return {
                "triggered": False,
                "error": str(e),
                "alert_type": self.get_alert_type()
            }
    
    @abstractmethod
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if the alert should trigger based on the data.
        
        Args:
            data: Input data for alert evaluation
            
        Returns:
            bool: True if alert should trigger
        """
        pass
    
    @abstractmethod
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """
        Format the alert message.
        
        Args:
            alert_data: Data to include in the alert message
            
        Returns:
            str: Formatted alert message
        """
        pass
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant data for the alert.
        
        Args:
            data: Raw input data
            
        Returns:
            Dict: Processed alert data
        """
        # Default implementation - can be overridden
        return data
    
    def get_alert_type(self) -> str:
        """
        Get the alert type identifier.
        
        Returns:
            str: Alert type name
        """
        # Default: use class name without 'Alert' suffix
        class_name = self.__class__.__name__
        if class_name.endswith('Alert'):
            return class_name[:-5].lower()
        return class_name.lower()
    
    def _check_cooldown(self) -> bool:
        """Check if alert is still in cooldown period."""
        from datetime import datetime, timedelta
        
        if not self.last_alert_time:
            return True
        
        cooldown_minutes = getattr(self.config, 'cooldown_minutes', 60)
        cooldown_period = timedelta(minutes=cooldown_minutes)
        return datetime.now() - self.last_alert_time >= cooldown_period
    
    def _update_alert_tracking(self) -> None:
        """Update alert tracking information."""
        from datetime import datetime
        
        self.alert_count += 1
        self.last_alert_time = datetime.now()
    
    def _filter_by_symbols(self, data: Dict[str, Any]) -> bool:
        """Filter alerts by symbol whitelist/blacklist."""
        symbol = data.get('symbol', '').upper()
        
        if not symbol:
            return True  # No symbol filtering if symbol not provided
        
        # Check blacklist first
        symbols_blacklist = getattr(self.config, 'symbols_blacklist', None)
        if symbols_blacklist and symbol in [s.upper() for s in symbols_blacklist]:
            return False
        
        # Check whitelist
        symbols_whitelist = getattr(self.config, 'symbols_whitelist', None)
        if symbols_whitelist:
            return symbol in [s.upper() for s in symbols_whitelist]
        
        return True  # No whitelist means all symbols allowed
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return {
            "alert_type": self.get_alert_type(),
            "plugin_name": self.name,
            "total_alerts": self.alert_count,
            "last_alert": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "config": {
                "threshold": getattr(self.config, 'threshold', 0),
                "cooldown_minutes": getattr(self.config, 'cooldown_minutes', 60),
                "priority": getattr(self.config, 'priority', 'medium'),
                "enabled": self.config.enabled
            }
        }
    
    async def test_alert(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test the alert with sample data (bypasses cooldown)."""
        original_last_alert = self.last_alert_time
        self.last_alert_time = None  # Bypass cooldown for testing
        
        try:
            result = await self._execute(test_data)
            return result
        finally:
            self.last_alert_time = original_last_alert
