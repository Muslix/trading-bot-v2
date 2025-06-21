"""
AI/ML Utility Plugin - sentiment analysis, pattern recognition, and ML helpers
"""

import re
import math
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from ..base import UtilPlugin, UtilConfig


class AIMLUtil(UtilPlugin):
    """
    AI/ML utility plugin for sentiment analysis and pattern recognition.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.analysis_count = 0
        self.last_analysis_time = None
        
        # Sentiment analysis configuration
        self.sentiment_keywords = {
            "positive": [
                "bullish", "buy", "long", "pump", "moon", "hodl", "diamond", "hands",
                "rocket", "surge", "rally", "breakout", "profit", "gains", "up", "rise",
                "growth", "increase", "positive", "optimistic", "confident", "strong"
            ],
            "negative": [
                "bearish", "sell", "short", "dump", "crash", "drop", "fall", "decline",
                "loss", "losses", "down", "red", "fear", "panic", "weak", "resistance",
                "support", "breakdown", "correction", "bubble", "overvalued", "risky"
            ],
            "neutral": [
                "stable", "sideways", "consolidation", "range", "wait", "watch", "analyze",
                "study", "research", "cautious", "uncertain", "mixed", "unclear"
            ]
        }
        
        # Technical analysis patterns
        self.ta_patterns = {
            "hammer": {"body_ratio": 0.3, "wick_ratio": 2.0, "direction": "bullish"},
            "doji": {"body_ratio": 0.1, "wick_ratio": 1.0, "direction": "neutral"},
            "shooting_star": {"body_ratio": 0.3, "wick_ratio": 2.0, "direction": "bearish"},
            "engulfing_bullish": {"pattern_type": "reversal", "direction": "bullish"},
            "engulfing_bearish": {"pattern_type": "reversal", "direction": "bearish"}
        }
        
        # News sources for sentiment analysis
        self.news_sources = {
            "cryptonews": "https://cryptonews.net/api/news",
            "coindesk": "https://api.coindesk.com/v1/news",
            "cointelegraph": "https://api.cointelegraph.com/news"
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize AI/ML utility."""
        try:
            # Initialize HTTP session for API calls
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
            
            # Try to import optional ML libraries
            try:
                import numpy as np
                import pandas as pd
                self.numpy_available = True
                self.pandas_available = True
                self.np = np
                self.pd = pd
            except ImportError:
                self.numpy_available = False
                self.pandas_available = False
                self.logger.warning("NumPy/Pandas not available - advanced ML features disabled")
            
            try:
                import requests
                self.requests_available = True
                self.requests = requests
            except ImportError:
                self.requests_available = False
                self.logger.warning("Requests not available - some API features disabled")
            
            self.logger.info("AI/ML utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI/ML utility: {e}")
            return False
    
    async def _cleanup_util(self) -> None:
        """Clean up AI/ML utility resources."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process AI/ML operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "analyze_sentiment")
        
        if action == "analyze_sentiment":
            return await self._analyze_sentiment(data)
        elif action == "detect_patterns":
            return await self._detect_technical_patterns(data)
        elif action == "predict_price_direction":
            return await self._predict_price_direction(data)
        elif action == "calculate_indicators":
            return await self._calculate_technical_indicators(data)
        elif action == "analyze_news_sentiment":
            return await self._analyze_news_sentiment(data)
        elif action == "risk_assessment":
            return await self._assess_risk(data)
        elif action == "correlation_analysis":
            return await self._analyze_correlations(data)
        elif action == "anomaly_detection":
            return await self._detect_anomalies(data)
        elif action == "get_models_info":
            return self._get_models_info()
        elif action == "get_stats":
            return self._get_aiml_stats()
        else:
            raise ValueError(f"Unknown AI/ML action: {action}")
    
    async def _analyze_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of text data."""
        try:
            text = data.get("text", "")
            source = data.get("source", "text")
            
            if not text:
                return {"success": False, "error": "No text provided for sentiment analysis"}
            
            # Preprocess text
            text_lower = text.lower()
            words = re.findall(r'\b\w+\b', text_lower)
            
            # Count sentiment keywords
            positive_count = sum(1 for word in words if word in self.sentiment_keywords["positive"])
            negative_count = sum(1 for word in words if word in self.sentiment_keywords["negative"])
            neutral_count = sum(1 for word in words if word in self.sentiment_keywords["neutral"])
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            # Calculate sentiment scores
            if total_sentiment_words > 0:
                positive_score = positive_count / total_sentiment_words
                negative_score = negative_count / total_sentiment_words
                neutral_score = neutral_count / total_sentiment_words
            else:
                positive_score = negative_score = neutral_score = 0.33
            
            # Determine overall sentiment
            if positive_score > negative_score and positive_score > neutral_score:
                overall_sentiment = "positive"
                confidence = positive_score
            elif negative_score > positive_score and negative_score > neutral_score:
                overall_sentiment = "negative"
                confidence = negative_score
            else:
                overall_sentiment = "neutral"
                confidence = neutral_score
            
            # Calculate sentiment strength
            sentiment_strength = abs(positive_score - negative_score)
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "sentiment": {
                    "overall": overall_sentiment,
                    "confidence": confidence,
                    "strength": sentiment_strength,
                    "scores": {
                        "positive": positive_score,
                        "negative": negative_score,
                        "neutral": neutral_score
                    },
                    "word_counts": {
                        "positive": positive_count,
                        "negative": negative_count,
                        "neutral": neutral_count,
                        "total": total_sentiment_words
                    }
                },
                "source": source,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _detect_technical_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect technical analysis patterns in price data."""
        try:
            price_data = data.get("price_data", [])
            pattern_types = data.get("pattern_types", list(self.ta_patterns.keys()))
            
            if not price_data:
                return {"success": False, "error": "No price data provided"}
            
            detected_patterns = []
            
            # Ensure price data has required fields
            required_fields = ["open", "high", "low", "close"]
            if not all(field in price_data[0] for field in required_fields):
                return {"success": False, "error": "Price data must contain OHLC values"}
            
            # Analyze each candle for patterns
            for i, candle in enumerate(price_data):
                candle_patterns = self._analyze_candle_pattern(candle, pattern_types)
                
                for pattern in candle_patterns:
                    detected_patterns.append({
                        "index": i,
                        "timestamp": candle.get("timestamp", ""),
                        "pattern": pattern["name"],
                        "direction": pattern["direction"],
                        "confidence": pattern["confidence"],
                        "description": pattern["description"]
                    })
            
            # Multi-candle pattern detection
            if len(price_data) >= 2:
                multi_patterns = self._detect_multi_candle_patterns(price_data)
                detected_patterns.extend(multi_patterns)
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "patterns": detected_patterns,
                "candles_analyzed": len(price_data),
                "pattern_types_searched": pattern_types,
                "total_patterns_found": len(detected_patterns),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_candle_pattern(self, candle: Dict[str, Any], pattern_types: List[str]) -> List[Dict[str, Any]]:
        """Analyze a single candle for patterns."""
        patterns = []
        
        open_price = float(candle["open"])
        high_price = float(candle["high"])
        low_price = float(candle["low"])
        close_price = float(candle["close"])
        
        # Calculate candle properties
        body_size = abs(close_price - open_price)
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price
        total_range = high_price - low_price
        
        if total_range == 0:
            return patterns
        
        body_ratio = body_size / total_range
        upper_wick_ratio = upper_wick / total_range
        lower_wick_ratio = lower_wick / total_range
        
        # Check for hammer pattern
        if "hammer" in pattern_types:
            if (body_ratio <= 0.3 and lower_wick_ratio >= 0.6 and upper_wick_ratio <= 0.1):
                patterns.append({
                    "name": "hammer",
                    "direction": "bullish",
                    "confidence": 0.8,
                    "description": "Hammer pattern - potential bullish reversal"
                })
        
        # Check for shooting star pattern
        if "shooting_star" in pattern_types:
            if (body_ratio <= 0.3 and upper_wick_ratio >= 0.6 and lower_wick_ratio <= 0.1):
                patterns.append({
                    "name": "shooting_star",
                    "direction": "bearish",
                    "confidence": 0.8,
                    "description": "Shooting star pattern - potential bearish reversal"
                })
        
        # Check for doji pattern
        if "doji" in pattern_types:
            if body_ratio <= 0.1:
                patterns.append({
                    "name": "doji",
                    "direction": "neutral",
                    "confidence": 0.7,
                    "description": "Doji pattern - market indecision"
                })
        
        return patterns
    
    def _detect_multi_candle_patterns(self, price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect multi-candle patterns."""
        patterns = []
        
        for i in range(len(price_data) - 1):
            current = price_data[i]
            next_candle = price_data[i + 1]
            
            # Engulfing patterns
            current_body = abs(float(current["close"]) - float(current["open"]))
            next_body = abs(float(next_candle["close"]) - float(next_candle["open"]))
            
            if next_body > current_body * 1.2:  # Next candle body is significantly larger
                if (float(current["close"]) < float(current["open"]) and  # Current is bearish
                    float(next_candle["close"]) > float(next_candle["open"]) and  # Next is bullish
                    float(next_candle["close"]) > float(current["open"]) and  # Next close > current open
                    float(next_candle["open"]) < float(current["close"])):  # Next open < current close
                    
                    patterns.append({
                        "index": i + 1,
                        "timestamp": next_candle.get("timestamp", ""),
                        "pattern": "engulfing_bullish",
                        "direction": "bullish",
                        "confidence": 0.85,
                        "description": "Bullish engulfing pattern - strong reversal signal"
                    })
                
                elif (float(current["close"]) > float(current["open"]) and  # Current is bullish
                      float(next_candle["close"]) < float(next_candle["open"]) and  # Next is bearish
                      float(next_candle["close"]) < float(current["open"]) and  # Next close < current open
                      float(next_candle["open"]) > float(current["close"])):  # Next open > current close
                    
                    patterns.append({
                        "index": i + 1,
                        "timestamp": next_candle.get("timestamp", ""),
                        "pattern": "engulfing_bearish",
                        "direction": "bearish",
                        "confidence": 0.85,
                        "description": "Bearish engulfing pattern - strong reversal signal"
                    })
        
        return patterns
    
    async def _predict_price_direction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict price direction using simple ML techniques."""
        try:
            price_data = data.get("price_data", [])
            lookback_periods = data.get("lookback_periods", 10)
            prediction_horizon = data.get("prediction_horizon", 1)  # periods ahead
            
            if len(price_data) < lookback_periods + 1:
                return {"success": False, "error": "Insufficient price data for prediction"}
            
            # Extract closing prices
            prices = [float(p["close"]) for p in price_data]
            
            # Calculate simple features
            features = []
            for i in range(lookback_periods, len(prices)):
                # Price changes over different periods
                price_changes = []
                for period in [1, 3, 5, 10]:
                    if i >= period:
                        change = (prices[i] - prices[i-period]) / prices[i-period]
                        price_changes.append(change)
                    else:
                        price_changes.append(0)
                
                # Simple moving averages
                ma_short = sum(prices[i-5:i]) / 5 if i >= 5 else prices[i]
                ma_long = sum(prices[i-10:i]) / 10 if i >= 10 else prices[i]
                ma_ratio = ma_short / ma_long if ma_long > 0 else 1
                
                # Volatility (standard deviation of recent prices)
                recent_prices = prices[max(0, i-5):i]
                volatility = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
                
                features.append(price_changes + [ma_ratio, volatility])
            
            if not features:
                return {"success": False, "error": "Could not extract features from price data"}
            
            # Simple trend prediction based on recent patterns
            recent_features = features[-1]
            
            # Calculate trend score
            trend_score = 0
            
            # Weight recent price changes
            if len(recent_features) >= 4:
                trend_score += recent_features[0] * 0.4  # 1-period change
                trend_score += recent_features[1] * 0.3  # 3-period change
                trend_score += recent_features[2] * 0.2  # 5-period change
                trend_score += recent_features[3] * 0.1  # 10-period change
            
            # Add MA signal
            if len(recent_features) >= 5:
                ma_signal = (recent_features[4] - 1) * 0.5  # MA ratio signal
                trend_score += ma_signal
            
            # Determine prediction
            if trend_score > 0.02:
                direction = "up"
                confidence = min(0.9, abs(trend_score) * 10)
            elif trend_score < -0.02:
                direction = "down"
                confidence = min(0.9, abs(trend_score) * 10)
            else:
                direction = "sideways"
                confidence = 0.5
            
            # Calculate support and resistance levels
            recent_prices = prices[-20:] if len(prices) >= 20 else prices
            support_level = min(recent_prices)
            resistance_level = max(recent_prices)
            current_price = prices[-1]
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "prediction": {
                    "direction": direction,
                    "confidence": confidence,
                    "trend_score": trend_score,
                    "horizon_periods": prediction_horizon,
                    "current_price": current_price,
                    "support_level": support_level,
                    "resistance_level": resistance_level,
                    "price_to_support_ratio": current_price / support_level if support_level > 0 else 1,
                    "price_to_resistance_ratio": current_price / resistance_level if resistance_level > 0 else 1
                },
                "model_info": {
                    "type": "simple_trend_analysis",
                    "features_used": ["price_changes", "moving_averages", "volatility"],
                    "lookback_periods": lookback_periods
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Price direction prediction failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calculate_technical_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical analysis indicators."""
        try:
            price_data = data.get("price_data", [])
            indicators = data.get("indicators", ["sma", "rsi", "macd"])
            
            if not price_data:
                return {"success": False, "error": "No price data provided"}
            
            # Extract price arrays
            closes = [float(p["close"]) for p in price_data]
            highs = [float(p["high"]) for p in price_data]
            lows = [float(p["low"]) for p in price_data]
            
            results = {}
            
            # Simple Moving Average
            if "sma" in indicators:
                sma_periods = [10, 20, 50]
                results["sma"] = {}
                for period in sma_periods:
                    if len(closes) >= period:
                        sma = sum(closes[-period:]) / period
                        results["sma"][f"sma_{period}"] = sma
            
            # RSI (Relative Strength Index)
            if "rsi" in indicators and len(closes) >= 14:
                rsi = self._calculate_rsi(closes, 14)
                results["rsi"] = rsi
            
            # MACD
            if "macd" in indicators and len(closes) >= 26:
                macd_data = self._calculate_macd(closes)
                results["macd"] = macd_data
            
            # Bollinger Bands
            if "bollinger" in indicators and len(closes) >= 20:
                bb_data = self._calculate_bollinger_bands(closes, 20, 2)
                results["bollinger"] = bb_data
            
            # Stochastic Oscillator
            if "stochastic" in indicators and len(highs) >= 14:
                stoch_data = self._calculate_stochastic(highs, lows, closes, 14)
                results["stochastic"] = stoch_data
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "indicators": results,
                "indicators_calculated": list(results.keys()),
                "data_points": len(price_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Technical indicators calculation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Dict[str, Any]:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return {"error": "Insufficient data for RSI calculation"}
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            return {"rsi": 100, "signal": "overbought"}
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signal
        if rsi > 70:
            signal = "overbought"
        elif rsi < 30:
            signal = "oversold"
        else:
            signal = "neutral"
        
        return {"rsi": rsi, "signal": signal}
    
    def _calculate_macd(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate MACD indicator."""
        if len(prices) < 26:
            return {"error": "Insufficient data for MACD calculation"}
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        macd_values = [macd_line]  # Simplified - would need full history for proper signal line
        signal_line = macd_line  # Simplified
        
        histogram = macd_line - signal_line
        
        # Generate signal
        if macd_line > signal_line and histogram > 0:
            signal = "bullish"
        elif macd_line < signal_line and histogram < 0:
            signal = "bearish"
        else:
            signal = "neutral"
        
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
            "signal": signal
        }
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int, std_dev: float) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            return {"error": "Insufficient data for Bollinger Bands calculation"}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        current_price = prices[-1]
        
        # Generate signal
        if current_price > upper_band:
            signal = "overbought"
        elif current_price < lower_band:
            signal = "oversold"
        else:
            signal = "neutral"
        
        return {
            "upper_band": upper_band,
            "middle_band": sma,
            "lower_band": lower_band,
            "current_price": current_price,
            "signal": signal
        }
    
    def _calculate_stochastic(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> Dict[str, Any]:
        """Calculate Stochastic Oscillator."""
        if len(highs) < period:
            return {"error": "Insufficient data for Stochastic calculation"}
        
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            k_percent = 50
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Generate signal
        if k_percent > 80:
            signal = "overbought"
        elif k_percent < 20:
            signal = "oversold"
        else:
            signal = "neutral"
        
        return {
            "k_percent": k_percent,
            "signal": signal
        }
    
    async def _analyze_news_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment from news sources."""
        try:
            symbols = data.get("symbols", ["BTC"])
            max_articles = data.get("max_articles", 10)
            
            # Simulate news sentiment analysis (would integrate with real news APIs)
            sentiment_results = {}
            
            for symbol in symbols:
                # Simulate fetching news articles
                articles = [
                    f"Breaking: {symbol} shows strong momentum as institutional adoption increases",
                    f"{symbol} faces regulatory uncertainty in major markets",
                    f"Technical analysis suggests {symbol} may test key resistance levels",
                    f"Market sentiment for {symbol} remains cautiously optimistic"
                ]
                
                symbol_sentiment = {"positive": 0, "negative": 0, "neutral": 0}
                
                for article in articles[:max_articles]:
                    sentiment = await self._analyze_sentiment({"text": article})
                    
                    if sentiment.get("success"):
                        overall = sentiment["sentiment"]["overall"]
                        symbol_sentiment[overall] += 1
                
                total_articles = sum(symbol_sentiment.values())
                if total_articles > 0:
                    sentiment_scores = {
                        k: v / total_articles for k, v in symbol_sentiment.items()
                    }
                else:
                    sentiment_scores = {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
                
                sentiment_results[symbol] = {
                    "scores": sentiment_scores,
                    "articles_analyzed": total_articles,
                    "overall_sentiment": max(sentiment_scores, key=sentiment_scores.get)
                }
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "news_sentiment": sentiment_results,
                "symbols_analyzed": symbols,
                "timestamp": datetime.now().isoformat(),
                "note": "This is a demo implementation - integrate with real news APIs for production"
            }
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _assess_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess investment risk based on various factors."""
        try:
            portfolio_data = data.get("portfolio_data", {})
            market_data = data.get("market_data", {})
            risk_tolerance = data.get("risk_tolerance", "medium")  # low, medium, high
            
            if not portfolio_data:
                return {"success": False, "error": "No portfolio data provided"}
            
            risk_scores = {}
            overall_risk_factors = []
            
            # Calculate portfolio concentration risk
            total_value = sum(asset.get("value", 0) for asset in portfolio_data.values())
            max_allocation = max(asset.get("value", 0) for asset in portfolio_data.values()) if portfolio_data else 0
            concentration_ratio = max_allocation / total_value if total_value > 0 else 0
            
            if concentration_ratio > 0.5:
                overall_risk_factors.append("High concentration risk - largest position > 50%")
                concentration_risk = "high"
            elif concentration_ratio > 0.3:
                concentration_risk = "medium"
            else:
                concentration_risk = "low"
            
            # Calculate volatility risk
            volatility_scores = []
            for symbol, asset_data in portfolio_data.items():
                volatility = asset_data.get("volatility", 0)
                if volatility > 50:
                    volatility_scores.append("high")
                elif volatility > 25:
                    volatility_scores.append("medium")
                else:
                    volatility_scores.append("low")
            
            high_vol_count = volatility_scores.count("high")
            if high_vol_count > len(volatility_scores) / 2:
                volatility_risk = "high"
                overall_risk_factors.append("High volatility - majority of holdings are high-risk")
            elif high_vol_count > 0:
                volatility_risk = "medium"
            else:
                volatility_risk = "low"
            
            # Calculate liquidity risk (simplified)
            liquidity_risk = "low"  # Assume crypto is generally liquid
            
            # Market correlation risk
            correlation_risk = "medium"  # Simplified - crypto markets are highly correlated
            
            # Overall risk assessment
            risk_factors = [concentration_risk, volatility_risk, liquidity_risk, correlation_risk]
            high_risk_count = risk_factors.count("high")
            medium_risk_count = risk_factors.count("medium")
            
            if high_risk_count >= 2:
                overall_risk = "high"
            elif high_risk_count >= 1 or medium_risk_count >= 3:
                overall_risk = "medium"
            else:
                overall_risk = "low"
            
            # Risk tolerance match
            tolerance_levels = {"low": 0, "medium": 1, "high": 2}
            risk_levels = {"low": 0, "medium": 1, "high": 2}
            
            risk_match = tolerance_levels[risk_tolerance] >= risk_levels[overall_risk]
            
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return {
                "success": True,
                "risk_assessment": {
                    "overall_risk": overall_risk,
                    "risk_factors": {
                        "concentration": concentration_risk,
                        "volatility": volatility_risk,
                        "liquidity": liquidity_risk,
                        "correlation": correlation_risk
                    },
                    "risk_tolerance_match": risk_match,
                    "recommendations": overall_risk_factors,
                    "portfolio_metrics": {
                        "total_value": total_value,
                        "asset_count": len(portfolio_data),
                        "concentration_ratio": concentration_ratio,
                        "max_single_allocation": max_allocation
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_models_info(self) -> Dict[str, Any]:
        """Get information about available AI/ML models."""
        return {
            "success": True,
            "available_models": {
                "sentiment_analysis": {
                    "type": "keyword_based",
                    "accuracy": "moderate",
                    "description": "Rule-based sentiment analysis using financial keywords"
                },
                "pattern_recognition": {
                    "type": "technical_analysis",
                    "patterns": list(self.ta_patterns.keys()),
                    "description": "Candlestick and multi-candle pattern detection"
                },
                "price_prediction": {
                    "type": "trend_analysis",
                    "features": ["price_changes", "moving_averages", "volatility"],
                    "description": "Simple trend-based direction prediction"
                },
                "technical_indicators": {
                    "indicators": ["SMA", "RSI", "MACD", "Bollinger Bands", "Stochastic"],
                    "description": "Standard technical analysis indicators"
                }
            },
            "dependencies": {
                "numpy": self.numpy_available,
                "pandas": self.pandas_available,
                "requests": self.requests_available
            }
        }
    
    def _get_aiml_stats(self) -> Dict[str, Any]:
        """Get AI/ML statistics."""
        return {
            "total_analyses": self.analysis_count,
            "last_analysis_time": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "available_features": {
                "sentiment_analysis": True,
                "pattern_recognition": True,
                "technical_indicators": True,
                "price_prediction": True,
                "risk_assessment": True,
                "news_sentiment": True
            },
            "sentiment_keywords_count": {
                "positive": len(self.sentiment_keywords["positive"]),
                "negative": len(self.sentiment_keywords["negative"]),
                "neutral": len(self.sentiment_keywords["neutral"])
            },
            "technical_patterns_count": len(self.ta_patterns),
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }