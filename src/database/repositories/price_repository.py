"""
Price Repository - Handles price history data operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import BaseRepository, DatabaseConfig
from ..models import PriceData


class PriceRepository(BaseRepository):
    """Repository for managing price history data"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "price_history")
        
    async def create_table(self) -> bool:
        """Create the price_history table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume REAL,
                        market_cap REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_timestamp ON price_history(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_exchange ON price_history(symbol, exchange)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol ON price_history(symbol)")
                
                conn.commit()
                self.logger.info("Price history table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create price history table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save price data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                price_data = PriceData.from_dict(data) if 'symbol' in data else PriceData(**data)
            else:
                price_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = price_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Saved price data for {price_data.symbol} on {price_data.exchange}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save price data: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find price data records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find price data: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single price data record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update price data record"""
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
            self.logger.error(f"Failed to update price data: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete price data record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete price data: {e}")
            return False
    
    # Specialized methods for price data
    
    async def get_latest_price(self, symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """Get the latest price for a symbol on an exchange"""
        return await self.find_one({
            'symbol': symbol,
            'exchange': exchange
        })
    
    async def get_price_history(
        self, 
        symbol: str, 
        exchange: Optional[str] = None, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get price history for a symbol within specified hours"""
        since_time = datetime.now() - timedelta(hours=hours)
        
        query = {
            'symbol': symbol,
            'timestamp': {'>=': since_time.isoformat()}
        }
        
        if exchange:
            query['exchange'] = exchange
        
        return await self.find(query)
    
    async def get_price_range(
        self, 
        symbol: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get price data within a specific time range"""
        query = {
            'symbol': symbol,
            'timestamp': {
                '>=': start_time.isoformat(),
                '<=': end_time.isoformat()
            }
        }
        
        return await self.find(query)
    
    async def get_symbols_by_exchange(self, exchange: str) -> List[str]:
        """Get all symbols available for an exchange"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"SELECT DISTINCT symbol FROM {self.table_name} WHERE exchange = ? ORDER BY symbol"
                cursor.execute(sql, [exchange])
                
                rows = cursor.fetchall()
                return [row[0] for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get symbols for exchange {exchange}: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up price data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE timestamp < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old price records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old price data: {e}")
            return 0