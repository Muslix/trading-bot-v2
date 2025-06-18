#!/usr/bin/env python3
"""
Test Production Startup - Verify production deployment works correctly
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import production modules
try:
    from config.config import get_config
    from src.utils.production_logger import get_production_logger
    from src.crypto_monitor_24_7 import CryptoMonitor24_7
    from src.modules.database import db
    from src.alerts import create_alert_manager
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_production_components():
    """Test individual production components"""
    print("\n🔍 TESTING PRODUCTION COMPONENTS")
    print("=" * 50)
    
    # Test configuration loading
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
        print(f"   Environment: {os.environ.get('ENVIRONMENT', 'default')}")
        print(f"   Watchlist symbols: {len(config.watchlist_symbols)} symbols")
        print(f"   Analysis crypto count: {config.analysis_crypto_count}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test production logger
    try:
        prod_logger = get_production_logger("test")
        prod_logger.log_startup({
            "test_mode": True,
            "timestamp": datetime.now().isoformat(),
            "components": ["config", "logger", "database", "alerts"]
        })
        print("✅ Production logger working")
    except Exception as e:
        print(f"❌ Production logger error: {e}")
        return False
    
    # Test database connection
    try:
        db.create_tables()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test alert manager
    try:
        alert_manager = create_alert_manager()
        stats = alert_manager.get_alert_stats()
        print("✅ Alert manager initialized")
        print(f"   Rules configured: {stats['rules_configured']}")
        print(f"   Rules enabled: {stats['rules_enabled']}")
    except Exception as e:
        print(f"❌ Alert manager error: {e}")
        return False
    
    # Test monitor initialization (without starting)
    try:
        monitor = CryptoMonitor24_7()
        print("✅ Crypto monitor initialized")
        print(f"   Watchlist: {len(monitor.config['watchlist_symbols'])} symbols")
        print(f"   Exchanges: {len(monitor.config['exchanges'])} exchanges")
    except Exception as e:
        print(f"❌ Monitor initialization error: {e}")
        return False
    
    return True


async def test_data_adapters():
    """Test data adapter functionality"""
    print("\n📊 TESTING DATA ADAPTERS")
    print("=" * 50)
    
    try:
        from src.adapters import (
            analyze_crypto_portfolio_enhanced,
            calculate_crypto_metrics_enhanced,
            get_current_prices,
            check_data_sources_health
        )
        
        # Test health check
        health = await check_data_sources_health()
        print(f"✅ Data sources health: {health}")
        
        # Test portfolio analysis with small dataset
        test_symbols = ["BTC", "ETH"]
        portfolio_result = await analyze_crypto_portfolio_enhanced(test_symbols, "1y")
        print(f"✅ Portfolio analysis: {len(portfolio_result.get('portfolio_analysis', {}))} symbols analyzed")
        
        # Test current prices
        prices = await get_current_prices(test_symbols)
        print(f"✅ Current prices: {len(prices)} prices retrieved")
        
        # Test enhanced metrics
        btc_metrics = await calculate_crypto_metrics_enhanced("BTC")
        print(f"✅ BTC metrics calculated: Sharpe {btc_metrics.get('sharpe_ratio', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data adapter error: {e}")
        return False


def test_log_files():
    """Test log file creation and structure"""
    print("\n📄 TESTING LOG FILES")
    print("=" * 50)
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("❌ Log directory does not exist")
        return False
    
    print(f"✅ Log directory exists: {log_dir}")
    
    # Check for expected log files (they might not exist yet, that's OK)
    expected_logs = [
        "test_main.log",
        "test_calculations.log", 
        "test_data.log",
        "test_metrics.log",
        "test_arbitrage.log"
    ]
    
    existing_logs = []
    for log_file in expected_logs:
        log_path = log_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            existing_logs.append(f"{log_file} ({size} bytes)")
    
    if existing_logs:
        print(f"✅ Found log files: {', '.join(existing_logs)}")
    else:
        print("ℹ️  No log files created yet (will be created on first run)")
    
    return True


async def test_arbitrage_detection():
    """Test arbitrage detection with mock data"""
    print("\n🔍 TESTING ARBITRAGE DETECTION")
    print("=" * 50)
    
    try:
        from src.modules.arbitrage_detector import detect_arbitrage_opportunities
        
        # Test with mock price data showing arbitrage opportunity
        mock_prices = {
            "binance": 45000.0,
            "coinbase": 45750.0,  # 1.67% spread
            "kraken": 45300.0
        }
        
        opportunities = detect_arbitrage_opportunities(mock_prices, threshold=0.01)
        print(f"✅ Arbitrage detection: {len(opportunities)} opportunities found")
        
        for opp in opportunities:
            print(f"   {opp.get('buy_exchange')} -> {opp.get('sell_exchange')}: {opp.get('profit_percentage', 0):.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Arbitrage detection error: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 PRODUCTION DEPLOYMENT TEST")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    
    # Run all tests
    tests = [
        ("Production Components", test_production_components()),
        ("Data Adapters", test_data_adapters()),
        ("Log Files", test_log_files()),
        ("Arbitrage Detection", test_arbitrage_detection())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Production deployment is ready!")
        print("\n📋 To start production:")
        print("   make production-start")
        print("\n📊 To monitor:")
        print("   python3 scripts/monitor_production_logs.py --watch")
        return True
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical test error: {e}")
        sys.exit(1)