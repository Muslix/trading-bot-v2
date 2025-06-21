"""
Database API Plugin
Handles database operations and queries
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from flask import Blueprint, jsonify, request
from ..base import BaseAPIPlugin


class DatabasePlugin(BaseAPIPlugin):
    """Database API endpoints"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.db_manager = None
        
    def get_route_prefix(self) -> str:
        return '/api/db'
    
    def get_blueprint(self) -> Blueprint:
        bp = Blueprint('database', __name__)
        
        @bp.route('/stats', methods=['GET'])
        def get_database_stats():
            """Get database statistics"""
            try:
                stats = self._get_database_stats()
                return jsonify(stats)
            except Exception as e:
                self.logger.error(f"Error getting database stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/live-prices', methods=['GET'])
        def get_live_prices():
            """Get recent price data"""
            try:
                limit = request.args.get('limit', 20, type=int)
                symbol = request.args.get('symbol')
                
                prices = self._get_live_prices(limit, symbol)
                return jsonify(prices)
            except Exception as e:
                self.logger.error(f"Error getting live prices: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/health', methods=['GET'])
        def get_database_health():
            """Get database health status"""
            try:
                health = self._get_database_health()
                return jsonify(health)
            except Exception as e:
                self.logger.error(f"Error checking database health: {e}")
                return jsonify({'error': str(e)}), 500
        
        return bp
    
    def initialize(self) -> bool:
        """Initialize database plugin"""
        try:
            from ...database import get_database_manager
            self.db_manager = asyncio.run(get_database_manager())
            return super().initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize database in database plugin: {e}")
            return False
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            if not self.db_manager:
                return {'error': 'Database not available'}
            
            stats = asyncio.run(self._fetch_db_stats())
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
    
    async def _fetch_db_stats(self) -> Dict[str, Any]:
        """Fetch database statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'repositories': {}
        }
        
        # Check each repository
        repositories = ['price', 'arbitrage', 'performance', 'portfolio', 'bot_statistics', 'telegram']
        
        for repo in repositories:
            try:
                count = await self.db_manager.execute('count', repository=repo)
                stats['repositories'][repo] = {
                    'record_count': count or 0,
                    'status': 'healthy'
                }
            except Exception as e:
                stats['repositories'][repo] = {
                    'record_count': 0,
                    'status': 'error',
                    'error': str(e)
                }
        
        return stats
    
    def _get_live_prices(self, limit: int, symbol: str = None) -> List[Dict]:
        """Get recent price data"""
        try:
            if not self.db_manager:
                return []
            
            # Get recent price data
            filters = {'limit': limit}
            if symbol:
                filters['symbol'] = symbol
            
            prices = asyncio.run(self.db_manager.execute(
                'get_recent',
                repository='price',
                **filters
            ))
            
            return prices or []
            
        except Exception as e:
            self.logger.error(f"Error getting live prices: {e}")
            return []
    
    def _get_database_health(self) -> Dict[str, Any]:
        """Get database health status"""
        try:
            if not self.db_manager:
                return {
                    'status': 'unhealthy',
                    'message': 'Database manager not available'
                }
            
            # Try a simple database operation
            asyncio.run(self.db_manager.execute('count', repository='price'))
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'connection': 'active'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }