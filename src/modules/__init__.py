"""
Legacy Modules Package - Compatibility wrappers for migrated plugins

DEPRECATED: All modules have been migrated to the new plugin architecture.
Use the corresponding plugins instead:

- arbitrage_detector -> src.analyzers.plugins.arbitrage_analyzer
- portfolio_analyzer -> src.analyzers.plugins.portfolio_analyzer  
- real_price_monitor -> src.monitors.plugins.price_monitor
- historical_data -> src.analyzers.plugins.historical_analyzer
"""

import warnings

# Legacy compatibility imports
try:
    from src.analyzers.plugins.arbitrage_analyzer import (
        alert_system, 
        detect_arbitrage_opportunities
    )
    from src.analyzers.plugins.portfolio_analyzer import (
        analyze_crypto_portfolio_parallel,
        display_portfolio_results,
        get_top_cryptocurrencies,
    )
    from src.monitors.plugins.price_monitor import monitor_real_exchange_prices
    
    # Warn about deprecated usage
    warnings.warn(
        "src.modules is deprecated. Use the new plugin architecture: "
        "src.analyzers, src.monitors, src.communication",
        DeprecationWarning,
        stacklevel=2
    )
    
except ImportError as e:
    warnings.warn(f"Some legacy imports failed: {e}", ImportWarning)

__all__ = [
    "analyze_crypto_portfolio_parallel",
    "get_top_cryptocurrencies", 
    "display_portfolio_results",
    "monitor_real_exchange_prices",
    "detect_arbitrage_opportunities",
    "alert_system",
]