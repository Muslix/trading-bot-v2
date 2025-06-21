"""
Utils Package - Modern utility functions with plugin architecture

This package provides all utility functions through a clean plugin-based architecture:
- Performance monitoring and decorators
- Logging utilities (error and production)
- Symbol normalization
- System health monitoring
- Telegram alerts

Usage:
    from src.utils import create_util_manager
    
    # Create and initialize manager
    util_manager = await create_util_manager()
    
    # Use convenience methods
    await util_manager.log_performance("my_function", 0.5)
    normalized = await util_manager.normalize_symbol("BTCUSDT")
    success = await util_manager.send_telegram_alert("Alert message")
    
    # Or use plugins directly
    result = await util_manager.process_with_util("performance", {
        "action": "log_performance",
        "func_name": "my_function",
        "duration": 0.5
    })

Legacy compatibility:
    # These imports still work for backward compatibility
    from src.utils.decorators import log_performance, async_log_performance
"""

from .manager import UtilManager, create_util_manager
from .base import UtilConfig, UtilPlugin

# Legacy compatibility - import decorators directly for existing code
from .decorators import log_performance, async_log_performance

__all__ = [
    "UtilManager",
    "create_util_manager", 
    "UtilConfig",
    "UtilPlugin",
    # Legacy compatibility
    "log_performance", 
    "async_log_performance"
]