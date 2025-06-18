"""
Performance Alert Plugin - detects significant performance changes.

This plugin monitors portfolio performance metrics and triggers alerts
when significant changes occur (Sharpe ratio changes, new top performers, etc.).
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

from ..base import AlertPlugin, AlertConfig


class PerformanceAlert(AlertPlugin):
    """
    Alert plugin for performance-related events.
    
    Triggers when:
    - Sharpe ratio changes significantly
    - New top performers emerge
    - Portfolio performance crosses thresholds
    """
    
    async def _initialize_alert(self) -> bool:
        """Initialize performance-specific settings."""
        self.logger.info("Initializing Performance Alert plugin")
        
        # Set default threshold if not configured
        if not hasattr(self.config, 'threshold') or self.config.threshold == 0:
            self.config.threshold = 0.5  # Default 0.5 Sharpe ratio change
        
        # Track previous performance snapshots
        self.previous_performers = {}
        self.previous_sharpe_ratios = {}
        
        return True
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if performance alert should trigger.
        
        Args:
            data: Should contain current_performers data
            
        Returns:
            bool: True if alert should trigger
        """
        current_performers = data.get('current_performers', [])
        if not current_performers:
            self.logger.debug("No current performers data")
            return False
        
        # Check for significant Sharpe ratio changes
        significant_changes = []
        new_top_performers = []
        
        for performer in current_performers:
            if isinstance(performer, (list, tuple)) and len(performer) >= 2:
                symbol = performer[0]
                current_sharpe = performer[1]
            else:
                continue
            
            # Check symbol filtering
            if not self._filter_by_symbols({'symbol': symbol}):
                continue
            
            # Check for significant Sharpe ratio change
            if symbol in self.previous_sharpe_ratios:
                previous_sharpe = self.previous_sharpe_ratios[symbol]
                sharpe_change = abs(current_sharpe - previous_sharpe)
                
                if sharpe_change >= self.config.threshold:
                    significant_changes.append({
                        'symbol': symbol,
                        'current_sharpe': current_sharpe,
                        'previous_sharpe': previous_sharpe,
                        'change': current_sharpe - previous_sharpe
                    })
            
            # Check for new top performers (Sharpe > 1.5 and not seen before)
            min_sharpe_for_top = self.config.custom_settings.get('min_sharpe_for_top', 1.5)
            if (current_sharpe >= min_sharpe_for_top and 
                symbol not in self.previous_performers):
                new_top_performers.append({
                    'symbol': symbol,
                    'sharpe': current_sharpe
                })
            
            # Update tracking
            self.previous_sharpe_ratios[symbol] = current_sharpe
            self.previous_performers[symbol] = current_sharpe
        
        # Store changes for message formatting
        self._significant_changes = significant_changes
        self._new_top_performers = new_top_performers
        
        return len(significant_changes) > 0 or len(new_top_performers) > 0
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process performance alert data."""
        significant_changes = getattr(self, '_significant_changes', [])
        new_top_performers = getattr(self, '_new_top_performers', [])
        
        return {
            'significant_changes': significant_changes,
            'new_top_performers': new_top_performers,
            'total_changes': len(significant_changes),
            'total_new_performers': len(new_top_performers),
            'timestamp': datetime.now().isoformat()
        }
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format performance alert message."""
        significant_changes = alert_data.get('significant_changes', [])
        new_top_performers = alert_data.get('new_top_performers', [])
        
        if not significant_changes and not new_top_performers:
            return "📈 Performance Alert: No significant changes detected"
        
        message_parts = ["📈 **PERFORMANCE ALERT**", ""]
        
        # Add significant Sharpe ratio changes
        if significant_changes:
            message_parts.append("🎯 **Significant Sharpe Changes:**")
            for change in significant_changes[:5]:  # Limit to top 5
                symbol = change['symbol']
                current = change['current_sharpe']
                previous = change['previous_sharpe']
                delta = change['change']
                
                emoji = "📈" if delta > 0 else "📉"
                message_parts.append(
                    f"{emoji} **{symbol}**: {previous:.2f} → {current:.2f} "
                    f"({delta:+.2f})"
                )
            
            if len(significant_changes) > 5:
                message_parts.append(f"   ... and {len(significant_changes) - 5} more")
            
            message_parts.append("")
        
        # Add new top performers
        if new_top_performers:
            message_parts.append("🌟 **New Top Performers:**")
            for performer in new_top_performers[:3]:  # Limit to top 3
                symbol = performer['symbol']
                sharpe = performer['sharpe']
                message_parts.append(f"⭐ **{symbol}**: {sharpe:.2f} Sharpe")
            
            if len(new_top_performers) > 3:
                message_parts.append(f"   ... and {len(new_top_performers) - 3} more")
            
            message_parts.append("")
        
        # Add timestamp
        message_parts.append(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        
        message = "\n".join(message_parts)
        
        # Ensure message isn't too long
        if len(message) > getattr(self.config, "max_message_length", 4096):
            message = message[:getattr(self.config, "max_message_length", 4096) - 3] + "..."
        
        return message
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "performance"
