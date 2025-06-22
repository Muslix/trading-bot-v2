#!/usr/bin/env python3
"""
Test Script for Smart Arbitrage Alert System
"""

import asyncio
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.alerts.manager import create_alert_manager
from src.alerts.plugins.smart_arbitrage_alert import SmartArbitrageAlert
from src.alerts.base import AlertConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def test_smart_arbitrage():
    """Test the Smart Arbitrage Alert system"""
    print("🚀 Testing Smart Arbitrage Alert System")
    print("=" * 50)
    
    # Test data - simulating arbitrage opportunities
    test_opportunities = [
        {
            'symbol': 'BTC',
            'profit_percentage': 2.5,
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'volume': 5000,
            'buy_price': 42000,
            'sell_price': 43050
        },
        {
            'symbol': 'ETH', 
            'profit_percentage': 1.8,
            'buy_exchange': 'kraken',
            'sell_exchange': 'binance',
            'volume': 2000,
            'buy_price': 3000,
            'sell_price': 3054
        },
        {
            'symbol': 'ADA',
            'profit_percentage': 0.5,  # Too low profit
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'volume': 500,
            'buy_price': 0.45,
            'sell_price': 0.4523
        },
        {
            'symbol': 'DOT',
            'profit_percentage': 4.2,  # High profit
            'buy_exchange': 'coinbase',
            'sell_exchange': 'kraken',
            'volume': 8000,
            'buy_price': 6.5,
            'sell_price': 6.77
        }
    ]
    
    test_data = {
        'arbitrage_opportunities': test_opportunities,
        'current_prices': {
            'BTC': 42025,
            'ETH': 3027,
            'ADA': 0.451,
            'DOT': 6.63
        },
        'volume_data': {
            'BTC': 150000000,
            'ETH': 80000000,
            'ADA': 12000000,
            'DOT': 15000000
        }
    }
    
    try:
        # Create alert manager with smart arbitrage enabled
        config = {
            'smart_arbitrage_threshold': 1.5,
            'smart_arbitrage_cooldown': 15
        }
        
        print("📊 Creating Smart Alert Manager...")
        alert_manager = await create_alert_manager(config)
        
        print("✅ Alert Manager created successfully")
        print(f"📈 Plugins initialized: {len(alert_manager.plugins)}")
        
        # Process alerts with test data
        print("\n🔍 Processing test arbitrage opportunities...")
        print(f"📋 Input opportunities: {len(test_opportunities)}")
        
        for i, opp in enumerate(test_opportunities, 1):
            print(f"  {i}. {opp['symbol']}: {opp['profit_percentage']:.2f}% "
                  f"({opp['buy_exchange']} → {opp['sell_exchange']})")
        
        # Execute alert processing
        results = await alert_manager.process_all_alerts(
            arbitrage_opportunities=test_opportunities,
            current_prices=test_data['current_prices'],
            volume_data=test_data['volume_data']
        )
        
        print("\n🎯 Alert Processing Results:")
        print(f"  • Total plugins executed: {results.get('total_plugins_executed', 0)}")
        print(f"  • Alerts triggered: {results.get('alerts_triggered', 0)}")
        print(f"  • Alerts sent: {results.get('alerts_sent', 0)}")
        print(f"  • Failed alerts: {results.get('failed_alerts', 0)}")
        
        # Show plugin-specific results
        plugin_results = results.get('plugin_results', {})
        if plugin_results:
            print("\n📊 Plugin Results:")
            for plugin_name, result in plugin_results.items():
                triggered = result.get('triggered', False)
                reason = result.get('reason', 'Unknown')
                status = "✅ TRIGGERED" if triggered else "❌ Not triggered"
                print(f"  • {plugin_name}: {status} ({reason})")
        
        # Test smart arbitrage directly
        print("\n🤖 Testing Smart Arbitrage Plugin Directly...")
        smart_plugin = alert_manager.get_plugin('smart_arbitrage')
        if smart_plugin:
            # Test intelligence scoring
            should_trigger = await smart_plugin.should_trigger(test_data)
            print(f"  • Should trigger: {should_trigger}")
            
            if should_trigger:
                alert_data = await smart_plugin.get_alert_data(test_data)
                message = await smart_plugin.format_message(alert_data)
                
                print("\n📩 Smart Alert Message:")
                print("-" * 40)
                print(message)
                print("-" * 40)
                
                # Show intelligence statistics
                if hasattr(smart_plugin, 'get_intelligence_stats'):
                    intel_stats = smart_plugin.get_intelligence_stats()
                    print("\n🧠 Intelligence Statistics:")
                    print(f"  • Market volatility: {intel_stats['market_conditions'].get('volatility_level', 'unknown')}")
                    print(f"  • Profitable pairs learned: {intel_stats['success_patterns']['profitable_pairs']}")
                    print(f"  • Reliable exchanges: {intel_stats['success_patterns']['reliable_exchanges']}")
                    print(f"  • Min profit threshold: {intel_stats['configuration']['min_profit_threshold']}%")
        else:
            print("❌ Smart arbitrage plugin not found")
        
        # Get alert statistics
        print("\n📈 Alert Manager Statistics:")
        stats = alert_manager.get_alert_stats()
        daily_stats = stats.get('daily_stats', {})
        system_stats = stats.get('system_stats', {})
        
        print(f"  • Alerts sent today: {daily_stats.get('alerts_sent_today', 0)}")
        print(f"  • Total alerts sent: {daily_stats.get('total_alerts_sent', 0)}")
        print(f"  • Total plugins: {system_stats.get('total_plugins', 0)}")
        print(f"  • Enabled plugins: {system_stats.get('enabled_plugins', 0)}")
        print(f"  • Telegram enabled: {system_stats.get('telegram_enabled', False)}")
        
        print("\n✅ Smart Arbitrage Alert Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run smart alert tests"""
    success = await test_smart_arbitrage()
    
    if success:
        print("\n🎉 All tests passed! Smart Arbitrage Alert system is ready.")
        return 0
    else:
        print("\n💥 Tests failed! Check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)