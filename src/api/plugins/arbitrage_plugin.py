"""
Arbitrage API Plugin
Handles arbitrage opportunities and alerts
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from flask import Blueprint, jsonify, request
from ..base import BaseAPIPlugin


class ArbitragePlugin(BaseAPIPlugin):
    """Arbitrage API endpoints"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.db_manager = None
        
    def get_route_prefix(self) -> str:
        return '/api'
    
    def get_blueprint(self) -> Blueprint:
        bp = Blueprint('arbitrage', __name__)
        
        @bp.route('/arbitrage-alerts', methods=['GET'])
        def get_arbitrage_alerts():
            """Get recent arbitrage opportunities"""
            try:
                limit = request.args.get('limit', 20, type=int)
                hours = request.args.get('hours', 24, type=int)
                
                alerts = self._get_arbitrage_alerts(limit, hours)
                return jsonify(alerts)
                
            except Exception as e:
                self.logger.error(f"Error getting arbitrage alerts: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/arbitrage-stats', methods=['GET'])
        def get_arbitrage_stats():
            """Get arbitrage statistics"""
            try:
                stats = self._get_arbitrage_stats()
                return jsonify(stats)
            except Exception as e:
                self.logger.error(f"Error getting arbitrage stats: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/live-opportunities', methods=['GET'])
        def get_live_opportunities():
            """Get currently active arbitrage opportunities"""
            try:
                opportunities = self._get_live_opportunities()
                return jsonify(opportunities)
            except Exception as e:
                self.logger.error(f"Error getting live opportunities: {e}")
                return jsonify({'error': str(e)}), 500
        
        return bp
    
    def initialize(self) -> bool:
        """Initialize arbitrage plugin with database"""
        try:
            from ...database import get_database_manager
            self.db_manager = asyncio.run(get_database_manager())
            return super().initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize database in arbitrage plugin: {e}")
            return False
    
    def _get_arbitrage_alerts(self, limit: int = 20, hours: int = 24) -> List[Dict]:
        """Get recent arbitrage alerts from database"""
        try:
            if not self.db_manager:
                return []
            
            # Get recent arbitrage opportunities
            since_time = datetime.now() - timedelta(hours=hours)
            alerts = asyncio.run(self.db_manager.execute(
                'get_recent',
                repository='arbitrage',
                limit=limit,
                since=since_time.isoformat()
            ))
            
            return alerts or []
            
        except Exception as e:
            self.logger.error(f"Error fetching arbitrage alerts: {e}")
            return []
    
    def _get_arbitrage_stats(self) -> Dict[str, Any]:
        """Get arbitrage statistics"""
        try:
            if not self.db_manager:
                return {'total_opportunities': 0, 'avg_profit': 0}
            
            # Get statistics from database
            stats = asyncio.run(self._fetch_arbitrage_stats())
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating arbitrage stats: {e}")
            return {
                'total_opportunities': 0,
                'avg_profit': 0,
                'best_profit': 0,
                'active_pairs': 0
            }
    
    async def _fetch_arbitrage_stats(self) -> Dict[str, Any]:
        """Fetch arbitrage statistics from database"""
        try:
            # Count total opportunities
            total_count = await self.db_manager.execute('count', repository='arbitrage')
            
            # Get recent opportunities for calculations
            recent_opportunities = await self.db_manager.execute(
                'get_recent',
                repository='arbitrage',
                limit=100
            )
            
            if not recent_opportunities:
                return {
                    'total_opportunities': total_count or 0,
                    'avg_profit': 0,
                    'best_profit': 0,
                    'active_pairs': 0
                }
            
            # Calculate statistics
            profits = [opp.get('profit_percentage', 0) for opp in recent_opportunities]
            symbols = set(opp.get('symbol', '') for opp in recent_opportunities)
            
            return {
                'total_opportunities': total_count or 0,
                'avg_profit': round(sum(profits) / len(profits), 2) if profits else 0,
                'best_profit': round(max(profits), 2) if profits else 0,
                'active_pairs': len(symbols)
            }
            
        except Exception as e:
            self.logger.error(f"Error in fetch_arbitrage_stats: {e}")
            return {
                'total_opportunities': 0,
                'avg_profit': 0,
                'best_profit': 0,
                'active_pairs': 0
            }
    
    def _get_live_opportunities(self) -> List[Dict]:
        """Get currently active arbitrage opportunities"""
        try:
            if not self.db_manager:
                return []
            
            # Get very recent opportunities (last 5 minutes)
            since_time = datetime.now() - timedelta(minutes=5)
            opportunities = asyncio.run(self.db_manager.execute(
                'get_recent',
                repository='arbitrage',
                limit=50,
                since=since_time.isoformat()
            ))
            
            # Filter for currently relevant opportunities
            live_opportunities = []
            if opportunities:
                for opp in opportunities:
                    if opp.get('profit_percentage', 0) >= 1.0:  # Only profitable ones
                        live_opportunities.append(opp)
            
            return live_opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting live opportunities: {e}")
            return []