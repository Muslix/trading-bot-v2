"""
Performance API Plugin
Handles performance data and analysis
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from flask import Blueprint, jsonify, request
from ..base import BaseAPIPlugin


class PerformancePlugin(BaseAPIPlugin):
    """Performance API endpoints"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.db_manager = None
        
    def get_route_prefix(self) -> str:
        return '/api'
    
    def get_blueprint(self) -> Blueprint:
        bp = Blueprint('performance', __name__)
        
        @bp.route('/performance-data', methods=['GET'])
        def get_performance_data():
            """Get performance analysis data"""
            try:
                limit = request.args.get('limit', 50, type=int)
                period = request.args.get('period', '24h')
                
                performance_data = self._get_performance_data(limit, period)
                return jsonify(performance_data)
                
            except Exception as e:
                self.logger.error(f"Error getting performance data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/top-performers', methods=['GET'])
        def get_top_performers():
            """Get top performing cryptocurrencies"""
            try:
                limit = request.args.get('limit', 10, type=int)
                performers = self._get_top_performers(limit)
                return jsonify(performers)
            except Exception as e:
                self.logger.error(f"Error getting top performers: {e}")
                return jsonify({'error': str(e)}), 500
        
        return bp
    
    def initialize(self) -> bool:
        """Initialize performance plugin with database"""
        try:
            from ...database import get_database_manager
            self.db_manager = asyncio.run(get_database_manager())
            return super().initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize database in performance plugin: {e}")
            return False
    
    def _get_performance_data(self, limit: int, period: str) -> List[Dict]:
        """Get performance data from database"""
        try:
            if not self.db_manager:
                return []
            
            performance_data = asyncio.run(self.db_manager.execute(
                'get_recent',
                repository='performance',
                limit=limit
            ))
            
            return performance_data or []
            
        except Exception as e:
            self.logger.error(f"Error fetching performance data: {e}")
            return []
    
    def _get_top_performers(self, limit: int) -> List[Dict]:
        """Get top performing cryptocurrencies"""
        try:
            if not self.db_manager:
                return []
            
            # This would be a specialized query in a real implementation
            recent_data = asyncio.run(self.db_manager.execute(
                'get_recent',
                repository='performance',
                limit=100
            ))
            
            if not recent_data:
                return []
            
            # Sort by performance metrics (simplified)
            sorted_performers = sorted(
                recent_data,
                key=lambda x: x.get('sharpe_ratio', 0),
                reverse=True
            )
            
            return sorted_performers[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return []