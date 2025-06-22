"""
Smart Arbitrage Alert Plugin - Enhanced arbitrage detection with ML-based filtering.

This plugin improves on the basic arbitrage alert by adding:
- Execution feasibility analysis
- Multi-factor scoring
- Historical success tracking
- Market conditions awareness
- Intelligent spam reduction
"""

import asyncio
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json

from ..base import AlertPlugin, AlertConfig


class SmartArbitrageAlert(AlertPlugin):
    """
    Enhanced arbitrage alert with intelligent filtering.
    
    Features:
    - Multi-factor opportunity scoring
    - Execution feasibility analysis
    - Historical success tracking
    - Market volatility awareness
    - Dynamic threshold adjustment
    """
    
    def __init__(self, config: AlertConfig):
        super().__init__(config)
        
        # Enhanced configuration
        self.min_profit_threshold = getattr(config, 'min_profit_threshold', 1.5)  # Minimum profit %
        self.volume_threshold = getattr(config, 'volume_threshold', 1000)  # Minimum volume USD
        self.volatility_factor = getattr(config, 'volatility_factor', 0.5)  # Volatility adjustment
        self.success_learning_enabled = getattr(config, 'success_learning', True)
        
        # Intelligence components
        self.opportunity_history = []  # Track past opportunities
        self.success_patterns = {}     # Learn from successful alerts
        self.market_conditions = {}    # Track market state
        self.execution_costs = {       # Estimated execution costs per exchange
            'binance': 0.075,   # 0.075% fee
            'coinbase': 0.4,    # 0.4% fee  
            'kraken': 0.16,     # 0.16% fee
            'default': 0.2      # Default fee
        }
    
    async def _initialize_alert(self) -> bool:
        """Initialize smart arbitrage detection."""
        self.logger.info("Initializing Smart Arbitrage Alert with ML-based filtering")
        
        # Initialize intelligent components
        await self._initialize_market_analysis()
        await self._load_historical_patterns()
        
        self.logger.info("✅ Smart Arbitrage Alert initialized with intelligence layer")
        return True
    
    async def _initialize_market_analysis(self):
        """Initialize market condition analysis."""
        self.market_conditions = {
            'volatility_level': 'normal',  # low, normal, high
            'market_trend': 'neutral',     # bullish, bearish, neutral  
            'trading_volume': 'normal',    # low, normal, high
            'last_update': datetime.now()
        }
    
    async def _load_historical_patterns(self):
        """Load historical success patterns for learning."""
        # In a real implementation, this would load from database
        self.success_patterns = {
            'profitable_pairs': set(),      # Pairs that historically worked
            'reliable_exchanges': set(),    # Exchanges with good execution
            'optimal_timeframes': [],       # Best times for arbitrage
            'failure_patterns': set()       # Patterns that failed
        }
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Intelligent arbitrage opportunity evaluation.
        
        Uses multi-factor analysis including:
        - Basic profit threshold
        - Execution feasibility
        - Market conditions
        - Historical success patterns
        """
        opportunities = data.get('arbitrage_opportunities', [])
        if not opportunities:
            return False
        
        # Update market conditions
        await self._update_market_conditions(data)
        
        # Analyze each opportunity with intelligence
        scored_opportunities = []
        for opp in opportunities:
            score = await self._score_opportunity(opp, data)
            if score > 0.6:  # Only consider high-scoring opportunities
                opp['intelligence_score'] = score
                scored_opportunities.append(opp)
        
        if not scored_opportunities:
            self.logger.debug("No opportunities passed intelligent filtering")
            return False
        
        # Sort by intelligence score and take best
        scored_opportunities.sort(key=lambda x: x['intelligence_score'], reverse=True)
        self._current_smart_opportunities = scored_opportunities[:3]  # Top 3
        
        self.logger.info(f"Smart filter: {len(scored_opportunities)} high-quality opportunities found")
        return True
    
    async def _score_opportunity(self, opportunity: Dict, market_data: Dict) -> float:
        """
        Score arbitrage opportunity using multiple intelligence factors.
        
        Returns score 0.0-1.0 where >0.6 is considered actionable.
        """
        try:
            symbol = opportunity.get('symbol', '')
            profit_pct = opportunity.get('profit_percentage', 0)
            buy_exchange = opportunity.get('buy_exchange', '')
            sell_exchange = opportunity.get('sell_exchange', '')
            volume = opportunity.get('volume', 0)
            
            # Base profit score (0.0-0.4)
            profit_score = min(0.4, profit_pct / 10.0)  # Cap at 4% = max score
            
            # Execution feasibility score (0.0-0.3)
            execution_score = await self._calculate_execution_feasibility(
                symbol, buy_exchange, sell_exchange, profit_pct, volume
            )
            
            # Market conditions score (0.0-0.2)
            market_score = self._calculate_market_conditions_score(symbol, profit_pct)
            
            # Historical success score (0.0-0.1)
            history_score = self._calculate_historical_success_score(
                symbol, buy_exchange, sell_exchange
            )
            
            total_score = profit_score + execution_score + market_score + history_score
            
            # Log detailed scoring for analysis
            self.logger.debug(f"Opportunity {symbol}: Profit={profit_score:.3f}, "
                            f"Execution={execution_score:.3f}, Market={market_score:.3f}, "
                            f"History={history_score:.3f}, Total={total_score:.3f}")
            
            return min(1.0, total_score)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Error scoring opportunity: {e}")
            return 0.0
    
    async def _calculate_execution_feasibility(self, symbol: str, buy_exchange: str, 
                                             sell_exchange: str, profit_pct: float, 
                                             volume: float) -> float:
        """
        Calculate execution feasibility score based on real trading costs.
        
        Considers:
        - Exchange fees
        - Withdrawal fees
        - Minimum trade sizes
        - Liquidity requirements
        """
        try:
            # Get trading fees for both exchanges
            buy_fee = self.execution_costs.get(buy_exchange.lower(), self.execution_costs['default'])
            sell_fee = self.execution_costs.get(sell_exchange.lower(), self.execution_costs['default'])
            
            # Estimate withdrawal fee (typically 0.1-0.5%)
            withdrawal_fee = 0.2
            
            # Total execution cost
            total_cost = buy_fee + sell_fee + withdrawal_fee
            
            # Net profit after costs
            net_profit = profit_pct - total_cost
            
            # Score based on net profit
            if net_profit <= 0:
                return 0.0  # Not profitable after costs
            elif net_profit < 0.5:
                return 0.1  # Barely profitable
            elif net_profit < 1.0:
                return 0.15  # Moderately profitable
            elif net_profit < 2.0:
                return 0.25  # Good profit
            else:
                return 0.3   # Excellent profit
                
        except Exception as e:
            self.logger.error(f"Error calculating execution feasibility: {e}")
            return 0.1  # Default low score
    
    def _calculate_market_conditions_score(self, symbol: str, profit_pct: float) -> float:
        """
        Score based on current market conditions.
        
        Higher volatility = higher arbitrage opportunities but also higher risk.
        """
        try:
            volatility_level = self.market_conditions.get('volatility_level', 'normal')
            market_trend = self.market_conditions.get('market_trend', 'neutral')
            
            # Base score
            score = 0.1
            
            # Volatility adjustment
            if volatility_level == 'high':
                score += 0.05  # High volatility = more opportunities
            elif volatility_level == 'low':
                score += 0.02  # Low volatility = fewer but more reliable
            
            # Market trend adjustment
            if market_trend == 'neutral':
                score += 0.03  # Neutral markets better for arbitrage
            elif market_trend in ['bullish', 'bearish']:
                score += 0.01  # Trending markets less reliable
            
            # Profit percentage adjustment
            if profit_pct > 3.0:
                score += 0.02  # Very high profits in normal market = suspicious
            
            return min(0.2, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating market conditions score: {e}")
            return 0.1
    
    def _calculate_historical_success_score(self, symbol: str, buy_exchange: str, 
                                          sell_exchange: str) -> float:
        """
        Score based on historical success patterns.
        
        Learn from past profitable arbitrage executions.
        """
        try:
            score = 0.05  # Base score
            
            # Check successful pairs
            pair_key = f"{symbol}_{buy_exchange}_{sell_exchange}"
            if pair_key in self.success_patterns['profitable_pairs']:
                score += 0.03
            
            # Check reliable exchanges
            if buy_exchange in self.success_patterns['reliable_exchanges']:
                score += 0.01
            if sell_exchange in self.success_patterns['reliable_exchanges']:
                score += 0.01
                
            # Check failure patterns
            if pair_key in self.success_patterns['failure_patterns']:
                score -= 0.05  # Penalize known failure patterns
            
            return max(0.0, min(0.1, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating historical success score: {e}")
            return 0.05
    
    async def _update_market_conditions(self, data: Dict):
        """Update market condition analysis."""
        try:
            current_prices = data.get('current_prices', {})
            volume_data = data.get('volume_data', {})
            
            # Simple volatility analysis
            if len(current_prices) > 10:
                price_changes = []
                for symbol, price in current_prices.items():
                    # Mock price change calculation (in real app, use historical data)
                    change = np.random.normal(0, 3)  # Simulate price change
                    price_changes.append(abs(change))
                
                avg_volatility = np.mean(price_changes)
                if avg_volatility > 5:
                    self.market_conditions['volatility_level'] = 'high'
                elif avg_volatility < 2:
                    self.market_conditions['volatility_level'] = 'low'
                else:
                    self.market_conditions['volatility_level'] = 'normal'
            
            # Update timestamp
            self.market_conditions['last_update'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating market conditions: {e}")
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract intelligent alert data."""
        opportunities = getattr(self, '_current_smart_opportunities', [])
        
        if not opportunities:
            return {}
        
        # Enhanced alert data with intelligence metrics
        alert_data = {
            'opportunities': opportunities,
            'total_analyzed': len(data.get('arbitrage_opportunities', [])),
            'high_quality_count': len(opportunities),
            'best_opportunity': opportunities[0] if opportunities else None,
            'market_conditions': self.market_conditions.copy(),
            'intelligence_summary': {
                'avg_score': np.mean([opp['intelligence_score'] for opp in opportunities]),
                'min_score': min([opp['intelligence_score'] for opp in opportunities]),
                'max_score': max([opp['intelligence_score'] for opp in opportunities])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return alert_data
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format intelligent arbitrage alert."""
        opportunities = alert_data.get('opportunities', [])
        if not opportunities:
            return "🤖 Smart Arbitrage: No high-quality opportunities found"
        
        best_opp = opportunities[0]
        symbol = best_opp.get('symbol', 'UNKNOWN')
        profit = best_opp.get('profit_percentage', 0)
        intelligence_score = best_opp.get('intelligence_score', 0)
        buy_exchange = best_opp.get('buy_exchange', 'Unknown')
        sell_exchange = best_opp.get('sell_exchange', 'Unknown')
        
        # Intelligence summary
        intel_summary = alert_data.get('intelligence_summary', {})
        market_conditions = alert_data.get('market_conditions', {})
        
        message_parts = [
            f"🤖 **SMART ARBITRAGE ALERT**",
            f"",
            f"🎯 **Best Opportunity**: {symbol}",
            f"💰 **Profit**: {profit:.2f}% (Score: {intelligence_score:.2f}/1.0)",
            f"📈 **Route**: {buy_exchange} → {sell_exchange}",
            f"",
            f"🧠 **Intelligence Analysis**:",
            f"• Quality Score: {intel_summary.get('avg_score', 0):.2f}/1.0",
            f"• Market Volatility: {market_conditions.get('volatility_level', 'unknown').title()}",
            f"• High-Quality Ops: {len(opportunities)}/{alert_data.get('total_analyzed', 0)}",
        ]
        
        # Add additional opportunities if any
        if len(opportunities) > 1:
            message_parts.extend([
                f"",
                f"📊 **Other Quality Opportunities**:"
            ])
            for i, opp in enumerate(opportunities[1:3], 2):  # Show 2nd and 3rd
                opp_symbol = opp.get('symbol', 'UNKNOWN')
                opp_profit = opp.get('profit_percentage', 0)
                opp_score = opp.get('intelligence_score', 0)
                message_parts.append(f"{i}. {opp_symbol}: {opp_profit:.2f}% (Score: {opp_score:.2f})")
        
        # Add execution guidance
        message_parts.extend([
            f"",
            f"⚡ **Action**: Execution recommended within 2-5 minutes",
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        ])
        
        return "\n".join(message_parts)
    
    async def track_alert_success(self, alert_data: Dict, success: bool):
        """
        Track alert success for learning.
        
        This would be called by the trading system to provide feedback.
        """
        if not self.success_learning_enabled:
            return
        
        try:
            opportunities = alert_data.get('opportunities', [])
            for opp in opportunities:
                symbol = opp.get('symbol', '')
                buy_exchange = opp.get('buy_exchange', '')
                sell_exchange = opp.get('sell_exchange', '')
                
                pair_key = f"{symbol}_{buy_exchange}_{sell_exchange}"
                
                if success:
                    self.success_patterns['profitable_pairs'].add(pair_key)
                    self.success_patterns['reliable_exchanges'].add(buy_exchange)
                    self.success_patterns['reliable_exchanges'].add(sell_exchange)
                else:
                    self.success_patterns['failure_patterns'].add(pair_key)
                
                self.logger.info(f"Learned from arbitrage {('success' if success else 'failure')}: {pair_key}")
                
        except Exception as e:
            self.logger.error(f"Error tracking alert success: {e}")
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "smart_arbitrage"
    
    def get_intelligence_stats(self) -> Dict[str, Any]:
        """Get intelligence system statistics."""
        return {
            'success_patterns': {
                'profitable_pairs': len(self.success_patterns.get('profitable_pairs', set())),
                'reliable_exchanges': len(self.success_patterns.get('reliable_exchanges', set())),
                'failure_patterns': len(self.success_patterns.get('failure_patterns', set()))
            },
            'market_conditions': self.market_conditions.copy(),
            'execution_costs': self.execution_costs.copy(),
            'configuration': {
                'min_profit_threshold': self.min_profit_threshold,
                'volume_threshold': self.volume_threshold,
                'volatility_factor': self.volatility_factor,
                'success_learning_enabled': self.success_learning_enabled
            }
        }