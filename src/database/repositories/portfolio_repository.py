"""
Portfolio Repository - Handles portfolio analysis snapshots and tracking
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from ..base import BaseRepository, DatabaseConfig
from ..models import PortfolioSnapshot


class PortfolioRepository(BaseRepository):
    """Repository for managing portfolio analysis snapshots"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "portfolio_snapshots")
        
    async def create_table(self) -> bool:
        """Create the portfolio_snapshots table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_type TEXT DEFAULT 'performance_check',
                        top_performers TEXT DEFAULT '[]',
                        total_coins_analyzed INTEGER DEFAULT 0,
                        avg_sharpe_ratio REAL DEFAULT 0.0,
                        best_performer_symbol TEXT DEFAULT '',
                        best_performer_sharpe REAL DEFAULT 0.0,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_snapshots(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_type ON portfolio_snapshots(snapshot_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_sharpe ON portfolio_snapshots(avg_sharpe_ratio)")
                
                conn.commit()
                self.logger.info("Portfolio snapshots table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create portfolio snapshots table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save portfolio snapshot data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                snapshot_data = PortfolioSnapshot.from_dict(data) if 'snapshot_type' in data else PortfolioSnapshot(**data)
            else:
                snapshot_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = snapshot_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Saved portfolio snapshot: {snapshot_data.total_coins_analyzed} coins, avg Sharpe {snapshot_data.avg_sharpe_ratio:.3f}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save portfolio snapshot: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find portfolio snapshot records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find portfolio snapshots: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single portfolio snapshot record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update portfolio snapshot record"""
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
            self.logger.error(f"Failed to update portfolio snapshot: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete portfolio snapshot record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete portfolio snapshot: {e}")
            return False
    
    # Specialized methods for portfolio snapshots
    
    async def save_performance_snapshot(
        self, 
        top_performers: List[Dict], 
        total_coins: int,
        avg_sharpe: float,
        best_performer: Dict[str, Any]
    ) -> Optional[int]:
        """Save a performance analysis snapshot"""
        snapshot = PortfolioSnapshot(
            snapshot_type="performance_check",
            total_coins_analyzed=total_coins,
            avg_sharpe_ratio=round(avg_sharpe, 3),
            best_performer_symbol=best_performer.get('symbol', ''),
            best_performer_sharpe=round(best_performer.get('sharpe_ratio', 0.0), 3)
        )
        
        # Set top performers using the model method
        snapshot.set_top_performers(top_performers)
        
        return await self.save(snapshot.to_dict())
    
    async def get_latest_snapshot(self, snapshot_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the latest portfolio snapshot"""
        query = {}
        if snapshot_type:
            query['snapshot_type'] = snapshot_type
        
        results = await self.find(query)
        return results[0] if results else None
    
    async def get_performance_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio performance trend over specified days"""
        since_time = datetime.now() - timedelta(days=days)
        
        query = {
            'snapshot_type': 'performance_check',
            'timestamp': {'>=': since_time.isoformat()}
        }
        
        snapshots = await self.find(query)
        
        # Process snapshots to extract trend data
        trend_data = []
        for snapshot in reversed(snapshots):  # Reverse to get chronological order
            trend_point = {
                'timestamp': snapshot['timestamp'],
                'total_coins': snapshot['total_coins_analyzed'],
                'avg_sharpe': snapshot['avg_sharpe_ratio'],
                'best_performer': snapshot['best_performer_symbol'],
                'best_sharpe': snapshot['best_performer_sharpe']
            }
            trend_data.append(trend_point)
        
        return trend_data
    
    async def get_top_performers_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get history of when a symbol appeared in top performers"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE snapshot_type = 'performance_check'
                    AND timestamp >= ?
                    AND (top_performers LIKE ? OR best_performer_symbol = ?)
                    ORDER BY timestamp DESC
                """
                
                cursor.execute(sql, [
                    since_time.isoformat(), 
                    f'%"{symbol}"%',  # Search for symbol in JSON
                    symbol
                ])
                
                rows = cursor.fetchall()
                appearances = []
                
                for row in rows:
                    snapshot = dict(row)
                    try:
                        top_performers = json.loads(snapshot.get('top_performers', '[]'))
                        # Check if symbol is in top performers
                        is_in_top = any(
                            perf.get('symbol') == symbol for perf in top_performers 
                            if isinstance(perf, dict)
                        )
                        
                        if is_in_top or snapshot.get('best_performer_symbol') == symbol:
                            # Find the performance data for this symbol
                            symbol_perf = None
                            for perf in top_performers:
                                if isinstance(perf, dict) and perf.get('symbol') == symbol:
                                    symbol_perf = perf
                                    break
                            
                            appearances.append({
                                'timestamp': snapshot['timestamp'],
                                'performance_data': symbol_perf,
                                'was_best_performer': snapshot.get('best_performer_symbol') == symbol,
                                'best_performer_sharpe': snapshot.get('best_performer_sharpe', 0)
                            })
                    except json.JSONDecodeError:
                        continue
                
                return appearances
                
        except Exception as e:
            self.logger.error(f"Failed to get top performers history for {symbol}: {e}")
            return []
    
    async def get_portfolio_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get portfolio statistics over specified days"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT 
                        COUNT(*) as total_snapshots,
                        AVG(total_coins_analyzed) as avg_coins_analyzed,
                        AVG(avg_sharpe_ratio) as overall_avg_sharpe,
                        MAX(avg_sharpe_ratio) as best_avg_sharpe,
                        MIN(avg_sharpe_ratio) as worst_avg_sharpe,
                        MAX(best_performer_sharpe) as highest_individual_sharpe
                    FROM {self.table_name} 
                    WHERE snapshot_type = 'performance_check'
                    AND timestamp >= ?
                """
                
                cursor.execute(sql, [since_time.isoformat()])
                row = cursor.fetchone()
                
                if row:
                    return {
                        'period_days': days,
                        'total_snapshots': row[0] or 0,
                        'avg_coins_analyzed': round(row[1] or 0, 1),
                        'overall_avg_sharpe': round(row[2] or 0, 3),
                        'best_avg_sharpe': round(row[3] or 0, 3),
                        'worst_avg_sharpe': round(row[4] or 0, 3),
                        'highest_individual_sharpe': round(row[5] or 0, 3),
                        'sharpe_improvement': round((row[3] or 0) - (row[4] or 0), 3)
                    }
                else:
                    return {'period_days': days, 'total_snapshots': 0}
                    
        except Exception as e:
            self.logger.error(f"Failed to get portfolio statistics: {e}")
            return {'error': str(e)}
    
    async def find_best_performing_periods(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find the best performing portfolio periods"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE snapshot_type = 'performance_check'
                    ORDER BY avg_sharpe_ratio DESC
                    LIMIT ?
                """
                
                cursor.execute(sql, [limit])
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find best performing periods: {e}")
            return []
    
    async def get_symbol_performance_summary(self, symbol: str) -> Dict[str, Any]:
        """Get performance summary for a specific symbol across all snapshots"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT 
                        COUNT(*) as total_appearances,
                        COUNT(CASE WHEN best_performer_symbol = ? THEN 1 END) as times_best_performer
                    FROM {self.table_name} 
                    WHERE snapshot_type = 'performance_check'
                    AND (top_performers LIKE ? OR best_performer_symbol = ?)
                """
                
                cursor.execute(sql, [symbol, f'%"{symbol}"%', symbol])
                row = cursor.fetchone()
                
                if row:
                    total_snapshots_query = f"""
                        SELECT COUNT(*) FROM {self.table_name} 
                        WHERE snapshot_type = 'performance_check'
                    """
                    cursor.execute(total_snapshots_query)
                    total_snapshots = cursor.fetchone()[0]
                    
                    return {
                        'symbol': symbol,
                        'total_appearances': row[0] or 0,
                        'times_best_performer': row[1] or 0,
                        'appearance_rate': round(((row[0] or 0) / max(total_snapshots, 1)) * 100, 2),
                        'best_performer_rate': round(((row[1] or 0) / max(row[0] or 1, 1)) * 100, 2)
                    }
                else:
                    return {'symbol': symbol, 'total_appearances': 0}
                    
        except Exception as e:
            self.logger.error(f"Failed to get symbol performance summary for {symbol}: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_snapshots(self, days: int = 90) -> int:
        """Clean up portfolio snapshots older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE timestamp < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old portfolio snapshots")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old portfolio snapshots: {e}")
            return 0