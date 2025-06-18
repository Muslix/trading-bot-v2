"""
Price Movement Alert Plugin - detects significant price movements.

This plugin monitors price changes and triggers alerts when significant
movements occur within specified timeframes.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from ..base import AlertPlugin, AlertConfig


class PriceMovementAlert(AlertPlugin):
    """
    Alert plugin for significant price movements.
    
    Triggers when:
    - Price moves more than threshold percentage
    - Movement occurs within specified timeframe
    - Symbol is not in cooldown period
    """
    
    async def _initialize_alert(self) -> bool:
        """Initialize price movement specific settings."""
        self.logger.info("Initializing Price Movement Alert plugin")
        
        # Set default threshold if not configured (5% price movement)
        if not hasattr(self.config, 'threshold') or self.config.threshold == 0:
            self.config.threshold = 5.0
        
        # Track price history for movement detection
        self.price_history = {}
        
        # Timeframe for price movement calculation (default 1 hour)
        self.movement_timeframe_hours = self.config.custom_settings.get('timeframe_hours', 1)
        
        return True
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if price movement alert should trigger.
        
        Args:
            data: Should contain current_prices data
            
        Returns:
            bool: True if alert should trigger
        """
        current_prices = data.get('current_prices', {})
        if not current_prices:
            self.logger.debug("No current prices data")
            return False
        
        significant_movements = []
        now = datetime.now()
        
        for symbol, price_data in current_prices.items():
            # Check symbol filtering
            if not self._filter_by_symbols({'symbol': symbol}):
                continue
            
            current_price = price_data.get('price', 0)
            if current_price <= 0:
                continue
            
            # Check if we have historical data for this symbol
            if symbol not in self.price_history:
                # First time seeing this symbol, just store the price
                self.price_history[symbol] = {
                    'price': current_price,
                    'timestamp': now
                }
                continue
            
            # Get historical price
            historical_data = self.price_history[symbol]
            historical_price = historical_data['price']
            historical_time = historical_data['timestamp']
            
            # Check if enough time has passed
            time_diff = now - historical_time
            if time_diff < timedelta(hours=self.movement_timeframe_hours):
                continue
            
            # Calculate price movement percentage
            price_change_pct = ((current_price - historical_price) / historical_price) * 100
            abs_price_change = abs(price_change_pct)
            
            # Check if movement exceeds threshold
            if abs_price_change >= self.config.threshold:
                significant_movements.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'previous_price': historical_price,
                    'change_percentage': price_change_pct,
                    'timeframe_hours': time_diff.total_seconds() / 3600
                })
            
            # Update price history
            self.price_history[symbol] = {
                'price': current_price,
                'timestamp': now
            }
        
        # Store movements for message formatting
        self._significant_movements = significant_movements
        
        return len(significant_movements) > 0
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process price movement alert data."""
        movements = getattr(self, '_significant_movements', [])
        
        if not movements:
            return {}
        
        # Sort by absolute change percentage (largest first)
        movements_sorted = sorted(
            movements,
            key=lambda x: abs(x['change_percentage']),
            reverse=True
        )
        
        return {
            'movements': movements_sorted,
            'total_count': len(movements),
            'largest_movement': movements_sorted[0] if movements_sorted else None,
            'symbols': [m['symbol'] for m in movements_sorted],
            'timestamp': datetime.now().isoformat()
        }
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format price movement alert message."""
        movements = alert_data.get('movements', [])
        if not movements:
            return "📊 Price Movement Alert: No significant movements detected"
        
        # Use custom template if provided
        if getattr(self.config, "message_template", None):
            return self._format_custom_message(alert_data)
        
        largest_movement = movements[0]
        symbol = largest_movement['symbol']
        change_pct = largest_movement['change_percentage']
        timeframe = largest_movement['timeframe_hours']
        
        # Determine direction emoji
        direction_emoji = "📈" if change_pct > 0 else "📉"
        direction_text = "increased" if change_pct > 0 else "decreased"
        
        message_parts = [
            f"{direction_emoji} **PRICE MOVEMENT ALERT**",
            f"",
            f"💰 **{symbol}** has {direction_text} by **{abs(change_pct):.2f}%**",
            f"📊 Timeframe: {timeframe:.1f} hours",
            f"💵 Price: ${largest_movement['previous_price']:.4f} → ${largest_movement['current_price']:.4f}"
        ]
        
        # Add additional movements if enabled and available
        if getattr(self.config, "include_details", True) and len(movements) > 1:
            message_parts.extend([
                f"",
                f"📊 **Other Significant Movements:**"
            ])
            
            for movement in movements[1:4]:  # Show next 3
                m_symbol = movement['symbol']
                m_change = movement['change_percentage']
                m_emoji = "📈" if m_change > 0 else "📉"
                message_parts.append(f"{m_emoji} {m_symbol}: {m_change:+.2f}%")
            
            if len(movements) > 4:
                message_parts.append(f"   ... and {len(movements) - 4} more")
        
        # Add timestamp
        message_parts.extend([
            f"",
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        ])
        
        message = "\n".join(message_parts)
        
        # Ensure message isn't too long
        if len(message) > getattr(self.config, "max_message_length", 4096):
            message = message[:getattr(self.config, "max_message_length", 4096) - 3] + "..."
        
        return message
    
    def _format_custom_message(self, alert_data: Dict[str, Any]) -> str:
        """Format message using custom template."""
        try:
            movements = alert_data.get('movements', [])
            largest = movements[0] if movements else {}
            
            template_vars = {
                'symbol': largest.get('symbol', 'UNKNOWN'),
                'change_pct': largest.get('change_percentage', 0),
                'current_price': largest.get('current_price', 0),
                'previous_price': largest.get('previous_price', 0),
                'timeframe': largest.get('timeframe_hours', 0),
                'count': len(movements),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            return getattr(self.config, "message_template", None).format(**template_vars)
            
        except Exception as e:
            self.logger.error(f"Failed to format custom message: {e}")
            return f"📊 Price Movement Alert: {abs(alert_data.get('largest_movement', {}).get('change_percentage', 0)):.2f}% movement detected"
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "price_movement"
