"""
Data Sources Module - Universal Plugin Architecture for Data Sources

This module provides a clean, extensible architecture for managing various
cryptocurrency data sources using the Universal Plugin Pattern.
"""

from .base import DataSourcePlugin, DataSourceConfig
from .manager import DataSourceManager, create_data_source_manager

__all__ = [
    'DataSourcePlugin',
    'DataSourceConfig',
    'DataSourceManager',
    'create_data_source_manager'
]