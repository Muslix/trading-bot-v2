"""
Modules Package - Kern-Module des Trading Bots
"""

from .arbitrage_detector import alert_system, detect_arbitrage_opportunities
from .portfolio_analyzer import (
    analyze_crypto_portfolio_parallel,
    display_portfolio_results,
    get_top_cryptocurrencies,
)
# price_monitor functions now in real_price_monitor
from .real_price_monitor import monitor_real_exchange_prices

__all__ = [
    "analyze_crypto_portfolio_parallel",
    "get_top_cryptocurrencies",
    "display_portfolio_results",
    "monitor_real_exchange_prices",
    "detect_arbitrage_opportunities",
    "alert_system",
]
