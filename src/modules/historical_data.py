"""
Historical Data Module - Echte historische Krypto-Daten
Erweiterte Risiko-Metriken für genauere Portfolio-Analyse
"""

import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from src.utils.decorators import log_performance

warnings.filterwarnings("ignore")


class HistoricalDataManager:
    """Manager für historische Krypto-Daten mit verschiedenen Zeiträumen"""

    def __init__(self):
        self.crypto_symbol_mapping = {
            # Haupt-Kryptowährungen mit Yahoo Finance Symbolen
            "BTC": "BTC-USD",
            "ETH": "ETH-USD",
            "BNB": "BNB-USD",
            "ADA": "ADA-USD",
            "DOT": "DOT-USD",
            "XRP": "XRP-USD",
            "LTC": "LTC-USD",
            "LINK": "LINK-USD",
            "BCH": "BCH-USD",
            "XLM": "XLM-USD",
            "DOGE": "DOGE-USD",
            "UNI": "UNI-USD",
            "THETA": "THETA-USD",
            "VET": "VET-USD",
            "FIL": "FIL-USD",
            "TRX": "TRX-USD",
            "ETC": "ETC-USD",
            "XMR": "XMR-USD",
            "SOL": "SOL-USD",
            "AAVE": "AAVE-USD",
            "EOS": "EOS-USD",
            "ATOM": "ATOM-USD",
            "MKR": "MKR-USD",
            "COMP": "COMP-USD",
            "ZEC": "ZEC-USD",
            "DASH": "DASH-USD",
            "NEO": "NEO-USD",
            "XTZ": "XTZ-USD",
            "AVAX": "AVAX-USD",
            "ALGO": "ALGO-USD",
            "NEAR": "NEAR-USD",
            "FTM": "FTM-USD",
            "MATIC": "MATIC-USD",
            "MANA": "MANA-USD",
            "SAND": "SAND-USD",
            "AXS": "AXS-USD",
            "CRO": "CRO-USD",
            "SHIB": "SHIB-USD",
        }

    @log_performance
    def fetch_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Lade historische Daten für einen Coin"""
        try:
            yahoo_symbol = self.crypto_symbol_mapping.get(symbol, "{symbol}-USD")

            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                print("⚠️ Keine Daten für {symbol} verfügbar")
                return None

            return hist

        except Exception as e:
            print("❌ Fehler beim Laden von {symbol}: {e}")
            return None

    @log_performance
    def calculate_advanced_metrics(self, symbol: str, period: str = "2y") -> Dict:
        """Berechne erweiterte Risiko-Metriken für einen Coin"""
        try:
            hist_data = self.fetch_historical_data(symbol, period)

            if hist_data is None or len(hist_data) < 30:
                return self._get_fallback_metrics(symbol)

            # Berechne tägliche Returns
            prices = hist_data["Close"]
            returns = prices.pct_change().dropna()

            if len(returns) < 30:
                return self._get_fallback_metrics(symbol)

            # Basis-Metriken
            annual_return = returns.mean() * 365
            volatility = returns.std() * np.sqrt(365)

            # Sharpe Ratio (Risk-free rate 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0

            # Sortino Ratio (nur negative Volatilität)
            negative_returns = returns[returns < 0]
            downside_volatility = (
                negative_returns.std() * np.sqrt(365) if len(negative_returns) > 0 else volatility
            )
            sortino_ratio = (
                (annual_return - risk_free_rate) / downside_volatility
                if downside_volatility > 0
                else 0
            )

            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min()

            # Value at Risk (95% confidence)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)

            # Conditional Value at Risk (Expected Shortfall)
            cvar_95 = (
                returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
            )

            # Beta vs Bitcoin (wenn BTC Daten verfügbar)
            beta = self._calculate_beta_vs_btc(returns)

            # Calmar Ratio
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

            # Win Rate
            win_rate = len(returns[returns > 0]) / len(returns)

            # Aktueller Preis
            current_price = float(prices.iloc[-1])

            return {
                "symbol": symbol,
                "period": period,
                "data_points": len(returns),
                "sharpe_ratio": round(float(sharpe_ratio), 4),
                "sortino_ratio": round(float(sortino_ratio), 4),
                "calmar_ratio": round(float(calmar_ratio), 4),
                "annual_return": round(float(annual_return * 100), 2),
                "volatility": round(float(volatility * 100), 2),
                "max_drawdown": round(float(max_drawdown * 100), 2),
                "var_95": round(float(var_95 * 100), 2),
                "var_99": round(float(var_99 * 100), 2),
                "cvar_95": round(float(cvar_95 * 100), 2),
                "beta_vs_btc": round(float(beta), 4),
                "win_rate": round(float(win_rate * 100), 2),
                "current_price": round(current_price, 2),
            }

        except Exception as e:
            print("❌ Fehler bei Metriken für {symbol}: {e}")
            return self._get_fallback_metrics(symbol)

    def _calculate_beta_vs_btc(self, returns: pd.Series) -> float:
        """Berechne Beta vs Bitcoin"""
        try:
            btc_data = self.fetch_historical_data("BTC", period="2y")
            if btc_data is None:
                return 1.0

            btc_returns = btc_data["Close"].pct_change().dropna()

            # Synchronisiere die Zeiträume
            common_dates = returns.index.intersection(btc_returns.index)
            if len(common_dates) < 30:
                return 1.0

            aligned_returns = returns.loc[common_dates]
            aligned_btc_returns = btc_returns.loc[common_dates]

            # Berechne Beta (Kovarianz / Varianz)
            covariance = np.cov(aligned_returns, aligned_btc_returns)[0, 1]
            btc_variance = np.var(aligned_btc_returns)

            beta = covariance / btc_variance if btc_variance > 0 else 1.0
            return beta

        except Exception:
            return 1.0

    def _get_fallback_metrics(self, symbol: str) -> Dict:
        """Fallback-Metriken wenn keine echten Daten verfügbar"""
        # Simulierte Daten basierend auf Symbol-Hash für Konsistenz
        np.random.seed(hash(symbol) % 10000)

        annual_return = np.random.normal(0.15, 0.40)  # 15% ± 40%
        volatility = np.random.uniform(0.30, 1.20)  # 30-120% Volatilität

        sharpe_ratio = (annual_return - 0.02) / volatility if volatility > 0 else 0
        sortino_ratio = sharpe_ratio * 1.2  # Typisch höher als Sharpe
        max_drawdown = np.random.uniform(-0.80, -0.20)  # -20% bis -80%

        return {
            "symbol": symbol,
            "period": "2y",
            "data_points": 730,
            "sharpe_ratio": round(sharpe_ratio, 4),
            "sortino_ratio": round(sortino_ratio, 4),
            "calmar_ratio": round(annual_return / abs(max_drawdown), 4),
            "annual_return": round(annual_return * 100, 2),
            "volatility": round(volatility * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "var_95": round(np.random.uniform(-8, -2), 2),
            "var_99": round(np.random.uniform(-15, -5), 2),
            "cvar_95": round(np.random.uniform(-12, -4), 2),
            "beta_vs_btc": round(np.random.uniform(0.5, 2.0), 4),
            "win_rate": round(np.random.uniform(40, 60), 2),
            "current_price": round(np.random.uniform(0.1, 50000), 2),
            "data_source": "simulated",
        }


def calculate_crypto_metrics_enhanced(symbol: str, period: str = "2y") -> Tuple[str, Dict]:
    """Enhanced Version der Crypto-Metriken mit echten Daten"""
    data_manager = HistoricalDataManager()
    metrics = data_manager.calculate_advanced_metrics(symbol, period)
    return (symbol, metrics)


def _analyze_symbol_with_period(args):
    """Helper function for multiprocessing"""
    symbol, period = args
    return calculate_crypto_metrics_enhanced(symbol, period)


@log_performance
def analyze_crypto_portfolio_enhanced(
    crypto_symbols: List[str], period: str = "2y"
) -> Dict[str, Dict]:
    """Erweiterte Portfolio-Analyse mit echten historischen Daten"""
    print("🔄 Analysiere {len(crypto_symbols)} Kryptowährungen mit {period} historischen Daten...")
    print("📊 Lade echte Marktdaten für erweiterte Risiko-Metriken...")

    from multiprocessing import Pool

    # Erstelle Argument-Liste für Pool
    args = [(symbol, period) for symbol in crypto_symbols]

    with Pool() as pool:
        results = pool.map(_analyze_symbol_with_period, args)

    return dict(results)


def get_analysis_timeframes() -> List[str]:
    """Verfügbare Zeiträume für die Analyse"""
    return ["1y", "2y", "3y", "5y", "max"]


def compare_timeframes(symbol: str, timeframes: List[str] = None) -> Dict[str, Dict]:
    """Vergleiche Metriken über verschiedene Zeiträume"""
    if timeframes is None:
        timeframes = ["1y", "2y", "3y"]

    data_manager = HistoricalDataManager()
    results = {}

    for period in timeframes:
        metrics = data_manager.calculate_advanced_metrics(symbol, period)
        results[period] = metrics

    return results
