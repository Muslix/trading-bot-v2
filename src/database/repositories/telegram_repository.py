"""
Telegram Repository - Handles Telegram message logs and notifications
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..base import BaseRepository, DatabaseConfig
from ..models import TelegramMessage


class TelegramRepository(BaseRepository):
    """Repository for managing Telegram message logs"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config, "telegram_messages")
        
    async def create_table(self) -> bool:
        """Create the telegram_messages table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telegram_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id TEXT NOT NULL,
                        message_type TEXT DEFAULT 'alert',
                        message_text TEXT NOT NULL,
                        telegram_message_id TEXT,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telegram_timestamp ON telegram_messages(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telegram_chat_id ON telegram_messages(chat_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telegram_type ON telegram_messages(message_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_telegram_success ON telegram_messages(success)")
                
                conn.commit()
                self.logger.info("Telegram messages table created successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create telegram messages table: {e}")
            return False
    
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save telegram message data"""
        try:
            # Convert to model for validation
            if isinstance(data, dict):
                msg_data = TelegramMessage.from_dict(data) if 'chat_id' in data else TelegramMessage(**data)
            else:
                msg_data = data
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                data_dict = msg_data.to_dict()
                # Remove id if present (auto-increment)
                data_dict.pop('id', None)
                
                columns, placeholders, values = self._dict_to_insert(data_dict)
                
                sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                
                record_id = cursor.lastrowid
                conn.commit()
                
                status = "✓" if msg_data.success else "✗"
                self.logger.debug(f"Logged Telegram message {status}: {msg_data.message_type} to {msg_data.chat_id}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to save telegram message: {e}")
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find telegram message records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"SELECT * FROM {self.table_name} WHERE {where_clause} ORDER BY timestamp DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find telegram messages: {e}")
            return []
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single telegram message record"""
        results = await self.find(query)
        return results[0] if results else None
    
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update telegram message record"""
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
            self.logger.error(f"Failed to update telegram message: {e}")
            return False
    
    async def delete(self, record_id: int) -> bool:
        """Delete telegram message record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE id = ?"
                cursor.execute(sql, [record_id])
                
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete telegram message: {e}")
            return False
    
    # Specialized methods for telegram messages
    
    async def log_message_sent(
        self, 
        chat_id: str, 
        message_text: str, 
        message_type: str = "alert",
        telegram_message_id: Optional[str] = None
    ) -> Optional[int]:
        """Log a successful message send"""
        msg_data = TelegramMessage(
            chat_id=chat_id,
            message_type=message_type,
            message_text=message_text,
            telegram_message_id=telegram_message_id,
            success=True
        )
        
        return await self.save(msg_data.to_dict())
    
    async def log_message_failed(
        self, 
        chat_id: str, 
        message_text: str, 
        error_message: str,
        message_type: str = "alert"
    ) -> Optional[int]:
        """Log a failed message send"""
        msg_data = TelegramMessage(
            chat_id=chat_id,
            message_type=message_type,
            message_text=message_text,
            success=False,
            error_message=error_message
        )
        
        return await self.save(msg_data.to_dict())
    
    async def get_recent_messages(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get messages from the last N hours"""
        since_time = datetime.now() - timedelta(hours=hours)
        
        query = {
            'timestamp': {'>=': since_time.isoformat()}
        }
        
        return await self.find(query)
    
    async def get_failed_messages(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed messages from the last N hours"""
        since_time = datetime.now() - timedelta(hours=hours)
        
        query = {
            'success': False,
            'timestamp': {'>=': since_time.isoformat()}
        }
        
        return await self.find(query)
    
    async def get_message_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get message sending statistics for the last N days"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(CASE WHEN success = 1 THEN 1 END) as successful_messages,
                        COUNT(CASE WHEN success = 0 THEN 1 END) as failed_messages,
                        COUNT(DISTINCT chat_id) as unique_chats,
                        COUNT(CASE WHEN message_type = 'alert' THEN 1 END) as alert_messages,
                        COUNT(CASE WHEN message_type = 'performance' THEN 1 END) as performance_messages,
                        COUNT(CASE WHEN message_type = 'status' THEN 1 END) as status_messages
                    FROM {self.table_name} 
                    WHERE timestamp >= ?
                """
                
                cursor.execute(sql, [since_time.isoformat()])
                row = cursor.fetchone()
                
                if row:
                    total = row[0] or 0
                    successful = row[1] or 0
                    failed = row[2] or 0
                    
                    return {
                        'period_days': days,
                        'total_messages': total,
                        'successful_messages': successful,
                        'failed_messages': failed,
                        'success_rate': round((successful / max(total, 1)) * 100, 2),
                        'failure_rate': round((failed / max(total, 1)) * 100, 2),
                        'unique_chats': row[3] or 0,
                        'alert_messages': row[4] or 0,
                        'performance_messages': row[5] or 0,
                        'status_messages': row[6] or 0
                    }
                else:
                    return {'period_days': days, 'total_messages': 0}
                    
        except Exception as e:
            self.logger.error(f"Failed to get message statistics: {e}")
            return {'error': str(e)}
    
    async def get_chat_message_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get message history for a specific chat"""
        query = {'chat_id': chat_id}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause, params = self._build_where_clause(query)
                sql = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE {where_clause} 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                
                params.append(limit)
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get chat message history: {e}")
            return []
    
    async def find_message_by_telegram_id(self, telegram_message_id: str) -> Optional[Dict[str, Any]]:
        """Find a message by its Telegram message ID"""
        return await self.find_one({'telegram_message_id': telegram_message_id})
    
    async def get_message_type_breakdown(self, days: int = 30) -> Dict[str, int]:
        """Get breakdown of message types for the last N days"""
        since_time = datetime.now() - timedelta(days=days)
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"""
                    SELECT message_type, COUNT(*) as count
                    FROM {self.table_name} 
                    WHERE timestamp >= ?
                    GROUP BY message_type
                    ORDER BY count DESC
                """
                
                cursor.execute(sql, [since_time.isoformat()])
                rows = cursor.fetchall()
                
                return {row[0]: row[1] for row in rows}
                
        except Exception as e:
            self.logger.error(f"Failed to get message type breakdown: {e}")
            return {}
    
    async def cleanup_old_messages(self, days: int = 90) -> int:
        """Clean up message logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = f"DELETE FROM {self.table_name} WHERE timestamp < ?"
                cursor.execute(sql, [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old telegram message logs")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old telegram messages: {e}")
            return 0