"""
Crypto Portfolio Analyzer - Multiprocessing Module
Analysiere 50-100 Kryptowährungen gleichzeitig
Berechne Sharpe Ratios, Volatilität, Korrelationen parallel
"""

import numpy as np
from multiprocessing import Pool
from typing import List, Dict, Tuple
from src.utils.decorators import log_performance


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


def get_top_cryptocurrencies(n: int = 100) -> List[str]:
    """Hole die Top N Kryptowährungen für die Analyse"""
    # Erweiterte Liste mit 200+ Top Kryptowährungen
    crypto_list = [
        # Top 50 - Major cryptocurrencies
        'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE', 'MATIC', 'SOL', 'DOT', 'SHIB',
        'AVAX', 'TRX', 'WBTC', 'LEO', 'LTC', 'UNI', 'LINK', 'XLM', 'ATOM', 'TON',
        'XMR', 'ETC', 'BCH', 'ICP', 'HBAR', 'APT', 'LDO', 'QNT', 'CRO', 'VET',
        'NEAR', 'ALGO', 'MANA', 'SAND', 'APE', 'FIL', 'CHZ', 'EGLD', 'EOS', 'THETA',
        'AXS', 'XTZ', 'ROSE', 'FLOW', 'KLAY', 'MINA', 'RUNE', 'FTM', 'LRC', 'GRT',
        
        # 51-100 - DeFi & Layer 2
        'AAVE', 'CRV', 'SNX', 'COMP', 'MKR', 'YFI', 'SUSHI', '1INCH', 'BAL', 'PERP',
        'DYDX', 'GMX', 'JOE', 'PNG', 'LOOKS', 'X2Y2', 'BLUR', 'MAGIC', 'TRB', 'API3',
        'OCEAN', 'FET', 'AGIX', 'RLC', 'NMR', 'STORJ', 'ANKR', 'REQ', 'CTSI', 'BAND',
        'REN', 'KNC', 'ZRX', 'ALPHA', 'BADGER', 'CREAM', 'COVER', 'HEGIC', 'PICKLE', 'HARVEST',
        'IDLE', 'RARI', 'FARM', 'CVX', 'FXS', 'TRIBE', 'FEI', 'LUSD', 'FRAX', 'OHM',
        
        # 101-150 - Gaming & NFT
        'ENJ', 'CHR', 'ALICE', 'TLM', 'SLP', 'PYR', 'GALA', 'GODS', 'IMX', 'SUPER',
        'HERO', 'SKILL', 'JEWEL', 'CRYSTAL', 'RARE', 'KLIMA', 'TIME', 'MEMO', 'ICE', 'SPELL',
        'MIM', 'DEUS', 'DEI', 'SOLID', 'SEX', 'SPIRIT', 'LQDR', 'EQUAL', 'VELO', 'THALES',
        'KWENTA', 'LYRA', 'OP', 'ARB', 'METIS', 'BOBA', 'POLYGON', 'ARBITRUM', 'OPTIMISM', 'ZKSYNC',
        'STARKNET', 'LOOPRING', 'XDAI', 'CELO', 'HARMONY', 'MOONBEAM', 'MOONRIVER', 'ASTAR', 'SHIDEN', 'ACALA',
        
        # 151-200 - Additional projects
        'KARURA', 'BIFROST', 'PARALLEL', 'CENTRIFUGE', 'PHALA', 'LITENTRY', 'SUBSOCIAL', 'ZEITGEIST',
        'BASILISK', 'TINKERNET', 'CALAMARI', 'SHADOW', 'MANTA', 'DOLPHIN', 'PIONEER', 'ROBONOMICS',
        'EDGEWARE', 'DARWINIA', 'CRAB', 'CHAINX', 'KAVA', 'OSMO', 'SCRT', 'JUNO',
        'STARS', 'HUAHUA', 'CMDX', 'CRE', 'SIF', 'ROWAN', 'IRIS', 'REGEN', 'IOV', 'CARTESI',
        'APTOS', 'SUI', 'SEI', 'CELESTIA', 'DYMENSION', 'NEUTRON', 'NOLUS', 'STRIDE', 'QUICKSILVER', 'COMDEX'
    ]
    
    # Erweitere Liste falls mehr Coins gewünscht
    if len(crypto_list) < n:
        additional_coins = [
            # Meme Coins
            'FLOKI', 'BABYDOGE', 'SAFEMOON', 'KISHU', 'HOGE', 'DOGELON', 'SAITAMA', 'JACY',
            # Exchange Tokens
            'FTT', 'HT', 'OKB', 'GT', 'KCS', 'BGB', 'WRX', 'BKEX', 'MX', 'BTSE',
            # Infrastructure
            'HELIUM', 'RNDR', 'LIVEPEER', 'STORJ', 'SIACOIN', 'FILECOIN', 'ARWEAVE', 'THETA', 'TFUEL', 'AKASH'
        ]
        
        crypto_list.extend(additional_coins[:n - len(crypto_list)])
    
    return crypto_list[:n]


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
