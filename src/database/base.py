"""
Base classes for Database plugins using the Universal Pattern.
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from src.core import UniversalPlugin, ModuleConfig


@dataclass
class DatabaseConfig(ModuleConfig):
    """Configuration for Database plugins"""
    db_path: str = "database/crypto_trading_bot.db"
    connection_timeout: float = 30.0
    enable_wal_mode: bool = True
    auto_vacuum: bool = True
    cache_size: int = -64000  # 64MB cache
    foreign_keys: bool = True
    
    def __post_init__(self):
        import os
        # Ensure absolute path
        if not os.path.isabs(self.db_path):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(project_root, self.db_path)


class DatabasePlugin(UniversalPlugin):
    """
    Base class for all database repository plugins.
    
    Each repository (Price, Alert, Performance, etc.) implements this interface
    using the Repository Pattern.
    """
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.config: DatabaseConfig = config
        self.table_name: str = ""  # To be set by subclasses
        
    @property
    def plugin_type(self) -> str:
        return "database_repository"
    
    @contextmanager
    def get_connection(self):
        """Get database connection with optimal settings"""
        conn = sqlite3.connect(
            self.config.db_path, 
            timeout=self.config.connection_timeout
        )
        conn.row_factory = sqlite3.Row  # Dict-like access
        
        try:
            # Optimize SQLite settings
            if self.config.enable_wal_mode:
                conn.execute("PRAGMA journal_mode=WAL")
            if self.config.auto_vacuum:
                conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
            if self.config.cache_size:
                conn.execute(f"PRAGMA cache_size={self.config.cache_size}")
            if self.config.foreign_keys:
                conn.execute("PRAGMA foreign_keys=ON")
                
            yield conn
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error in {self.name}: {e}")
            raise
        finally:
            conn.close()
    
    @abstractmethod
    async def create_table(self) -> bool:
        """Create the table for this repository"""
        pass
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> Optional[int]:
        """Save data to the repository"""
        pass
    
    @abstractmethod
    async def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find data in the repository"""
        pass
    
    @abstractmethod
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single record in the repository"""
        pass
    
    @abstractmethod
    async def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """Update a record in the repository"""
        pass
    
    @abstractmethod
    async def delete(self, record_id: int) -> bool:
        """Delete a record from the repository"""
        pass
    
    async def _execute(self, data: Dict[str, Any]) -> Any:
        """
        Universal execute method - handles different database operations
        """
        operation = data.get('operation', 'find')
        
        try:
            if operation == 'save':
                result = await self.save(data.get('data', {}))
                return {
                    'success': True,
                    'operation': 'save',
                    'record_id': result,
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'find':
                query = data.get('query', {})
                results = await self.find(query)
                return {
                    'success': True,
                    'operation': 'find',
                    'data': results,
                    'count': len(results),
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'find_one':
                query = data.get('query', {})
                result = await self.find_one(query)
                return {
                    'success': True,
                    'operation': 'find_one',
                    'data': result,
                    'found': result is not None,
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'update':
                record_id = data.get('record_id')
                update_data = data.get('data', {})
                success = await self.update(record_id, update_data)
                return {
                    'success': success,
                    'operation': 'update',
                    'record_id': record_id,
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'delete':
                record_id = data.get('record_id')
                success = await self.delete(record_id)
                return {
                    'success': success,
                    'operation': 'delete',
                    'record_id': record_id,
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif operation == 'create_table':
                success = await self.create_table()
                return {
                    'success': success,
                    'operation': 'create_table',
                    'table': self.table_name,
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                return {
                    'success': False,
                    'error': f"Unknown operation: {operation}",
                    'repository': self.name,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'operation': operation,
                'repository': self.name,
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources - base implementation"""
        self.logger.info(f"{self.name} repository cleaned up")
        
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        import os
        db_dir = os.path.dirname(self.config.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            self.logger.info(f"Created database directory: {db_dir}")


class BaseRepository(DatabasePlugin):
    """
    Base repository with common CRUD operations implementation.
    
    Provides default implementations that can be overridden by specific repositories.
    """
    
    def __init__(self, config: DatabaseConfig, table_name: str):
        super().__init__(config)
        self.table_name = table_name
        
    async def _initialize(self) -> bool:
        """Initialize the repository"""
        try:
            self._ensure_db_directory()
            await self.create_table()
            self.logger.info(f"Repository {self.name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize repository {self.name}: {e}")
            return False
    
    async def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Find a record by ID"""
        return await self.find_one({'id': record_id})
    
    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if query:
                    where_clause, params = self._build_where_clause(query)
                    sql = f"SELECT COUNT(*) FROM {self.table_name} WHERE {where_clause}"
                    cursor.execute(sql, params)
                else:
                    sql = f"SELECT COUNT(*) FROM {self.table_name}"
                    cursor.execute(sql)
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"Error counting records in {self.table_name}: {e}")
            return 0
    
    def _build_where_clause(self, query: Dict[str, Any]) -> tuple:
        """Build WHERE clause and parameters from query dict"""
        conditions = []
        params = []
        
        for key, value in query.items():
            if isinstance(value, list):
                placeholders = ','.join(['?' for _ in value])
                conditions.append(f"{key} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, dict):
                # Support for operators like {'price': {'>=': 100}}
                for op, val in value.items():
                    conditions.append(f"{key} {op} ?")
                    params.append(val)
            else:
                conditions.append(f"{key} = ?")
                params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
    
    def _dict_to_insert(self, data: Dict[str, Any]) -> tuple:
        """Convert dict to INSERT clause"""
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        values = list(data.values())
        
        columns_str = ', '.join(columns)
        placeholders_str = ', '.join(placeholders)
        
        return columns_str, placeholders_str, values