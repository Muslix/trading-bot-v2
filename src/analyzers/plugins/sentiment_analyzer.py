"""
Sentiment Analysis Plugin for Crypto Trading Bot

This analyzer processes news, social media, and market sentiment to generate
trading signals. Features include:
- Multi-source sentiment aggregation (News, Twitter, Reddit)
- Real-time sentiment scoring
- Sentiment-to-signal conversion
- Historical sentiment tracking
- Market impact correlation
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import numpy as np

from ..base import BaseAnalyzer


class SentimentAnalyzer(BaseAnalyzer):
    """
    Advanced sentiment analyzer for cryptocurrency markets.
    
    Analyzes sentiment from multiple sources and converts it to actionable
    trading signals with confidence scores.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.sentiment_sources = config.get('sentiment_sources', ['news', 'social'])
        self.update_interval = config.get('update_interval_minutes', 15)
        self.sentiment_threshold = config.get('sentiment_threshold', 0.1)
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        
        # Sentiment scoring weights
        self.source_weights = {
            'news': 0.4,      # News articles have high impact
            'social': 0.3,    # Social media sentiment  
            'technical': 0.2, # Technical indicators sentiment
            'whale': 0.1      # Whale movement sentiment
        }
        
        # Sentiment history for trend analysis
        self.sentiment_history = {}
        self.signal_cache = {}
        
        # Keywords and patterns for sentiment analysis
        self.positive_keywords = {
            'strong': ['bullish', 'moon', 'pump', 'breakout', 'rally', 'surge', 'gains', 'bull run'],
            'medium': ['positive', 'growth', 'adoption', 'partnership', 'upgrade', 'development'],
            'weak': ['stable', 'holding', 'support', 'resistance']
        }
        
        self.negative_keywords = {
            'strong': ['bearish', 'crash', 'dump', 'collapse', 'panic', 'sell-off', 'bear market'],
            'medium': ['decline', 'drop', 'correction', 'uncertainty', 'regulation', 'ban'],
            'weak': ['caution', 'volatility', 'risk', 'concern']
        }
        
        # News API configuration (mock for demo)
        self.news_sources = [
            'coindesk.com',
            'cointelegraph.com', 
            'decrypt.co',
            'theblock.co',
            'cryptonews.com'
        ]
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis.
        
        Args:
            data: Market data including symbols and timeframe
            
        Returns:
            Sentiment analysis results with trading signals
        """
        try:
            self.logger.info("Starting sentiment analysis...")
            
            symbols = data.get('symbols', ['BTC', 'ETH', 'ADA', 'DOT'])
            timeframe = data.get('timeframe', '24h')
            
            # Gather sentiment data from multiple sources
            sentiment_results = {}
            
            for symbol in symbols:
                self.logger.debug(f"Analyzing sentiment for {symbol}")
                
                # Collect sentiment from all sources
                sentiment_scores = await self._collect_sentiment_scores(symbol, timeframe)
                
                # Calculate aggregated sentiment
                aggregated_sentiment = self._aggregate_sentiment(sentiment_scores)
                
                # Generate trading signals
                trading_signals = self._generate_trading_signals(symbol, aggregated_sentiment)
                
                # Store results
                sentiment_results[symbol] = {
                    'sentiment_scores': sentiment_scores,
                    'aggregated_sentiment': aggregated_sentiment,
                    'trading_signals': trading_signals,
                    'confidence': aggregated_sentiment.get('confidence', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Update sentiment history
                self._update_sentiment_history(symbol, aggregated_sentiment)
            
            # Market-wide sentiment analysis
            market_sentiment = self._analyze_market_sentiment(sentiment_results)
            
            # Generate analysis summary
            analysis_summary = {
                'total_symbols_analyzed': len(symbols),
                'strong_signals': len([r for r in sentiment_results.values() 
                                     if r['trading_signals'].get('strength', 0) > 0.7]),
                'market_sentiment': market_sentiment,
                'analysis_timestamp': datetime.now().isoformat(),
                'next_update': (datetime.now() + timedelta(minutes=self.update_interval)).isoformat()
            }
            
            self.logger.info(f"Sentiment analysis completed for {len(symbols)} symbols")
            
            return {
                'sentiment_results': sentiment_results,
                'market_sentiment': market_sentiment,
                'analysis_summary': analysis_summary,
                'trading_recommendations': self._generate_trading_recommendations(sentiment_results)
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return {'error': str(e), 'sentiment_results': {}}
    
    async def _collect_sentiment_scores(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Collect sentiment scores from multiple sources."""
        sentiment_scores = {}
        
        # News sentiment analysis
        if 'news' in self.sentiment_sources:
            news_sentiment = await self._analyze_news_sentiment(symbol, timeframe)
            sentiment_scores['news'] = news_sentiment
        
        # Social media sentiment
        if 'social' in self.sentiment_sources:
            social_sentiment = await self._analyze_social_sentiment(symbol, timeframe)
            sentiment_scores['social'] = social_sentiment
        
        # Technical indicator sentiment
        technical_sentiment = self._analyze_technical_sentiment(symbol)
        sentiment_scores['technical'] = technical_sentiment
        
        # Whale movement sentiment
        whale_sentiment = await self._analyze_whale_sentiment(symbol)
        sentiment_scores['whale'] = whale_sentiment
        
        return sentiment_scores
    
    async def _analyze_news_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment from news articles."""
        try:
            # In a real implementation, this would fetch actual news articles
            # For demo purposes, we'll simulate news sentiment analysis
            
            # Mock news articles for sentiment analysis
            mock_articles = [
                f"{symbol} shows strong bullish momentum amid institutional adoption",
                f"Market experts predict {symbol} breakthrough to new highs",
                f"{symbol} faces regulatory uncertainty but fundamentals remain strong",
                f"Major partnership announcement boosts {symbol} sentiment",
                f"{symbol} technical analysis suggests potential correction ahead"
            ]
            
            # Analyze sentiment for each article
            article_sentiments = []
            for article in mock_articles:
                sentiment_score = self._analyze_text_sentiment(article)
                article_sentiments.append(sentiment_score)
            
            # Calculate average sentiment
            if article_sentiments:
                avg_sentiment = np.mean(article_sentiments)
                sentiment_strength = abs(avg_sentiment)
                confidence = min(0.9, sentiment_strength + 0.3)
            else:
                avg_sentiment = 0.0
                confidence = 0.0
            
            return {
                'score': float(avg_sentiment),
                'confidence': float(confidence),
                'article_count': len(mock_articles),
                'source': 'news',
                'timeframe': timeframe
            }
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed for {symbol}: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    async def _analyze_social_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment from social media."""
        try:
            # Mock social media sentiment analysis
            # In reality, this would connect to Twitter API, Reddit API, etc.
            
            # Simulate social media posts
            mock_posts = [
                f"{symbol} to the moon! 🚀 Best investment of 2024",
                f"Just bought more {symbol}, this dip won't last long",
                f"{symbol} looking weak, might sell soon",
                f"HODL {symbol}! Diamond hands 💎🙌",
                f"{symbol} chart looks bullish, expecting breakout"
            ]
            
            # Analyze sentiment for each post
            post_sentiments = []
            for post in mock_posts:
                sentiment_score = self._analyze_text_sentiment(post)
                # Social media sentiment is often more extreme
                sentiment_score *= 1.2  # Amplify social sentiment
                post_sentiments.append(sentiment_score)
            
            # Calculate weighted average (recent posts have more weight)
            if post_sentiments:
                weights = np.linspace(0.5, 1.0, len(post_sentiments))  # Recent posts weighted higher
                avg_sentiment = np.average(post_sentiments, weights=weights)
                confidence = min(0.8, len(post_sentiments) / 10)  # More posts = higher confidence
            else:
                avg_sentiment = 0.0
                confidence = 0.0
            
            return {
                'score': float(avg_sentiment),
                'confidence': float(confidence),
                'post_count': len(mock_posts),
                'source': 'social',
                'timeframe': timeframe
            }
            
        except Exception as e:
            self.logger.error(f"Social sentiment analysis failed for {symbol}: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    def _analyze_technical_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze sentiment from technical indicators."""
        try:
            # Mock technical analysis sentiment
            # In reality, this would analyze RSI, MACD, moving averages, etc.
            
            # Simulate technical indicators
            rsi = np.random.uniform(20, 80)  # RSI value
            macd_signal = np.random.choice([-1, 0, 1])  # MACD signal
            ma_trend = np.random.choice([-1, 0, 1])  # Moving average trend
            
            # Calculate technical sentiment
            technical_signals = []
            
            # RSI sentiment
            if rsi < 30:
                technical_signals.append(0.3)  # Oversold = bullish
            elif rsi > 70:
                technical_signals.append(-0.3)  # Overbought = bearish
            else:
                technical_signals.append(0.0)  # Neutral
            
            # MACD sentiment
            technical_signals.append(macd_signal * 0.2)
            
            # Moving average sentiment
            technical_signals.append(ma_trend * 0.25)
            
            # Average technical sentiment
            avg_sentiment = np.mean(technical_signals)
            confidence = 0.7  # Technical analysis has good confidence
            
            return {
                'score': float(avg_sentiment),
                'confidence': float(confidence),
                'indicators': {
                    'rsi': float(rsi),
                    'macd_signal': int(macd_signal),
                    'ma_trend': int(ma_trend)
                },
                'source': 'technical'
            }
            
        except Exception as e:
            self.logger.error(f"Technical sentiment analysis failed for {symbol}: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    async def _analyze_whale_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze sentiment from whale movements and on-chain data."""
        try:
            # Mock whale movement analysis
            # In reality, this would analyze large transactions, whale wallets, etc.
            
            # Simulate whale activity
            large_transactions = np.random.randint(0, 10)  # Number of large transactions
            net_flow = np.random.uniform(-1000, 1000)  # Net flow to exchanges
            whale_accumulation = np.random.choice([True, False])  # Are whales accumulating?
            
            # Calculate whale sentiment
            sentiment_factors = []
            
            # Large transaction activity
            if large_transactions > 7:
                sentiment_factors.append(-0.2)  # High activity = potential selling
            elif large_transactions < 3:
                sentiment_factors.append(0.1)  # Low activity = holding
            
            # Exchange net flow
            if net_flow > 500:
                sentiment_factors.append(-0.3)  # Money flowing to exchanges = bearish
            elif net_flow < -500:
                sentiment_factors.append(0.3)  # Money flowing out = bullish
            
            # Whale accumulation
            if whale_accumulation:
                sentiment_factors.append(0.4)  # Whales accumulating = bullish
            else:
                sentiment_factors.append(-0.2)  # Whales not accumulating = bearish
            
            avg_sentiment = np.mean(sentiment_factors) if sentiment_factors else 0.0
            confidence = 0.6  # Whale data has medium confidence
            
            return {
                'score': float(avg_sentiment),
                'confidence': float(confidence),
                'whale_metrics': {
                    'large_transactions': int(large_transactions),
                    'net_flow': float(net_flow),
                    'whale_accumulation': bool(whale_accumulation)
                },
                'source': 'whale'
            }
            
        except Exception as e:
            self.logger.error(f"Whale sentiment analysis failed for {symbol}: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using keyword-based approach."""
        try:
            text_lower = text.lower()
            sentiment_score = 0.0
            
            # Check positive keywords
            for strength, keywords in self.positive_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        if strength == 'strong':
                            sentiment_score += 0.4
                        elif strength == 'medium':
                            sentiment_score += 0.2
                        else:  # weak
                            sentiment_score += 0.1
            
            # Check negative keywords
            for strength, keywords in self.negative_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        if strength == 'strong':
                            sentiment_score -= 0.4
                        elif strength == 'medium':
                            sentiment_score -= 0.2
                        else:  # weak
                            sentiment_score -= 0.1
            
            # Normalize to [-1, 1] range
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            return sentiment_score
            
        except Exception as e:
            self.logger.error(f"Text sentiment analysis failed: {e}")
            return 0.0
    
    def _aggregate_sentiment(self, sentiment_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate sentiment scores from multiple sources."""
        try:
            weighted_scores = []
            total_confidence = 0.0
            
            for source, score_data in sentiment_scores.items():
                if 'error' not in score_data:
                    weight = self.source_weights.get(source, 0.1)
                    score = score_data.get('score', 0.0)
                    confidence = score_data.get('confidence', 0.0)
                    
                    weighted_scores.append(score * weight * confidence)
                    total_confidence += weight * confidence
            
            # Calculate final sentiment
            if total_confidence > 0:
                final_sentiment = sum(weighted_scores) / total_confidence
                final_confidence = min(1.0, total_confidence)
            else:
                final_sentiment = 0.0
                final_confidence = 0.0
            
            # Determine sentiment category
            if final_sentiment > 0.3:
                category = 'bullish'
            elif final_sentiment < -0.3:
                category = 'bearish'
            else:
                category = 'neutral'
            
            return {
                'score': float(final_sentiment),
                'confidence': float(final_confidence),
                'category': category,
                'strength': abs(final_sentiment),
                'sources_count': len(sentiment_scores)
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment aggregation failed: {e}")
            return {'score': 0.0, 'confidence': 0.0, 'category': 'neutral'}
    
    def _generate_trading_signals(self, symbol: str, sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on sentiment analysis."""
        try:
            sentiment_score = sentiment.get('score', 0.0)
            confidence = sentiment.get('confidence', 0.0)
            
            # Only generate signals if confidence is above threshold
            if confidence < self.confidence_threshold:
                return {
                    'signal': 'hold',
                    'strength': 0.0,
                    'confidence': confidence,
                    'reason': 'Low confidence sentiment data'
                }
            
            # Generate signal based on sentiment score
            if sentiment_score > self.sentiment_threshold:
                signal_strength = min(1.0, sentiment_score * confidence)
                if signal_strength > 0.7:
                    signal = 'strong_buy'
                elif signal_strength > 0.4:
                    signal = 'buy'
                else:
                    signal = 'weak_buy'
            elif sentiment_score < -self.sentiment_threshold:
                signal_strength = min(1.0, abs(sentiment_score) * confidence)
                if signal_strength > 0.7:
                    signal = 'strong_sell'
                elif signal_strength > 0.4:
                    signal = 'sell'
                else:
                    signal = 'weak_sell'
            else:
                signal = 'hold'
                signal_strength = confidence * 0.5
            
            # Add historical context
            historical_context = self._get_historical_context(symbol, sentiment_score)
            
            return {
                'signal': signal,
                'strength': float(signal_strength),
                'confidence': float(confidence),
                'sentiment_score': float(sentiment_score),
                'historical_context': historical_context,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Signal generation failed for {symbol}: {e}")
            return {'signal': 'hold', 'strength': 0.0, 'confidence': 0.0, 'error': str(e)}
    
    def _update_sentiment_history(self, symbol: str, sentiment: Dict[str, Any]):
        """Update sentiment history for trend analysis."""
        try:
            if symbol not in self.sentiment_history:
                self.sentiment_history[symbol] = []
            
            # Add current sentiment to history
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'score': sentiment.get('score', 0.0),
                'confidence': sentiment.get('confidence', 0.0),
                'category': sentiment.get('category', 'neutral')
            }
            
            self.sentiment_history[symbol].append(history_entry)
            
            # Keep only last 100 entries
            if len(self.sentiment_history[symbol]) > 100:
                self.sentiment_history[symbol] = self.sentiment_history[symbol][-100:]
                
        except Exception as e:
            self.logger.error(f"Failed to update sentiment history for {symbol}: {e}")
    
    def _get_historical_context(self, symbol: str, current_sentiment: float) -> Dict[str, Any]:
        """Get historical context for sentiment analysis."""
        try:
            if symbol not in self.sentiment_history:
                return {'trend': 'unknown', 'deviation': 0.0}
            
            history = self.sentiment_history[symbol]
            if len(history) < 3:
                return {'trend': 'insufficient_data', 'deviation': 0.0}
            
            # Calculate trend
            recent_scores = [entry['score'] for entry in history[-10:]]
            if len(recent_scores) >= 3:
                trend_slope = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                if trend_slope > 0.05:
                    trend = 'improving'
                elif trend_slope < -0.05:
                    trend = 'deteriorating'
                else:
                    trend = 'stable'
            else:
                trend = 'unknown'
            
            # Calculate deviation from historical average
            historical_avg = np.mean([entry['score'] for entry in history])
            deviation = current_sentiment - historical_avg
            
            return {
                'trend': trend,
                'deviation': float(deviation),
                'historical_average': float(historical_avg),
                'data_points': len(history)
            }
            
        except Exception as e:
            self.logger.error(f"Historical context analysis failed for {symbol}: {e}")
            return {'trend': 'error', 'deviation': 0.0}
    
    def _analyze_market_sentiment(self, sentiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market sentiment."""
        try:
            if not sentiment_results:
                return {'overall': 'neutral', 'confidence': 0.0}
            
            # Calculate market-wide metrics
            all_scores = []
            all_confidences = []
            categories = {'bullish': 0, 'bearish': 0, 'neutral': 0}
            
            for symbol, result in sentiment_results.items():
                sentiment = result.get('aggregated_sentiment', {})
                score = sentiment.get('score', 0.0)
                confidence = sentiment.get('confidence', 0.0)
                category = sentiment.get('category', 'neutral')
                
                all_scores.append(score)
                all_confidences.append(confidence)
                categories[category] += 1
            
            # Calculate overall market sentiment
            if all_scores:
                market_score = np.mean(all_scores)
                market_confidence = np.mean(all_confidences)
                
                if market_score > 0.2:
                    overall_sentiment = 'bullish'
                elif market_score < -0.2:
                    overall_sentiment = 'bearish'
                else:
                    overall_sentiment = 'neutral'
            else:
                market_score = 0.0
                market_confidence = 0.0
                overall_sentiment = 'neutral'
            
            return {
                'overall': overall_sentiment,
                'score': float(market_score),
                'confidence': float(market_confidence),
                'distribution': categories,
                'fear_greed_index': self._calculate_fear_greed_index(market_score, categories)
            }
            
        except Exception as e:
            self.logger.error(f"Market sentiment analysis failed: {e}")
            return {'overall': 'neutral', 'confidence': 0.0, 'error': str(e)}
    
    def _calculate_fear_greed_index(self, market_score: float, categories: Dict[str, int]) -> int:
        """Calculate a simplified Fear & Greed Index (0-100)."""
        try:
            # Base score from sentiment
            base_score = (market_score + 1) * 50  # Convert from [-1,1] to [0,100]
            
            # Adjust based on category distribution
            total_assets = sum(categories.values())
            if total_assets > 0:
                bullish_ratio = categories['bullish'] / total_assets
                bearish_ratio = categories['bearish'] / total_assets
                
                # Extreme fear or greed adjustments
                if bullish_ratio > 0.8:
                    base_score = min(100, base_score + 20)  # Extreme greed
                elif bearish_ratio > 0.8:
                    base_score = max(0, base_score - 20)  # Extreme fear
            
            return int(max(0, min(100, base_score)))
            
        except Exception as e:
            self.logger.error(f"Fear & Greed index calculation failed: {e}")
            return 50  # Neutral
    
    def _generate_trading_recommendations(self, sentiment_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable trading recommendations."""
        try:
            recommendations = []
            
            for symbol, result in sentiment_results.items():
                signals = result.get('trading_signals', {})
                sentiment = result.get('aggregated_sentiment', {})
                
                signal = signals.get('signal', 'hold')
                strength = signals.get('strength', 0.0)
                confidence = signals.get('confidence', 0.0)
                
                if confidence > self.confidence_threshold and strength > 0.5:
                    recommendation = {
                        'symbol': symbol,
                        'action': signal,
                        'strength': strength,
                        'confidence': confidence,
                        'reasoning': self._generate_recommendation_reasoning(symbol, sentiment, signals),
                        'risk_level': self._assess_recommendation_risk(sentiment, signals),
                        'time_horizon': self._estimate_time_horizon(sentiment),
                        'priority': self._calculate_priority(strength, confidence)
                    }
                    
                    recommendations.append(recommendation)
            
            # Sort by priority
            recommendations.sort(key=lambda x: x['priority'], reverse=True)
            
            return recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            self.logger.error(f"Trading recommendations generation failed: {e}")
            return []
    
    def _generate_recommendation_reasoning(self, symbol: str, sentiment: Dict, signals: Dict) -> str:
        """Generate human-readable reasoning for recommendations."""
        try:
            category = sentiment.get('category', 'neutral')
            score = sentiment.get('score', 0.0)
            confidence = sentiment.get('confidence', 0.0)
            signal = signals.get('signal', 'hold')
            
            reasoning_parts = []
            
            # Sentiment-based reasoning
            if category == 'bullish':
                reasoning_parts.append(f"Strong positive sentiment detected ({score:.2f})")
            elif category == 'bearish':
                reasoning_parts.append(f"Negative sentiment prevailing ({score:.2f})")
            else:
                reasoning_parts.append("Neutral market sentiment")
            
            # Confidence-based reasoning
            if confidence > 0.8:
                reasoning_parts.append("High confidence in analysis")
            elif confidence > 0.6:
                reasoning_parts.append("Moderate confidence")
            else:
                reasoning_parts.append("Low confidence - proceed with caution")
            
            # Signal-specific reasoning
            if 'strong' in signal:
                reasoning_parts.append("Multiple indicators align for strong signal")
            elif signal in ['buy', 'sell']:
                reasoning_parts.append("Clear directional bias identified")
            
            return ". ".join(reasoning_parts) + "."
            
        except Exception as e:
            return f"Analysis available but reasoning generation failed: {e}"
    
    def _assess_recommendation_risk(self, sentiment: Dict, signals: Dict) -> str:
        """Assess risk level of recommendation."""
        try:
            confidence = sentiment.get('confidence', 0.0)
            strength = signals.get('strength', 0.0)
            
            if confidence > 0.8 and strength > 0.7:
                return 'low'
            elif confidence > 0.6 and strength > 0.5:
                return 'medium'
            else:
                return 'high'
                
        except Exception:
            return 'high'
    
    def _estimate_time_horizon(self, sentiment: Dict) -> str:
        """Estimate optimal time horizon for trade."""
        try:
            strength = sentiment.get('strength', 0.0)
            
            if strength > 0.8:
                return 'short_term'  # 1-7 days
            elif strength > 0.5:
                return 'medium_term'  # 1-4 weeks
            else:
                return 'long_term'  # 1-3 months
                
        except Exception:
            return 'medium_term'
    
    def _calculate_priority(self, strength: float, confidence: float) -> float:
        """Calculate recommendation priority score."""
        return strength * confidence
    
    def get_analyzer_type(self) -> str:
        """Return analyzer type."""
        return "sentiment"
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get analyzer performance metrics."""
        try:
            total_analyses = getattr(self, '_total_analyses', 0)
            successful_analyses = getattr(self, '_successful_analyses', 0)
            total_signals = getattr(self, '_total_signals', 0)
            
            success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
            
            return {
                'total_analyses': total_analyses,
                'success_rate': success_rate,
                'total_signals_generated': total_signals,
                'sources_monitored': len(self.sentiment_sources),
                'update_interval_minutes': self.update_interval,
                'sentiment_threshold': self.sentiment_threshold,
                'confidence_threshold': self.confidence_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Performance metrics calculation failed: {e}")
            return {'error': str(e)}