"""
Comprehensive Logging Configuration for Crypto Trading Bot v2
Ensures all new features have detailed logging for monitoring and debugging
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any


class TradingBotFormatter(logging.Formatter):
    """Custom formatter with emojis and enhanced information for trading bot logs"""
    
    # Color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    # Emojis for different log levels
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '📊',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def format(self, record):
        # Add emoji and color
        emoji = self.EMOJIS.get(record.levelname, '📝')
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Module identification
        module_name = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Function and line info
        func_info = f"{record.funcName}:{record.lineno}" if hasattr(record, 'funcName') else ""
        
        # Build formatted message
        formatted_msg = f"{color}{emoji} {timestamp} | {module_name} | {record.levelname} | {func_info} | {record.getMessage()}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            formatted_msg += f"\n{self.formatException(record.exc_info)}"
            
        return formatted_msg


def setup_comprehensive_logging(config: Dict[str, Any] = None) -> None:
    """
    Set up comprehensive logging for all trading bot components
    
    Args:
        config: Logging configuration dictionary
    """
    if config is None:
        config = get_default_logging_config()
    
    # Create logs directory
    log_dir = config.get('log_dir', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.get('root_level', 'INFO')))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors and emojis
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.get('console_level', 'INFO')))
    console_handler.setFormatter(TradingBotFormatter())
    root_logger.addHandler(console_handler)
    
    # Main application log file
    main_file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'trading_bot.log'),
        maxBytes=config.get('max_file_size', 50 * 1024 * 1024),  # 50MB
        backupCount=config.get('backup_count', 10)
    )
    main_file_handler.setLevel(getattr(logging, config.get('file_level', 'DEBUG')))
    main_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(main_file_handler)
    
    # Component-specific loggers
    setup_component_loggers(log_dir, config)
    
    # Error-only log file
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'errors.log'),
        maxBytes=config.get('max_file_size', 50 * 1024 * 1024),
        backupCount=config.get('backup_count', 10)
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(error_handler)


def setup_component_loggers(log_dir: str, config: Dict[str, Any]) -> None:
    """Set up specialized loggers for different components"""
    
    components = {
        'defi': {
            'filename': 'defi_operations.log',
            'level': 'INFO',
            'modules': ['src.utils.plugins.defi_util']
        },
        'strategy_sharing': {
            'filename': 'strategy_sharing.log',
            'level': 'INFO',
            'modules': ['src.utils.plugins.strategy_sharing_util']
        },
        'web_api': {
            'filename': 'web_api.log',
            'level': 'INFO',
            'modules': ['src.web_api']
        },
        'arbitrage': {
            'filename': 'arbitrage.log',
            'level': 'INFO',
            'modules': ['src.analyzers.plugins.arbitrage_analyzer']
        },
        'portfolio': {
            'filename': 'portfolio.log',
            'level': 'INFO',
            'modules': ['src.analyzers.plugins.portfolio_analyzer']
        },
        'performance': {
            'filename': 'performance.log',
            'level': 'DEBUG',
            'modules': ['src.utils.plugins.performance_util']
        },
        'security': {
            'filename': 'security.log',
            'level': 'WARNING',
            'modules': ['src.utils.plugins.security_util']
        },
        'communication': {
            'filename': 'communication.log',
            'level': 'INFO',
            'modules': ['src.communication', 'src.utils.plugins.notification_util']
        }
    }
    
    for component_name, component_config in components.items():
        # Create component-specific file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, component_config['filename']),
            maxBytes=config.get('max_file_size', 10 * 1024 * 1024),  # 10MB per component
            backupCount=config.get('backup_count', 5)
        )
        file_handler.setLevel(getattr(logging, component_config['level']))
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Apply to relevant modules
        for module_name in component_config['modules']:
            module_logger = logging.getLogger(module_name)
            module_logger.addHandler(file_handler)
            module_logger.setLevel(getattr(logging, component_config['level']))


def get_default_logging_config() -> Dict[str, Any]:
    """Get default logging configuration"""
    return {
        'log_dir': 'logs',
        'root_level': 'INFO',
        'console_level': 'INFO',
        'file_level': 'DEBUG',
        'max_file_size': 50 * 1024 * 1024,  # 50MB
        'backup_count': 10,
        'format': '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S'
    }


def log_feature_usage(feature_name: str, user_context: Dict[str, Any] = None):
    """
    Log usage of specific features for analytics
    
    Args:
        feature_name: Name of the feature being used
        user_context: Additional context about the usage
    """
    usage_logger = logging.getLogger('feature_usage')
    
    context_str = ""
    if user_context:
        context_items = [f"{k}={v}" for k, v in user_context.items()]
        context_str = f" | {', '.join(context_items)}"
    
    usage_logger.info(f"🎯 Feature used: {feature_name}{context_str}")


def log_performance_metric(operation: str, duration: float, context: Dict[str, Any] = None):
    """
    Log performance metrics for monitoring
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        context: Additional context
    """
    perf_logger = logging.getLogger('performance')
    
    context_str = ""
    if context:
        context_items = [f"{k}={v}" for k, v in context.items()]
        context_str = f" | {', '.join(context_items)}"
    
    # Color code based on performance
    if duration < 1.0:
        emoji = "🚀"  # Fast
    elif duration < 5.0:
        emoji = "⚡"  # Good
    elif duration < 30.0:
        emoji = "🐌"  # Slow
    else:
        emoji = "🔥"  # Very slow
    
    perf_logger.info(f"{emoji} {operation}: {duration:.3f}s{context_str}")


def log_user_action(action: str, user_id: str = "anonymous", details: Dict[str, Any] = None):
    """
    Log user actions for audit trail
    
    Args:
        action: The action performed
        user_id: User identifier
        details: Additional action details
    """
    audit_logger = logging.getLogger('user_actions')
    
    details_str = ""
    if details:
        details_items = [f"{k}={v}" for k, v in details.items()]
        details_str = f" | {', '.join(details_items)}"
    
    audit_logger.info(f"👤 User {user_id} performed: {action}{details_str}")


def log_security_event(event_type: str, severity: str, details: Dict[str, Any] = None):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        severity: Severity level (low, medium, high, critical)
        details: Event details
    """
    security_logger = logging.getLogger('security')
    
    severity_emojis = {
        'low': '🔒',
        'medium': '⚠️',
        'high': '🚨',
        'critical': '🔥'
    }
    
    emoji = severity_emojis.get(severity.lower(), '🔐')
    
    details_str = ""
    if details:
        details_items = [f"{k}={v}" for k, v in details.items()]
        details_str = f" | {', '.join(details_items)}"
    
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    security_logger.log(log_level, f"{emoji} Security event: {event_type}{details_str}")


