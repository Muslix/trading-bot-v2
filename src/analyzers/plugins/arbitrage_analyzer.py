"""
Arbitrage Analyzer Plugin - Detects arbitrage opportunities
"""

from typing import Dict, List, Any, Optional
import logging

from ..base import BaseAnalyzer
from src.core.base import UniversalPlugin, ModuleConfig
from src.utils.decorators import log_performance


class ArbitrageAnalyzer(BaseAnalyzer):
    """Arbitrage opportunity detection and analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Access custom settings from ModuleConfig
        settings = self.config.custom_settings
        self.threshold = settings.get("threshold", 0.01)  # 1% default
        self.min_profit = settings.get("min_profit", 1.0)  # 1% minimum profit
        self.trading_fee_rate = settings.get("trading_fee_rate", 0.001)  # 0.1% default
        
    def get_analyzer_type(self) -> str:
        return "arbitrage"
        
    @log_performance
    async def analyze(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Analyze price data for arbitrage opportunities
        
        Args:
            data: Dict[str, float] - prices from different exchanges
            kwargs: Additional parameters (threshold override, etc.)
        """
        if not isinstance(data, dict):
            return {"error": "Invalid data format - expected price dictionary"}
            
        prices = data
        threshold = kwargs.get("threshold", self.threshold)
        
        opportunities = self._detect_opportunities(prices, threshold)
        
        return {
            "opportunities": opportunities,
            "total_opportunities": len(opportunities),
            "best_opportunity": self._get_best_opportunity(opportunities),
            "analysis_params": {
                "threshold": threshold,
                "exchanges_analyzed": list(prices.keys()),
                "price_count": len(prices)
            }
        }
        
    def _detect_opportunities(self, prices: Dict[str, float], threshold: float) -> List[Dict]:
        """Detect arbitrage opportunities in real-time"""
        opportunities = []
        exchanges = list(prices.keys())

        for i, exchange1 in enumerate(exchanges):
            for exchange2 in exchanges[i + 1:]:
                price1 = prices[exchange1]
                price2 = prices[exchange2]

                if price1 > 0 and price2 > 0:
                    # Calculate percentage price difference
                    diff_percent = abs(price1 - price2) / min(price1, price2)

                    if diff_percent > threshold:
                        buy_exchange = exchange1 if price1 < price2 else exchange2
                        sell_exchange = exchange2 if price1 < price2 else exchange1
                        buy_price = min(price1, price2)
                        sell_price = max(price1, price2)

                        opportunity = {
                            "buy_exchange": buy_exchange,
                            "sell_exchange": sell_exchange,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "profit_percent": round(diff_percent * 100, 2),
                            "profit_percentage": round(diff_percent * 100, 2),  # Consistent key
                            "profit_per_unit": round(sell_price - buy_price, 2),
                        }
                        opportunities.append(opportunity)

        return opportunities
        
    def _get_best_opportunity(self, opportunities: List[Dict]) -> Optional[Dict]:
        """Get the best arbitrage opportunity"""
        if not opportunities:
            return None
            
        return max(opportunities, key=lambda x: x["profit_percent"])
        
    async def calculate_profit_potential(self, opportunity: Dict, volume: float = 1.0) -> Dict:
        """Calculate profit potential for given volume"""
        profit_per_unit = opportunity["profit_per_unit"]
        total_profit = profit_per_unit * volume

        # Consider trading fees
        buy_fee = opportunity["buy_price"] * volume * self.trading_fee_rate
        sell_fee = opportunity["sell_price"] * volume * self.trading_fee_rate
        total_fees = buy_fee + sell_fee

        net_profit = total_profit - total_fees

        return {
            "volume": volume,
            "gross_profit": round(total_profit, 2),
            "trading_fees": round(total_fees, 2),
            "net_profit": round(net_profit, 2),
            "net_profit_percent": round((net_profit / (opportunity["buy_price"] * volume)) * 100, 2),
        }
        
    async def filter_opportunities(self, opportunities: List[Dict], **kwargs) -> List[Dict]:
        """Filter arbitrage opportunities by criteria"""
        min_profit = kwargs.get("min_profit", self.min_profit)
        min_volume_support = kwargs.get("min_volume_support", 1000)
        
        filtered = []

        for opp in opportunities:
            # Profit filter
            if opp["profit_percent"] < min_profit:
                continue

            # Volume filter (simplified - in reality you'd check order book depth)
            estimated_volume_support = opp["buy_price"] * 100  # Simplified estimation
            if estimated_volume_support < min_volume_support:
                continue

            filtered.append(opp)

        return filtered
        
    async def analyze_history(self, opportunities_history: List[List[Dict]]) -> Dict:
        """Analyze historical arbitrage opportunities"""
        total_opportunities = sum(len(opps) for opps in opportunities_history)

        if total_opportunities == 0:
            return {
                "total_opportunities": 0,
                "avg_profit_percent": 0,
                "max_profit_percent": 0,
                "profitable_periods": 0,
                "total_periods": len(opportunities_history),
            }

        all_profits = []
        profitable_periods = 0

        for opportunities in opportunities_history:
            if opportunities:
                profitable_periods += 1
                for opp in opportunities:
                    all_profits.append(opp["profit_percent"])

        return {
            "total_opportunities": total_opportunities,
            "avg_profit_percent": round(sum(all_profits) / len(all_profits), 2) if all_profits else 0,
            "max_profit_percent": round(max(all_profits), 2) if all_profits else 0,
            "profitable_periods": profitable_periods,
            "total_periods": len(opportunities_history),
        }


# Legacy compatibility functions
@log_performance  
def detect_arbitrage_opportunities(prices: Dict[str, float], threshold: float = 0.01) -> List[Dict]:
    """Legacy compatibility function"""
    analyzer = ArbitrageAnalyzer({"threshold": threshold})
    
    # Direct synchronous call to avoid event loop issues
    opportunities = analyzer._detect_opportunities(prices, threshold)
    return opportunities