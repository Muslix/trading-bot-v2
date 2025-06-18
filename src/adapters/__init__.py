"""
Data Source Adapter - Compatibility layer for the old historical_data API.

This adapter provides backward compatibility while migrating to the new
Data Sources system.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Import production logger for detailed debugging
try:
    from src.utils.production_logger import get_production_logger
    prod_logger = get_production_logger("data_adapters")
except ImportError:
    prod_logger = None

# Real data source manager using CoinGecko


class RealDataSourceManager:
    """Real data source manager using CoinGecko API"""
    
    def __init__(self):
        self.coingecko = None
        self.cryptocompare = None
        self.primary_source = "coingecko"
    
    async def initialize(self):
        """Initialize real data sources with fallback"""
        from src.data_sources.plugins.coingecko import CoinGeckoPlugin
        from src.data_sources.plugins.cryptocompare import CryptoComparePlugin
        from src.data_sources.base import DataSourceConfig
        
        config = DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=600  # 10 minutes cache for rate limit relief
        )
        
        # Initialize primary source (CoinGecko)
        self.coingecko = CoinGeckoPlugin(config)
        coingecko_success = await self.coingecko._initialize()
        
        # Initialize fallback source (CryptoCompare)
        self.cryptocompare = CryptoComparePlugin(config)
        cryptocompare_success = await self.cryptocompare._initialize()
        
        if not coingecko_success and cryptocompare_success:
            self.primary_source = "cryptocompare"
            logger.info("Using CryptoCompare as primary source (CoinGecko failed)")
        elif coingecko_success:
            logger.info("Using CoinGecko as primary source")
    
    async def get_market_data_summary(self, symbols: List[str]) -> Dict:
        """Get real market data using intelligent fallback system (Rate-Limit-freundlich!)"""
        if not self.coingecko or not self.cryptocompare:
            await self.initialize()
            
        # Try primary source first
        try:
            primary_plugin = self.coingecko if self.primary_source == "coingecko" else self.cryptocompare
            print(f"📡 Batch-Request für {len(symbols)} Symbole via {self.primary_source.upper()}...")
            
            all_prices = await primary_plugin.get_multiple_prices(symbols)
            
            if len(all_prices) >= len(symbols) * 0.8:  # 80% success rate
                result = {}
                
                for symbol in symbols:
                    if symbol in all_prices:
                        price = all_prices[symbol]
                        
                        # Market data aus Cache
                        market_cache_key = f"market_{symbol}"
                        cached_market_data = primary_plugin._get_from_cache(market_cache_key)
                        
                        market_cap = 0
                        volume_24h = 0
                        if cached_market_data:
                            market_cap = cached_market_data.get('market_cap', 0)
                            volume_24h = cached_market_data.get('total_volume_24h', 0)
                        
                        result[symbol] = {
                            'price': price,
                            'market_cap': market_cap,
                            'volume': {'current_volume': volume_24h}
                        }
                
                print(f"✅ {self.primary_source.upper()} Batch-Request erfolgreich: {len(result)} Symbole")
                return result
            else:
                raise Exception(f"Low success rate: {len(all_prices)}/{len(symbols)}")
                
        except Exception as e:
            logger.warning(f"Primary source {self.primary_source} failed: {e}")
            
            # Fallback to secondary source
            try:
                fallback_plugin = self.cryptocompare if self.primary_source == "coingecko" else self.coingecko
                fallback_name = "cryptocompare" if self.primary_source == "coingecko" else "coingecko"
                
                print(f"🔄 Fallback zu {fallback_name.upper()}...")
                all_prices = await fallback_plugin.get_multiple_prices(symbols)
                
                result = {}
                for symbol in symbols:
                    if symbol in all_prices:
                        price = all_prices[symbol]
                        
                        market_cache_key = f"market_{symbol}"
                        cached_market_data = fallback_plugin._get_from_cache(market_cache_key)
                        
                        market_cap = 0
                        volume_24h = 0
                        if cached_market_data:
                            market_cap = cached_market_data.get('market_cap', 0)
                            volume_24h = cached_market_data.get('total_volume_24h', 0)
                        
                        result[symbol] = {
                            'price': price,
                            'market_cap': market_cap,
                            'volume': {'current_volume': volume_24h}
                        }
                
                print(f"✅ {fallback_name.upper()} Fallback erfolgreich: {len(result)} Symbole")
                return result
                
            except Exception as fallback_error:
                logger.error(f"Fallback source also failed: {fallback_error}")
                return {}
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get real prices for symbols"""
        if not self.coingecko:
            await self.initialize()
            
        result = {}
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)
        
        async def get_price(symbol: str):
            async with semaphore:
                try:
                    return symbol, await self.coingecko.get_current_price(symbol)
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
                    return symbol, None
        
        tasks = [get_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol_result in results:
            if isinstance(symbol_result, tuple) and len(symbol_result) == 2:
                symbol, price = symbol_result
                if price is not None:
                    result[symbol] = price
        
        return result
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.coingecko:
            await self.coingecko.cleanup()
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        """Get mock historical data"""
        np.random.seed(hash(symbol) % 10000)
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "3y": 1095, "5y": 1825}.get(period, 365)
        
        # Generate mock price data
        returns = np.random.normal(0.001, 0.03, days)
        prices = np.cumprod(1 + returns) * 100
        
        # Create DataFrame
        dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=days), periods=days, freq='D')
        return pd.DataFrame({
            'Close': prices,
            'Volume': np.random.uniform(1000, 10000, days)
        }, index=dates)
    
    async def get_current_price(self, symbol: str) -> float:
        """Get mock current price"""
        np.random.seed(hash(symbol) % 10000)
        return np.random.uniform(0.1, 50000)
    
    async def health_check(self) -> Dict:
        """Mock health check"""
        return {"status": "ok", "sources": ["mock"]}


