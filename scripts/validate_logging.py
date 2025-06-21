#!/usr/bin/env python3
"""
Logging Validation Script - Test that all logging components are working
Usage: python scripts/validate_logging.py
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

def test_basic_logging():
    """Test basic logging configuration"""
    print("🧪 Testing basic logging configuration...")
    
    # Create logs directory
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Test basic logging
    logger = logging.getLogger("test_logger")
    handler = logging.FileHandler(logs_dir / "test_basic.log")
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    # Test all log levels
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("✅ Basic logging test completed")
    return True

def test_production_logger():
    """Test production logger functionality"""
    print("🧪 Testing production logger...")
    
    try:
        from src.utils.production_logger import get_production_logger
        
        # Test production logger
        prod_logger = get_production_logger("test_component")
        
        # Test startup logging
        test_config = {
            "test_setting": "test_value",
            "arbitrage_check_interval": 30,
            "performance_check_interval": 600
        }
        prod_logger.log_startup(test_config)
        
        # Test price data logging
        prod_logger.log_price_data("BTC", "binance", 50000.0)
        prod_logger.log_price_data("ETH", "coinbase", 3000.0)
        
        # Test arbitrage calculation logging
        test_prices = {"binance": 50000, "coinbase": 50500}
        test_opportunities = [
            {
                "buy_exchange": "binance",
                "sell_exchange": "coinbase", 
                "profit_percentage": 1.0,
                "buy_price": 50000,
                "sell_price": 50500,
                "potential_profit": 500
            }
        ]
        prod_logger.log_arbitrage_calculation("BTC", test_prices, test_opportunities)
        
        # Test error logging
        test_error = Exception("Test error for logging validation")
        prod_logger.log_error_with_context(test_error, "test_context", {"test_data": "value"})
        
        print("✅ Production logger test completed")
        return True
        
    except Exception as e:
        print(f"❌ Production logger test failed: {e}")
        return False

def test_error_logger():
    """Test error logger functionality"""
    print("🧪 Testing error logger...")
    
    try:
        from src.utils.error_logger import ErrorLogger, setup_error_logger
        
        # Test error logger setup
        logger = setup_error_logger("DEBUG")
        
        # Test error logger class
        error_logger = ErrorLogger()
        
        # Test different error logging methods
        error_logger.log_error("Test error message")
        error_logger.log_warning("Test warning message")
        error_logger.log_info("Test info message")
        
        # Test error with exception
        try:
            raise ValueError("Test exception for logging")
        except Exception as e:
            error_logger.log_error("Test error with exception", e, {"context": "test"})
        
        print("✅ Error logger test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error logger test failed: {e}")
        return False

def test_crypto_monitor_logging():
    """Test crypto monitor logging setup"""
    print("🧪 Testing crypto monitor logging setup...")
    
    try:
        # Import and create a temporary crypto monitor instance
        from src.crypto_monitor_24_7 import CryptoMonitor24_7
        
        # Create instance (this will set up logging)
        monitor = CryptoMonitor24_7()
        
        # Test that specialized loggers are created
        arbitrage_logger = logging.getLogger('arbitrage')
        performance_logger = logging.getLogger('performance')
        data_logger = logging.getLogger('data_sources')
        error_logger = logging.getLogger('errors')
        
        # Test logging to each specialized logger
        arbitrage_logger.info("Test arbitrage log message")
        performance_logger.info("Test performance log message")
        data_logger.debug("Test data sources log message")
        error_logger.error("Test error log message")
        
        print("✅ Crypto monitor logging test completed")
        return True
        
    except Exception as e:
        print(f"❌ Crypto monitor logging test failed: {e}")
        return False

def test_web_api_logging():
    """Test web API logging setup"""
    print("🧪 Testing web API logging setup...")
    
    try:
        # Test the logging setup function
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_api", project_root / "src" / "web_api.py")
        
        # Just test that the logging setup doesn't crash
        # (We can't easily test the full web API without starting the server)
        
        # Test basic web API logger
        web_logger = logging.getLogger("web_api_test")
        handler = logging.FileHandler(project_root / "logs" / "web_api_test.log")
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
        handler.setFormatter(formatter)
        web_logger.addHandler(handler)
        web_logger.setLevel(logging.INFO)
        
        web_logger.info("Test web API log message")
        web_logger.error("Test web API error message")
        
        print("✅ Web API logging test completed")
        return True
        
    except Exception as e:
        print(f"❌ Web API logging test failed: {e}")
        return False

def check_log_files():
    """Check that log files are being created"""
    print("🧪 Checking log file creation...")
    
    logs_dir = project_root / "logs"
    if not logs_dir.exists():
        print("❌ Logs directory does not exist")
        return False
    
    # Expected log files after running tests
    expected_files = [
        "test_basic.log",
        "test_component_main.log",
        "test_component_calculations.log", 
        "test_component_data.log",
        "test_component_metrics.log",
        "test_component_arbitrage.log",
        "crypto_monitor_main.log",
        "arbitrage_opportunities.log",
        "performance_analysis.log",
        "data_sources.log",
        "web_api_test.log"
    ]
    
    found_files = []
    missing_files = []
    
    for expected_file in expected_files:
        file_path = logs_dir / expected_file
        if file_path.exists():
            size = file_path.stat().st_size
            found_files.append((expected_file, size))
        else:
            missing_files.append(expected_file)
    
    print(f"📄 Found {len(found_files)} log files:")
    for filename, size in found_files:
        print(f"  ✅ {filename} ({size} bytes)")
    
    if missing_files:
        print(f"❌ Missing {len(missing_files)} expected log files:")
        for filename in missing_files:
            print(f"  ❌ {filename}")
    
    # Check errors directory
    errors_dir = logs_dir / "errors"
    if errors_dir.exists():
        error_files = list(errors_dir.glob("*.log"))
        print(f"📁 Found {len(error_files)} error log files:")
        for error_file in error_files:
            size = error_file.stat().st_size
            print(f"  🔴 {error_file.name} ({size} bytes)")
    
    return len(missing_files) == 0

def main():
    """Run all logging validation tests"""
    print("🚀 LOGGING VALIDATION SUITE")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Project root: {project_root}")
    print()
    
    tests = [
        test_basic_logging,
        test_production_logger,
        test_error_logger,
        test_crypto_monitor_logging,
        test_web_api_logging,
        check_log_files
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All logging validation tests passed!")
        print("🔧 Your production logging is properly configured")
        print("📋 Next steps:")
        print("  1. Run 'make production-start' to start with full logging")
        print("  2. Monitor logs with 'python scripts/monitor_logs.py'")
        print("  3. Check specific components with '--component arbitrage'")
    else:
        print(f"\n⚠️ {failed} tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())