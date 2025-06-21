"""
Technical Analyzer Plugin - Technical analysis indicators
"""

from typing import Dict, List, Any, Optional
import numpy as np
import logging

from ..base import BaseAnalyzer
from src.utils.decorators import log_performance


class TechnicalAnalyzer(BaseAnalyzer):
    """Technical analysis for cryptocurrency data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sma_periods = config.get("sma_periods", [20, 50, 200])
        self.ema_periods = config.get("ema_periods", [12, 26])
        self.rsi_period = config.get("rsi_period", 14)
        self.bollinger_period = config.get("bollinger_period", 20)
        self.bollinger_std = config.get("bollinger_std", 2)
        
    def get_analyzer_type(self) -> str:
        return "technical"
        
    @log_performance
    async def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform technical analysis on price data
        
        Args:
            data: Dict with 'Close', 'High', 'Low', 'Volume' arrays or pandas DataFrame
            kwargs: Additional parameters
        """
        try:
            if hasattr(data, 'Close'):
                # DataFrame input
                close_prices = data['Close'].values
                high_prices = data['High'].values if 'High' in data else close_prices
                low_prices = data['Low'].values if 'Low' in data else close_prices
                volume = data['Volume'].values if 'Volume' in data else np.ones_like(close_prices)
            elif isinstance(data, dict):
                # Dictionary input
                close_prices = np.array(data.get('Close', []))
                high_prices = np.array(data.get('High', close_prices))
                low_prices = np.array(data.get('Low', close_prices))
                volume = np.array(data.get('Volume', np.ones_like(close_prices)))
            else:
                return {"error": "Invalid data format - expected DataFrame or dict with OHLCV data"}
                
            if len(close_prices) < max(self.sma_periods + self.ema_periods + [self.rsi_period, self.bollinger_period]):
                return {"error": "Insufficient data for technical analysis"}
                
            # Calculate indicators
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma'] = {}
            for period in self.sma_periods:
                if len(close_prices) >= period:
                    indicators['sma'][f'sma_{period}'] = self._calculate_sma(close_prices, period)
                    
            # Exponential Moving Averages
            indicators['ema'] = {}
            for period in self.ema_periods:
                if len(close_prices) >= period:
                    indicators['ema'][f'ema_{period}'] = self._calculate_ema(close_prices, period)
                    
            # RSI
            if len(close_prices) >= self.rsi_period:
                indicators['rsi'] = self._calculate_rsi(close_prices, self.rsi_period)
                
            # Bollinger Bands
            if len(close_prices) >= self.bollinger_period:
                bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                    close_prices, self.bollinger_period, self.bollinger_std
                )
                indicators['bollinger_bands'] = {
                    'upper': bb_upper,
                    'middle': bb_middle,
                    'lower': bb_lower
                }
                
            # MACD
            if len(close_prices) >= max(self.ema_periods):
                macd_line, signal_line, histogram = self._calculate_macd(close_prices)
                indicators['macd'] = {
                    'macd_line': macd_line,
                    'signal_line': signal_line,
                    'histogram': histogram
                }
                
            # Volume indicators
            if len(volume) > 1:
                indicators['volume'] = {
                    'volume_sma_20': self._calculate_sma(volume, 20) if len(volume) >= 20 else None,
                    'volume_ratio': volume[-1] / np.mean(volume[-20:]) if len(volume) >= 20 else 1.0
                }
                
            # Price action signals
            indicators['signals'] = self._generate_signals(close_prices, indicators)
            
            return {
                "indicators": indicators,
                "current_price": float(close_prices[-1]),
                "data_points": len(close_prices),
                "analysis_timestamp": kwargs.get("timestamp", "unknown")
            }
            
        except Exception as e:
            return {"error": f"Technical analysis failed: {str(e)}"}
            
    def _calculate_sma(self, prices: np.ndarray, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return float(np.mean(prices[-period:]))
        
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
            
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return float(ema)
        
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
        
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int, std_dev: float):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
            
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return float(upper), float(sma), float(lower)
        
    def _calculate_macd(self, prices: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """Calculate MACD"""
        if len(prices) < slow_period:
            return None, None, None
            
        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)
        
        if ema_fast is None or ema_slow is None:
            return None, None, None
            
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD line)
        # Simplified - in reality you'd need MACD history
        signal_line = macd_line  # Placeholder
        histogram = macd_line - signal_line
        
        return float(macd_line), float(signal_line), float(histogram)
        
    def _generate_signals(self, prices: np.ndarray, indicators: Dict) -> Dict[str, Any]:
        """Generate trading signals based on indicators"""
        signals = {
            "trend": "neutral",
            "momentum": "neutral",
            "volume_signal": "neutral",
            "overall_signal": "neutral"
        }
        
        current_price = prices[-1]
        
        # Trend signals
        if 'sma' in indicators:
            sma_20 = indicators['sma'].get('sma_20')
            sma_50 = indicators['sma'].get('sma_50')
            
            if sma_20 and sma_50:
                if current_price > sma_20 > sma_50:
                    signals["trend"] = "bullish"
                elif current_price < sma_20 < sma_50:
                    signals["trend"] = "bearish"
                    
        # Momentum signals
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi and rsi > 70:
                signals["momentum"] = "overbought"
            elif rsi and rsi < 30:
                signals["momentum"] = "oversold"
                
        # Volume signals
        if 'volume' in indicators:
            volume_ratio = indicators['volume'].get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                signals["volume_signal"] = "high_volume"
            elif volume_ratio < 0.5:
                signals["volume_signal"] = "low_volume"
                
        # Overall signal
        bullish_signals = sum([
            signals["trend"] == "bullish",
            signals["momentum"] == "oversold",
            signals["volume_signal"] == "high_volume"
        ])
        
        bearish_signals = sum([
            signals["trend"] == "bearish", 
            signals["momentum"] == "overbought",
            signals["volume_signal"] == "low_volume"
        ])
        
        if bullish_signals > bearish_signals:
            signals["overall_signal"] = "bullish"
        elif bearish_signals > bullish_signals:
            signals["overall_signal"] = "bearish"
            
        return signals