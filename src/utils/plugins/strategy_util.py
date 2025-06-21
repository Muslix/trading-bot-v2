"""
Strategy Utility Plugin - backtesting, validation, and strategy management
"""

import json
import math
import statistics
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import pandas as pd

from ..base import UtilPlugin, UtilConfig


@dataclass
class Trade:
    """Represents a single trade."""
    timestamp: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    fees: float = 0.0
    strategy: str = "unknown"
    signal_strength: float = 1.0
    
    @property
    def value(self) -> float:
        return self.quantity * self.price


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    trades: List[Trade]


class StrategyUtil(UtilPlugin):
    """
    Strategy utility plugin for backtesting and strategy management.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.backtests_run = 0
        self.strategies_validated = 0
        self.last_backtest_time = None
        
        # Default trading parameters
        self.default_params = {
            "initial_capital": 10000.0,
            "commission": 0.001,  # 0.1%
            "slippage": 0.0005,   # 0.05%
            "position_size": 0.1,  # 10% of capital per trade
            "stop_loss": 0.05,     # 5%
            "take_profit": 0.10,   # 10%
            "max_positions": 5
        }
        
        # Built-in strategies
        self.built_in_strategies = {
            "sma_crossover": self._sma_crossover_strategy,
            "rsi_oversold": self._rsi_oversold_strategy,
            "bollinger_bounce": self._bollinger_bounce_strategy,
            "momentum": self._momentum_strategy,
            "mean_reversion": self._mean_reversion_strategy
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize strategy utility."""
        try:
            # Try to import optional dependencies
            try:
                import numpy as np
                import pandas as pd
                self.numpy_available = True
                self.pandas_available = True
                self.np = np
                self.pd = pd
            except ImportError:
                self.numpy_available = False
                self.pandas_available = False
                self.logger.warning("NumPy/Pandas not available - some features disabled")
            
            self.logger.info("Strategy utility initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize strategy utility: {e}")
            return False
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process strategy operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "backtest")
        
        if action == "backtest":
            return await self._run_backtest(data)
        elif action == "validate_strategy":
            return await self._validate_strategy(data)
        elif action == "optimize_parameters":
            return await self._optimize_parameters(data)
        elif action == "compare_strategies":
            return await self._compare_strategies(data)
        elif action == "calculate_metrics":
            return await self._calculate_performance_metrics(data)
        elif action == "generate_signals":
            return await self._generate_trading_signals(data)
        elif action == "paper_trade":
            return await self._run_paper_trade(data)
        elif action == "risk_analysis":
            return await self._analyze_strategy_risk(data)
        elif action == "get_strategies":
            return self._get_available_strategies()
        elif action == "export_strategy":
            return self._export_strategy(data)
        elif action == "import_strategy":
            return self._import_strategy(data)
        elif action == "get_stats":
            return self._get_strategy_stats()
        else:
            raise ValueError(f"Unknown strategy action: {action}")
    
    async def _run_backtest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a backtest on historical data."""
        try:
            strategy_name = data.get("strategy_name", "sma_crossover")
            price_data = data.get("price_data", [])
            parameters = data.get("parameters", {})
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            
            if not price_data:
                return {"success": False, "error": "No price data provided"}
            
            # Merge default parameters with provided ones
            backtest_params = {**self.default_params, **parameters}
            
            # Filter data by date range if provided
            if start_date or end_date:
                price_data = self._filter_by_date_range(price_data, start_date, end_date)
            
            if len(price_data) < 20:
                return {"success": False, "error": "Insufficient price data for backtest"}
            
            # Get strategy function
            if strategy_name in self.built_in_strategies:
                strategy_func = self.built_in_strategies[strategy_name]
            else:
                return {"success": False, "error": f"Unknown strategy: {strategy_name}"}
            
            # Run backtest
            result = await self._execute_backtest(
                strategy_func,
                price_data,
                backtest_params,
                strategy_name
            )
            
            self.backtests_run += 1
            self.last_backtest_time = datetime.now()
            
            return {
                "success": True,
                "backtest_result": asdict(result),
                "strategy_name": strategy_name,
                "parameters_used": backtest_params,
                "data_points": len(price_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_backtest(self, strategy_func: Callable, price_data: List[Dict], 
                              params: Dict[str, Any], strategy_name: str) -> BacktestResult:
        """Execute the actual backtest logic."""
        initial_capital = params["initial_capital"]
        current_capital = initial_capital
        commission = params["commission"]
        slippage = params["slippage"]
        position_size = params["position_size"]
        
        trades = []
        positions = {}  # symbol -> position info
        equity_curve = []
        max_equity = initial_capital
        max_drawdown = 0.0
        
        for i, candle in enumerate(price_data):
            current_price = float(candle["close"])
            timestamp = candle.get("timestamp", f"period_{i}")
            symbol = candle.get("symbol", "UNKNOWN")
            
            # Generate trading signals
            signals = strategy_func(price_data[:i+1], params)
            
            # Process signals
            for signal in signals:
                if signal["action"] == "buy" and symbol not in positions:
                    # Calculate position size
                    trade_amount = current_capital * position_size
                    quantity = trade_amount / (current_price * (1 + slippage))
                    fees = trade_amount * commission
                    
                    if current_capital >= trade_amount + fees:
                        # Execute buy
                        trade = Trade(
                            timestamp=timestamp,
                            symbol=symbol,
                            side="buy",
                            quantity=quantity,
                            price=current_price * (1 + slippage),
                            fees=fees,
                            strategy=strategy_name,
                            signal_strength=signal.get("strength", 1.0)
                        )
                        
                        trades.append(trade)
                        positions[symbol] = {
                            "quantity": quantity,
                            "entry_price": trade.price,
                            "entry_time": timestamp
                        }
                        current_capital -= (trade_amount + fees)
                
                elif signal["action"] == "sell" and symbol in positions:
                    # Execute sell
                    position = positions[symbol]
                    quantity = position["quantity"]
                    sell_value = quantity * current_price * (1 - slippage)
                    fees = sell_value * commission
                    
                    trade = Trade(
                        timestamp=timestamp,
                        symbol=symbol,
                        side="sell",
                        quantity=quantity,
                        price=current_price * (1 - slippage),
                        fees=fees,
                        strategy=strategy_name,
                        signal_strength=signal.get("strength", 1.0)
                    )
                    
                    trades.append(trade)
                    current_capital += (sell_value - fees)
                    del positions[symbol]
            
            # Calculate current equity (capital + unrealized P&L)
            unrealized_pnl = 0
            for symbol, position in positions.items():
                unrealized_pnl += position["quantity"] * (current_price - position["entry_price"])
            
            current_equity = current_capital + unrealized_pnl
            equity_curve.append(current_equity)
            
            # Track drawdown
            if current_equity > max_equity:
                max_equity = current_equity
            else:
                drawdown = (max_equity - current_equity) / max_equity
                max_drawdown = max(max_drawdown, drawdown)
        
        # Close remaining positions at final price
        final_price = float(price_data[-1]["close"])
        for symbol, position in positions.items():
            quantity = position["quantity"]
            sell_value = quantity * final_price * (1 - slippage)
            fees = sell_value * commission
            
            trade = Trade(
                timestamp=price_data[-1].get("timestamp", "final"),
                symbol=symbol,
                side="sell",
                quantity=quantity,
                price=final_price * (1 - slippage),
                fees=fees,
                strategy=strategy_name + "_close",
                signal_strength=0.5
            )
            
            trades.append(trade)
            current_capital += (sell_value - fees)
        
        # Calculate performance metrics
        final_capital = current_capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Trade analysis
        winning_trades = 0
        losing_trades = 0
        profits = []
        losses = []
        
        # Group trades by pairs (buy/sell)
        trade_pairs = self._group_trades_by_pairs(trades)
        
        for pair in trade_pairs:
            if len(pair) == 2:
                buy_trade, sell_trade = pair
                pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity - buy_trade.fees - sell_trade.fees
                
                if pnl > 0:
                    winning_trades += 1
                    profits.append(pnl)
                else:
                    losing_trades += 1
                    losses.append(abs(pnl))
        
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = statistics.mean(profits) if profits else 0
        avg_loss = statistics.mean(losses) if losses else 0
        profit_factor = sum(profits) / sum(losses) if losses else float('inf')
        
        # Calculate Sharpe ratio (simplified)
        if len(equity_curve) > 1:
            returns = [(equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1] 
                      for i in range(1, len(equity_curve))]
            if returns and statistics.stdev(returns) > 0:
                sharpe_ratio = (statistics.mean(returns) / statistics.stdev(returns)) * math.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Calculate Sortino ratio (simplified)
        if len(equity_curve) > 1:
            negative_returns = [r for r in returns if r < 0]
            if negative_returns and statistics.stdev(negative_returns) > 0:
                sortino_ratio = (statistics.mean(returns) / statistics.stdev(negative_returns)) * math.sqrt(252)
            else:
                sortino_ratio = sharpe_ratio
        else:
            sortino_ratio = 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=price_data[0].get("timestamp", "unknown"),
            end_date=price_data[-1].get("timestamp", "unknown"),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_consecutive_wins=self._calculate_consecutive_trades(trade_pairs, True),
            max_consecutive_losses=self._calculate_consecutive_trades(trade_pairs, False),
            trades=trades
        )
    
    def _group_trades_by_pairs(self, trades: List[Trade]) -> List[List[Trade]]:
        """Group buy/sell trades into pairs."""
        pairs = []
        open_positions = {}
        
        for trade in trades:
            symbol = trade.symbol
            
            if trade.side == "buy":
                if symbol not in open_positions:
                    open_positions[symbol] = []
                open_positions[symbol].append(trade)
            
            elif trade.side == "sell" and symbol in open_positions:
                if open_positions[symbol]:
                    buy_trade = open_positions[symbol].pop(0)
                    pairs.append([buy_trade, trade])
        
        return pairs
    
    def _calculate_consecutive_trades(self, trade_pairs: List[List[Trade]], winning: bool) -> int:
        """Calculate maximum consecutive wins or losses."""
        if not trade_pairs:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for pair in trade_pairs:
            if len(pair) == 2:
                buy_trade, sell_trade = pair
                pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity
                
                is_win = pnl > 0
                if is_win == winning:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
        
        return max_consecutive
    
    def _sma_crossover_strategy(self, price_data: List[Dict], params: Dict) -> List[Dict]:
        """Simple Moving Average crossover strategy."""
        if len(price_data) < 20:
            return []
        
        short_period = params.get("sma_short", 10)
        long_period = params.get("sma_long", 20)
        
        if len(price_data) < long_period:
            return []
        
        # Calculate SMAs
        closes = [float(p["close"]) for p in price_data]
        short_sma = sum(closes[-short_period:]) / short_period
        long_sma = sum(closes[-long_period:]) / long_period
        
        # Previous SMAs
        if len(price_data) > long_period:
            prev_closes = closes[:-1]
            prev_short_sma = sum(prev_closes[-short_period:]) / short_period
            prev_long_sma = sum(prev_closes[-long_period:]) / long_period
            
            # Crossover signals
            if prev_short_sma <= prev_long_sma and short_sma > long_sma:
                return [{"action": "buy", "strength": 0.8, "reason": "SMA bullish crossover"}]
            elif prev_short_sma >= prev_long_sma and short_sma < long_sma:
                return [{"action": "sell", "strength": 0.8, "reason": "SMA bearish crossover"}]
        
        return []
    
    def _rsi_oversold_strategy(self, price_data: List[Dict], params: Dict) -> List[Dict]:
        """RSI oversold/overbought strategy."""
        if len(price_data) < 15:
            return []
        
        rsi_period = params.get("rsi_period", 14)
        oversold_level = params.get("rsi_oversold", 30)
        overbought_level = params.get("rsi_overbought", 70)
        
        # Calculate RSI
        closes = [float(p["close"]) for p in price_data]
        rsi = self._calculate_rsi(closes, rsi_period)
        
        if rsi is None:
            return []
        
        signals = []
        if rsi < oversold_level:
            signals.append({"action": "buy", "strength": 0.7, "reason": f"RSI oversold ({rsi:.1f})"})
        elif rsi > overbought_level:
            signals.append({"action": "sell", "strength": 0.7, "reason": f"RSI overbought ({rsi:.1f})"})
        
        return signals
    
    def _bollinger_bounce_strategy(self, price_data: List[Dict], params: Dict) -> List[Dict]:
        """Bollinger Bands bounce strategy."""
        if len(price_data) < 20:
            return []
        
        bb_period = params.get("bb_period", 20)
        bb_std = params.get("bb_std", 2)
        
        closes = [float(p["close"]) for p in price_data]
        current_price = closes[-1]
        
        # Calculate Bollinger Bands
        recent_closes = closes[-bb_period:]
        sma = sum(recent_closes) / bb_period
        variance = sum((p - sma) ** 2 for p in recent_closes) / bb_period
        std_dev = math.sqrt(variance)
        
        upper_band = sma + (bb_std * std_dev)
        lower_band = sma - (bb_std * std_dev)
        
        signals = []
        if current_price <= lower_band:
            signals.append({"action": "buy", "strength": 0.6, "reason": "Price at lower Bollinger Band"})
        elif current_price >= upper_band:
            signals.append({"action": "sell", "strength": 0.6, "reason": "Price at upper Bollinger Band"})
        
        return signals
    
    def _momentum_strategy(self, price_data: List[Dict], params: Dict) -> List[Dict]:
        """Momentum strategy based on price changes."""
        if len(price_data) < 10:
            return []
        
        momentum_period = params.get("momentum_period", 5)
        momentum_threshold = params.get("momentum_threshold", 0.02)  # 2%
        
        closes = [float(p["close"]) for p in price_data]
        
        if len(closes) < momentum_period + 1:
            return []
        
        # Calculate momentum
        current_price = closes[-1]
        past_price = closes[-momentum_period - 1]
        momentum = (current_price - past_price) / past_price
        
        signals = []
        if momentum > momentum_threshold:
            signals.append({"action": "buy", "strength": 0.6, "reason": f"Strong upward momentum ({momentum*100:.1f}%)"})
        elif momentum < -momentum_threshold:
            signals.append({"action": "sell", "strength": 0.6, "reason": f"Strong downward momentum ({momentum*100:.1f}%)"})
        
        return signals
    
    def _mean_reversion_strategy(self, price_data: List[Dict], params: Dict) -> List[Dict]:
        """Mean reversion strategy."""
        if len(price_data) < 20:
            return []
        
        lookback_period = params.get("mean_reversion_period", 20)
        deviation_threshold = params.get("deviation_threshold", 0.05)  # 5%
        
        closes = [float(p["close"]) for p in price_data]
        current_price = closes[-1]
        
        # Calculate mean and deviation
        recent_closes = closes[-lookback_period:]
        mean_price = sum(recent_closes) / len(recent_closes)
        deviation = (current_price - mean_price) / mean_price
        
        signals = []
        if deviation < -deviation_threshold:
            signals.append({"action": "buy", "strength": 0.5, "reason": f"Price below mean ({deviation*100:.1f}%)"})
        elif deviation > deviation_threshold:
            signals.append({"action": "sell", "strength": 0.5, "reason": f"Price above mean ({deviation*100:.1f}%)"})
        
        return signals
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _filter_by_date_range(self, price_data: List[Dict], start_date: Optional[str], 
                            end_date: Optional[str]) -> List[Dict]:
        """Filter price data by date range."""
        filtered_data = price_data.copy()
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_data = [
                p for p in filtered_data 
                if datetime.fromisoformat(p.get("timestamp", "1970-01-01")) >= start_dt
            ]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_data = [
                p for p in filtered_data 
                if datetime.fromisoformat(p.get("timestamp", "2100-01-01")) <= end_dt
            ]
        
        return filtered_data
    
    async def _validate_strategy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a trading strategy."""
        try:
            strategy_code = data.get("strategy_code", "")
            strategy_name = data.get("strategy_name", "custom")
            
            if not strategy_code:
                return {"success": False, "error": "No strategy code provided"}
            
            validation_results = {
                "syntax_valid": True,
                "security_issues": [],
                "performance_warnings": [],
                "recommendations": []
            }
            
            # Basic syntax validation
            try:
                compile(strategy_code, '<strategy>', 'exec')
            except SyntaxError as e:
                validation_results["syntax_valid"] = False
                validation_results["security_issues"].append(f"Syntax error: {e}")
            
            # Security checks
            dangerous_imports = ['os', 'sys', 'subprocess', 'eval', 'exec']
            for danger in dangerous_imports:
                if danger in strategy_code:
                    validation_results["security_issues"].append(f"Potentially dangerous: {danger}")
            
            # Performance warnings
            if 'sleep' in strategy_code:
                validation_results["performance_warnings"].append("Strategy contains sleep - may slow down backtesting")
            
            if strategy_code.count('for') > 5:
                validation_results["performance_warnings"].append("Many loops detected - consider optimization")
            
            # Recommendations
            if 'def generate_signals' not in strategy_code:
                validation_results["recommendations"].append("Strategy should have a 'generate_signals' function")
            
            if 'params' not in strategy_code:
                validation_results["recommendations"].append("Strategy should accept parameters for optimization")
            
            self.strategies_validated += 1
            
            return {
                "success": True,
                "strategy_name": strategy_name,
                "validation_results": validation_results,
                "is_valid": validation_results["syntax_valid"] and not validation_results["security_issues"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Strategy validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_available_strategies(self) -> Dict[str, Any]:
        """Get list of available built-in strategies."""
        strategy_info = {}
        
        for name, func in self.built_in_strategies.items():
            strategy_info[name] = {
                "description": func.__doc__ or "No description available",
                "parameters": self._get_strategy_parameters(name)
            }
        
        return {
            "success": True,
            "built_in_strategies": strategy_info,
            "total_strategies": len(strategy_info),
            "default_parameters": self.default_params
        }
    
    def _get_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """Get default parameters for a strategy."""
        param_maps = {
            "sma_crossover": {"sma_short": 10, "sma_long": 20},
            "rsi_oversold": {"rsi_period": 14, "rsi_oversold": 30, "rsi_overbought": 70},
            "bollinger_bounce": {"bb_period": 20, "bb_std": 2},
            "momentum": {"momentum_period": 5, "momentum_threshold": 0.02},
            "mean_reversion": {"mean_reversion_period": 20, "deviation_threshold": 0.05}
        }
        
        return param_maps.get(strategy_name, {})
    
    def _get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy utility statistics."""
        return {
            "backtests_run": self.backtests_run,
            "strategies_validated": self.strategies_validated,
            "last_backtest_time": self.last_backtest_time.isoformat() if self.last_backtest_time else None,
            "available_strategies": list(self.built_in_strategies.keys()),
            "default_parameters": self.default_params,
            "features": {
                "backtesting": True,
                "strategy_validation": True,
                "parameter_optimization": True,
                "risk_analysis": True,
                "paper_trading": True,
                "strategy_comparison": True
            },
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }