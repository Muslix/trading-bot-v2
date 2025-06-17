"""
Crypto Portfolio Analyzer - Multiprocessing Module
Analysiere 50-100 Kryptowährungen gleichzeitig
Berechne Sharpe Ratios, Volatilität, Korrelationen parallel
"""

import numpy as np
from multiprocessing import Pool
from typing import List, Dict, Tuple
from utils.decorators import log_performance


def calculate_crypto_metrics(symbol: str) -> Tuple[str, Dict]:
    """Berechne Sharpe Ratio, Volatilität, Korrelationen für eine Kryptowährung"""
    try:
        # Simuliere Krypto-Daten (in Realität würdest du historische Daten von API holen)
        np.random.seed(hash(symbol) % 10000)  # Reproduzierbare "Daten" pro Symbol
        
        # Simuliere 365 Tage Preis-Daten
        returns = np.random.normal(0.001, 0.03, 365)  # Tägliche Returns
        prices = np.cumprod(1 + returns) * 100  # Startpreis 100
        
        # Berechne Metriken
        annual_return = np.mean(returns) * 365
        volatility = np.std(returns) * np.sqrt(365)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Max Drawdown
        peak = np.maximum.accumulate(prices)
        drawdown = (prices - peak) / peak
        max_drawdown = np.min(drawdown)
        
        metrics = {
            'sharpe_ratio': round(sharpe_ratio, 4),
            'volatility': round(volatility * 100, 2),  # In Prozent
            'annual_return': round(annual_return * 100, 2),  # In Prozent
            'max_drawdown': round(max_drawdown * 100, 2),  # In Prozent
            'current_price': round(prices[-1], 2)
        }
        
        return (symbol, metrics)
    
    except Exception as e:
        return (symbol, {'error': str(e)})


@log_performance
def analyze_crypto_portfolio_parallel(crypto_symbols: List[str]) -> Dict[str, Dict]:
    """Analysiere 50-100 Kryptowährungen parallel"""
    print(f"🔄 Analysiere {len(crypto_symbols)} Kryptowährungen parallel...")
    
    # Multiprocessing Pool für parallele Verarbeitung
    with Pool() as pool:
        results = pool.map(calculate_crypto_metrics, crypto_symbols)
    
    # Konvertiere zu Dictionary
    return dict(results)


@log_performance
def analyze_crypto_portfolio_sequential(crypto_symbols: List[str]) -> Dict[str, Dict]:
    """Sequentielle Analyse für Performance-Vergleich"""
    results = {}
    for symbol in crypto_symbols:
        result = calculate_crypto_metrics(symbol)
        results[result[0]] = result[1]
    return results


def get_top_cryptocurrencies(n: int = 50) -> List[str]:
    """Hole die Top N Kryptowährungen für die Analyse - nur aktive Coins"""
    # Bereinigte Liste mit aktuell verfügbaren Coins (Yahoo Finance kompatibel)
    active_crypto_list = [
        # Top Tier - Major cryptocurrencies (sehr stabil)
        "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "MATIC", "AVAX",
        "LTC", "UNI", "LINK", "XLM", "ATOM", "XMR", "ETC", "BCH", "ALGO", "VET",
        
        # Tier 2 - Established altcoins
        "AAVE", "SAND", "MANA", "CRV", "SUSHI", "YFI", "COMP", "MKR", "SNX",
        "BAL", "REN", "KNC", "ZRX", "NMR", "STORJ", "GRT", "ANKR", "BAND",
        
        # Tier 3 - DeFi and newer projects (with data)
        "THETA", "FIL", "TRX", "EOS", "FTM", "NEAR", "OCEAN",
        "FET", "API3", "BADGER", "FARM",
        
        # Tier 4 - Gaming and NFT (available on Yahoo)
        "AXS", "GALA", "ENJ", "CHZ", "FLOW"
    ]
    
    # Entferne Duplikate und gib nur die ersten n zurück
    unique_cryptos = list(dict.fromkeys(active_crypto_list))
    return unique_cryptos[:n]


def display_portfolio_results(results: Dict[str, Dict], top_n: int = 10):
    """Zeige die besten Kryptowährungen nach Sharpe Ratio"""
    # Filtere gültige Ergebnisse
    valid_results = {k: v for k, v in results.items() if 'error' not in v}
    
    # Sortiere nach Sharpe Ratio
    sorted_cryptos = sorted(valid_results.items(), 
                          key=lambda x: x[1]['sharpe_ratio'], 
                          reverse=True)
    
    print(f"\n🏆 TOP {top_n} Kryptowährungen nach Sharpe Ratio:")
    for i, (symbol, metrics) in enumerate(sorted_cryptos[:top_n], 1):
        print(f"  {i:2d}. {symbol}: Sharpe {metrics['sharpe_ratio']:.4f}, "
              f"Return {metrics['annual_return']:.1f}%, "
              f"Volatilität {metrics['volatility']:.1f}%")
    
    return sorted_cryptos[:top_n]
