"""
Modules Package - Kern-Module des Trading Bots
"""

from .arbitrage_detector import alert_system, detect_arbitrage_opportunities
from .portfolio_analyzer import (
    analyze_crypto_portfolio_parallel,
    display_portfolio_results,
    get_top_cryptocurrencies,
)
from .price_monitor import get_popular_crypto_symbols, monitor_multi_exchange_prices

__all__ = [
    "analyze_crypto_portfolio_parallel",
    "get_top_cryptocurrencies",
    "display_portfolio_results",
    "monitor_multi_exchange_prices",
    "get_popular_crypto_symbols",
    "detect_arbitrage_opportunities",
    "alert_system",
]
