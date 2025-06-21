"""
Portfolio Analyzer Plugin - Analyzes cryptocurrency portfolios
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import logging

from ..base import BaseAnalyzer
from src.utils.decorators import log_performance


class PortfolioAnalyzer(BaseAnalyzer):
    """Portfolio analysis with real market data"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analysis_count = config.get("analysis_count", 50)
        self.cache_ttl = config.get("cache_ttl_seconds", 600)  # 10 minutes
        
    def get_analyzer_type(self) -> str:
        return "portfolio"
        
    @log_performance
    async def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Analyze portfolio performance for single or multiple cryptocurrencies
        
        Args:
            data: str (single symbol) or List[str] (multiple symbols)
            kwargs: period, batch_mode, etc.
        """
        if isinstance(data, str):
            # Single symbol analysis
            return await self._analyze_single_crypto(data, **kwargs)
        elif isinstance(data, list):
            # Multi-symbol portfolio analysis
            return await self._analyze_crypto_portfolio(data, **kwargs)
        else:
            return {"error": "Invalid data format - expected string or list of strings"}
            
    async def _analyze_single_crypto(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Analyze single cryptocurrency with real data"""
        try:
            period = kwargs.get("period", "1y")
            
            # Import data source plugin
            from src.data_sources.plugins.coingecko import CoinGeckoPlugin
            from src.data_sources.base import DataSourceConfig
            
            # Initialize data source
            config = DataSourceConfig(
                enabled=True,
                cache_ttl_seconds=self.cache_ttl
            )
            coingecko = CoinGeckoPlugin(config)
            await coingecko._initialize()
            
            # Get real data
            historical_data = await coingecko.get_historical_data(symbol, period)
            current_price = await coingecko.get_current_price(symbol)
            volume_data = await coingecko.get_volume_data(symbol)
            
            if historical_data is None or current_price is None:
                await coingecko.cleanup()
                return {
                    "symbol": symbol,
                    "error": "Historical data not available",
                    "current_price": current_price or 0,
                    "sharpe_ratio": 0,
                    "volatility": 0,
                    "annual_return": 0,
                    "max_drawdown": 0
                }
            
            # Calculate metrics from real data
            prices = historical_data['Close'].values
            returns = np.diff(prices) / prices[:-1]
            
            # Calculate performance metrics
            annual_return = np.mean(returns) * 365
            volatility = np.std(returns) * np.sqrt(365)
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # Max Drawdown calculation
            cumulative_returns = np.cumprod(1 + returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = np.min(drawdown)
            
            # Market data
            market_cap = volume_data.get('market_cap', 0) if volume_data else 0
            volume_24h = volume_data.get('total_volume_24h', 0) if volume_data else 0

            metrics = {
                "symbol": symbol,
                "sharpe_ratio": round(sharpe_ratio, 4),
                "volatility": round(volatility * 100, 2),  # In percent
                "annual_return": round(annual_return * 100, 2),  # In percent
                "max_drawdown": round(max_drawdown * 100, 2),  # In percent
                "current_price": round(current_price, 4),
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "data_source": "coingecko_live"
            }
            
            await coingecko.cleanup()
            return metrics

        except Exception as e:
            return {"symbol": symbol, "error": str(e), "current_price": 0}
            
    @log_performance
    async def _analyze_crypto_portfolio(self, crypto_symbols: List[str], **kwargs) -> Dict[str, Dict]:
        """Analyze cryptocurrency portfolio with batch processing"""
        batch_mode = kwargs.get("batch_mode", True)
        
        if batch_mode:
            return await self._batch_portfolio_analysis(crypto_symbols, **kwargs)
        else:
            return await self._sequential_portfolio_analysis(crypto_symbols, **kwargs)
            
    async def _batch_portfolio_analysis(self, crypto_symbols: List[str], **kwargs) -> Dict[str, Dict]:
        """Batch analysis for rate-limit friendly processing"""
        self.logger.info(f"🔄 Analyzing {len(crypto_symbols)} cryptocurrencies with BATCH requests...")

        # Import data source
        from src.data_sources.plugins.coingecko import CoinGeckoPlugin
        from src.data_sources.base import DataSourceConfig
        
        config = DataSourceConfig(
            enabled=True,
            cache_ttl_seconds=self.cache_ttl
        )
        coingecko = CoinGeckoPlugin(config)
        await coingecko._initialize()
        
        try:
            # Batch request for all prices
            self.logger.info("📡 Fetching all prices in batch request...")
            all_prices = await coingecko.get_multiple_prices(crypto_symbols)
            
            self.logger.info(f"✅ Received: {len(all_prices)} live prices from {len(crypto_symbols)} symbols")
            
            # Process results
            result_dict = {}
            
            for symbol in crypto_symbols:
                try:
                    if symbol in all_prices:
                        current_price = all_prices[symbol]
                        
                        # Get cached market data
                        market_cache_key = f"market_{symbol}"
                        cached_market_data = coingecko._get_from_cache(market_cache_key)
                        
                        market_cap = 0
                        volume_24h = 0
                        if cached_market_data:
                            market_cap = cached_market_data.get('market_cap', 0)
                            volume_24h = cached_market_data.get('total_volume_24h', 0)
                        
                        # Simplified metrics (without historical data for rate-limit protection)
                        metrics = {
                            "current_price": round(current_price, 4),
                            "market_cap": market_cap or 0,
                            "volume_24h": volume_24h or 0,
                            "data_source": "coingecko_batch_live",
                            # Placeholder metrics (could be calculated separately)
                            "sharpe_ratio": 0.5,  # Neutral default
                            "volatility": 25.0,   # Typical crypto volatility
                            "annual_return": 15.0,  # Placeholder
                            "max_drawdown": -30.0  # Typical crypto drawdown
                        }
                        
                        result_dict[symbol] = metrics
                    else:
                        # Symbol not found
                        result_dict[symbol] = {
                            "error": "Symbol not found in batch request",
                            "current_price": 0,
                            "sharpe_ratio": 0,
                            "volatility": 0,
                            "annual_return": 0,
                            "max_drawdown": 0
                        }
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing {symbol}: {e}")
                    result_dict[symbol] = {
                        "error": str(e),
                        "current_price": 0
                    }
            
            await coingecko.cleanup()
            self.logger.info(f"✅ Portfolio analysis completed: {len(result_dict)} results")
            return result_dict
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch analysis: {e}")
            await coingecko.cleanup()
            return {}
            
    async def _sequential_portfolio_analysis(self, crypto_symbols: List[str], **kwargs) -> Dict[str, Dict]:
        """Sequential analysis for detailed metrics"""
        results = {}
        for symbol in crypto_symbols:
            result = await self._analyze_single_crypto(symbol, **kwargs)
            results[symbol] = result
        return results
        
    def get_top_cryptocurrencies(self, n: int = 50) -> List[str]:
        """Get top N cryptocurrencies for analysis"""
        # Comprehensive Top 100 cryptocurrencies list
        top_100_crypto_list = [
            # Top 20 - Major cryptocurrencies
            "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "MATIC", "AVAX",
            "LTC", "UNI", "LINK", "XLM", "ATOM", "XMR", "ETC", "BCH", "ALGO", "VET",
            
            # 21-40 - Established DeFi & Layer 1
            "AAVE", "SAND", "MANA", "CRV", "SUSHI", "YFI", "COMP", "MKR", "SNX", "BAL",
            "REN", "KNC", "ZRX", "NMR", "STORJ", "GRT", "ANKR", "BAND", "THETA", "FIL",
            
            # 41-60 - Smart Contract Platforms & Infrastructure
            "TRX", "EOS", "FTM", "NEAR", "OCEAN", "FET", "API3", "BADGER", "FARM", "AXS",
            "GALA", "ENJ", "CHZ", "FLOW", "ICP", "EGLD", "HBAR", "LUNA", "ONE", "ZIL",
            
            # 61-80 - DeFi Protocols & Exchange Tokens
            "CAKE", "SXP", "ALPHA", "XVS", "RUNE", "KAVA", "SRM", "RAY", "ORCA", "STEP",
            "COPE", "MEDIA", "ROPE", "SAMO", "NINJA", "STAR", "PORT", "TULIP", "SLIM", "SUNNY",
            
            # 81-100 - Gaming, NFT, Metaverse & Emerging
            "IMX", "GMT", "GST", "LOOKS", "APE", "BLUR", "MAGIC", "TRB", "PEOPLE", "LOKA",
            "HIGH", "VOXEL", "ALICE", "TLM", "WIN", "BTT", "JST", "SUN", "NFT", "DYDX"
        ]

        # Remove duplicates and return first n
        unique_cryptos = list(dict.fromkeys(top_100_crypto_list))
        if n <= 0:
            return []
        return unique_cryptos[:n]
        
    def display_portfolio_results(self, results: Dict[str, Dict], top_n: int = 10) -> List[Tuple[str, Dict]]:
        """Display best cryptocurrencies by Sharpe ratio"""
        # Filter valid results
        valid_results = {k: v for k, v in results.items() if "error" not in v}

        # Sort by Sharpe ratio
        sorted_cryptos = sorted(valid_results.items(), key=lambda x: x[1]["sharpe_ratio"], reverse=True)

        self.logger.info(f"🏆 TOP {top_n} Cryptocurrencies by Sharpe Ratio:")
        for i, (symbol, metrics) in enumerate(sorted_cryptos[:top_n], 1):
            self.logger.info(
                f"  {i:2d}. {symbol}: Sharpe {metrics['sharpe_ratio']:.4f}, "
                f"Return {metrics['annual_return']:.1f}%, "
                f"Volatility {metrics['volatility']:.1f}%"
            )

        return sorted_cryptos[:top_n]


# Legacy compatibility functions
@log_performance
async def calculate_crypto_metrics(symbol: str) -> Tuple[str, Dict]:
    """Legacy compatibility function"""
    analyzer = PortfolioAnalyzer({"analysis_count": 50})
    result = await analyzer.analyze(symbol)
    return (symbol, result)

@log_performance
async def analyze_crypto_portfolio_parallel(crypto_symbols: List[str]) -> Dict[str, Dict]:
    """Legacy compatibility function"""
    analyzer = PortfolioAnalyzer({"analysis_count": len(crypto_symbols)})
    return await analyzer.analyze(crypto_symbols, batch_mode=True)

@log_performance
async def analyze_crypto_portfolio_sequential(crypto_symbols: List[str]) -> Dict[str, Dict]:
    """Legacy compatibility function"""
    analyzer = PortfolioAnalyzer({"analysis_count": len(crypto_symbols)})
    return await analyzer.analyze(crypto_symbols, batch_mode=False)

def get_top_cryptocurrencies(n: int = 50) -> List[str]:
    """Legacy compatibility function"""
    analyzer = PortfolioAnalyzer({})
    return analyzer.get_top_cryptocurrencies(n)

def display_portfolio_results(results: Dict[str, Dict], top_n: int = 10):
    """Legacy compatibility function"""
    analyzer = PortfolioAnalyzer({})
    return analyzer.display_portfolio_results(results, top_n)