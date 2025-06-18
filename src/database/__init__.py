"""
Database Module - Universal Plugin Architecture for Database Operations

This module provides a clean, extensible architecture for managing database
operations using the Repository Pattern with the Universal Plugin system.
"""

from .base import DatabasePlugin, DatabaseConfig
from .manager import DatabaseManager, get_database_manager, cleanup_database_manager
from .models import (
    PriceData, 
    ArbitrageAlert, 
    PerformanceData,
    BotStatistics,
    TelegramMessage,
    PortfolioSnapshot
)
from .repositories import (
    PriceRepository,
    ArbitrageRepository,
    PerformanceRepository,
    BotStatisticsRepository,
    TelegramRepository,
    PortfolioRepository
)

__all__ = [
    'DatabasePlugin',
    'DatabaseConfig', 
    'DatabaseManager',
    'get_database_manager',
    'cleanup_database_manager',
    'PriceData',
    'ArbitrageAlert', 
    'PerformanceData',
    'BotStatistics',
    'TelegramMessage',
    'PortfolioSnapshot',
    'PriceRepository',
    'ArbitrageRepository',
    'PerformanceRepository',
    'BotStatisticsRepository',
    'TelegramRepository',
    'PortfolioRepository'
]