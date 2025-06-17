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
    
    with Pool() as pool:
        results = pool.map(calculate_crypto_metrics, crypto_symbols)
    
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
        # Top 50 - Marktführer
        'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'XRP', 'LTC', 'LINK', 'BCH', 'XLM',
        'USDT', 'USDC', 'DOGE', 'UNI', 'WBTC', 'THETA', 'ICP', 'VET', 'FIL', 'TRX',
        'ETC', 'XMR', 'SOL', 'AAVE', 'EOS', 'ATOM', 'CAKE', 'MKR', 'COMP', 'ZEC',
        'DASH', 'NEO', 'IOTA', 'XTZ', 'KSM', 'AVAX', 'LUNA', 'ALGO', 'EGLD', 'NEAR',
        'FTM', 'MATIC', 'HBAR', 'ONE', 'MANA', 'SAND', 'AXS', 'ENJ', 'CHZ', 'BAT',
        
        # 51-100 - Aufstrebende Projekte
        'CRO', 'SHIB', 'LEO', 'DAI', 'BUSD', 'APE', 'LDO', 'STETH', 'ARB', 'OP',
        'TON', 'TIA', 'INJ', 'HBAR', 'KAS', 'TAO', 'PEPE', 'ICP', 'NEAR', 'RUNE',
        'GRT', 'IMX', 'ASTR', 'FLOW', 'XTZ', 'MINA', 'ROSE', 'CFG', 'GLMR', 'MOVR',
        'KAVA', 'OSMO', 'SCRT', 'JUNO', 'STARS', 'HUAHUA', 'CMDX', 'CRE', 'SIF', 'ROWAN',
        'IRIS', 'REGEN', 'IOV', 'BAND', 'CTSI', 'NMR', 'STORJ', 'ANKR', 'REQ', 'LRC',
        
        # 101-150 - DeFi & Gaming
        '1INCH', 'SUSHI', 'CRV', 'YFI', 'BAL', 'PERP', 'DYDX', 'GMX', 'JOE', 'PNG',
        'LOOKS', 'X2Y2', 'BLUR', 'MAGIC', 'TRB', 'API3', 'ALPHA', 'BETA', 'RARI', 'FARM',
        'IDLE', 'PICKLE', 'BADGER', 'DIGG', 'CVX', 'FXS', 'TRIBE', 'FEI', 'LUSD', 'FRAX',
        'OHM', 'KLIMA', 'TIME', 'MEMO', 'ICE', 'SPELL', 'MIM', 'DEUS', 'DEI', 'SOLID',
        'SEX', 'SPIRIT', 'LQDR', 'EQUAL', 'VELO', 'VELODROME', 'THALES', 'SNX', 'KWENTA', 'LYRA',
        
        # 151-200 - Layer 2 & Infrastruktur  
        'POLYGON', 'ARBITRUM', 'OPTIMISM', 'ZKSYNC', 'STARKNET', 'LOOPRING', 'BOBA', 'METIS',
        'XDAI', 'CELO', 'HARMONY', 'MOONBEAM', 'MOONRIVER', 'ASTAR', 'SHIDEN', 'ACALA',
        'KARURA', 'BIFROST', 'PARALLEL', 'CENTRIFUGE', 'PHALA', 'LITENTRY', 'SUBSOCIAL', 'ZEITGEIST',
        'BASILISK', 'TINKERNET', 'CALAMARI', 'SHADOW', 'MANTA', 'DOLPHIN', 'PIONEER', 'ROBONOMICS',
        'EDGEWARE', 'DARWINIA', 'CRAB', 'CHAINX', 'BITCOIN', 'LITECOIN', 'DOGECOIN', 'SHIBAINU'
    ]
    
    # Erweitere Liste falls mehr Coins gewünscht
    if len(crypto_list) < n:
        additional_coins = [
            # Weitere DeFi Projekte
            'BNTX', 'REN', 'KNC', 'ZRX', 'HEGIC', 'COVER', 'CREAM', 'HARVEST', 'PICKLE',
            'BADGER', 'DIGG', 'RARI', 'FARM', 'IDLE', 'ALPHA', 'BETA', 'GAMMA', 'DELTA',
            
            # Gaming & NFT
            'GALA', 'GODS', 'ALICE', 'TLM', 'SLP', 'PYR', 'MAGIC', 'BLUR', 'LOOKS', 'X2Y2',
            'RARE', 'SUPER', 'HERO', 'SKILL', 'JEWEL', 'CRYSTAL', 'DFKTEARS', 'ONE', 'HARMONY',
            
            # Meme Coins
            'FLOKI', 'BABYDOGE', 'SAFEMOON', 'KISHU', 'HOGE', 'DOGELON', 'SAITAMA', 'JACY',
            
            # Infrastructure
            'HELIUM', 'FTT', 'HT', 'OKB', 'GT', 'KCS', 'LEO', 'CRO', 'BGB', 'WRX'
        ]
        
        crypto_list.extend(additional_coins[:n - len(crypto_list)])
    
    return crypto_list[:n]
        'TON', 'TIA', 'INJ', 'HBAR', 'KAS', 'TAO', 'PEPE', 'ICP', 'NEAR', 'RUNE',
        'GRT', 'IMX', 'ASTR', 'FLOW', 'XTZ', 'MINA', 'ROSE', 'CFG', 'GLMR', 'MOVR',
        'KAVA', 'OSMO', 'SCRT', 'JUNO', 'STARS', 'HUAHUA', 'CMDX', 'CRE', 'SIF', 'ROWAN',
        'IRIS', 'REGEN', 'IOV', 'BAND', 'CTSI', 'NMR', 'STORJ', 'ANKR', 'REQ', 'LRC',
        
        # 101-150 - DeFi & Gaming
        '1INCH', 'SUSHI', 'CRV', 'YFI', 'BAL', 'PERP', 'DYDX', 'GMX', 'JOE', 'PNG',
        'LOOKS', 'X2Y2', 'BLUR', 'MAGIC', 'TRB', 'API3', 'ALPHA', 'BETA', 'RARI', 'FARM',
        'IDLE', 'PICKLE', 'BADGER', 'DIGG', 'CVX', 'FXS', 'TRIBE', 'FEI', 'LUSD', 'FRAX',
        'OHM', 'KLIMA', 'TIME', 'MEMO', 'ICE', 'SPELL', 'MIM', 'DEUS', 'DEI', 'SOLID',
        'SEX', 'SPIRIT', 'LQDR', 'EQUAL', 'VELO', 'OP', 'VELODROME', 'THALES', 'SNX', 'KWENTA',
        
        # 151-200 - Layer 2 & Infrastruktur  
        'POLYGON', 'ARBITRUM', 'OPTIMISM', 'ZKSYNC', 'STARKNET', 'LOOPRING', 'BOBA', 'METIS',
        'XDAI', 'CELO', 'HARMONY', 'MOONBEAM', 'MOONRIVER', 'ASTAR', 'SHIDEN', 'ACALA',
        'KARURA', 'BIFROST', 'PARALLEL', 'CENTRIFUGE', 'PHALA', 'LITENTRY', 'SUBSOCIAL', 'ZEITGEIST',
        'BASILISK', 'TINKERNET', 'CALAMARI', 'SHADOW', 'MANTA', 'DOLPHIN', 'PIONEER', 'ROBONOMICS',
        'EDGEWARE', 'DARWINIA', 'CRAB', 'CHAINX', 'BITCOIN', 'LITECOIN', 'DOGECOIN', 'SHIBAINU',
        'ETHEREUM', 'CARDANO', 'POLKADOT', 'CHAINLINK', 'UNISWAP', 'AVALANCHE', 'TERRA', 'ALGORAND',
        
        # 201+ - Weitere interessante Projekte
        'APTOS', 'SUI', 'SEI', 'CELESTIA', 'DYMENSION', 'NEUTRON', 'NOLUS', 'STRIDE',
        'QUICKSILVER', 'COMDEX', 'CRESCENT', 'KUJIRA', 'MIGALOO', 'CHIHUAHUA', 'BITCANNA', 'LUMNETWORK',
        'VIDULUM', 'KICHAIN', 'RIZON', 'KONSTELLATION', 'OMNIFLIX', 'GALAXY', 'CUDOS', 'FETCH'
    ]
    
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