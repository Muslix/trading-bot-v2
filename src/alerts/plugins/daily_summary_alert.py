"""
Daily Summary Alert Plugin - generates daily performance summaries.

This plugin creates comprehensive daily summaries of trading performance,
market movements, and key metrics.
"""

from typing import Dict, Any, List
from datetime import datetime, time
import logging

from ..base import AlertPlugin, AlertConfig


class DailySummaryAlert(AlertPlugin):
    """
    Alert plugin for daily summaries.
    
    Triggers when:
    - Daily summary time is reached (configurable hour)
    - Force parameter is provided
    - Sufficient data is available for summary
    """
    
    async def _initialize_alert(self) -> bool:
        """Initialize daily summary specific settings."""
        self.logger.info("Initializing Daily Summary Alert plugin")
        
        # Default summary time (8:00 AM)
        self.summary_hour = self.config.custom_settings.get('summary_hour', 8)
        
        # Track when last summary was sent
        self.last_summary_date = None
        
        # Reset cooldown for daily summaries (override base class default)
        self.config.cooldown_minutes = 60  # Minimum 1 hour between summaries
        
        return True
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if daily summary alert should trigger.
        
        Args:
            data: Market data and performance metrics
            
        Returns:
            bool: True if alert should trigger
        """
        # Check for force flag
        if data.get('force_summary', False):
            self.logger.info("Daily summary forced")
            return True
        
        # Check if it's time for daily summary
        now = datetime.now()
        current_date = now.date()
        
        # Don't send if we already sent today
        if self.last_summary_date == current_date:
            self.logger.debug("Daily summary already sent today")
            return False
        
        # Check if it's the right time
        if now.hour != self.summary_hour:
            self.logger.debug(f"Not summary time yet (current: {now.hour}, target: {self.summary_hour})")
            return False
        
        # Update last summary date
        self.last_summary_date = current_date
        
        return True
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process daily summary data."""
        # Collect all available data for summary
        summary_data = {
            'date': datetime.now().date().isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Performance data
        current_performers = data.get('current_performers', [])
        if current_performers:
            summary_data['top_performers'] = current_performers[:5]  # Top 5
            summary_data['total_tracked'] = len(current_performers)
        
        # Price data
        current_prices = data.get('current_prices', {})
        if current_prices:
            summary_data['total_symbols'] = len(current_prices)
            
            # Calculate average price changes if historical data available
            price_changes = []
            for symbol, price_info in current_prices.items():
                if isinstance(price_info, dict):
                    change = price_info.get('change_24h', 0)
                    if change != 0:
                        price_changes.append(change)
            
            if price_changes:
                summary_data['avg_price_change_24h'] = sum(price_changes) / len(price_changes)
                summary_data['positive_changes'] = sum(1 for c in price_changes if c > 0)
                summary_data['negative_changes'] = sum(1 for c in price_changes if c < 0)
        
        # Arbitrage data
        arbitrage_opportunities = data.get('arbitrage_opportunities', [])
        if arbitrage_opportunities:
            summary_data['arbitrage_opportunities'] = len(arbitrage_opportunities)
            
            # Best arbitrage opportunity
            if arbitrage_opportunities:
                best_arb = max(arbitrage_opportunities, key=lambda x: x.get('profit_percentage', 0))
                summary_data['best_arbitrage'] = {
                    'symbol': best_arb.get('symbol'),
                    'profit': best_arb.get('profit_percentage', 0)
                }
        
        # Volume data
        volume_data = data.get('volume_data', {})
        if volume_data:
            volumes = [v for v in volume_data.values() if isinstance(v, (int, float)) and v > 0]
            if volumes:
                summary_data['total_volume'] = sum(volumes)
                summary_data['avg_volume'] = sum(volumes) / len(volumes)
        
        return summary_data
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format daily summary message."""
        date = alert_data.get('date', datetime.now().date().isoformat())
        
        # Use custom template if provided
        if getattr(self.config, "message_template", None):
            return self._format_custom_message(alert_data)
        
        message_parts = [
            f"📊 **DAILY SUMMARY** - {date}",
            f"",
            f"🔍 **Market Overview:**"
        ]
        
        # Market statistics
        total_symbols = alert_data.get('total_symbols', 0)
        if total_symbols > 0:
            message_parts.append(f"📈 Tracking {total_symbols} symbols")
        
        # Price changes
        avg_change = alert_data.get('avg_price_change_24h')
        if avg_change is not None:
            emoji = "📈" if avg_change > 0 else "📉" if avg_change < 0 else "➡️"
            message_parts.append(f"{emoji} Avg 24h change: {avg_change:+.2f}%")
        
        positive_changes = alert_data.get('positive_changes', 0)
        negative_changes = alert_data.get('negative_changes', 0)
        if positive_changes > 0 or negative_changes > 0:
            total_changes = positive_changes + negative_changes
            message_parts.append(f"📊 Winners: {positive_changes}, Losers: {negative_changes}")
        
        # Top performers
        top_performers = alert_data.get('top_performers', [])
        if top_performers:
            message_parts.extend([
                f"",
                f"🌟 **Top Performers:**"
            ])
            
            for i, performer in enumerate(top_performers[:3], 1):
                if isinstance(performer, (list, tuple)) and len(performer) >= 2:
                    symbol = performer[0]
                    sharpe = performer[1]
                    message_parts.append(f"{i}. **{symbol}**: {sharpe:.2f} Sharpe")
        
        # Arbitrage opportunities
        arb_count = alert_data.get('arbitrage_opportunities', 0)
        if arb_count > 0:
            message_parts.extend([
                f"",
                f"💰 **Arbitrage:**"
            ])
            message_parts.append(f"🔥 {arb_count} opportunities detected")
            
            best_arb = alert_data.get('best_arbitrage')
            if best_arb:
                message_parts.append(
                    f"🎯 Best: **{best_arb['symbol']}** ({best_arb['profit']:.2f}%)"
                )
        
        # Volume statistics
        total_volume = alert_data.get('total_volume')
        if total_volume:
            message_parts.extend([
                f"",
                f"📊 **Trading Volume:**"
            ])
            message_parts.append(f"💹 Total: {self._format_volume(total_volume)}")
        
        # System status
        message_parts.extend([
            f"",
            f"⚙️ **System Status:** ✅ All systems operational",
            f"🕐 Generated: {datetime.now().strftime('%H:%M:%S')}"
        ])
        
        message = "\n".join(message_parts)
        
        # Ensure message isn't too long
        if len(message) > getattr(self.config, "max_message_length", 4096):
            message = message[:getattr(self.config, "max_message_length", 4096) - 3] + "..."
        
        return message
    
    def _format_volume(self, volume: float) -> str:
        """Format volume number for display."""
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        else:
            return f"{volume:.0f}"
    
    def _format_custom_message(self, alert_data: Dict[str, Any]) -> str:
        """Format message using custom template."""
        try:
            template_vars = {
                'date': alert_data.get('date', ''),
                'total_symbols': alert_data.get('total_symbols', 0),
                'avg_change': alert_data.get('avg_price_change_24h', 0),
                'positive_changes': alert_data.get('positive_changes', 0),
                'negative_changes': alert_data.get('negative_changes', 0),
                'arbitrage_count': alert_data.get('arbitrage_opportunities', 0),
                'total_volume': alert_data.get('total_volume', 0),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            # Add top performer if available
            top_performers = alert_data.get('top_performers', [])
            if top_performers and len(top_performers[0]) >= 2:
                template_vars['top_performer'] = top_performers[0][0]
                template_vars['top_sharpe'] = top_performers[0][1]
            else:
                template_vars['top_performer'] = 'N/A'
                template_vars['top_sharpe'] = 0
            
            return getattr(self.config, "message_template", None).format(**template_vars)
            
        except Exception as e:
            self.logger.error(f"Failed to format custom message: {e}")
            return f"📊 Daily Summary - {alert_data.get('date', 'Unknown date')}"
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "daily_summary"
