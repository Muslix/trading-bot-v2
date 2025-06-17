"""
Arbitrage Detection & Alert System
Arbitrage-Möglichkeiten in Echtzeit erkennen
Alert-System wenn Preisunterschiede > 1% auftreten
"""

from typing import Dict, List
from utils.decorators import log_performance


@log_performance
def detect_arbitrage_opportunities(prices: Dict[str, float], threshold: float = 0.01) -> List[Dict]:
    """Arbitrage-Möglichkeiten in Echtzeit erkennen"""
    opportunities = []
    exchanges = list(prices.keys())
    
    for i, exchange1 in enumerate(exchanges):
        for exchange2 in exchanges[i+1:]:
            price1 = prices[exchange1]
            price2 = prices[exchange2]
            
            if price1 > 0 and price2 > 0:
                # Prozentuale Preisdifferenz berechnen
                diff_percent = abs(price1 - price2) / min(price1, price2)
                
                if diff_percent > threshold:
                    buy_exchange = exchange1 if price1 < price2 else exchange2
                    sell_exchange = exchange2 if price1 < price2 else exchange1
                    buy_price = min(price1, price2)
                    sell_price = max(price1, price2)
                    
                    opportunity = {
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_percent': round(diff_percent * 100, 2),
                        'profit_percentage': round(diff_percent * 100, 2),  # Konsistenter Key
                        'profit_per_unit': round(sell_price - buy_price, 2)
                    }
                    opportunities.append(opportunity)
    
    return opportunities


@log_performance
def alert_system(opportunities: List[Dict], min_profit: float = 1.0) -> List[str]:
    """Alert-System wenn Preisunterschiede > 1% auftreten"""
    alerts = []
    
    for opp in opportunities:
        if opp['profit_percent'] >= min_profit:
            alert = f"🚨 ARBITRAGE ALERT! {opp['profit_percent']:.2f}% Profit möglich!"
            alert += f"\n   📈 Kaufe auf {opp['buy_exchange'].upper()}: ${opp['buy_price']:,.2f}"
            alert += f"\n   📉 Verkaufe auf {opp['sell_exchange'].upper()}: ${opp['sell_price']:,.2f}"
            alert += f"\n   💰 Profit pro Einheit: ${opp['profit_per_unit']:,.2f}"
            
            alerts.append(alert)
            print(alert)
    
    return alerts


def calculate_profit_potential(opportunity: Dict, volume: float = 1.0) -> Dict:
    """Berechne Profit-Potential für gegebenes Volumen"""
    profit_per_unit = opportunity['profit_per_unit']
    total_profit = profit_per_unit * volume
    
    # Trading-Fees berücksichtigen (typisch 0.1% pro Trade)
    trading_fee_rate = 0.001
    buy_fee = opportunity['buy_price'] * volume * trading_fee_rate
    sell_fee = opportunity['sell_price'] * volume * trading_fee_rate
    total_fees = buy_fee + sell_fee
    
    net_profit = total_profit - total_fees
    
    return {
        'volume': volume,
        'gross_profit': round(total_profit, 2),
        'trading_fees': round(total_fees, 2),
        'net_profit': round(net_profit, 2),
        'net_profit_percent': round((net_profit / (opportunity['buy_price'] * volume)) * 100, 2)
    }


def analyze_arbitrage_history(opportunities_history: List[List[Dict]]) -> Dict:
    """Analysiere historische Arbitrage-Möglichkeiten"""
    total_opportunities = sum(len(opps) for opps in opportunities_history)
    
    if total_opportunities == 0:
        return {
            'total_opportunities': 0,
            'avg_profit_percent': 0,
            'max_profit_percent': 0,
            'profitable_periods': 0,
            'total_periods': len(opportunities_history)
        }
    
    all_profits = []
    profitable_periods = 0
    
    for opportunities in opportunities_history:
        if opportunities:
            profitable_periods += 1
            for opp in opportunities:
                all_profits.append(opp['profit_percent'])
    
    return {
        'total_opportunities': total_opportunities,
        'avg_profit_percent': round(sum(all_profits) / len(all_profits), 2) if all_profits else 0,
        'max_profit_percent': round(max(all_profits), 2) if all_profits else 0,
        'profitable_periods': profitable_periods,
        'total_periods': len(opportunities_history)
    }


def filter_opportunities_by_criteria(opportunities: List[Dict], 
                                   min_profit: float = 1.0,
                                   min_volume_support: float = 1000) -> List[Dict]:
    """Filtere Arbitrage-Möglichkeiten nach Kriterien"""
    filtered = []
    
    for opp in opportunities:
        # Profit-Filter
        if opp['profit_percent'] < min_profit:
            continue
        
        # Volumen-Filter (simuliert - in Realität würdest du Order-Book-Tiefe prüfen)
        estimated_volume_support = opp['buy_price'] * 100  # Vereinfachte Schätzung
        if estimated_volume_support < min_volume_support:
            continue
        
        filtered.append(opp)
    
    return filtered


def get_best_arbitrage_opportunity(opportunities: List[Dict]) -> Dict:
    """Hole die beste Arbitrage-Möglichkeit"""
    if not opportunities:
        return {}
    
    # Sortiere nach Profit-Prozent
    best_opp = max(opportunities, key=lambda x: x['profit_percent'])
    return best_opp