#!/usr/bin/env python3
"""
Test Script for Enhanced Arbitrage Analyzer
"""

import asyncio
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.analyzers.plugins.enhanced_arbitrage_analyzer import EnhancedArbitrageAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def test_enhanced_arbitrage():
    """Test the Enhanced Arbitrage Analyzer"""
    print("🚀 Testing Enhanced Arbitrage Analyzer")
    print("=" * 50)
    
    # Enhanced test data with more realistic market conditions
    test_data = {
        'prices': {
            'binance': {
                'BTC': 42000.0,
                'ETH': 3000.0,
                'ADA': 0.45,
                'DOT': 6.50,
                'LINK': 12.30
            },
            'coinbase': {
                'BTC': 43100.0,  # 2.6% higher
                'ETH': 3054.0,   # 1.8% higher
                'ADA': 0.451,    # 0.2% higher (too small)
                'DOT': 6.77,     # 4.2% higher
                'LINK': 12.45    # 1.2% higher
            },
            'kraken': {
                'BTC': 42050.0,  # 0.1% higher
                'ETH': 2995.0,   # 0.2% lower
                'ADA': 0.449,    # 0.2% lower
                'DOT': 6.55,     # 0.8% higher
                'LINK': 12.28    # 0.2% lower
            }
        },
        'volumes': {
            'binance': {
                'BTC': 150000000,  # High volume
                'ETH': 80000000,
                'ADA': 12000000,
                'DOT': 15000000,
                'LINK': 8000000
            },
            'coinbase': {
                'BTC': 85000000,   # Medium volume
                'ETH': 45000000,
                'ADA': 3000000,    # Low volume
                'DOT': 8000000,
                'LINK': 4000000
            },
            'kraken': {
                'BTC': 60000000,   # Medium volume
                'ETH': 30000000,
                'ADA': 2000000,    # Low volume
                'DOT': 5000000,
                'LINK': 3000000
            }
        },
        'symbols': ['BTC', 'ETH', 'ADA', 'DOT', 'LINK'],
        'market_conditions': {
            'volatility_level': 'normal',
            'trend': 'neutral',
            'volume_level': 'high'
        }
    }
    
    try:
        # Create enhanced arbitrage analyzer
        config = {
            'min_profit_threshold': 1.0,      # 1% minimum profit
            'min_volume_usd': 1000,           # $1000 minimum volume
            'max_execution_time_seconds': 300, # 5 minutes max
            'slippage_tolerance': 0.5         # 0.5% slippage tolerance
        }
        
        print("📊 Creating Enhanced Arbitrage Analyzer...")
        analyzer = EnhancedArbitrageAnalyzer(config)
        
        print("✅ Analyzer created successfully")
        print(f"📋 Configuration: Min profit {config['min_profit_threshold']}%, Min volume ${config['min_volume_usd']}")
        
        # Perform analysis
        print("\n🔍 Starting enhanced arbitrage analysis...")
        print(f"📈 Analyzing {len(test_data['symbols'])} symbols across {len(test_data['prices'])} exchanges")
        
        # Show input data summary
        print("\n📊 Input Market Data:")
        for symbol in test_data['symbols']:
            prices = []
            for exchange in test_data['prices']:
                if symbol in test_data['prices'][exchange]:
                    price = test_data['prices'][exchange][symbol]
                    prices.append(f"{exchange}: ${price:.2f}")
            print(f"  • {symbol}: {' | '.join(prices)}")
        
        # Execute analysis
        results = await analyzer.analyze(test_data)
        
        print("\n🎯 Enhanced Analysis Results:")
        print("=" * 40)
        
        # Analysis summary
        summary = results.get('analysis_summary', {})
        opportunities = results.get('opportunities', [])
        
        print(f"📊 Analysis Summary:")
        print(f"  • Symbols analyzed: {summary.get('total_symbols_analyzed', 0)}")
        print(f"  • Raw opportunities: {summary.get('raw_opportunities_found', 0)}")
        print(f"  • High-quality opportunities: {summary.get('high_quality_opportunities', 0)}")
        print(f"  • Best execution score: {summary.get('best_execution_score', 0):.3f}")
        
        # Market conditions
        market_conditions = summary.get('market_conditions', {})
        if market_conditions:
            print(f"\n🌍 Market Conditions:")
            print(f"  • Overall volatility: {market_conditions.get('overall_volatility', 'unknown')}")
            print(f"  • Arbitrage environment: {market_conditions.get('arbitrage_environment', 'unknown')}")
            print(f"  • Execution difficulty: {market_conditions.get('execution_difficulty', 'unknown')}")
        
        # Detailed opportunities
        if opportunities:
            print(f"\n💎 High-Quality Arbitrage Opportunities:")
            print("-" * 60)
            
            for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
                symbol = opp['symbol']
                profit_gross = opp['profit_percentage']
                profit_net = opp.get('net_profit_percentage', profit_gross)
                execution_score = opp.get('execution_score', 0)
                buy_exchange = opp['buy_exchange']
                sell_exchange = opp['sell_exchange']
                
                print(f"\n{i}. **{symbol}** - Score: {execution_score:.3f}/1.0")
                print(f"   📈 Route: {buy_exchange} → {sell_exchange}")
                print(f"   💰 Gross Profit: {profit_gross:.2f}%")
                print(f"   💸 Net Profit: {profit_net:.2f}% (after costs)")
                
                # Execution details
                execution_costs = opp.get('execution_costs', {})
                if execution_costs:
                    total_cost = execution_costs.get('total_cost_pct', 0)
                    execution_time = execution_costs.get('estimated_time_minutes', 0)
                    print(f"   ⚡ Execution Cost: {total_cost:.2f}%")
                    print(f"   ⏱️  Estimated Time: {execution_time:.1f} minutes")
                
                # Risk assessment
                liquidity_score = opp.get('liquidity_score', 0)
                risk_score = opp.get('risk_score', 0)
                recommended_amount = opp.get('recommended_amount_usd', 0)
                
                print(f"   📊 Liquidity Score: {liquidity_score:.2f}/1.0")
                print(f"   🛡️  Risk Score: {risk_score:.2f}/1.0")
                print(f"   💼 Recommended Amount: ${recommended_amount:,.0f}")
                
                # Feasibility
                feasible = opp.get('execution_feasible', False)
                success_prob = opp.get('success_probability', 0)
                print(f"   ✅ Execution Feasible: {'Yes' if feasible else 'No'}")
                print(f"   🎯 Success Probability: {success_prob:.1%}")
        
        # Execution guidance
        guidance = results.get('execution_guidance', {})
        if guidance and not guidance.get('error'):
            print(f"\n🎯 Execution Guidance:")
            print(f"  • Strategy: {guidance.get('execution_strategy', 'unknown')}")
            print(f"  • Timing: {guidance.get('timing_recommendation', 'unknown')}")
            
            execution_steps = guidance.get('execution_steps', [])
            if execution_steps:
                print(f"  • Execution Steps:")
                for step in execution_steps:
                    print(f"    {step}")
        
        print("\n✅ Enhanced Arbitrage Analysis Completed Successfully!")
        
        # Performance summary
        if opportunities:
            avg_score = sum(opp.get('execution_score', 0) for opp in opportunities) / len(opportunities)
            best_profit = max(opp.get('net_profit_percentage', 0) for opp in opportunities)
            total_volume = sum(opp.get('recommended_amount_usd', 0) for opp in opportunities)
            
            print(f"\n📈 Performance Summary:")
            print(f"  • Average Execution Score: {avg_score:.3f}/1.0")
            print(f"  • Best Net Profit: {best_profit:.2f}%")
            print(f"  • Total Recommended Volume: ${total_volume:,.0f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run enhanced arbitrage tests"""
    success = await test_enhanced_arbitrage()
    
    if success:
        print("\n🎉 All tests passed! Enhanced Arbitrage Analyzer is ready.")
        return 0
    else:
        print("\n💥 Tests failed! Check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)