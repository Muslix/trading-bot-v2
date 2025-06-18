"""
Bot Statistics Repository - Handles bot runtime statistics and metrics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import BaseRepository, DatabaseConfig
from ..models import BotStatistics


class BotStatisticsRepository(BaseRepository):
    """Repository for managing bot runtime statistics"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "bot_statistics")
        
    async def create_table(self) -> bool:
        """Create the bot_statistics table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bot_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_arbitrage_checks INTEGER DEFAULT 0,
                        total_performance_analyses INTEGER DEFAULT 0,
                        arbitrage_opportunities_found INTEGER DEFAULT 0,
                        alerts_sent INTEGER DEFAULT 0,
                        uptime_hours REAL DEFAULT 0.0,
                        session_start DATETIME,
                        session_end DATETIME,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_stats_timestamp ON bot_statistics(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_stats_session ON bot_statistics(session_start, session_end)")
                
                conn.commit()
                self.logger.info("Bot statistics table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create bot statistics table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save bot statistics data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                stats_data = BotStatistics.from_dict(data) if 'total_arbitrage_checks' in data else BotStatistics(**data)
            else:
                stats_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = stats_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Saved bot statistics: {stats_data.arbitrage_opportunities_found} opportunities found")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save bot statistics: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find bot statistics records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find bot statistics: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single bot statistics record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update bot statistics record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build SET clause
                set_parts = []
                params = []
                for key, value in data.items():
                    if key != 'id':  # Don't update ID
                        set_parts.append(f"{key} = ?")
                        params.append(value)
                
                if not set_parts:
                    return False
                
                params.append(record_id)
                set_clause = ", ".join(set_parts)
                
                sql = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
                cursor.execute(sql, params)
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update bot statistics: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete bot statistics record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete bot statistics: {e}")
            return False
    
    # Specialized methods for bot statistics
    
    async def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get the current active session statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE session_end IS NULL 
                    ORDER BY session_start DESC 
                    LIMIT 1
                """
                
                cursor.execute(sql)
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except Exception as e:
            self.logger.error(f"Failed to get current session: {e}")
            return None
    
    async def start_new_session(self) -> Optional[int]:
        """Start a new bot session"""
        session_data = BotStatistics(
            session_start=datetime.now(),
            timestamp=datetime.now()
        )
        
        return await self.save(session_data.to_dict())
    
    async def end_current_session(self) -> bool:
        """End the current active session"""
        current_session = await self.get_current_session()
        if not current_session:
            return False
        
        # Calculate uptime
        session_start = datetime.fromisoformat(current_session['session_start'])
        session_end = datetime.now()
        uptime_hours = (session_end - session_start).total_seconds() / 3600
        
        return await self.update(current_session['id'], {
            'session_end': session_end.isoformat(),
            'uptime_hours': round(uptime_hours, 2)
        })
    
    async def increment_counter(self, counter_name: str, increment: int = 1) -> bool:
        """Increment a counter in the current session"""
        valid_counters = [
            'total_arbitrage_checks',
            'total_performance_analyses', 
            'arbitrage_opportunities_found',
            'alerts_sent'
        ]
        
        if counter_name not in valid_counters:
            self.logger.error(f"Invalid counter name: {counter_name}")
            return False
        
        current_session = await self.get_current_session()
        if not current_session:
            # Start new session if none exists
            session_id = await self.start_new_session()
            if not session_id:
                return False
            current_session = await self.find_one({'id': session_id})
        
        current_value = current_session.get(counter_name, 0)
        new_value = current_value + increment
        
        return await self.update(current_session['id'], {counter_name: new_value})
    
    async def get_session_summary(self, session_id: Optional[int] = None) -> Dict[str, Any]:
        """Get summary for a specific session or current session"""
        if session_id:
            session = await self.find_one({'id': session_id})
        else:
            session = await self.get_current_session()
        
        if not session:
            return {}
        
        # Calculate rates if session has uptime
        uptime_hours = session.get('uptime_hours', 0.0)
        
        summary = {
            'session_id': session['id'],
            'session_start': session['session_start'],
            'session_end': session.get('session_end'),
            'uptime_hours': uptime_hours,
            'total_arbitrage_checks': session.get('total_arbitrage_checks', 0),
            'total_performance_analyses': session.get('total_performance_analyses', 0),
            'arbitrage_opportunities_found': session.get('arbitrage_opportunities_found', 0),
            'alerts_sent': session.get('alerts_sent', 0)
        }
        
        # Add rates if we have uptime
        if uptime_hours > 0:
            summary.update({
                'arbitrage_checks_per_hour': round(summary['total_arbitrage_checks'] / uptime_hours, 2),
                'performance_analyses_per_hour': round(summary['total_performance_analyses'] / uptime_hours, 2),
                'opportunities_found_rate': round((summary['arbitrage_opportunities_found'] / max(summary['total_arbitrage_checks'], 1)) * 100, 2),
                'alert_success_rate': round((summary['alerts_sent'] / max(summary['arbitrage_opportunities_found'], 1)) * 100, 2)
            })
        
        return summary
    
    async def get_historical_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated statistics for the last N days"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT 
                        COUNT(*) as total_sessions,
                        SUM(total_arbitrage_checks) as total_checks,
                        SUM(total_performance_analyses) as total_analyses,
                        SUM(arbitrage_opportunities_found) as total_opportunities,
                        SUM(alerts_sent) as total_alerts,
                        SUM(uptime_hours) as total_uptime,
                        AVG(uptime_hours) as avg_session_length
                    FROM {self.table_name} 
                    WHERE timestamp >= ?
                """
                
                cursor.execute(sql, [since_time.isoformat()])
                row = cursor.fetchone()
                
                if row:
                    total_uptime = row[5] or 0
                    return {
                        'period_days': days,
                        'total_sessions': row[0] or 0,
                        'total_arbitrage_checks': row[1] or 0,
                        'total_performance_analyses': row[2] or 0,
                        'total_opportunities_found': row[3] or 0,
                        'total_alerts_sent': row[4] or 0,
                        'total_uptime_hours': round(total_uptime, 2),
                        'avg_session_length_hours': round(row[6] or 0, 2),
                        'opportunities_per_hour': round((row[3] or 0) / max(total_uptime, 1), 2),
                        'success_rate': round(((row[4] or 0) / max(row[3] or 1, 1)) * 100, 2)
                    }
                else:
                    return {'period_days': days, 'total_sessions': 0}
                    
        except Exception as e:
            self.logger.error(f"Failed to get historical summary: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up session data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE timestamp < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old session records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old session data: {e}")
            return 0