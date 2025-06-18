"""
Database Manager - Central manager following Universal Plugin Pattern
"""

import asyncio
from typing import Dict, Any, Optional, List, Type
from datetime import datetime

from ..core.manager import UniversalManager
from ..core.base import ModuleConfig
from .base import DatabasePlugin, DatabaseConfig
from .repositories import (
    PriceRepository,
    ArbitrageRepository, 
    PerformanceRepository,
    BotStatisticsRepository,
    TelegramRepository,
    PortfolioRepository
)


class DatabaseManager(UniversalManager):
    """Central database manager following Universal Plugin Pattern"""
    
    def __init__(self, config: Optional[ModuleConfig] = None):
        super().__init__("database", None)
        
        # Repository registry
        self._repositories: Dict[str, DatabasePlugin] = {}
        
        # Repository type mapping
        self._repository_types: Dict[str, Type[DatabasePlugin]] = {
            'price': PriceRepository,
            'arbitrage': ArbitrageRepository,
            'performance': PerformanceRepository,
            'bot_statistics': BotStatisticsRepository,
            'telegram': TelegramRepository,
            'portfolio': PortfolioRepository
        }
        
        # Default database configuration
        config = config or ModuleConfig()
        custom_settings = getattr(config, 'custom_settings', {})
        
        self._db_config = DatabaseConfig(
            db_path=custom_settings.get('database_path', 'trading_bot.db'),
            connection_timeout=custom_settings.get('database_timeout', 30.0),
            enable_wal_mode=True,
            foreign_keys=True,
            cache_size=2000
        )
    
    async def initialize(self) -> bool:
        """Initialize database manager and create tables"""
        if self.is_initialized:
            self.logger.debug("Database manager already initialized")
            return True
            
        try:
            self.logger.info("Initializing database manager...")
            
            # Initialize all repositories
            for repo_name, repo_class in self._repository_types.items():
                try:
                    repo = repo_class(self._db_config)
                    await repo._initialize()
                    
                    # Create table for this repository
                    table_created = await repo.create_table()
                    if not table_created:
                        self.logger.warning(f"Failed to create table for {repo_name} repository")
                    
                    self._repositories[repo_name] = repo
                    self.logger.debug(f"Initialized {repo_name} repository")
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize {repo_name} repository: {e}")
                    return False
            
            self.is_initialized = True
            self.initialized_at = datetime.now()
            self.logger.info(f"Database manager initialized with {len(self._repositories)} repositories")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {e}")
            return False
    
    async def _execute(self, operation: str, **kwargs) -> Any:
        """Execute database operations"""
        try:
            if operation == "save":
                repo_name = kwargs.get('repository')
                data = kwargs.get('data')
                
                if not repo_name or not data:
                    raise ValueError("Repository name and data required for save operation")
                
                repo = self._repositories.get(repo_name)
                if not repo:
                    raise ValueError(f"Repository '{repo_name}' not found")
                
                return await repo.save(data)
            
            elif operation == "find":
                repo_name = kwargs.get('repository')
                query = kwargs.get('query', {})
                
                if not repo_name:
                    raise ValueError("Repository name required for find operation")
                
                repo = self._repositories.get(repo_name)
                if not repo:
                    raise ValueError(f"Repository '{repo_name}' not found")
                
                return await repo.find(query)
            
            elif operation == "update":
                repo_name = kwargs.get('repository')
                record_id = kwargs.get('record_id')
                data = kwargs.get('data')
                
                if not repo_name or record_id is None or not data:
                    raise ValueError("Repository name, record_id and data required for update operation")
                
                repo = self._repositories.get(repo_name)
                if not repo:
                    raise ValueError(f"Repository '{repo_name}' not found")
                
                return await repo.update(record_id, data)
            
            elif operation == "delete":
                repo_name = kwargs.get('repository')
                record_id = kwargs.get('record_id')
                
                if not repo_name or record_id is None:
                    raise ValueError("Repository name and record_id required for delete operation")
                
                repo = self._repositories.get(repo_name)
                if not repo:
                    raise ValueError(f"Repository '{repo_name}' not found")
                
                return await repo.delete(record_id)
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            self.logger.error(f"Database operation '{operation}' failed: {e}")
            return None
    
    # Repository Access Methods
    
    def get_repository(self, repo_name: str) -> Optional[DatabasePlugin]:
        """Get a specific repository by name"""
        return self._repositories.get(repo_name)
    
    @property
    def price(self) -> Optional[PriceRepository]:
        """Get price repository"""
        return self._repositories.get('price')
    
    @property
    def arbitrage(self) -> Optional[ArbitrageRepository]:
        """Get arbitrage repository"""
        return self._repositories.get('arbitrage')
    
    @property
    def performance(self) -> Optional[PerformanceRepository]:
        """Get performance repository"""
        return self._repositories.get('performance')
    
    @property
    def bot_statistics(self) -> Optional[BotStatisticsRepository]:
        """Get bot statistics repository"""
        return self._repositories.get('bot_statistics')
    
    @property
    def telegram(self) -> Optional[TelegramRepository]:
        """Get telegram repository"""
        return self._repositories.get('telegram')
    
    @property
    def portfolio(self) -> Optional[PortfolioRepository]:
        """Get portfolio repository"""
        return self._repositories.get('portfolio')
    
    # High-level convenience methods
    
    async def save_price_data(self, symbol: str, exchange: str, price: float, **kwargs) -> Optional[int]:
        """Save price data with convenience method"""
        price_data = {
            'symbol': symbol,
            'exchange': exchange,
            'price': price,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        return await self._execute('save', repository='price', data=price_data)
    
    async def save_arbitrage_alert(
        self, 
        symbol: str, 
        buy_exchange: str, 
        sell_exchange: str,
        buy_price: float,
        sell_price: float,
        **kwargs
    ) -> Optional[int]:
        """Save arbitrage alert with convenience method"""
        profit_percentage = ((sell_price - buy_price) / buy_price) * 100
        profit_amount = sell_price - buy_price
        
        alert_data = {
            'symbol': symbol,
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit_percentage': profit_percentage,
            'profit_amount': profit_amount,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        return await self._execute('save', repository='arbitrage', data=alert_data)
    
    async def save_performance_data(self, symbol: str, metrics: Dict[str, Any]) -> Optional[int]:
        """Save performance analysis data with convenience method"""
        perf_data = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat(),
            **metrics
        }
        
        return await self._execute('save', repository='performance', data=perf_data)
    
    async def log_telegram_message(
        self, 
        chat_id: str, 
        message_text: str, 
        success: bool = True,
        **kwargs
    ) -> Optional[int]:
        """Log telegram message with convenience method"""
        msg_data = {
            'chat_id': chat_id,
            'message_text': message_text,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        return await self._execute('save', repository='telegram', data=msg_data)
    
    async def start_bot_session(self) -> Optional[int]:
        """Start a new bot session"""
        if self.bot_statistics:
            return await self.bot_statistics.start_new_session()
        return None
    
    async def end_bot_session(self) -> bool:
        """End the current bot session"""
        if self.bot_statistics:
            return await self.bot_statistics.end_current_session()
        return False
    
    async def increment_bot_counter(self, counter_name: str, increment: int = 1) -> bool:
        """Increment a bot statistics counter"""
        if self.bot_statistics:
            return await self.bot_statistics.increment_counter(counter_name, increment)
        return False
    
    async def save_portfolio_snapshot(
        self, 
        top_performers: List[Dict], 
        total_coins: int,
        avg_sharpe: float,
        best_performer: Dict[str, Any]
    ) -> Optional[int]:
        """Save portfolio analysis snapshot"""
        if self.portfolio:
            return await self.portfolio.save_performance_snapshot(
                top_performers, total_coins, avg_sharpe, best_performer
            )
        return None
    
    # Data cleanup methods
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data across all repositories"""
        cleanup_results = {}
        
        cleanup_tasks = []
        for repo_name, repo in self._repositories.items():
            if hasattr(repo, 'cleanup_old_data'):
                task = asyncio.create_task(repo.cleanup_old_data(days))
                cleanup_tasks.append((repo_name, task))
        
        # Wait for all cleanup tasks to complete
        for repo_name, task in cleanup_tasks:
            try:
                deleted_count = await task
                cleanup_results[repo_name] = deleted_count
            except Exception as e:
                self.logger.error(f"Failed to cleanup {repo_name} data: {e}")
                cleanup_results[repo_name] = 0
        
        total_deleted = sum(cleanup_results.values())
        self.logger.info(f"Cleanup completed: {total_deleted} total records deleted")
        
        return cleanup_results
    
    # Health and status methods
    
    async def get_database_status(self) -> Dict[str, Any]:
        """Get overall database status"""
        status = {
            'initialized': self._initialized,
            'repositories': {}
        }
        
        for repo_name, repo in self._repositories.items():
            try:
                # Test repository with a simple query
                test_result = await repo.find({'id': -1})  # Should return empty list
                status['repositories'][repo_name] = {
                    'status': 'healthy',
                    'table_exists': isinstance(test_result, list)
                }
            except Exception as e:
                status['repositories'][repo_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return status
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of data across all repositories"""
        summary = {}
        
        for repo_name, repo in self._repositories.items():
            try:
                # Get count of records
                all_records = await repo.find({})
                summary[repo_name] = {
                    'total_records': len(all_records),
                    'latest_record': all_records[0] if all_records else None
                }
            except Exception as e:
                summary[repo_name] = {
                    'total_records': 0,
                    'error': str(e)
                }
        
        return summary


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    
    return _db_manager


async def cleanup_database_manager():
    """Clean up the global database manager"""
    global _db_manager
    
    if _db_manager is not None:
        # Close any open connections in repositories
        for repo in _db_manager._repositories.values():
            if hasattr(repo, 'close'):
                try:
                    await repo.close()
                except:
                    pass
        
        _db_manager = None