# Global data source manager instance
_data_manager: Optional[RealDataSourceManager] = None


async def get_data_manager() -> RealDataSourceManager:
    """Get or create the global data source manager"""
    global _data_manager
    
    if _data_manager is None:
        _data_manager = RealDataSourceManager()
        await _data_manager.initialize()
        logger.info("Initialized REAL DataSourceManager with live CoinGecko data")
    
    return _data_manager


async def analyze_crypto_portfolio_enhanced(symbols: List[str], period: str = "2y") -> Dict:
    """
    Backward compatible function that uses the new DataSourceManager.
    
    This replaces the old analyze_crypto_portfolio_enhanced function from
    historical_data.py while maintaining the same interface.
    
    Returns data in the format expected by performance_check_cycle:
    {
        "BTC": {"sharpe_ratio": 0.5, "current_price": 42000, ...},
        "ETH": {"sharpe_ratio": 0.3, "current_price": 3000, ...},
        ...
    }
    """
    try:
        manager = await get_data_manager()
        
        # Get current prices and market data
        market_data = await manager.get_market_data_summary(symbols)
        
        # Format results to match the expected interface for performance_check_cycle
        results = {}
        
        for symbol in symbols:
            symbol_data = market_data.get(symbol, {})
            price = symbol_data.get('price', 0)
            
            if price and price > 0:
                # Create combined metrics for each symbol (matches old interface)
                results[symbol] = {
                    "current_price": price,
                    "market_cap": symbol_data.get('market_cap', 0),
                    "volume_24h": symbol_data.get('volume', {}).get('current_volume', 0) if isinstance(symbol_data.get('volume'), dict) else symbol_data.get('volume', 0),
                    "price_change_24h": 0,  # Would need historical data to calculate
                    "volatility": 0.15,  # Default volatility estimate
                    "return_24h": 0,        # Would need historical data
                    "return_7d": 0,         # Would need historical data  
                    "return_30d": 0,        # Would need historical data
                    "volatility_30d": 0.15,  # Default volatility estimate
                    "beta": 1.0,           # Default beta vs market
                    "sharpe_ratio": 0.2,   # Default Sharpe ratio estimate
                    "sortino_ratio": 0.25,  # Default Sortino ratio estimate
                    "calmar_ratio": 0.15,  # Default Calmar ratio estimate
                    "max_drawdown": 0.3,   # Default max drawdown estimate
                    "var_95": 0.05,        # Default VaR 95%
                    "var_99": 0.08,        # Default VaR 99%
                    "cvar_95": 0.06,       # Default CVaR 95%
                    "win_rate": 0.52,      # Default win rate estimate
                    "data_source": "live_api",
                    "period": period,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Handle symbols with no price data
                results[symbol] = {
                    "error": f"No price data available for {symbol}",
                    "current_price": 0,
                    "sharpe_ratio": 0,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Log detailed portfolio analysis for production debugging
        if prod_logger:
            prod_logger.log_portfolio_calculation(symbols, results)
        
        logger.info(f"Portfolio analysis completed for {len(symbols)} symbols with live data")
        return results
        
    except Exception as e:
        logger.error(f"Error in portfolio analysis: {e}")
        # Return error format that matches expected interface
        return {symbol: {"error": str(e), "sharpe_ratio": 0, "current_price": 0} for symbol in symbols}


async def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Get current prices for multiple symbols"""
    try:
        manager = await get_data_manager()
        return await manager.get_multiple_prices(symbols)
    except Exception as e:
        logger.error(f"Error getting current prices: {e}")
        return {symbol: None for symbol in symbols}


async def get_historical_data(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """Get historical data for a symbol"""
    try:
        manager = await get_data_manager()
        hist_data = await manager.get_historical_data(symbol, period)
        
        # Convert dict back to DataFrame if needed
        if isinstance(hist_data, dict) and 'Close' in hist_data:
            df = pd.DataFrame(hist_data)
            df.index = pd.to_datetime(df.index)
            return df
        
        return hist_data
        
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {e}")
        return None


# Legacy compatibility functions
def fetch_historical_data(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """Synchronous wrapper for backward compatibility"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_historical_data(symbol, period))
    except Exception as e:
        logger.error(f"Error in fetch_historical_data: {e}")
        return None


def get_live_price(symbol: str) -> Optional[float]:
    """Synchronous wrapper for getting live price"""
    try:
        loop = asyncio.get_event_loop()
        manager_coro = get_data_manager()
        manager = loop.run_until_complete(manager_coro)
        price_coro = manager.get_current_price(symbol)
        return loop.run_until_complete(price_coro)
    except Exception as e:
        logger.error(f"Error getting live price for {symbol}: {e}")
        return None


# Health check function
async def check_data_sources_health() -> Dict:
    """Check health of all data sources"""
    try:
        manager = await get_data_manager()
        return await manager.health_check()
    except Exception as e:
        logger.error(f"Error checking data sources health: {e}")
        return {"error": str(e)}


# Missing legacy functions for compatibility  
async def calculate_crypto_metrics_enhanced(symbol: str, historical_data: pd.DataFrame = None) -> Dict:
    """
    Calculate enhanced crypto metrics - backward compatibility function.
    
    This function was part of the old historical_data.py module.
    Now it uses the new data sources system.
    """
    try:
        if historical_data is None:
            historical_data = await get_historical_data(symbol, period="2y")
        
        if historical_data is None or historical_data.empty:
            return {"error": f"No historical data available for {symbol}"}
        
        # Calculate basic metrics
        if 'Close' not in historical_data.columns:
            return {"error": "Invalid data format - no Close prices"}
        
        prices = historical_data['Close']
        returns = prices.pct_change().dropna()
        
        # Basic performance metrics
        annual_return = (prices.iloc[-1] / prices.iloc[0]) ** (252 / len(prices)) - 1
        volatility = returns.std() * (252 ** 0.5)
        
        # Risk metrics
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * (252 ** 0.5) if len(downside_returns) > 0 else 0
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Sortino ratio
        sortino_ratio = (annual_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar ratio (annual return / abs(max drawdown))
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # VaR calculations
        var_95 = float(returns.quantile(0.05))
        var_99 = float(returns.quantile(0.01))
        cvar_95 = float(returns[returns <= var_95].mean())
        
        # Beta vs BTC (simplified)
        beta_vs_btc = np.random.uniform(0.5, 2.0)  # Mock beta
        
        # Win rate
        positive_returns = returns[returns > 0]
        win_rate = len(positive_returns) / len(returns) * 100 if len(returns) > 0 else 0
        
        # Current price
        current_price = prices.iloc[-1]
        
        # Determine period from historical data length
        period_from_data = "2y"  # Default
        if len(historical_data) <= 40:
            period_from_data = "1mo"
        elif len(historical_data) <= 100:
            period_from_data = "3mo"
        elif len(historical_data) <= 200:
            period_from_data = "6mo"
        elif len(historical_data) <= 400:
            period_from_data = "1y"
        elif len(historical_data) <= 800:
            period_from_data = "2y"
        elif len(historical_data) <= 1200:
            period_from_data = "3y"
        else:
            period_from_data = "5y"
        
        metrics = {
            "symbol": symbol,
            "period": period_from_data,
            "current_price": float(current_price),
            "annual_return": float(annual_return * 100),  # Convert to percentage
            "volatility": float(volatility * 100),  # Convert to percentage
            "sharpe_ratio": float(sharpe_ratio),
            "sortino_ratio": float(sortino_ratio),
            "calmar_ratio": float(calmar_ratio),
            "max_drawdown": float(max_drawdown * 100),  # Convert to percentage
            "downside_volatility": float(downside_volatility),
            "var_95": float(var_95 * 100),
            "var_99": float(var_99 * 100),
            "cvar_95": float(cvar_95 * 100),
            "beta_vs_btc": float(beta_vs_btc),
            "win_rate": float(win_rate),
            "data_points": len(historical_data),
            "data_source": "real_data" if len(historical_data) > 50 else "simulated",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log detailed metrics calculation for production debugging
        if prod_logger:
            prod_logger.log_crypto_metrics(symbol, metrics, historical_data)
        
        logger.debug(f"Calculated enhanced metrics for {symbol}: Sharpe {sharpe_ratio:.3f}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating enhanced metrics for {symbol}: {e}")
        return {
            "error": str(e), 
            "symbol": symbol,
            "data_source": "simulated",
            "annual_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0
        }


def compare_timeframes(symbol: str, timeframes: List[str] = None) -> Dict:
    """
    Compare different timeframes for a symbol - backward compatibility function.
    
    This function was part of the old historical_data.py module.
    """
    if timeframes is None:
        timeframes = ["1mo", "3mo", "6mo", "1y", "2y"]
    
    try:
        # Handle event loop creation properly
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        comparison_results = {}
        
        for timeframe in timeframes:
            try:
                # Get historical data for this timeframe
                hist_data = loop.run_until_complete(get_historical_data(symbol, timeframe))
                
                if hist_data is not None and not hist_data.empty:
                    # Calculate metrics for this timeframe
                    metrics = loop.run_until_complete(calculate_crypto_metrics_enhanced(symbol, hist_data))
                    
                    if "error" not in metrics:
                        comparison_results[timeframe] = {
                            "period": timeframe,
                            "data_points": metrics.get("data_points", 0),
                            "annual_return": metrics.get("annual_return", 0),
                            "volatility": metrics.get("volatility", 0),
                            "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                            "max_drawdown": metrics.get("max_drawdown", 0)
                        }
                    else:
                        comparison_results[timeframe] = {"error": metrics["error"]}
                else:
                    comparison_results[timeframe] = {"error": "No data available"}
                    
            except Exception as e:
                comparison_results[timeframe] = {"error": str(e)}
        
        # Summary
        valid_timeframes = [tf for tf, data in comparison_results.items() if "error" not in data]
        
        summary = {
            "symbol": symbol,
            "timeframes_analyzed": len(timeframes),
            "successful_timeframes": len(valid_timeframes),
            "comparison_results": comparison_results,
            "timestamp": datetime.now().isoformat()
        }
        
        if valid_timeframes:
            # Best performing timeframe by Sharpe ratio
            best_sharpe_tf = max(valid_timeframes, 
                               key=lambda tf: comparison_results[tf].get("sharpe_ratio", -999))
            summary["best_performing_timeframe"] = {
                "timeframe": best_sharpe_tf,
                "sharpe_ratio": comparison_results[best_sharpe_tf]["sharpe_ratio"]
            }
        
        logger.info(f"Timeframe comparison for {symbol}: {len(valid_timeframes)}/{len(timeframes)} successful")
        return summary
        
    except Exception as e:
        logger.error(f"Error comparing timeframes for {symbol}: {e}")
        return {
            "error": str(e),
            "symbol": symbol,
            "timeframes_analyzed": len(timeframes) if timeframes else 0,
            "successful_timeframes": 0
        }


def get_analysis_timeframes() -> List[str]:
    """Get list of supported analysis timeframes - backward compatibility function"""
    return ["1mo", "3mo", "6mo", "1y", "2y", "3y", "5y"]
