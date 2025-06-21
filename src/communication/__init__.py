"""
Communication Module - Plugin Architecture for Communication Components
"""

from .manager import CommunicationManager, create_communication_manager

__all__ = ['CommunicationManager', 'create_communication_manager']