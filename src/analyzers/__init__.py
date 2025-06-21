"""
Analyzers Module - Plugin Architecture for Analysis Components
"""

from .manager import AnalyzerManager, create_analyzer_manager

__all__ = ['AnalyzerManager', 'create_analyzer_manager']