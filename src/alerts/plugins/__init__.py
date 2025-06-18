"""
Alert plugins - specific implementations of different alert types.

This module contains all concrete alert implementations using the Universal Pattern.
Each alert type is a separate plugin that can be independently configured and enabled.
"""

from .arbitrage_alert import ArbitrageAlert
from .performance_alert import PerformanceAlert
from .price_movement_alert import PriceMovementAlert
from .volume_alert import VolumeAlert
from .daily_summary_alert import DailySummaryAlert

__all__ = [
    'ArbitrageAlert',
    'PerformanceAlert', 
    'PriceMovementAlert',
    'VolumeAlert',
    'DailySummaryAlert'
]