def create_operation_logger(operation_name: str) -> logging.Logger:
    """
    Create a specialized logger for specific operations
    
    Args:
        operation_name: Name of the operation
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"operations.{operation_name}")
    
    # Add operation-specific formatting if needed
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f'🔧 {operation_name.upper()} | %(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


# Feature-specific logging helpers
class DeFiLogger:
    """Specialized logger for DeFi operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('defi_operations')
    
    def log_pool_fetch(self, protocol: str, token_pair: str, pool_count: int, duration: float):
        self.logger.info(f"🏊 {protocol}: {pool_count} pools for {token_pair} ({duration:.3f}s)")
    
    def log_arbitrage_found(self, buy_protocol: str, sell_protocol: str, profit_pct: float):
        self.logger.info(f"💰 Arbitrage: {buy_protocol} → {sell_protocol} | {profit_pct:.2f}% profit")
    
    def log_yield_opportunity(self, protocol: str, pool: str, apy: float, risk: str):
        self.logger.info(f"🌾 Yield: {protocol}/{pool} | {apy:.1f}% APY | {risk} risk")


class StrategyLogger:
    """Specialized logger for strategy sharing operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('strategy_sharing')
    
    def log_strategy_share(self, name: str, author: str, category: str, code_length: int):
        self.logger.info(f"📤 Strategy shared: '{name}' by {author} | {category} | {code_length} chars")
    
    def log_strategy_download(self, strategy_id: str, user_id: str):
        self.logger.info(f"📥 Download: {strategy_id[:8]}... by {user_id}")
    
    def log_strategy_rating(self, strategy_id: str, rating: int, reviewer: str):
        self.logger.info(f"⭐ Rating: {strategy_id[:8]}... rated {rating}/5 by {reviewer}")


# Initialize logging on import
if __name__ != "__main__":
    # Auto-setup when imported
    setup_comprehensive_logging()