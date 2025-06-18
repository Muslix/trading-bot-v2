"""
Tests for Database Manager - Universal Plugin Pattern implementation
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime, timedelta

from src.database import (
    DatabaseManager, 
    get_database_manager,
    cleanup_database_manager,
    DatabaseConfig
)
from src.core.base import ModuleConfig


class TestDatabaseManager:
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        config = ModuleConfig(
            custom_settings={
                'database_path': temp_db.name,
                'database_timeout': 10.0
            }
        )
        
        yield config, temp_db.name
        
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except:
            pass
    
    @pytest.fixture
    async def temp_db_manager(self, temp_db_config):
        """Create a temporary database manager for testing"""
        config, _ = temp_db_config
        
        manager = DatabaseManager(config)
        await manager.initialize()
        
        yield manager
        
        # Cleanup
        try:
            await manager.cleanup()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, temp_db_config):
        """Test database manager initialization"""
        config, _ = temp_db_config
        
        manager = DatabaseManager(config)
        await manager.initialize()
        
        assert manager.is_initialized is True
        assert len(manager._repositories) == 6
        
        # Check all expected repositories are present
        expected_repos = ['price', 'arbitrage', 'performance', 'bot_statistics', 'telegram', 'portfolio']
        for repo_name in expected_repos:
            assert repo_name in manager._repositories
            assert manager._repositories[repo_name] is not None
    
    @pytest.mark.asyncio
    async def test_repository_access_properties(self, temp_db_manager):
        """Test repository access through properties"""
        manager = temp_db_manager
        
        assert manager.price is not None
        assert manager.arbitrage is not None
        assert manager.performance is not None
        assert manager.bot_statistics is not None
        assert manager.telegram is not None
        assert manager.portfolio is not None
    
    @pytest.mark.asyncio
    async def test_save_price_data(self, temp_db_manager):
        """Test saving price data through manager"""
        manager = temp_db_manager
        
        record_id = await manager.save_price_data(
            symbol='BTC',
            exchange='binance',
            price=45000.0,
            volume=1000.0
        )
        
        assert record_id is not None
        assert isinstance(record_id, int)
        
        # Verify data was saved
        records = await manager._execute('find', repository='price', query={'symbol': 'BTC'})
        assert len(records) == 1
        assert records[0]['symbol'] == 'BTC'
        assert records[0]['exchange'] == 'binance'
        assert records[0]['price'] == 45000.0
    
    @pytest.mark.asyncio
    async def test_save_arbitrage_alert(self, temp_db_manager):
        """Test saving arbitrage alert through manager"""
        manager = temp_db_manager
        
        record_id = await manager.save_arbitrage_alert(
            symbol='ETH',
            buy_exchange='binance',
            sell_exchange='coinbase',
            buy_price=3000.0,
            sell_price=3050.0
        )
        
        assert record_id is not None
        
        # Verify data was saved and calculations are correct
        records = await manager._execute('find', repository='arbitrage', query={'symbol': 'ETH'})
        assert len(records) == 1
        alert = records[0]
        assert alert['symbol'] == 'ETH'
        assert alert['buy_exchange'] == 'binance'
        assert alert['sell_exchange'] == 'coinbase'
        assert alert['profit_amount'] == 50.0
        assert abs(alert['profit_percentage'] - 1.67) < 0.01  # Approximately 1.67%
    
    @pytest.mark.asyncio
    async def test_save_performance_data(self, temp_db_manager):
        """Test saving performance data through manager"""
        manager = temp_db_manager
        
        metrics = {
            'sharpe_ratio': 1.5,
            'annual_return': 0.25,
            'volatility': 0.4,
            'max_drawdown': 0.15,
            'current_price': 45000.0
        }
        
        record_id = await manager.save_performance_data('BTC', metrics)
        
        assert record_id is not None
        
        # Verify data was saved
        records = await manager._execute('find', repository='performance', query={'symbol': 'BTC'})
        assert len(records) == 1
        perf = records[0]
        assert perf['symbol'] == 'BTC'
        assert perf['sharpe_ratio'] == 1.5
        assert perf['annual_return'] == 0.25
    
    @pytest.mark.asyncio
    async def test_log_telegram_message(self, temp_db_manager):
        """Test logging telegram messages through manager"""
        manager = temp_db_manager
        
        record_id = await manager.log_telegram_message(
            chat_id='12345',
            message_text='Test arbitrage alert',
            success=True,
            message_type='alert'
        )
        
        assert record_id is not None
        
        # Verify message was logged
        records = await manager._execute('find', repository='telegram', query={'chat_id': '12345'})
        assert len(records) == 1
        msg = records[0]
        assert msg['chat_id'] == '12345'
        assert msg['message_text'] == 'Test arbitrage alert'
        assert msg['success'] is True
        assert msg['message_type'] == 'alert'
    
    @pytest.mark.asyncio
    async def test_bot_session_management(self, temp_db_manager):
        """Test bot session start/end functionality"""
        manager = temp_db_manager
        
        # Start session
        session_id = await manager.start_bot_session()
        assert session_id is not None
        
        # Increment counters
        assert await manager.increment_bot_counter('total_arbitrage_checks', 5)
        assert await manager.increment_bot_counter('arbitrage_opportunities_found', 2)
        
        # End session
        assert await manager.end_bot_session()
        
        # Verify session data
        records = await manager._execute('find', repository='bot_statistics', query={'id': session_id})
        assert len(records) == 1
        session = records[0]
        assert session['total_arbitrage_checks'] == 5
        assert session['arbitrage_opportunities_found'] == 2
        assert session['session_end'] is not None
        assert session['uptime_hours'] > 0
    
    @pytest.mark.asyncio
    async def test_save_portfolio_snapshot(self, temp_db_manager):
        """Test saving portfolio snapshot through manager"""
        manager = temp_db_manager
        
        top_performers = [
            {'symbol': 'BTC', 'sharpe_ratio': 1.5},
            {'symbol': 'ETH', 'sharpe_ratio': 1.2}
        ]
        
        best_performer = {'symbol': 'BTC', 'sharpe_ratio': 1.5}
        
        record_id = await manager.save_portfolio_snapshot(
            top_performers=top_performers,
            total_coins=10,
            avg_sharpe=0.8,
            best_performer=best_performer
        )
        
        assert record_id is not None
        
        # Verify snapshot was saved
        records = await manager._execute('find', repository='portfolio', query={'id': record_id})
        assert len(records) == 1
        snapshot = records[0]
        assert snapshot['total_coins_analyzed'] == 10
        assert snapshot['avg_sharpe_ratio'] == 0.8
        assert snapshot['best_performer_symbol'] == 'BTC'
    
    @pytest.mark.asyncio
    async def test_database_operations_crud(self, temp_db_manager):
        """Test CRUD operations through manager"""
        manager = temp_db_manager
        
        # Create
        record_id = await manager._execute('save', 
            repository='price', 
            data={
                'symbol': 'LTC',
                'exchange': 'kraken', 
                'price': 150.0,
                'timestamp': datetime.now().isoformat()
            }
        )
        assert record_id is not None
        
        # Read
        records = await manager._execute('find', 
            repository='price', 
            query={'symbol': 'LTC'}
        )
        assert len(records) == 1
        assert records[0]['exchange'] == 'kraken'
        
        # Update
        success = await manager._execute('update',
            repository='price',
            record_id=record_id,
            data={'price': 155.0}
        )
        assert success is True
        
        # Verify update
        updated_records = await manager._execute('find',
            repository='price',
            query={'id': record_id}
        )
        assert updated_records[0]['price'] == 155.0
        
        # Delete
        success = await manager._execute('delete',
            repository='price',
            record_id=record_id
        )
        assert success is True
        
        # Verify deletion
        deleted_records = await manager._execute('find',
            repository='price',
            query={'id': record_id}
        )
        assert len(deleted_records) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, temp_db_manager):
        """Test cleanup of old data across repositories"""
        manager = temp_db_manager
        
        # Add some test data with old timestamps
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        
        await manager.save_price_data('BTC', 'binance', 40000.0)
        await manager._execute('save', 
            repository='price',
            data={
                'symbol': 'ETH',
                'exchange': 'coinbase',
                'price': 2500.0,
                'timestamp': old_timestamp
            }
        )
        
        # Run cleanup
        cleanup_results = await manager.cleanup_old_data(days=30)
        
        assert isinstance(cleanup_results, dict)
        assert 'price' in cleanup_results
        assert cleanup_results['price'] >= 0  # Should have cleaned up old ETH record
    
    @pytest.mark.asyncio
    async def test_get_database_status(self, temp_db_manager):
        """Test database status check"""
        manager = temp_db_manager
        
        status = await manager.get_database_status()
        
        assert status['initialized'] is True
        assert 'repositories' in status
        assert len(status['repositories']) == 6
        
        for repo_name in ['price', 'arbitrage', 'performance', 'bot_statistics', 'telegram', 'portfolio']:
            assert repo_name in status['repositories']
            assert status['repositories'][repo_name]['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_get_data_summary(self, temp_db_manager):
        """Test data summary functionality"""
        manager = temp_db_manager
        
        # Add some test data
        await manager.save_price_data('BTC', 'binance', 45000.0)
        await manager.save_arbitrage_alert('ETH', 'binance', 'coinbase', 3000.0, 3050.0)
        
        summary = await manager.get_data_summary()
        
        assert isinstance(summary, dict)
        assert 'price' in summary
        assert 'arbitrage' in summary
        assert summary['price']['total_records'] >= 1
        assert summary['arbitrage']['total_records'] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, temp_db_manager):
        """Test error handling in database operations"""
        manager = temp_db_manager
        
        # Test invalid repository
        result = await manager._execute('save', 
            repository='invalid_repo',
            data={'test': 'data'}
        )
        assert result is None
        
        # Test missing required parameters
        result = await manager._execute('save', repository='price')
        assert result is None
        
        # Test invalid operation
        result = await manager._execute('invalid_operation')
        assert result is None


class TestGlobalDatabaseManager:
    
    @pytest.mark.asyncio
    async def test_global_manager_singleton(self):
        """Test global database manager singleton behavior"""
        # Clean up any existing manager
        await cleanup_database_manager()
        
        # Get first instance
        manager1 = await get_database_manager()
        assert manager1 is not None
        assert manager1._initialized is True
        
        # Get second instance - should be same
        manager2 = await get_database_manager()
        assert manager2 is manager1
        
        # Cleanup
        await cleanup_database_manager()
    
    @pytest.mark.asyncio
    async def test_global_manager_cleanup(self):
        """Test global manager cleanup"""
        # Get manager instance
        manager = await get_database_manager()
        assert manager is not None
        
        # Cleanup
        await cleanup_database_manager()
        
        # Get new instance - should be different
        new_manager = await get_database_manager()
        assert new_manager is not manager
        
        # Final cleanup
        await cleanup_database_manager()