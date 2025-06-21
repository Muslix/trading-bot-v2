"""
Symbol Normalizer Utility Plugin - symbol normalization functionality
"""

from typing import Dict, Any, Set
import re

from ..base import UtilPlugin, UtilConfig


class SymbolNormalizerUtil(UtilPlugin):
    """
    Symbol normalizer utility plugin.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        
        # Cache for normalized symbols
        self.normalization_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Symbol mappings and rules
        self.symbol_mappings = {
            # Common mappings
            "BITCOIN": "BTC",
            "ETHEREUM": "ETH", 
            "LITECOIN": "LTC",
            "BITCOIN CASH": "BCH",
            "CARDANO": "ADA",
            "POLKADOT": "DOT",
            "CHAINLINK": "LINK",
            # Exchange-specific mappings
            "BTCUSDT": "BTC/USDT",
            "ETHUSDT": "ETH/USDT",
            "BNBUSDT": "BNB/USDT",
        }
        
        # Known trading pairs patterns
        self.pair_patterns = [
            r"^([A-Z]{2,10})/([A-Z]{2,10})$",  # BTC/USDT
            r"^([A-Z]{2,10})([A-Z]{2,10})$",   # BTCUSDT
            r"^([A-Z]{2,10})-([A-Z]{2,10})$",  # BTC-USDT
            r"^([A-Z]{2,10})_([A-Z]{2,10})$",  # BTC_USDT
        ]
    
    async def _initialize_util(self) -> bool:
        """Initialize symbol normalizer utility."""
        try:
            # Import original symbol normalizer functionality if exists
            from ..symbol_normalizer import normalize_symbol as orig_normalize
            self.original_normalize = orig_normalize
        except ImportError:
            self.original_normalize = None
        
        self.logger.info("Symbol normalizer utility initialized")
        return True
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process symbol normalization operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "normalize")
        
        if action == "normalize":
            return await self._normalize_symbol(data)
        elif action == "normalize_batch":
            return await self._normalize_symbol_batch(data)
        elif action == "add_mapping":
            return self._add_symbol_mapping(data)
        elif action == "get_mappings":
            return self._get_symbol_mappings()
        elif action == "clear_cache":
            return self._clear_cache()
        elif action == "get_stats":
            return self._get_normalizer_stats()
        else:
            raise ValueError(f"Unknown symbol normalizer action: {action}")
    
    async def _normalize_symbol(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single symbol."""
        symbol = data.get("symbol", "").strip().upper()
        
        if not symbol:
            return {"success": False, "error": "No symbol provided"}
        
        # Check cache first
        if self.config.cache_enabled and symbol in self.normalization_cache:
            self.cache_hits += 1
            return {
                "success": True,
                "original_symbol": symbol,
                "normalized_symbol": self.normalization_cache[symbol],
                "from_cache": True
            }
        
        self.cache_misses += 1
        
        try:
            # Try original normalizer first if available
            if self.original_normalize:
                normalized = self.original_normalize(symbol)
            else:
                normalized = self._normalize_symbol_internal(symbol)
            
            # Cache the result
            if self.config.cache_enabled:
                self.normalization_cache[symbol] = normalized
            
            return {
                "success": True,
                "original_symbol": symbol,
                "normalized_symbol": normalized,
                "from_cache": False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to normalize symbol {symbol}: {e}")
            return {"success": False, "error": str(e), "original_symbol": symbol}
    
    def _normalize_symbol_internal(self, symbol: str) -> str:
        """Internal symbol normalization logic."""
        # Remove common prefixes/suffixes
        symbol = symbol.replace("USDT", "/USDT").replace("USD", "/USD")
        symbol = symbol.replace("BTC", "/BTC").replace("ETH", "/ETH")
        
        # Check direct mappings
        if symbol in self.symbol_mappings:
            return self.symbol_mappings[symbol]
        
        # Try to parse as trading pair
        for pattern in self.pair_patterns:
            match = re.match(pattern, symbol)
            if match:
                base, quote = match.groups()
                return f"{base}/{quote}"
        
        # If no pattern matches, return as-is but cleaned
        return symbol.replace("-", "/").replace("_", "/")
    
    async def _normalize_symbol_batch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize multiple symbols at once."""
        symbols = data.get("symbols", [])
        
        if not symbols:
            return {"success": False, "error": "No symbols provided"}
        
        results = {}
        errors = {}
        
        for symbol in symbols:
            try:
                result = await self._normalize_symbol({"symbol": symbol})
                if result["success"]:
                    results[symbol] = result["normalized_symbol"]
                else:
                    errors[symbol] = result.get("error", "Unknown error")
            except Exception as e:
                errors[symbol] = str(e)
        
        return {
            "success": True,
            "results": results,
            "errors": errors,
            "total_processed": len(symbols),
            "successful": len(results),
            "failed": len(errors)
        }
    
    def _add_symbol_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new symbol mapping."""
        from_symbol = data.get("from_symbol", "").strip().upper()
        to_symbol = data.get("to_symbol", "").strip().upper()
        
        if not from_symbol or not to_symbol:
            return {"success": False, "error": "Both from_symbol and to_symbol required"}
        
        self.symbol_mappings[from_symbol] = to_symbol
        
        # Clear cache entry if it exists
        if from_symbol in self.normalization_cache:
            del self.normalization_cache[from_symbol]
        
        return {
            "success": True,
            "mapping_added": f"{from_symbol} -> {to_symbol}",
            "total_mappings": len(self.symbol_mappings)
        }
    
    def _get_symbol_mappings(self) -> Dict[str, Any]:
        """Get all symbol mappings."""
        return {
            "success": True,
            "mappings": self.symbol_mappings.copy(),
            "total_mappings": len(self.symbol_mappings)
        }
    
    def _clear_cache(self) -> Dict[str, Any]:
        """Clear the normalization cache."""
        cache_size = len(self.normalization_cache)
        self.normalization_cache.clear()
        
        return {
            "success": True,
            "cache_cleared": True,
            "entries_cleared": cache_size
        }
    
    def _get_normalizer_stats(self) -> Dict[str, Any]:
        """Get normalizer statistics."""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_stats": {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "total_requests": total_requests,
                "cache_hit_rate": f"{cache_hit_rate:.2f}%",
                "cache_size": len(self.normalization_cache)
            },
            "mapping_stats": {
                "total_mappings": len(self.symbol_mappings),
                "pattern_count": len(self.pair_patterns)
            },
            "plugin_stats": {
                "plugin_name": self.name,
                "enabled": self.config.enabled,
                "cache_enabled": self.config.cache_enabled
            }
        }