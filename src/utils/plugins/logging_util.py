"""
Logging Utility Plugin - error and production logging functionality
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..base import UtilPlugin, UtilConfig


class LoggingUtil(UtilPlugin):
    """
    Logging utility plugin for error and production logging.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.log_count = 0
        self.error_count = 0
        self.last_log_time = None
    
    async def _initialize_util(self) -> bool:
        """Initialize logging utility."""
        try:
            # Import original logging functionality
            from ..error_logger import (
                log_error,
                log_warning,
                log_info,
                log_critical,
                log_performance,
                ErrorLogger
            )
            
            from ..production_logger import (
                production_logger,
                get_production_logger,
                ProductionLogger
            )
            
            # Store functions for use
            self.log_error = log_error
            self.log_warning = log_warning
            self.log_info = log_info
            self.log_critical = log_critical
            self.log_performance = log_performance
            self.ErrorLogger = ErrorLogger
            
            self.production_logger = production_logger
            self.get_production_logger = get_production_logger
            self.ProductionLogger = ProductionLogger
            
            self.logger.info("Logging utility initialized")
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import logging utilities: {e}")
            return False
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process logging operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "log_info")
        
        if action == "log_error":
            return await self._log_error(data)
        elif action == "log_warning":
            return await self._log_warning(data)
        elif action == "log_info":
            return await self._log_info(data)
        elif action == "log_critical":
            return await self._log_critical(data)
        elif action == "log_performance":
            return await self._log_performance(data)
        elif action == "production_log":
            return await self._production_log(data)
        elif action == "get_stats":
            return self._get_logging_stats()
        else:
            raise ValueError(f"Unknown logging action: {action}")
    
    async def _log_error(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an error message."""
        message = data.get("message", "")
        exception = data.get("exception")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'log_error'):
                self.log_error(message, exception, context)
            else:
                self.logger.error(f"{message}: {exception}")
            
            self.log_count += 1
            self.error_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": "error",
                "message": message,
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _log_warning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a warning message."""
        message = data.get("message", "")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'log_warning'):
                self.log_warning(message, context)
            else:
                self.logger.warning(message)
            
            self.log_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": "warning",
                "message": message,
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _log_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an info message."""
        message = data.get("message", "")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'log_info'):
                self.log_info(message, context)
            else:
                self.logger.info(message)
            
            self.log_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": "info",
                "message": message,
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _log_critical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a critical message."""
        message = data.get("message", "")
        exception = data.get("exception")
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'log_critical'):
                self.log_critical(message, exception, context)
            else:
                self.logger.critical(f"{message}: {exception}")
            
            self.log_count += 1
            self.error_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": "critical",
                "message": message,
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _log_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log performance metrics."""
        operation = data.get("operation", "")
        duration = data.get("duration", 0)
        context = data.get("context", {})
        
        try:
            if hasattr(self, 'log_performance'):
                self.log_performance(operation, duration, context)
            else:
                self.logger.info(f"Performance: {operation} - {duration:.3f}s")
            
            self.log_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": "performance",
                "operation": operation,
                "duration": duration,
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _production_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle production logging operations."""
        log_type = data.get("log_type", "startup")
        
        try:
            if not hasattr(self, 'production_logger'):
                return {"success": False, "error": "Production logger not available"}
            
            if log_type == "startup":
                config = data.get("config", {})
                self.production_logger.log_startup(config)
                
            elif log_type == "arbitrage_calculation":
                symbol = data.get("symbol", "")
                prices = data.get("prices", {})
                opportunities = data.get("opportunities", [])
                self.production_logger.log_arbitrage_calculation(symbol, prices, opportunities)
                
            elif log_type == "portfolio_calculation":
                symbols = data.get("symbols", [])
                results = data.get("results", {})
                log_level = data.get("log_level", "summary")
                self.production_logger.log_portfolio_calculation(symbols, results, log_level)
                
            elif log_type == "data_source_health":
                health_data = data.get("health_data", {})
                self.production_logger.log_data_source_health(health_data)
                
            elif log_type == "alert_decision":
                alert_type = data.get("alert_type", "")
                symbol = data.get("symbol", "")
                decision = data.get("decision", False)
                reason = data.get("reason", "")
                alert_data = data.get("alert_data", {})
                self.production_logger.log_alert_decision(alert_type, symbol, decision, reason, alert_data)
                
            else:
                return {"success": False, "error": f"Unknown production log type: {log_type}"}
            
            self.log_count += 1
            self.last_log_time = datetime.now()
            
            return {
                "success": True,
                "log_type": f"production_{log_type}",
                "logged_at": self.last_log_time.isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_logging_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            "total_logs": self.log_count,
            "error_logs": self.error_count,
            "last_log_time": self.last_log_time.isoformat() if self.last_log_time else None,
            "error_rate": (self.error_count / self.log_count * 100) if self.log_count > 0 else 0,
            "logging_available": {
                "error_logger": hasattr(self, 'log_error'),
                "production_logger": hasattr(self, 'production_logger')
            },
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }