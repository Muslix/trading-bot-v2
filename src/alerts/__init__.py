"""
Modern Alert System - Plugin-based architecture using Universal Pattern.

This module provides a clean, extensible alert system that replaces the
monolithic SmartAlertManager with individual, configurable alert plugins.

Key Components:
- AlertPlugin: Base class for all alert types
- AlertManager: Orchestrates all alert plugins
- Alert Plugins: Specific implementations (arbitrage, performance, etc.)

Usage:
    from src.alerts import AlertManager, AlertConfig
    
    # Create and configure manager
    manager = AlertManager()
    await manager.initialize_with_configs()
    
    # Process alerts with market data
    results = await manager.process_all_alerts(
        arbitrage_opportunities=arbitrage_data,
        current_performers=performance_data,
        current_prices=price_data
    )
"""

from .base import AlertPlugin, AlertConfig
from .manager import AlertManager, create_alert_manager
from .plugins import (
    ArbitrageAlert,
    PerformanceAlert,
    PriceMovementAlert,
    VolumeAlert,
    DailySummaryAlert
)

__all__ = [
    # Base classes
    'AlertPlugin',
    'AlertConfig',
    
    # Manager
    'AlertManager', 
    'create_alert_manager',
    
    # Plugin implementations
    'ArbitrageAlert',
    'PerformanceAlert',
    'PriceMovementAlert', 
    'VolumeAlert',
    'DailySummaryAlert'
]
