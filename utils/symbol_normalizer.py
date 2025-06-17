"""
Symbol Normalization Utility
Normalisiert Crypto-Symbole von verschiedenen APIs zu einheitlichen Namen
"""

def normalize_crypto_symbol(symbol: str) -> str:
    """Normalisiert Crypto-Symbol zu einheitlichem Format"""
    
    # Entferne gängige Suffixe und Präfixe
    symbol = symbol.upper().strip()
    
    # Mapping für bekannte Varianten zu Standardnamen
    symbol_mapping = {
        # Bitcoin Varianten
        'BTC': 'BTC',
        'BITCOIN': 'BTC',
        'BTC-USD': 'BTC',
        'BTCUSD': 'BTC',
        'BTCUSDT': 'BTC',
        'XBT': 'BTC',
        'XBTUSD': 'BTC',
        
        # Ethereum Varianten
        'ETH': 'ETH',
        'ETHEREUM': 'ETH',
        'ETH-USD': 'ETH',
        'ETHUSD': 'ETH',
        'ETHUSDT': 'ETH',
        
        # XRP Varianten
        'XRP': 'XRP',
        'XRP-USD': 'XRP',
        'XRPUSD': 'XRP',
        'XRPUSDT': 'XRP',
        'RIPPLE': 'XRP',
        
        # Stellar Varianten
        'XLM': 'XLM',
        'XLM-USD': 'XLM',
        'XLMUSD': 'XLM',
        'XLMUSDT': 'XLM',
        'STELLAR': 'XLM',
        
        # Wrapped Bitcoin
        'WBTC': 'WBTC',
        'WBTC-USD': 'WBTC',
        'WBTCUSD': 'WBTC',
        'WBTCUSDT': 'WBTC',
        
        # Cardano
        'ADA': 'ADA',
        'ADA-USD': 'ADA',
        'ADAUSD': 'ADA',
        'ADAUSDT': 'ADA',
        'CARDANO': 'ADA',
        
        # Solana
        'SOL': 'SOL',
        'SOL-USD': 'SOL',
        'SOLUSD': 'SOL',
        'SOLUSDT': 'SOL',
        'SOLANA': 'SOL',
        
        # Binance Coin
        'BNB': 'BNB',
        'BNB-USD': 'BNB',
        'BNBUSD': 'BNB',
        'BNBUSDT': 'BNB',
        
        # Chainlink
        'LINK': 'LINK',
        'LINK-USD': 'LINK',
        'LINKUSD': 'LINK',
        'LINKUSDT': 'LINK',
        'CHAINLINK': 'LINK',
        
        # Polkadot
        'DOT': 'DOT',
        'DOT-USD': 'DOT',
        'DOTUSD': 'DOT',
        'DOTUSDT': 'DOT',
        'POLKADOT': 'DOT',
        
        # Dogecoin
        'DOGE': 'DOGE',
        'DOGE-USD': 'DOGE',
        'DOGEUSD': 'DOGE',
        'DOGEUSDT': 'DOGE',
        'DOGECOIN': 'DOGE',
        
        # Avalanche
        'AVAX': 'AVAX',
        'AVAX-USD': 'AVAX',
        'AVAXUSD': 'AVAX',
        'AVAXUSDT': 'AVAX',
        'AVALANCHE': 'AVAX',
        
        # Polygon
        'MATIC': 'MATIC',
        'MATIC-USD': 'MATIC',
        'MATICUSD': 'MATIC',
        'MATICUSDT': 'MATIC',
        'POLYGON': 'MATIC',
        
        # Litecoin
        'LTC': 'LTC',
        'LTC-USD': 'LTC',
        'LTCUSD': 'LTC',
        'LTCUSDT': 'LTC',
        'LITECOIN': 'LTC',
        
        # Bitcoin Cash
        'BCH': 'BCH',
        'BCH-USD': 'BCH',
        'BCHUSD': 'BCH',
        'BCHUSDT': 'BCH',
        'BITCOIN-CASH': 'BCH',
        
        # Uniswap
        'UNI': 'UNI',
        'UNI-USD': 'UNI',
        'UNIUSD': 'UNI',
        'UNIUSDT': 'UNI',
        'UNISWAP': 'UNI',
    }
    
    # Direkte Mapping-Suche
    if symbol in symbol_mapping:
        return symbol_mapping[symbol]
    
    # Fallback: Entferne gängige Suffixe
    suffixes_to_remove = [
        '-USD', '-USDT', '-EUR', '-GBP', '-BTC', '-ETH',
        'USD', 'USDT', 'EUR', 'GBP', 'BTC', 'ETH'
    ]
    
    for suffix in suffixes_to_remove:
        if symbol.endswith(suffix):
            clean_symbol = symbol[:-len(suffix)]
            if len(clean_symbol) >= 2:  # Mindestens 2 Zeichen
                return clean_symbol
    
    # Fallback: Original-Symbol zurückgeben
    return symbol


def merge_duplicate_performance_data(performance_data: list) -> list:
    """Merged duplicate crypto symbols and averages their metrics"""
    
    # Gruppiere nach normalisiertem Symbol
    grouped_data = {}
    
    for item in performance_data:
        original_symbol = item.get('symbol', '')
        normalized_symbol = normalize_crypto_symbol(original_symbol)
        
        if normalized_symbol not in grouped_data:
            grouped_data[normalized_symbol] = []
        
        # Füge Original-Daten mit normalisiertem Symbol hinzu
        item_copy = item.copy()
        item_copy['symbol'] = normalized_symbol
        item_copy['original_symbol'] = original_symbol
        grouped_data[normalized_symbol].append(item_copy)
    
    # Merge Duplikate durch Durchschnittsbildung
    merged_data = []
    
    for symbol, items in grouped_data.items():
        if len(items) == 1:
            # Kein Duplikat, nehme Original
            merged_data.append(items[0])
        else:
            # Mehrere Einträge - merge durch Durchschnitt
            merged_item = {
                'symbol': symbol,
                'sharpe_ratio': sum(item.get('sharpe_ratio', 0) for item in items) / len(items),
                'annual_return': sum(item.get('annual_return', 0) for item in items) / len(items),
                'volatility': sum(item.get('volatility', 0) for item in items) / len(items),
                'max_drawdown': sum(item.get('max_drawdown', 0) for item in items) / len(items),
                'current_price': sum(item.get('current_price', 0) for item in items) / len(items),
                'timestamp': max(item.get('timestamp', '') for item in items),  # Neueste Timestamp
                'merged_count': len(items),
                'original_symbols': [item.get('original_symbol', '') for item in items]
            }
            merged_data.append(merged_item)
    
    # Sortiere nach Sharpe Ratio
    merged_data.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True)
    
    return merged_data


# Test der Normalisierung
if __name__ == "__main__":
    test_symbols = [
        'BTC', 'BTC-USD', 'BTCUSD', 'XBT', 'BITCOIN',
        'XRP', 'XRP-USD', 'XRPUSD', 'RIPPLE',
        'XLM', 'XLM-USD', 'XLMUSD', 'STELLAR',
        'ETH', 'ETH-USD', 'ETHUSD', 'ETHEREUM'
    ]
    
    print("Symbol Normalisierung Test:")
    for symbol in test_symbols:
        normalized = normalize_crypto_symbol(symbol)
        print(f"{symbol:12} -> {normalized}")
