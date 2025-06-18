"""
Arbitrage Alert Plugin - detects arbitrage opportunities across exchanges.

This plugin monitors price differences between exchanges and triggers alerts
when profitable arbitrage opportunities are detected.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from ..base import AlertPlugin, AlertConfig


class ArbitrageAlert(AlertPlugin):
    """
    Alert plugin for arbitrage opportunities.
    
    Triggers when:
    - Price difference between exchanges exceeds threshold
    - Profit potential is above configured minimum
    - Opportunity hasn't been alerted recently (cooldown)
    """
    
    async def _initialize_alert(self) -> bool:
        """Initialize arbitrage-specific settings."""
        self.logger.info("Initializing Arbitrage Alert plugin")
        
        # Set default threshold if not configured
        if not hasattr(self.config, 'threshold') or self.config.threshold == 0:
            self.config.threshold = 2.0  # Default 2% arbitrage threshold
        
        # Track seen opportunities to avoid duplicates
        self.seen_opportunities = set()
        
        return True
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if arbitrage alert should trigger.
        
        Args:
            data: Should contain arbitrage opportunities data
            
        Returns:
            bool: True if alert should trigger
        """
        # Check if we have arbitrage data
        opportunities = data.get('arbitrage_opportunities', [])
        if not opportunities:
            self.logger.debug("No arbitrage opportunities in data")
            return False
        
        # Filter opportunities above threshold
        significant_opportunities = []
        for opp in opportunities:
            profit_pct = opp.get('profit_percentage', 0)
            symbol = opp.get('symbol', '')
            
            # Check threshold
            if profit_pct < self.config.threshold:
                continue
            
            # Check symbol filtering
            if not self._filter_by_symbols(opp):
                continue
            
            # Check minimum value if configured
            min_value_threshold = getattr(self.config, 'min_value_threshold', None)
            if min_value_threshold:
                volume = opp.get('volume', 0)
                if volume < min_value_threshold:
                    continue
            
            significant_opportunities.append(opp)
        
        # Check if we have any significant opportunities
        if not significant_opportunities:
            self.logger.debug(f"No arbitrage opportunities above {self.config.threshold}% threshold")
            return False
        
        # Store for message formatting
        self._current_opportunities = significant_opportunities
        return True
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process arbitrage alert data."""
        opportunities = getattr(self, '_current_opportunities', [])
        
        if not opportunities:
            return {}
        
        # Group by symbol and take best opportunity per symbol
        symbol_opportunities = {}
        for opp in opportunities:
            symbol = opp.get('symbol', 'UNKNOWN')
            profit = opp.get('profit_percentage', 0)
            
            if symbol not in symbol_opportunities or profit > symbol_opportunities[symbol]['profit_percentage']:
                symbol_opportunities[symbol] = opp
        
        # Sort by profit potential
        best_opportunities = sorted(
            symbol_opportunities.values(),
            key=lambda x: x.get('profit_percentage', 0),
            reverse=True
        )
        
        # Take top opportunities (limit to avoid spam)
        max_opportunities = min(len(best_opportunities), 5)
        top_opportunities = best_opportunities[:max_opportunities]
        
        return {
            'opportunities': top_opportunities,
            'total_count': len(opportunities),
            'best_profit': top_opportunities[0]['profit_percentage'] if top_opportunities else 0,
            'symbols': [opp['symbol'] for opp in top_opportunities],
            'timestamp': datetime.now().isoformat()
        }
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format arbitrage alert message."""
        opportunities = alert_data.get('opportunities', [])
        if not opportunities:
            return "🔥 Arbitrage Alert: No opportunities data available"
        
        # Use custom template if provided
        message_template = getattr(self.config, 'message_template', None)
        if message_template:
            return self._format_custom_message(alert_data)
        
        # Default message format
        best_opp = opportunities[0]
        symbol = best_opp.get('symbol', 'UNKNOWN')
        profit = best_opp.get('profit_percentage', 0)
        buy_exchange = best_opp.get('buy_exchange', 'Unknown')
        sell_exchange = best_opp.get('sell_exchange', 'Unknown')
        
        message_parts = [
            f"🔥 **ARBITRAGE ALERT**",
            f"",
            f"💰 **{symbol}**: {profit:.2f}% profit opportunity",
            f"📈 Buy: {buy_exchange} → Sell: {sell_exchange}",
        ]
        
        # Add details if enabled and we have multiple opportunities
        include_details = getattr(self.config, 'include_details', True)
        if include_details and len(opportunities) > 1:
            message_parts.extend([
                f"",
                f"📊 **All Opportunities ({len(opportunities)}):**"
            ])
            
            for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
                opp_symbol = opp.get('symbol', 'UNKNOWN')
                opp_profit = opp.get('profit_percentage', 0)
                message_parts.append(f"{i}. {opp_symbol}: {opp_profit:.2f}%")
            
            if len(opportunities) > 3:
                message_parts.append(f"   ... and {len(opportunities) - 3} more")
        
        # Add timestamp
        message_parts.extend([
            f"",
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        ])
        
        message = "\n".join(message_parts)
        
        # Ensure message isn't too long
        max_message_length = getattr(self.config, 'max_message_length', 4096)
        if len(message) > max_message_length:
            message = message[:max_message_length - 3] + "..."
        
        return message
    
    def _format_custom_message(self, alert_data: Dict[str, Any]) -> str:
        """Format message using custom template."""
        try:
            opportunities = alert_data.get('opportunities', [])
            best_opp = opportunities[0] if opportunities else {}
            
            # Template variables
            template_vars = {
                'symbol': best_opp.get('symbol', 'UNKNOWN'),
                'profit': best_opp.get('profit_percentage', 0),
                'buy_exchange': best_opp.get('buy_exchange', 'Unknown'),
                'sell_exchange': best_opp.get('sell_exchange', 'Unknown'),
                'count': len(opportunities),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            message_template = getattr(self.config, 'message_template', '')
            return message_template.format(**template_vars)
            
        except Exception as e:
            self.logger.error(f"Failed to format custom message: {e}")
            # Fallback to default
            return f"🔥 Arbitrage Alert: {alert_data.get('best_profit', 0):.2f}% opportunity detected"
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "arbitrage"
