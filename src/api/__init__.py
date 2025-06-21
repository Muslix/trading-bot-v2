"""
API Plugin System for Crypto Trading Bot
Modular Web API with plugin architecture
"""

from .manager import create_api_manager

__all__ = ['create_api_manager']