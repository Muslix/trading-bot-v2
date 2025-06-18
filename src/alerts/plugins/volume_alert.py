"""
Volume Alert Plugin - detects significant volume spikes.

This plugin monitors trading volume and triggers alerts when
volume significantly exceeds normal levels.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from ..base import AlertPlugin, AlertConfig


class VolumeAlert(AlertPlugin):
    """
    Alert plugin for volume spikes.
    
    Triggers when:
    - Volume exceeds normal levels by threshold percentage
    - Volume data is available and reliable
    - Symbol is not in cooldown period
    """
    
    async def _initialize_alert(self) -> bool:
        """Initialize volume alert specific settings."""
        self.logger.info("Initializing Volume Alert plugin")
        
        # Set default threshold if not configured (200% above normal)
        if not hasattr(self.config, 'threshold') or self.config.threshold == 0:
            self.config.threshold = 200.0
        
        # Track volume history for baseline calculation
        self.volume_history = {}
        
        # Number of periods to use for baseline (default 24 hours of hourly data)
        self.baseline_periods = self.config.custom_settings.get('baseline_periods', 24)
        
        return True
    
    async def should_trigger(self, data: Dict[str, Any]) -> bool:
        """
        Check if volume alert should trigger.
        
        Args:
            data: Should contain volume data for symbols
            
        Returns:
            bool: True if alert should trigger
        """
        # Check for volume data in different possible formats
        volume_data = data.get('volume_data', {})
        current_prices = data.get('current_prices', {})
        
        # Extract volume from either source
        symbol_volumes = {}
        
        # From direct volume data
        if volume_data:
            symbol_volumes.update(volume_data)
        
        # From price data that might include volume
        if current_prices:
            for symbol, price_info in current_prices.items():
                if isinstance(price_info, dict) and 'volume' in price_info:
                    symbol_volumes[symbol] = price_info['volume']
        
        if not symbol_volumes:
            self.logger.debug("No volume data available")
            return False
        
        volume_spikes = []
        now = datetime.now()
        
        for symbol, current_volume in symbol_volumes.items():
            # Check symbol filtering
            if not self._filter_by_symbols({'symbol': symbol}):
                continue
            
            if current_volume <= 0:
                continue
            
            # Initialize history for new symbols
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            
            # Add current volume to history
            self.volume_history[symbol].append({
                'volume': current_volume,
                'timestamp': now
            })
            
            # Keep only recent history
            cutoff_time = now - timedelta(hours=self.baseline_periods)
            self.volume_history[symbol] = [
                v for v in self.volume_history[symbol]
                if v['timestamp'] > cutoff_time
            ]
            
            # Need at least some history to establish baseline
            if len(self.volume_history[symbol]) < 3:
                continue
            
            # Calculate baseline (average of historical volumes, excluding current)
            historical_volumes = [v['volume'] for v in self.volume_history[symbol][:-1]]
            if not historical_volumes:
                continue
            
            baseline_volume = sum(historical_volumes) / len(historical_volumes)
            
            if baseline_volume <= 0:
                continue
            
            # Calculate volume increase percentage
            volume_increase_pct = ((current_volume - baseline_volume) / baseline_volume) * 100
            
            # Check if volume spike exceeds threshold
            if volume_increase_pct >= self.config.threshold:
                volume_spikes.append({
                    'symbol': symbol,
                    'current_volume': current_volume,
                    'baseline_volume': baseline_volume,
                    'increase_percentage': volume_increase_pct,
                    'baseline_periods': len(historical_volumes)
                })
        
        # Store spikes for message formatting
        self._volume_spikes = volume_spikes
        
        return len(volume_spikes) > 0
    
    async def get_alert_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process volume alert data."""
        spikes = getattr(self, '_volume_spikes', [])
        
        if not spikes:
            return {}
        
        # Sort by increase percentage (largest first)
        spikes_sorted = sorted(
            spikes,
            key=lambda x: x['increase_percentage'],
            reverse=True
        )
        
        return {
            'volume_spikes': spikes_sorted,
            'total_count': len(spikes),
            'largest_spike': spikes_sorted[0] if spikes_sorted else None,
            'symbols': [s['symbol'] for s in spikes_sorted],
            'timestamp': datetime.now().isoformat()
        }
    
    async def format_message(self, alert_data: Dict[str, Any]) -> str:
        """Format volume alert message."""
        spikes = alert_data.get('volume_spikes', [])
        if not spikes:
            return "📊 Volume Alert: No significant volume spikes detected"
        
        # Use custom template if provided
        if getattr(self.config, "message_template", None):
            return self._format_custom_message(alert_data)
        
        largest_spike = spikes[0]
        symbol = largest_spike['symbol']
        increase_pct = largest_spike['increase_percentage']
        current_vol = largest_spike['current_volume']
        baseline_vol = largest_spike['baseline_volume']
        
        message_parts = [
            f"🔥 **VOLUME SPIKE ALERT**",
            f"",
            f"📈 **{symbol}** volume surge: **+{increase_pct:.0f}%**",
            f"📊 Current: {self._format_volume(current_vol)}",
            f"📊 Baseline: {self._format_volume(baseline_vol)}",
            f"📈 Multiplier: {current_vol / baseline_vol:.1f}x"
        ]
        
        # Add additional spikes if enabled and available
        if getattr(self.config, "include_details", True) and len(spikes) > 1:
            message_parts.extend([
                f"",
                f"📊 **Other Volume Spikes:**"
            ])
            
            for spike in spikes[1:4]:  # Show next 3
                s_symbol = spike['symbol']
                s_increase = spike['increase_percentage']
                message_parts.append(f"📈 {s_symbol}: +{s_increase:.0f}%")
            
            if len(spikes) > 4:
                message_parts.append(f"   ... and {len(spikes) - 4} more")
        
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
            spikes = alert_data.get('volume_spikes', [])
            largest = spikes[0] if spikes else {}
            
            template_vars = {
                'symbol': largest.get('symbol', 'UNKNOWN'),
                'increase_pct': largest.get('increase_percentage', 0),
                'current_volume': largest.get('current_volume', 0),
                'baseline_volume': largest.get('baseline_volume', 0),
                'multiplier': largest.get('current_volume', 1) / max(largest.get('baseline_volume', 1), 1),
                'count': len(spikes),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            return getattr(self.config, "message_template", None).format(**template_vars)
            
        except Exception as e:
            self.logger.error(f"Failed to format custom message: {e}")
            return f"🔥 Volume Alert: +{alert_data.get('largest_spike', {}).get('increase_percentage', 0):.0f}% volume spike detected"
    
    def get_alert_type(self) -> str:
        """Return alert type identifier."""
        return "volume_spike"
