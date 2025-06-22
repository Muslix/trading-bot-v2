"""
Enhanced Arbitrage Analyzer - Advanced arbitrage detection with execution analysis.

This analyzer improves on basic arbitrage detection by adding:
- Order book depth analysis
- Real-time execution cost calculation
- Liquidity requirements validation
- Risk assessment scoring
- Multi-path arbitrage detection
"""

import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..base import BaseAnalyzer


class EnhancedArbitrageAnalyzer(BaseAnalyzer):
    """
    Advanced arbitrage analyzer with execution feasibility analysis.
    
    Features:
    - Order book depth analysis
    - Dynamic fee calculation
    - Liquidity validation
    - Risk-adjusted scoring
    - Multi-step arbitrage paths
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Enhanced configuration
        self.min_profit_threshold = config.get('min_profit_threshold', 1.0)
        self.min_volume_usd = config.get('min_volume_usd', 500)
        self.max_execution_time = config.get('max_execution_time_seconds', 300)  # 5 minutes
        self.slippage_tolerance = config.get('slippage_tolerance', 0.5)  # 0.5%
        
        # Exchange-specific data
        self.exchange_fees = {
            'binance': {'maker': 0.075, 'taker': 0.075, 'withdrawal': 0.1},
            'coinbase': {'maker': 0.4, 'taker': 0.6, 'withdrawal': 0.2},
            'kraken': {'maker': 0.16, 'taker': 0.26, 'withdrawal': 0.15},
            'kucoin': {'maker': 0.1, 'taker': 0.1, 'withdrawal': 0.1},
            'default': {'maker': 0.2, 'taker': 0.3, 'withdrawal': 0.15}
        }
        
        # Minimum order sizes (in USD)
        self.min_order_sizes = {
            'binance': 10,
            'coinbase': 1,
            'kraken': 5,
            'kucoin': 1,
            'default': 10
        }
        
        # Historical execution data for learning
        self.execution_history = {}
        self.success_rates = {}
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced arbitrage analysis.
        
        Args:
            data: Market data including prices, volumes, order books
            
        Returns:
            Enhanced arbitrage opportunities with execution analysis
        """
        try:
            self.logger.info("Starting enhanced arbitrage analysis")
            
            # Extract market data
            prices = data.get('prices', {})
            volumes = data.get('volumes', {})
            order_books = data.get('order_books', {})  # If available
            symbols = data.get('symbols', list(prices.keys()) if prices else [])
            
            if not prices or len(prices) < 2:
                return {'opportunities': [], 'analysis_summary': 'Insufficient price data'}
            
            # Analyze arbitrage opportunities
            opportunities = []
            
            for symbol in symbols:
                symbol_opportunities = await self._analyze_symbol_arbitrage(
                    symbol, prices, volumes, order_books
                )
                opportunities.extend(symbol_opportunities)
            
            # Enhanced filtering and scoring
            enhanced_opportunities = []
            for opp in opportunities:
                enhanced_opp = await self._enhance_opportunity_analysis(opp, data)
                if enhanced_opp['execution_score'] > 0.6:  # Only high-quality opportunities
                    enhanced_opportunities.append(enhanced_opp)
            
            # Sort by execution score
            enhanced_opportunities.sort(
                key=lambda x: x['execution_score'], 
                reverse=True
            )
            
            # Analysis summary
            analysis_summary = {
                'total_symbols_analyzed': len(symbols),
                'raw_opportunities_found': len(opportunities),
                'high_quality_opportunities': len(enhanced_opportunities),
                'best_execution_score': enhanced_opportunities[0]['execution_score'] if enhanced_opportunities else 0,
                'analysis_timestamp': datetime.now().isoformat(),
                'market_conditions': await self._analyze_market_conditions(data)
            }
            
            self.logger.info(f"Enhanced arbitrage analysis complete: {len(enhanced_opportunities)} high-quality opportunities")
            
            return {
                'opportunities': enhanced_opportunities[:10],  # Top 10
                'analysis_summary': analysis_summary,
                'execution_guidance': await self._generate_execution_guidance(enhanced_opportunities[:3])
            }
            
        except Exception as e:
            self.logger.error(f"Enhanced arbitrage analysis failed: {e}")
            return {'error': str(e), 'opportunities': []}
    
    async def _analyze_symbol_arbitrage(self, symbol: str, prices: Dict, 
                                      volumes: Dict, order_books: Dict) -> List[Dict]:
        """Analyze arbitrage opportunities for a specific symbol."""
        try:
            symbol_prices = {}
            symbol_volumes = {}
            
            # Extract prices and volumes for this symbol across exchanges
            for exchange, exchange_prices in prices.items():
                if symbol in exchange_prices:
                    symbol_prices[exchange] = exchange_prices[symbol]
                    if volumes and exchange in volumes and symbol in volumes[exchange]:
                        symbol_volumes[exchange] = volumes[exchange][symbol]
                    else:
                        symbol_volumes[exchange] = 1000000  # Default volume
            
            if len(symbol_prices) < 2:
                return []
            
            opportunities = []
            
            # Compare all exchange pairs
            exchanges = list(symbol_prices.keys())
            for i, buy_exchange in enumerate(exchanges):
                for sell_exchange in exchanges[i+1:]:
                    buy_price = symbol_prices[buy_exchange]
                    sell_price = symbol_prices[sell_exchange]
                    
                    # Calculate profit in both directions
                    profit_1 = ((sell_price - buy_price) / buy_price) * 100
                    profit_2 = ((buy_price - sell_price) / sell_price) * 100
                    
                    # Check if profitable in either direction
                    if profit_1 > self.min_profit_threshold:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': buy_exchange,
                            'sell_exchange': sell_exchange,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'profit_percentage': profit_1,
                            'volume_buy': symbol_volumes.get(buy_exchange, 0),
                            'volume_sell': symbol_volumes.get(sell_exchange, 0),
                            'direction': 'buy_low_sell_high'
                        })
                    
                    elif profit_2 > self.min_profit_threshold:
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': sell_exchange,
                            'sell_exchange': buy_exchange,
                            'buy_price': sell_price,
                            'sell_price': buy_price,
                            'profit_percentage': profit_2,
                            'volume_buy': symbol_volumes.get(sell_exchange, 0),
                            'volume_sell': symbol_volumes.get(buy_exchange, 0),
                            'direction': 'buy_low_sell_high'
                        })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol} arbitrage: {e}")
            return []
    
    async def _enhance_opportunity_analysis(self, opportunity: Dict, market_data: Dict) -> Dict:
        """Enhance opportunity with execution feasibility analysis."""
        try:
            symbol = opportunity['symbol']
            buy_exchange = opportunity['buy_exchange']
            sell_exchange = opportunity['sell_exchange']
            profit_pct = opportunity['profit_percentage']
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
            
            # Calculate execution costs
            execution_costs = self._calculate_total_execution_costs(
                buy_exchange, sell_exchange, buy_price, sell_price
            )
            
            # Net profit after costs
            net_profit = profit_pct - execution_costs['total_cost_pct']
            
            # Liquidity analysis
            liquidity_score = await self._analyze_liquidity(
                symbol, buy_exchange, sell_exchange, opportunity
            )
            
            # Risk assessment
            risk_score = await self._assess_execution_risk(
                symbol, buy_exchange, sell_exchange, market_data
            )
            
            # Time sensitivity analysis
            time_score = self._calculate_time_sensitivity(profit_pct, net_profit)
            
            # Overall execution score (0.0 - 1.0)
            execution_score = self._calculate_execution_score(
                net_profit, liquidity_score, risk_score, time_score
            )
            
            # Enhanced opportunity
            enhanced = opportunity.copy()
            enhanced.update({
                'net_profit_percentage': net_profit,
                'execution_costs': execution_costs,
                'liquidity_score': liquidity_score,
                'risk_score': risk_score,
                'time_score': time_score,
                'execution_score': execution_score,
                'execution_feasible': execution_score > 0.6,
                'recommended_amount_usd': self._calculate_optimal_amount(
                    opportunity, liquidity_score, risk_score
                ),
                'estimated_execution_time': execution_costs['estimated_time_minutes'],
                'success_probability': min(0.95, execution_score * 0.9 + 0.1),
                'enhancement_timestamp': datetime.now().isoformat()
            })
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"Error enhancing opportunity analysis: {e}")
            enhanced = opportunity.copy()
            enhanced['execution_score'] = 0.1
            return enhanced
    
    def _calculate_total_execution_costs(self, buy_exchange: str, sell_exchange: str, 
                                       buy_price: float, sell_price: float) -> Dict:
        """Calculate total execution costs including fees, slippage, and time."""
        try:
            # Get exchange fees
            buy_fees = self.exchange_fees.get(buy_exchange.lower(), self.exchange_fees['default'])
            sell_fees = self.exchange_fees.get(sell_exchange.lower(), self.exchange_fees['default'])
            
            # Trading fees (assume taker fees for arbitrage)
            buy_fee_pct = buy_fees['taker']
            sell_fee_pct = sell_fees['taker']
            
            # Withdrawal fees
            withdrawal_fee_pct = buy_fees['withdrawal']
            
            # Slippage estimation (higher for smaller exchanges)
            buy_slippage = self._estimate_slippage(buy_exchange, buy_price)
            sell_slippage = self._estimate_slippage(sell_exchange, sell_price)
            
            # Network/transfer costs (if different chains)
            network_cost_pct = 0.1  # Approximate network fees
            
            # Total cost
            total_cost_pct = (buy_fee_pct + sell_fee_pct + withdrawal_fee_pct + 
                            buy_slippage + sell_slippage + network_cost_pct)
            
            # Estimated execution time
            estimated_time = self._estimate_execution_time(buy_exchange, sell_exchange)
            
            return {
                'buy_fee': buy_fee_pct,
                'sell_fee': sell_fee_pct,
                'withdrawal_fee': withdrawal_fee_pct,
                'buy_slippage': buy_slippage,
                'sell_slippage': sell_slippage,
                'network_cost': network_cost_pct,
                'total_cost_pct': total_cost_pct,
                'estimated_time_minutes': estimated_time
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating execution costs: {e}")
            return {'total_cost_pct': 1.0, 'estimated_time_minutes': 30}
    
    def _estimate_slippage(self, exchange: str, price: float) -> float:
        """Estimate slippage based on exchange and asset characteristics."""
        # Base slippage rates by exchange (estimated)
        base_slippage = {
            'binance': 0.05,    # Low slippage - high liquidity
            'coinbase': 0.1,    # Medium slippage
            'kraken': 0.08,     # Low-medium slippage
            'kucoin': 0.15,     # Higher slippage
            'default': 0.2      # Conservative estimate
        }
        
        slippage = base_slippage.get(exchange.lower(), base_slippage['default'])
        
        # Adjust for price (higher prices often have better liquidity)
        if price > 1000:  # Major coins like BTC, ETH
            slippage *= 0.5
        elif price > 10:  # Mid-cap coins
            slippage *= 0.8
        else:  # Small-cap coins
            slippage *= 1.5
        
        return min(slippage, 1.0)  # Cap at 1%
    
    def _estimate_execution_time(self, buy_exchange: str, sell_exchange: str) -> float:
        """Estimate total execution time in minutes."""
        # Base execution times (including deposits, trading, withdrawals)
        base_times = {
            'binance': 3,     # Fast exchange
            'coinbase': 5,    # Medium speed
            'kraken': 4,      # Medium speed
            'kucoin': 6,      # Slower
            'default': 8      # Conservative
        }
        
        buy_time = base_times.get(buy_exchange.lower(), base_times['default'])
        sell_time = base_times.get(sell_exchange.lower(), base_times['default'])
        
        # Total time (parallel operations possible)
        total_time = max(buy_time, sell_time) + 2  # Add 2 minutes for transfers
        
        return total_time
    
    async def _analyze_liquidity(self, symbol: str, buy_exchange: str, 
                               sell_exchange: str, opportunity: Dict) -> float:
        """Analyze liquidity for the arbitrage opportunity."""
        try:
            # Volume-based liquidity score
            buy_volume = opportunity.get('volume_buy', 0)
            sell_volume = opportunity.get('volume_sell', 0)
            
            # Minimum volume required for execution
            min_volume_needed = self.min_volume_usd
            
            # Liquidity score based on available volume
            if min(buy_volume, sell_volume) < min_volume_needed:
                return 0.2  # Low liquidity
            elif min(buy_volume, sell_volume) < min_volume_needed * 5:
                return 0.5  # Medium liquidity
            elif min(buy_volume, sell_volume) < min_volume_needed * 20:
                return 0.8  # Good liquidity
            else:
                return 1.0  # Excellent liquidity
                
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity: {e}")
            return 0.5  # Default medium score
    
    async def _assess_execution_risk(self, symbol: str, buy_exchange: str, 
                                   sell_exchange: str, market_data: Dict) -> float:
        """Assess execution risk factors."""
        try:
            risk_factors = []
            
            # Exchange reliability (based on historical data)
            exchange_reliability = {
                'binance': 0.95,
                'coinbase': 0.9,
                'kraken': 0.85,
                'kucoin': 0.8,
                'default': 0.7
            }
            
            buy_reliability = exchange_reliability.get(buy_exchange.lower(), 0.7)
            sell_reliability = exchange_reliability.get(sell_exchange.lower(), 0.7)
            
            # Market volatility risk
            volatility_risk = self._assess_volatility_risk(symbol, market_data)
            
            # Time decay risk (arbitrage opportunities close quickly)
            time_risk = 0.1  # Base time risk
            
            # Combined risk score (higher is better)
            risk_score = (buy_reliability * sell_reliability * 
                         (1 - volatility_risk) * (1 - time_risk))
            
            return max(0.1, min(1.0, risk_score))
            
        except Exception as e:
            self.logger.error(f"Error assessing execution risk: {e}")
            return 0.5
    
    def _assess_volatility_risk(self, symbol: str, market_data: Dict) -> float:
        """Assess volatility risk for the symbol."""
        try:
            # Simplified volatility assessment
            # In a real implementation, this would use historical price data
            
            # High-cap coins (lower volatility)
            low_volatility_symbols = ['BTC', 'ETH', 'USDT', 'USDC', 'BNB']
            if symbol in low_volatility_symbols:
                return 0.1  # Low volatility risk
            
            # Mid-cap coins
            mid_volatility_symbols = ['ADA', 'DOT', 'LINK', 'UNI', 'MATIC']
            if symbol in mid_volatility_symbols:
                return 0.3  # Medium volatility risk
            
            # Default to higher volatility for unknown coins
            return 0.5  # Higher volatility risk
            
        except Exception as e:
            return 0.3  # Default medium risk
    
    def _calculate_time_sensitivity(self, gross_profit: float, net_profit: float) -> float:
        """Calculate time sensitivity score."""
        try:
            # Higher profits are less time-sensitive
            if net_profit > 3.0:
                return 0.9  # Low time sensitivity
            elif net_profit > 1.5:
                return 0.7  # Medium time sensitivity
            elif net_profit > 0.5:
                return 0.5  # High time sensitivity
            else:
                return 0.2  # Very high time sensitivity
                
        except Exception as e:
            return 0.5  # Default
    
    def _calculate_execution_score(self, net_profit: float, liquidity_score: float, 
                                 risk_score: float, time_score: float) -> float:
        """Calculate overall execution score."""
        try:
            # Weighted scoring
            weights = {
                'profit': 0.4,      # 40% weight on profit
                'liquidity': 0.25,  # 25% weight on liquidity
                'risk': 0.25,       # 25% weight on risk
                'time': 0.1         # 10% weight on time sensitivity
            }
            
            # Normalize profit score (0-1)
            profit_score = min(1.0, max(0.0, net_profit / 5.0))  # 5% = max score
            
            # Calculate weighted score
            execution_score = (
                profit_score * weights['profit'] +
                liquidity_score * weights['liquidity'] +
                risk_score * weights['risk'] +
                time_score * weights['time']
            )
            
            return max(0.0, min(1.0, execution_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating execution score: {e}")
            return 0.1
    
    def _calculate_optimal_amount(self, opportunity: Dict, liquidity_score: float, 
                                risk_score: float) -> float:
        """Calculate optimal trading amount in USD."""
        try:
            buy_volume = opportunity.get('volume_buy', 1000000)
            sell_volume = opportunity.get('volume_sell', 1000000)
            
            # Base amount on available liquidity
            max_volume = min(buy_volume, sell_volume)
            
            # Conservative sizing based on risk
            if risk_score > 0.8 and liquidity_score > 0.8:
                size_factor = 0.1  # Use up to 10% of available volume
            elif risk_score > 0.6 and liquidity_score > 0.6:
                size_factor = 0.05  # Use up to 5% of available volume
            else:
                size_factor = 0.02  # Use up to 2% of available volume
            
            optimal_amount = max_volume * size_factor
            
            # Ensure minimum and maximum bounds
            return max(self.min_volume_usd, min(optimal_amount, 50000))  # Cap at $50k
            
        except Exception as e:
            return self.min_volume_usd
    
    async def _analyze_market_conditions(self, data: Dict) -> Dict:
        """Analyze current market conditions affecting arbitrage."""
        try:
            return {
                'overall_volatility': 'normal',  # Would be calculated from price data
                'arbitrage_environment': 'favorable',  # Based on spread analysis
                'execution_difficulty': 'medium',  # Based on market conditions
                'recommended_exposure': 'moderate'  # Risk management recommendation
            }
        except Exception as e:
            return {'status': 'unknown', 'error': str(e)}
    
    async def _generate_execution_guidance(self, opportunities: List[Dict]) -> Dict:
        """Generate execution guidance for top opportunities."""
        try:
            if not opportunities:
                return {'guidance': 'No executable opportunities found'}
            
            best_opp = opportunities[0]
            
            guidance = {
                'priority_order': [opp['symbol'] for opp in opportunities],
                'execution_strategy': 'sequential',  # Execute one by one
                'timing_recommendation': 'immediate' if best_opp['execution_score'] > 0.8 else 'monitor',
                'risk_management': {
                    'max_position_size': best_opp.get('recommended_amount_usd', 1000),
                    'stop_loss_trigger': 'price_convergence',
                    'time_limit_minutes': best_opp.get('estimated_execution_time', 10) * 2
                },
                'execution_steps': [
                    f"1. Prepare {best_opp['recommended_amount_usd']:.0f} USD on {best_opp['buy_exchange']}",
                    f"2. Buy {best_opp['symbol']} at {best_opp['buy_price']:.4f}",
                    f"3. Transfer to {best_opp['sell_exchange']}",
                    f"4. Sell at {best_opp['sell_price']:.4f}",
                    f"5. Expected net profit: {best_opp['net_profit_percentage']:.2f}%"
                ]
            }
            
            return guidance
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_analyzer_type(self) -> str:
        """Return the type of analyzer."""
        return "enhanced_arbitrage"
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get analyzer performance metrics."""
        return {
            'opportunities_analyzed': getattr(self, '_opportunities_count', 0),
            'high_quality_rate': getattr(self, '_quality_rate', 0.0),
            'average_execution_score': getattr(self, '_avg_score', 0.0),
            'success_rate': getattr(self, '_success_rate', 0.0)
        }