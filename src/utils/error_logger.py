"""
Simple Error Logging System
Structured logging for debugging and monitoring
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


# Configure structured logger
def setup_error_logger(log_level: str = "INFO") -> logging.Logger:
    """Setup structured error logger"""
    logger = logging.getLogger("crypto_bot_errors")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with structured format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler for errors
    file_handler = logging.FileHandler("logs/error.log", mode='a')
    file_handler.setLevel(logging.ERROR)
    
    # Structured formatter
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra context if available
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
            
        return json.dumps(log_entry, indent=2)


class ErrorLogger:
    """Simple error logger with structured format"""
    
    def __init__(self):
        self.logger = setup_error_logger()
        
    def log_error(self, message: str, exception: Optional[Exception] = None, 
                  context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with structured format"""
        extra = {"context": context} if context else {}
        
        if exception:
            self.logger.error(message, exc_info=exception, extra=extra)
        else:
            self.logger.error(message, extra=extra)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning with context"""
        extra = {"context": context} if context else {}
        self.logger.warning(message, extra=extra)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info with context"""
        extra = {"context": context} if context else {}
        self.logger.info(message, extra=extra)
    
    def log_critical(self, message: str, exception: Optional[Exception] = None,
                    context: Optional[Dict[str, Any]] = None) -> None:
        """Log critical error with structured format"""
        extra = {"context": context} if context else {}
        
        if exception:
            self.logger.critical(message, exc_info=exception, extra=extra)
        else:
            self.logger.critical(message, extra=extra)
    
    def log_performance(self, operation: str, duration: float, 
                       context: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics"""
        perf_context = {"operation": operation, "duration_ms": round(duration * 1000, 2)}
        if context:
            perf_context.update(context)
            
        extra = {"context": perf_context}
        self.logger.info(f"Performance: {operation} completed in {duration:.3f}s", extra=extra)


# Global error logger instance
error_logger = ErrorLogger()


def log_error(message: str, exception: Optional[Exception] = None,
              context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for error logging"""
    error_logger.log_error(message, exception, context)


def log_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for warning logging"""
    error_logger.log_warning(message, context)


def log_info(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for info logging"""
    error_logger.log_info(message, context)


def log_critical(message: str, exception: Optional[Exception] = None,
                context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for critical error logging"""
    error_logger.log_critical(message, exception, context)


def log_performance(operation: str, duration: float,
                   context: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function for performance logging"""
    error_logger.log_performance(operation, duration, context)