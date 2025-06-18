"""
Tests for Database Repositories - Individual repository testing
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from src.database import (
    DatabaseConfig,
    PriceRepository,
    ArbitrageRepository,
    PerformanceRepository,
    BotStatisticsRepository,
    TelegramRepository,
    PortfolioRepository,
    PriceData,
    ArbitrageAlert,
    PerformanceData
)


class TestRepositories:
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        config = DatabaseConfig(
            database_path=temp_db.name,
            timeout=10.0
        )
        
        yield config
        
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except:
            pass


class TestPriceRepository(TestRepositories):
    
    @pytest.fixture
    async def price_repo(self, temp_db_config):
        """Create price repository with temporary database"""
        repo = PriceRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_save_and_find_price_data(self, price_repo):
        """Test saving and retrieving price data"""
        price_data = PriceData(
            symbol='BTC',
            exchange='binance',
            price=45000.0,
            volume=1000.0
        )
        
        # Save data
        record_id = await price_repo.save(price_data.to_dict())
        assert record_id is not None
        
        # Find data
        records = await price_repo.find({'symbol': 'BTC'})
        assert len(records) == 1
        assert records[0]['symbol'] == 'BTC'
        assert records[0]['exchange'] == 'binance'
        assert records[0]['price'] == 45000.0
    
    @pytest.mark.asyncio
    async def test_get_latest_price(self, price_repo):
        """Test getting latest price for symbol/exchange"""
        # Save multiple prices
        await price_repo.save({
            'symbol': 'ETH',
            'exchange': 'coinbase', 
            'price': 3000.0,
            'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat()
        })
        
        await price_repo.save({
            'symbol': 'ETH',
            'exchange': 'coinbase',
            'price': 3050.0,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get latest
        latest = await price_repo.get_latest_price('ETH', 'coinbase')
        assert latest is not None
        assert latest['price'] == 3050.0
    
    @pytest.mark.asyncio
    async def test_get_price_history(self, price_repo):
        """Test getting price history within time range"""
        # Save historical data
        for i, price in enumerate([40000, 41000, 42000]):
            timestamp = (datetime.now() - timedelta(hours=i+1)).isoformat()
            await price_repo.save({
                'symbol': 'BTC',
                'exchange': 'binance',
                'price': price,
                'timestamp': timestamp
            })
        
        # Get history
        history = await price_repo.get_price_history('BTC', 'binance', hours=5)
        assert len(history) == 3
        # Should be ordered by timestamp DESC
        assert history[0]['price'] == 40000  # Most recent first


class TestArbitrageRepository(TestRepositories):
    
    @pytest.fixture
    async def arbitrage_repo(self, temp_db_config):
        """Create arbitrage repository with temporary database"""
        repo = ArbitrageRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_save_arbitrage_alert(self, arbitrage_repo):
        """Test saving arbitrage alert with auto-calculations"""
        alert_data = {
            'symbol': 'ETH',
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'buy_price': 3000.0,
            'sell_price': 3060.0
        }
        
        # Save alert
        record_id = await arbitrage_repo.save(alert_data)
        assert record_id is not None
        
        # Verify calculations
        records = await arbitrage_repo.find({'symbol': 'ETH'})
        assert len(records) == 1
        alert = records[0]
        assert alert['profit_amount'] == 60.0
        assert abs(alert['profit_percentage'] - 2.0) < 0.01
    
    @pytest.mark.asyncio 
    async def test_check_recent_similar_alert(self, arbitrage_repo):
        """Test checking for recent similar alerts"""
        # Save an alert
        await arbitrage_repo.save({
            'symbol': 'BTC',
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'buy_price': 45000.0,
            'sell_price': 45500.0,
            'profit_percentage': 1.11,
            'profit_amount': 500.0
        })
        
        # Check for similar alert
        exists = await arbitrage_repo.check_recent_similar_alert(
            'BTC', 'binance', 'coinbase', profit_threshold=1.11, hours=1
        )
        assert exists is True
        
        # Check for non-similar alert
        exists = await arbitrage_repo.check_recent_similar_alert(
            'BTC', 'binance', 'coinbase', profit_threshold=5.0, hours=1
        )
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_mark_alert_sent(self, arbitrage_repo):
        """Test marking alert as sent"""
        # Save alert
        record_id = await arbitrage_repo.save({
            'symbol': 'LTC',
            'buy_exchange': 'kraken',
            'sell_exchange': 'binance',
            'buy_price': 150.0,
            'sell_price': 152.0
        })
        
        # Mark as sent
        success = await arbitrage_repo.mark_alert_sent(record_id, 'telegram_msg_123')
        assert success is True
        
        # Verify
        records = await arbitrage_repo.find({'id': record_id})
        assert records[0]['alert_sent'] is True
        assert records[0]['telegram_message_id'] == 'telegram_msg_123'


class TestPerformanceRepository(TestRepositories):
    
    @pytest.fixture
    async def performance_repo(self, temp_db_config):
        """Create performance repository with temporary database"""
        repo = PerformanceRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_save_performance_data(self, performance_repo):
        """Test saving performance analysis data"""
        perf_data = PerformanceData(
            symbol='BTC',
            sharpe_ratio=1.5,
            annual_return=0.25,
            volatility=0.4,
            max_drawdown=0.15,
            current_price=45000.0
        )
        
        record_id = await performance_repo.save(perf_data.to_dict())
        assert record_id is not None
        
        # Verify data
        records = await performance_repo.find({'symbol': 'BTC'})
        assert len(records) == 1
        assert records[0]['sharpe_ratio'] == 1.5
        assert records[0]['annual_return'] == 0.25
    
    @pytest.mark.asyncio
    async def test_get_top_performers(self, performance_repo):
        """Test getting top performing cryptocurrencies"""
        # Save multiple performance records
        symbols_data = [
            ('BTC', 1.5), ('ETH', 1.2), ('ADA', 0.8), ('DOT', 1.8)
        ]
        
        for symbol, sharpe in symbols_data:
            await performance_repo.save({
                'symbol': symbol,
                'sharpe_ratio': sharpe,
                'annual_return': 0.2,
                'volatility': 0.3,
                'max_drawdown': 0.1,
                'current_price': 1000.0
            })
        
        # Get top performers by Sharpe ratio
        top_performers = await performance_repo.get_top_performers(limit=3, metric='sharpe_ratio')
        assert len(top_performers) == 3
        # Should be ordered by Sharpe ratio DESC
        assert top_performers[0]['symbol'] == 'DOT'  # 1.8
        assert top_performers[1]['symbol'] == 'BTC'  # 1.5
        assert top_performers[2]['symbol'] == 'ETH'  # 1.2
    
    @pytest.mark.asyncio
    async def test_save_batch_performance(self, performance_repo):
        """Test batch saving performance results"""
        performance_results = {
            'BTC': {
                'sharpe_ratio': 1.5,
                'annual_return': 0.25,
                'volatility': 0.4,
                'current_price': 45000.0
            },
            'ETH': {
                'sharpe_ratio': 1.2,
                'annual_return': 0.22,
                'volatility': 0.45,
                'current_price': 3000.0
            },
            'ADA': {
                'error': 'Failed to fetch data'  # Should be skipped
            }
        }
        
        saved_count = await performance_repo.save_batch_performance(performance_results)
        assert saved_count == 2  # BTC and ETH, ADA skipped due to error
        
        # Verify data was saved
        btc_records = await performance_repo.find({'symbol': 'BTC'})
        eth_records = await performance_repo.find({'symbol': 'ETH'})
        ada_records = await performance_repo.find({'symbol': 'ADA'})
        
        assert len(btc_records) == 1
        assert len(eth_records) == 1
        assert len(ada_records) == 0  # Should be empty due to error


class TestBotStatisticsRepository(TestRepositories):
    
    @pytest.fixture
    async def bot_stats_repo(self, temp_db_config):
        """Create bot statistics repository with temporary database"""
        repo = BotStatisticsRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_session_management(self, bot_stats_repo):
        """Test bot session start/end functionality"""
        # Start session
        session_id = await bot_stats_repo.start_new_session()
        assert session_id is not None
        
        # Get current session
        current = await bot_stats_repo.get_current_session()
        assert current is not None
        assert current['id'] == session_id
        assert current['session_end'] is None
        
        # Increment counters
        assert await bot_stats_repo.increment_counter('total_arbitrage_checks', 10)
        assert await bot_stats_repo.increment_counter('arbitrage_opportunities_found', 3)
        
        # End session
        assert await bot_stats_repo.end_current_session()
        
        # Verify session ended
        updated_session = await bot_stats_repo.find_one({'id': session_id})
        assert updated_session['session_end'] is not None
        assert updated_session['uptime_hours'] > 0
        assert updated_session['total_arbitrage_checks'] == 10
        assert updated_session['arbitrage_opportunities_found'] == 3
    
    @pytest.mark.asyncio
    async def test_get_session_summary(self, bot_stats_repo):
        """Test getting session summary with rates"""
        # Create session with data
        session_id = await bot_stats_repo.start_new_session()
        await bot_stats_repo.increment_counter('total_arbitrage_checks', 100)
        await bot_stats_repo.increment_counter('arbitrage_opportunities_found', 5)
        await bot_stats_repo.increment_counter('alerts_sent', 3)
        await bot_stats_repo.end_current_session()
        
        # Get summary
        summary = await bot_stats_repo.get_session_summary(session_id)
        assert summary['session_id'] == session_id
        assert summary['total_arbitrage_checks'] == 100
        assert summary['arbitrage_opportunities_found'] == 5
        assert summary['alerts_sent'] == 3
        assert 'opportunities_found_rate' in summary
        assert 'alert_success_rate' in summary


class TestTelegramRepository(TestRepositories):
    
    @pytest.fixture
    async def telegram_repo(self, temp_db_config):
        """Create telegram repository with temporary database"""
        repo = TelegramRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_log_message_sent(self, telegram_repo):
        """Test logging successful message"""
        record_id = await telegram_repo.log_message_sent(
            chat_id='12345',
            message_text='Test alert message',
            message_type='alert',
            telegram_message_id='msg_789'
        )
        
        assert record_id is not None
        
        # Verify message
        records = await telegram_repo.find({'chat_id': '12345'})
        assert len(records) == 1
        msg = records[0]
        assert msg['success'] is True
        assert msg['message_type'] == 'alert'
        assert msg['telegram_message_id'] == 'msg_789'
    
    @pytest.mark.asyncio
    async def test_log_message_failed(self, telegram_repo):
        """Test logging failed message"""
        record_id = await telegram_repo.log_message_failed(
            chat_id='12345',
            message_text='Failed message',
            error_message='Network timeout',
            message_type='status'
        )
        
        assert record_id is not None
        
        # Verify failed message
        records = await telegram_repo.find({'chat_id': '12345'})
        assert len(records) == 1
        msg = records[0]
        assert msg['success'] is False
        assert msg['error_message'] == 'Network timeout'
    
    @pytest.mark.asyncio
    async def test_get_message_statistics(self, telegram_repo):
        """Test getting message statistics"""
        # Log multiple messages
        await telegram_repo.log_message_sent('12345', 'Alert 1', 'alert')
        await telegram_repo.log_message_sent('12345', 'Alert 2', 'alert')
        await telegram_repo.log_message_failed('12345', 'Failed', 'Error', 'alert')
        await telegram_repo.log_message_sent('67890', 'Performance', 'performance')
        
        # Get statistics
        stats = await telegram_repo.get_message_statistics(days=1)
        assert stats['total_messages'] == 4
        assert stats['successful_messages'] == 3
        assert stats['failed_messages'] == 1
        assert stats['success_rate'] == 75.0
        assert stats['unique_chats'] == 2
        assert stats['alert_messages'] == 3
        assert stats['performance_messages'] == 1


class TestPortfolioRepository(TestRepositories):
    
    @pytest.fixture
    async def portfolio_repo(self, temp_db_config):
        """Create portfolio repository with temporary database"""
        repo = PortfolioRepository(temp_db_config)
        await repo._initialize()
        await repo.create_table()
        return repo
    
    @pytest.mark.asyncio
    async def test_save_performance_snapshot(self, portfolio_repo):
        """Test saving portfolio performance snapshot"""
        top_performers = [
            {'symbol': 'BTC', 'sharpe_ratio': 1.5},
            {'symbol': 'ETH', 'sharpe_ratio': 1.2},
            {'symbol': 'ADA', 'sharpe_ratio': 0.8}
        ]
        
        best_performer = {'symbol': 'BTC', 'sharpe_ratio': 1.5}
        
        record_id = await portfolio_repo.save_performance_snapshot(
            top_performers=top_performers,
            total_coins=10,
            avg_sharpe=0.95,
            best_performer=best_performer
        )
        
        assert record_id is not None
        
        # Verify snapshot
        records = await portfolio_repo.find({'id': record_id})
        assert len(records) == 1
        snapshot = records[0]
        assert snapshot['total_coins_analyzed'] == 10
        assert snapshot['avg_sharpe_ratio'] == 0.95
        assert snapshot['best_performer_symbol'] == 'BTC'
        assert snapshot['best_performer_sharpe'] == 1.5
    
    @pytest.mark.asyncio
    async def test_get_top_performers_history(self, portfolio_repo):
        """Test getting top performers history for a symbol"""
        # Create snapshots with BTC in top performers
        top_performers_1 = [
            {'symbol': 'BTC', 'sharpe_ratio': 1.5},
            {'symbol': 'ETH', 'sharpe_ratio': 1.2}
        ]
        
        top_performers_2 = [
            {'symbol': 'ETH', 'sharpe_ratio': 1.8},
            {'symbol': 'BTC', 'sharpe_ratio': 1.3}
        ]
        
        # Save snapshots
        await portfolio_repo.save_performance_snapshot(
            top_performers_1, 5, 1.0, {'symbol': 'BTC', 'sharpe_ratio': 1.5}
        )
        
        await portfolio_repo.save_performance_snapshot(
            top_performers_2, 5, 1.2, {'symbol': 'ETH', 'sharpe_ratio': 1.8}
        )
        
        # Get BTC history
        btc_history = await portfolio_repo.get_top_performers_history('BTC', days=1)
        assert len(btc_history) == 2  # BTC appeared in both snapshots
        
        # Check if BTC was best performer in first snapshot
        first_appearance = btc_history[0]  # Most recent first
        assert first_appearance['was_best_performer'] is False  # ETH was best in second snapshot
    
    @pytest.mark.asyncio
    async def test_get_portfolio_statistics(self, portfolio_repo):
        """Test getting portfolio statistics"""
        # Create multiple snapshots
        for i, avg_sharpe in enumerate([0.8, 1.0, 1.2]):
            await portfolio_repo.save_performance_snapshot(
                [{'symbol': 'BTC', 'sharpe_ratio': avg_sharpe + 0.3}],
                total_coins=5 + i,
                avg_sharpe=avg_sharpe,
                best_performer={'symbol': 'BTC', 'sharpe_ratio': avg_sharpe + 0.3}
            )
        
        # Get statistics
        stats = await portfolio_repo.get_portfolio_statistics(days=1)
        assert stats['total_snapshots'] == 3
        assert stats['avg_coins_analyzed'] == 6.0  # (5+6+7)/3
        assert stats['overall_avg_sharpe'] == 1.0  # (0.8+1.0+1.2)/3
        assert stats['best_avg_sharpe'] == 1.2
        assert stats['worst_avg_sharpe'] == 0.8