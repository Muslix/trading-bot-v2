"""
Dashboard API Plugin
Handles general dashboard data and statistics
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from flask import Blueprint, jsonify, request
from ..base import BaseAPIPlugin


class DashboardPlugin(BaseAPIPlugin):
    """Dashboard API endpoints"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.db_manager = None
        
    def get_route_prefix(self) -> str:
        return '/api'
    
    def get_blueprint(self) -> Blueprint:
        bp = Blueprint('dashboard', __name__)
        
        @bp.route('/dashboard-data', methods=['GET'])
        def get_dashboard_data():
            """Get comprehensive dashboard data"""
            start_time = time.time()
            client_ip = request.remote_addr
            self.logger.info(f"Dashboard data request from {client_ip}")
            
            try:
                dashboard_data = self._get_dashboard_data()
                duration = time.time() - start_time
                self.logger.info(f"Dashboard data request completed in {duration:.3f}s for {client_ip}")
                return jsonify(dashboard_data)
                
            except Exception as e:
                self.logger.error(f"Error getting dashboard data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @bp.route('/system-status', methods=['GET'])
        def get_system_status():
            """Get system status information"""
            try:
                status_data = self._get_system_status()
                return jsonify(status_data)
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                return jsonify({'error': str(e)}), 500
        
        return bp
    
    def initialize(self) -> bool:
        """Initialize dashboard plugin with database"""
        try:
            # Import and initialize database manager
            from ...database import get_database_manager
            
            # Handle async initialization properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an event loop, skip database initialization for now
                    self.logger.warning("Skipping database initialization (event loop running)")
                    self.db_manager = None
                else:
                    self.db_manager = asyncio.run(get_database_manager())
            except RuntimeError:
                # No event loop running
                self.db_manager = asyncio.run(get_database_manager())
                
            return super().initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize database in dashboard plugin: {e}")
            return False
    
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Basic system info
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'running',
                'uptime': self._calculate_uptime(),
                'system_info': {
                    'cpu_usage': '45%',  # Could be real system metrics
                    'memory_usage': '2.1GB',
                    'active_threads': 8
                }
            }
            
            # Get database statistics if available
            if self.db_manager:
                try:
                    stats = asyncio.run(self._get_database_stats())
                    dashboard_data.update(stats)
                except Exception as e:
                    self.logger.warning(f"Could not get database stats: {e}")
                    dashboard_data.update({
                        'total_price_records': 0,
                        'total_arbitrage_records': 0,
                        'recent_opportunities': []
                    })
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error building dashboard data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Get price record count
            price_count = await self.db_manager.execute('count', repository='price')
            stats['total_price_records'] = price_count
            
            # Get arbitrage record count 
            arbitrage_count = await self.db_manager.execute('count', repository='arbitrage')
            stats['total_arbitrage_records'] = arbitrage_count
            
            # Get recent arbitrage opportunities
            recent_opportunities = await self.db_manager.execute(
                'get_recent', 
                repository='arbitrage',
                limit=10
            )
            stats['recent_opportunities'] = recent_opportunities or []
            
        except Exception as e:
            self.logger.warning(f"Error getting database stats: {e}")
            stats = {
                'total_price_records': 0,
                'total_arbitrage_records': 0,
                'recent_opportunities': []
            }
            
        return stats
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': 'healthy' if self.db_manager else 'unavailable',
                'api_server': 'healthy',
                'monitoring': 'active'
            },
            'version': '2.0.0',
            'environment': 'production'
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate system uptime"""
        # This would normally track actual start time
        return "2h 15m"