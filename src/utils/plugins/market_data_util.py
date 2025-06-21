"""
Market Data Utility Plugin - multi-exchange data aggregation and processing
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from ..base import UtilPlugin, UtilConfig


class MarketDataUtil(UtilPlugin):
    """
    Market data utility plugin for multi-exchange operations.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.api_calls_made = 0
        self.last_api_call = None
        self.data_cache = {}
        self.cache_ttl = 60  # Cache TTL in seconds
        
        # Exchange endpoints and configurations
        self.exchanges = {
            "binance": {
                "base_url": "https://api.binance.com/api/v3",
                "ticker_endpoint": "/ticker/24hr",
                "orderbook_endpoint": "/depth",
                "rate_limit": 1200,  # requests per minute
                "weight_limit": 1200
            },
            "coinbase": {
                "base_url": "https://api.exchange.coinbase.com",
                "ticker_endpoint": "/products/{symbol}/ticker",
                "orderbook_endpoint": "/products/{symbol}/book",
                "rate_limit": 100,
                "weight_limit": 100
            },
            "kraken": {
                "base_url": "https://api.kraken.com/0/public",
                "ticker_endpoint": "/Ticker",
                "orderbook_endpoint": "/Depth",
                "rate_limit": 120,
                "weight_limit": 120
            },
            "bitfinex": {
                "base_url": "https://api-pub.bitfinex.com/v2",
                "ticker_endpoint": "/ticker/t{symbol}",
                "orderbook_endpoint": "/book/t{symbol}/P0",
                "rate_limit": 60,
                "weight_limit": 60
            }
        }
        
        # Symbol mappings for different exchanges
        self.symbol_mappings = {
            "binance": {"BTC/USDT": "BTCUSDT", "ETH/USDT": "ETHUSDT", "BNB/USDT": "BNBUSDT"},
            "coinbase": {"BTC/USDT": "BTC-USDT", "ETH/USDT": "ETH-USDT", "BNB/USDT": "BNB-USDT"},
            "kraken": {"BTC/USDT": "XBTUSD", "ETH/USDT": "ETHUSD", "BNB/USDT": "BNBUSD"},
            "bitfinex": {"BTC/USDT": "BTCUSDT", "ETH/USDT": "ETHUSDT", "BNB/USDT": "BNBUSDT"}
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize market data utility."""
        try:
            # Test connectivity to exchanges
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
            
            self.logger.info("Market data utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize market data utility: {e}")
            return False
    
    async def _cleanup_util(self) -> None:
        """Clean up market data utility resources."""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process market data operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "get_prices")
        
        if action == "get_prices":
            return await self._get_multi_exchange_prices(data)
        elif action == "find_arbitrage":
            return await self._find_arbitrage_opportunities(data)
        elif action == "get_orderbook":
            return await self._get_multi_exchange_orderbook(data)
        elif action == "get_volume_data":
            return await self._get_volume_data(data)
        elif action == "compare_exchanges":
            return await self._compare_exchanges(data)
        elif action == "get_best_price":
            return await self._get_best_price(data)
        elif action == "aggregate_data":
            return await self._aggregate_market_data(data)
        elif action == "get_supported_exchanges":
            return self._get_supported_exchanges()
        elif action == "clear_cache":
            return self._clear_cache()
        elif action == "get_stats":
            return self._get_market_data_stats()
        else:
            raise ValueError(f"Unknown market data action: {action}")
    
    async def _get_multi_exchange_prices(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get prices from multiple exchanges."""
        try:
            symbols = data.get("symbols", ["BTC/USDT"])
            exchanges = data.get("exchanges", list(self.exchanges.keys()))
            use_cache = data.get("use_cache", True)
            
            results = {}
            errors = {}
            
            # Create tasks for all exchange/symbol combinations
            tasks = []
            for exchange in exchanges:
                for symbol in symbols:
                    cache_key = f"{exchange}_{symbol}_price"
                    
                    # Check cache first
                    if use_cache and self._is_cache_valid(cache_key):
                        if exchange not in results:
                            results[exchange] = {}
                        results[exchange][symbol] = self.data_cache[cache_key]["data"]
                        continue
                    
                    # Create async task for API call
                    task = self._fetch_price_from_exchange(exchange, symbol)
                    tasks.append((exchange, symbol, task))
            
            # Execute all API calls concurrently
            if tasks:
                task_results = await asyncio.gather(
                    *[task for _, _, task in tasks],
                    return_exceptions=True
                )
                
                # Process results
                for i, (exchange, symbol, _) in enumerate(tasks):
                    result = task_results[i]
                    
                    if isinstance(result, Exception):
                        if exchange not in errors:
                            errors[exchange] = {}
                        errors[exchange][symbol] = str(result)
                    else:
                        if exchange not in results:
                            results[exchange] = {}
                        results[exchange][symbol] = result
                        
                        # Cache successful results
                        if use_cache:
                            cache_key = f"{exchange}_{symbol}_price"
                            self._cache_data(cache_key, result)
            
            return {
                "success": True,
                "results": results,
                "errors": errors,
                "symbols_requested": symbols,
                "exchanges_requested": exchanges,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Multi-exchange price fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_price_from_exchange(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Fetch price from a specific exchange."""
        if exchange not in self.exchanges:
            raise ValueError(f"Unsupported exchange: {exchange}")
        
        exchange_config = self.exchanges[exchange]
        mapped_symbol = self._map_symbol(symbol, exchange)
        
        try:
            if exchange == "binance":
                return await self._fetch_binance_price(mapped_symbol)
            elif exchange == "coinbase":
                return await self._fetch_coinbase_price(mapped_symbol)
            elif exchange == "kraken":
                return await self._fetch_kraken_price(mapped_symbol)
            elif exchange == "bitfinex":
                return await self._fetch_bitfinex_price(mapped_symbol)
            else:
                raise ValueError(f"Handler not implemented for exchange: {exchange}")
                
        except Exception as e:
            self.logger.error(f"Failed to fetch {symbol} from {exchange}: {e}")
            raise e
    
    async def _fetch_binance_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Binance."""
        url = f"{self.exchanges['binance']['base_url']}/ticker/24hr"
        params = {"symbol": symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                self.api_calls_made += 1
                self.last_api_call = datetime.now()
                
                return {
                    "price": float(data["lastPrice"]),
                    "volume": float(data["volume"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "high_24h": float(data["highPrice"]),
                    "low_24h": float(data["lowPrice"]),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Binance API error: {response.status}")
    
    async def _fetch_coinbase_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Coinbase."""
        url = f"{self.exchanges['coinbase']['base_url']}/products/{symbol}/ticker"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                self.api_calls_made += 1
                self.last_api_call = datetime.now()
                
                return {
                    "price": float(data["price"]),
                    "volume": float(data["volume"]),
                    "change_24h": 0,  # Coinbase doesn't provide this directly
                    "high_24h": 0,
                    "low_24h": 0,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Coinbase API error: {response.status}")
    
    async def _fetch_kraken_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Kraken."""
        url = f"{self.exchanges['kraken']['base_url']}/Ticker"
        params = {"pair": symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                self.api_calls_made += 1
                self.last_api_call = datetime.now()
                
                if "result" in data and symbol in data["result"]:
                    ticker_data = data["result"][symbol]
                    return {
                        "price": float(ticker_data["c"][0]),  # Last trade price
                        "volume": float(ticker_data["v"][1]),  # 24h volume
                        "change_24h": 0,  # Would need calculation
                        "high_24h": float(ticker_data["h"][1]),
                        "low_24h": float(ticker_data["l"][1]),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise Exception("Invalid Kraken response format")
            else:
                raise Exception(f"Kraken API error: {response.status}")
    
    async def _fetch_bitfinex_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Bitfinex."""
        url = f"{self.exchanges['bitfinex']['base_url']}/ticker/t{symbol}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                self.api_calls_made += 1
                self.last_api_call = datetime.now()
                
                if isinstance(data, list) and len(data) >= 10:
                    return {
                        "price": float(data[6]),  # Last price
                        "volume": float(data[7]),  # Volume
                        "change_24h": float(data[5]) * 100,  # Daily change percent
                        "high_24h": float(data[8]),  # Daily high
                        "low_24h": float(data[9]),  # Daily low
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise Exception("Invalid Bitfinex response format")
            else:
                raise Exception(f"Bitfinex API error: {response.status}")
    
    async def _find_arbitrage_opportunities(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find arbitrage opportunities across exchanges."""
        try:
            symbols = data.get("symbols", ["BTC/USDT"])
            min_profit_percentage = data.get("min_profit_percentage", 1.0)
            exchanges = data.get("exchanges", list(self.exchanges.keys()))
            
            # Get prices from all exchanges
            price_data = await self._get_multi_exchange_prices({
                "symbols": symbols,
                "exchanges": exchanges,
                "use_cache": True
            })
            
            if not price_data.get("success"):
                return {"success": False, "error": "Failed to fetch price data"}
            
            opportunities = []
            
            for symbol in symbols:
                symbol_prices = {}
                
                # Collect prices for this symbol from all exchanges
                for exchange, exchange_data in price_data["results"].items():
                    if symbol in exchange_data:
                        symbol_prices[exchange] = exchange_data[symbol]["price"]
                
                if len(symbol_prices) < 2:
                    continue
                
                # Find arbitrage opportunities
                min_exchange = min(symbol_prices, key=symbol_prices.get)
                max_exchange = max(symbol_prices, key=symbol_prices.get)
                
                min_price = symbol_prices[min_exchange]
                max_price = symbol_prices[max_exchange]
                
                profit_percentage = ((max_price - min_price) / min_price) * 100
                
                if profit_percentage >= min_profit_percentage:
                    opportunities.append({
                        "symbol": symbol,
                        "buy_exchange": min_exchange,
                        "sell_exchange": max_exchange,
                        "buy_price": min_price,
                        "sell_price": max_price,
                        "profit_percentage": profit_percentage,
                        "potential_profit": max_price - min_price,
                        "all_prices": symbol_prices,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return {
                "success": True,
                "opportunities": opportunities,
                "symbols_analyzed": symbols,
                "min_profit_threshold": min_profit_percentage,
                "total_opportunities": len(opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Arbitrage opportunity search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_best_price(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get the best price for a symbol across exchanges."""
        try:
            symbol = data.get("symbol", "BTC/USDT")
            side = data.get("side", "buy")  # buy or sell
            exchanges = data.get("exchanges", list(self.exchanges.keys()))
            
            # Get prices from all exchanges
            price_data = await self._get_multi_exchange_prices({
                "symbols": [symbol],
                "exchanges": exchanges,
                "use_cache": True
            })
            
            if not price_data.get("success"):
                return {"success": False, "error": "Failed to fetch price data"}
            
            prices = {}
            for exchange, exchange_data in price_data["results"].items():
                if symbol in exchange_data:
                    prices[exchange] = exchange_data[symbol]["price"]
            
            if not prices:
                return {"success": False, "error": f"No prices found for {symbol}"}
            
            # Find best price based on side
            if side.lower() == "buy":
                best_exchange = min(prices, key=prices.get)
                best_price = prices[best_exchange]
                comparison = "lowest"
            else:  # sell
                best_exchange = max(prices, key=prices.get)
                best_price = prices[best_exchange]
                comparison = "highest"
            
            return {
                "success": True,
                "symbol": symbol,
                "side": side,
                "best_exchange": best_exchange,
                "best_price": best_price,
                "comparison": comparison,
                "all_prices": prices,
                "price_spread": max(prices.values()) - min(prices.values()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Best price search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _aggregate_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate market data across exchanges."""
        try:
            symbols = data.get("symbols", ["BTC/USDT"])
            exchanges = data.get("exchanges", list(self.exchanges.keys()))
            aggregation_method = data.get("method", "weighted_average")  # mean, median, weighted_average
            
            # Get prices from all exchanges
            price_data = await self._get_multi_exchange_prices({
                "symbols": symbols,
                "exchanges": exchanges,
                "use_cache": True
            })
            
            if not price_data.get("success"):
                return {"success": False, "error": "Failed to fetch price data"}
            
            aggregated_data = {}
            
            for symbol in symbols:
                symbol_data = []
                
                # Collect data for this symbol
                for exchange, exchange_data in price_data["results"].items():
                    if symbol in exchange_data:
                        symbol_data.append(exchange_data[symbol])
                
                if not symbol_data:
                    continue
                
                # Aggregate based on method
                prices = [d["price"] for d in symbol_data]
                volumes = [d["volume"] for d in symbol_data]
                
                if aggregation_method == "mean":
                    aggregated_price = statistics.mean(prices)
                elif aggregation_method == "median":
                    aggregated_price = statistics.median(prices)
                elif aggregation_method == "weighted_average":
                    total_volume = sum(volumes)
                    if total_volume > 0:
                        aggregated_price = sum(p * v for p, v in zip(prices, volumes)) / total_volume
                    else:
                        aggregated_price = statistics.mean(prices)
                else:
                    aggregated_price = statistics.mean(prices)
                
                aggregated_data[symbol] = {
                    "aggregated_price": aggregated_price,
                    "price_range": {
                        "min": min(prices),
                        "max": max(prices),
                        "spread": max(prices) - min(prices)
                    },
                    "total_volume": sum(volumes),
                    "exchange_count": len(symbol_data),
                    "method": aggregation_method,
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "success": True,
                "aggregated_data": aggregated_data,
                "method": aggregation_method,
                "symbols_processed": list(aggregated_data.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Market data aggregation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _map_symbol(self, symbol: str, exchange: str) -> str:
        """Map symbol to exchange-specific format."""
        if exchange in self.symbol_mappings and symbol in self.symbol_mappings[exchange]:
            return self.symbol_mappings[exchange][symbol]
        return symbol.replace("/", "")  # Default: remove slash
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.data_cache:
            return False
        
        cache_time = self.data_cache[cache_key]["timestamp"]
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with timestamp."""
        self.data_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def _clear_cache(self) -> Dict[str, Any]:
        """Clear the data cache."""
        cache_size = len(self.data_cache)
        self.data_cache.clear()
        
        return {
            "success": True,
            "cache_cleared": True,
            "entries_cleared": cache_size
        }
    
    def _get_supported_exchanges(self) -> Dict[str, Any]:
        """Get list of supported exchanges."""
        return {
            "success": True,
            "exchanges": list(self.exchanges.keys()),
            "exchange_details": {
                name: {
                    "rate_limit": config["rate_limit"],
                    "base_url": config["base_url"]
                }
                for name, config in self.exchanges.items()
            }
        }
    
    def _get_market_data_stats(self) -> Dict[str, Any]:
        """Get market data statistics."""
        return {
            "api_calls_made": self.api_calls_made,
            "last_api_call": self.last_api_call.isoformat() if self.last_api_call else None,
            "cache_stats": {
                "cache_size": len(self.data_cache),
                "cache_ttl_seconds": self.cache_ttl
            },
            "supported_exchanges": list(self.exchanges.keys()),
            "symbol_mappings_count": sum(len(mappings) for mappings in self.symbol_mappings.values()),
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }