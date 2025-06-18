"""
Arbitrage Repository - Handles arbitrage alert data operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import BaseRepository, DatabaseConfig
from ..models import ArbitrageAlert


class ArbitrageRepository(BaseRepository):
    """Repository for managing arbitrage alert data"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "arbitrage_alerts")
        
    async def create_table(self) -> bool:
        """Create the arbitrage_alerts table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS arbitrage_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        buy_exchange TEXT NOT NULL,
                        sell_exchange TEXT NOT NULL,
                        buy_price REAL NOT NULL,
                        sell_price REAL NOT NULL,
                        profit_percentage REAL NOT NULL,
                        profit_amount REAL NOT NULL,
                        volume_available REAL,
                        alert_sent BOOLEAN DEFAULT 0,
                        telegram_message_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_timestamp ON arbitrage_alerts(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_symbol ON arbitrage_alerts(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_exchanges ON arbitrage_alerts(buy_exchange, sell_exchange)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_arbitrage_profit ON arbitrage_alerts(profit_percentage)")
                
                conn.commit()
                self.logger.info("Arbitrage alerts table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create arbitrage alerts table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save arbitrage alert data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                alert_data = ArbitrageAlert.from_dict(data) if 'symbol' in data else ArbitrageAlert(**data)
            else:
                alert_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = alert_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Saved arbitrage alert for {alert_data.symbol}: {alert_data.profit_percentage:.2f}%")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save arbitrage alert: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find arbitrage alert records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find arbitrage alerts: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single arbitrage alert record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update arbitrage alert record"""
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
            self.logger.error(f"Failed to update arbitrage alert: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete arbitrage alert record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete arbitrage alert: {e}")
            return False
    
    # Specialized methods for arbitrage alerts
    
    async def check_recent_similar_alert(
        self, 
        symbol: str, 
        buy_exchange: str, 
        sell_exchange: str, 
        profit_threshold: float = 0.5,
        hours: int = 1
    ) -> bool:
        """Check if a similar arbitrage alert exists within specified time"""
        since_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT COUNT(*) FROM {self.table_name} 
                    WHERE symbol = ? 
                    AND buy_exchange = ? 
                    AND sell_exchange = ? 
                    AND ABS(profit_percentage - ?) <= ?
                    AND timestamp >= ?
                """
                
                cursor.execute(sql, [
                    symbol, buy_exchange, sell_exchange, 
                    profit_threshold, profit_threshold, 
                    since_time.isoformat()
                ])
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Failed to check recent similar alerts: {e}")
            return False
    
    async def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get arbitrage alerts from the last N hours"""
        since_time = datetime.now() - timedelta(hours=hours)
        
        query = {
            'timestamp': {'>=': since_time.isoformat()}
        }
        
        return await self.find(query)
    
    async def get_profitable_alerts(self, min_profit: float = 1.0) -> List[Dict[str, Any]]:
        """Get alerts above a minimum profit threshold"""
        query = {
            'profit_percentage': {'>=': min_profit}
        }
        
        return await self.find(query)
    
    async def mark_alert_sent(self, alert_id: int, telegram_message_id: Optional[str] = None) -> bool:
        """Mark an alert as sent with optional Telegram message ID"""
        update_data = {'alert_sent': True}
        if telegram_message_id:
            update_data['telegram_message_id'] = telegram_message_id
        
        return await self.update(alert_id, update_data)
    
    async def get_unsent_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts that haven't been sent yet"""
        query = {'alert_sent': False}
        return await self.find(query)
    
    async def get_symbol_statistics(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get arbitrage statistics for a specific symbol"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT 
                        COUNT(*) as total_alerts,
                        AVG(profit_percentage) as avg_profit,
                        MAX(profit_percentage) as max_profit,
                        MIN(profit_percentage) as min_profit,
                        COUNT(CASE WHEN alert_sent = 1 THEN 1 END) as sent_alerts
                    FROM {self.table_name} 
                    WHERE symbol = ? AND timestamp >= ?
                """
                
                cursor.execute(sql, [symbol, since_time.isoformat()])
                row = cursor.fetchone()
                
                if row:
                    return {
                        'symbol': symbol,
                        'total_alerts': row[0] or 0,
                        'avg_profit': round(row[1] or 0, 2),
                        'max_profit': round(row[2] or 0, 2),
                        'min_profit': round(row[3] or 0, 2),
                        'sent_alerts': row[4] or 0,
                        'period_days': days
                    }
                else:
                    return {
                        'symbol': symbol,
                        'total_alerts': 0,
                        'avg_profit': 0,
                        'max_profit': 0,
                        'min_profit': 0,
                        'sent_alerts': 0,
                        'period_days': days
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get symbol statistics: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_alerts(self, days: int = 30) -> int:
        """Clean up arbitrage alerts older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE timestamp < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old arbitrage alerts")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old arbitrage alerts: {e}")
            return 0