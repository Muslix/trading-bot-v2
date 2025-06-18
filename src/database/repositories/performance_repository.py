"""
Performance Repository - Handles cryptocurrency performance analysis data
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import BaseRepository, DatabaseConfig
from ..models import PerformanceData


class PerformanceRepository(BaseRepository):
    """Repository for managing performance analysis data"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "performance_data")
        
    async def create_table(self) -> bool:
        """Create the performance_data table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        sharpe_ratio REAL NOT NULL,
                        sortino_ratio REAL DEFAULT 0,
                        annual_return REAL NOT NULL,
                        volatility REAL NOT NULL,
                        max_drawdown REAL NOT NULL,
                        var_95 REAL DEFAULT 0,
                        beta_vs_btc REAL DEFAULT 1,
                        current_price REAL NOT NULL,
                        data_source TEXT DEFAULT 'unknown',
                        analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_data(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_symbol ON performance_data(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_sharpe ON performance_data(sharpe_ratio)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_analysis_date ON performance_data(analysis_date)")
                
                conn.commit()
                self.logger.info("Performance data table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create performance data table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save performance data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                perf_data = PerformanceData.from_dict(data) if 'symbol' in data else PerformanceData(**data)
            else:
                perf_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = perf_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Saved performance data for {perf_data.symbol}: Sharpe {perf_data.sharpe_ratio:.2f}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save performance data: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find performance data records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find performance data: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single performance data record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update performance data record"""
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
            self.logger.error(f"Failed to update performance data: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete performance data record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete performance data: {e}")
            return False
    
    # Specialized methods for performance data
    
    async def get_latest_analysis(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the latest performance analysis data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT * FROM {self.table_name} 
                    ORDER BY analysis_date DESC, timestamp DESC 
                    LIMIT ?
                """
                
                cursor.execute(sql, [limit])
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get latest analysis: {e}")
            return []
    
    async def get_top_performers(self, limit: int = 10, metric: str = 'sharpe_ratio') -> List[Dict[str, Any]]:
        """Get top performing cryptocurrencies by specified metric"""
        valid_metrics = ['sharpe_ratio', 'annual_return', 'sortino_ratio']
        if metric not in valid_metrics:
            metric = 'sharpe_ratio'
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest data for each symbol, then order by metric
                sql = f"""
                    SELECT * FROM {self.table_name} p1
                    WHERE p1.analysis_date = (
                        SELECT MAX(p2.analysis_date) 
                        FROM {self.table_name} p2 
                        WHERE p2.symbol = p1.symbol
                    )
                    ORDER BY {metric} DESC
                    LIMIT ?
                """
                
                cursor.execute(sql, [limit])
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get top performers: {e}")
            return []
    
    async def get_symbol_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get performance history for a specific symbol"""
        since_time = datetime.now() - timedelta(days=days)
        
        query = {
            'symbol': symbol,
            'analysis_date': {'>=': since_time.isoformat()}
        }
        
        return await self.find(query)
    
    async def save_batch_performance(self, performance_results: Dict[str, Dict]) -> int:
        """Save multiple performance results efficiently"""
        saved_count = 0
        
        for symbol, metrics in performance_results.items():
            if 'error' in metrics:
                continue  # Skip error results
            
            try:
                # Prepare data with symbol
                perf_data = {
                    'symbol': symbol,
                    **metrics
                }
                
                record_id = await self.save(perf_data)
                if record_id:
                    saved_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to save performance data for {symbol}: {e}")
                continue
        
        self.logger.info(f"Saved {saved_count} performance records")
        return saved_count
    
    async def get_portfolio_summary(self, symbols: List[str]) -> Dict[str, Any]:
        """Get portfolio summary for specified symbols"""
        if not symbols:
            return {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get latest data for each symbol
                placeholders = ','.join(['?' for _ in symbols])
                sql = f"""
                    SELECT 
                        COUNT(*) as total_coins,
                        AVG(sharpe_ratio) as avg_sharpe,
                        AVG(annual_return) as avg_return,
                        AVG(volatility) as avg_volatility,
                        MAX(sharpe_ratio) as best_sharpe,
                        MIN(max_drawdown) as min_drawdown
                    FROM {self.table_name} p1
                    WHERE p1.symbol IN ({placeholders})
                    AND p1.analysis_date = (
                        SELECT MAX(p2.analysis_date) 
                        FROM {self.table_name} p2 
                        WHERE p2.symbol = p1.symbol
                    )
                """
                
                cursor.execute(sql, symbols)
                row = cursor.fetchone()
                
                if row:
                    return {
                        'total_coins': row[0] or 0,
                        'avg_sharpe_ratio': round(row[1] or 0, 3),
                        'avg_annual_return': round(row[2] or 0, 3),
                        'avg_volatility': round(row[3] or 0, 3),
                        'best_sharpe_ratio': round(row[4] or 0, 3),
                        'min_drawdown': round(row[5] or 0, 3)
                    }
                else:
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up performance data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE analysis_date < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old performance records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old performance data: {e}")
            return 0