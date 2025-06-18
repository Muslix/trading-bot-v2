"""
Production Logger - Enhanced logging for production debugging
Provides detailed logging of calculations, values, and data sources for production verification
"""

import json
import logging
import logging.handlers
import os
import glob
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import pandas as pd


class ProductionLogger:
    """Enhanced logger for production debugging of calculations and values"""
    
    def __init__(self, log_dir: str = "logs", component: str = "production"):
        self.log_dir = log_dir
        self.component = component
        
        # Create logs directory structure if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(f"{log_dir}/archive", exist_ok=True)
        
        # Set up different log files for different types of data
        self.setup_loggers()
        
        # Schedule daily cleanup
        self._schedule_cleanup()
        
    def setup_loggers(self):
        """Set up specialized loggers for different data types"""
        
        # Main production logger
        self.main_logger = self._create_logger(
            f"{self.component}_main",
            f"{self.log_dir}/{self.component}_main.log",
            logging.INFO
        )
        
        # Calculation debugging logger
        self.calc_logger = self._create_logger(
            f"{self.component}_calculations", 
            f"{self.log_dir}/{self.component}_calculations.log",
            logging.DEBUG
        )
        
        # Data source logger
        self.data_logger = self._create_logger(
            f"{self.component}_data",
            f"{self.log_dir}/{self.component}_data.log", 
            logging.DEBUG
        )
        
        # Performance metrics logger
        self.metrics_logger = self._create_logger(
            f"{self.component}_metrics",
            f"{self.log_dir}/{self.component}_metrics.log",
            logging.INFO
        )
        
        # Arbitrage opportunities logger
        self.arbitrage_logger = self._create_logger(
            f"{self.component}_arbitrage",
            f"{self.log_dir}/{self.component}_arbitrage.log",
            logging.INFO
        )
        
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """Create a specialized logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        # File handler
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_startup(self, config: Dict[str, Any]):
        """Log bot startup with configuration"""
        self.main_logger.info("=" * 80)
        self.main_logger.info("🚀 PRODUCTION BOT STARTUP")
        self.main_logger.info("=" * 80)
        self.main_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self.main_logger.info(f"Configuration: {json.dumps(config, indent=2, default=str)}")
        
    def log_data_source_health(self, health_data: Dict[str, Any]):
        """Log data source health status"""
        self.data_logger.info("=" * 60)
        self.data_logger.info("🔍 DATA SOURCE HEALTH CHECK")
        self.data_logger.info("=" * 60)
        
        for source, status in health_data.items():
            self.data_logger.info(f"Source: {source}")
            self.data_logger.info(f"Status: {json.dumps(status, indent=2, default=str)}")
    
    def log_price_data(self, symbol: str, exchange: str, price: float, timestamp: datetime = None):
        """Log individual price data points for verification"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.data_logger.debug(f"PRICE_DATA | {symbol} | {exchange} | ${price:,.4f} | {timestamp.isoformat()}")
    
    def log_arbitrage_calculation(self, symbol: str, prices: Dict[str, float], opportunities: List[Dict]):
        """Log detailed arbitrage calculation for debugging"""
        self.arbitrage_logger.info("=" * 80)
        self.arbitrage_logger.info(f"🔍 ARBITRAGE CALCULATION: {symbol}")
        self.arbitrage_logger.info("=" * 80)
        self.arbitrage_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Log input prices
        self.arbitrage_logger.info("INPUT PRICES:")
        for exchange, price in prices.items():
            self.arbitrage_logger.info(f"  {exchange}: ${price:,.4f}")
        
        # Calculate and log price spread
        if len(prices) >= 2:
            min_price = min(prices.values())
            max_price = max(prices.values())
            spread_pct = ((max_price - min_price) / min_price) * 100
            self.arbitrage_logger.info(f"Price Spread: {spread_pct:.4f}%")
        
        # Log opportunities found
        self.arbitrage_logger.info(f"OPPORTUNITIES FOUND: {len(opportunities)}")
        for i, opp in enumerate(opportunities):
            self.arbitrage_logger.info(f"  Opportunity {i+1}:")
            self.arbitrage_logger.info(f"    Buy: {opp.get('buy_exchange')} @ ${opp.get('buy_price', 0):,.4f}")
            self.arbitrage_logger.info(f"    Sell: {opp.get('sell_exchange')} @ ${opp.get('sell_price', 0):,.4f}")
            self.arbitrage_logger.info(f"    Profit: {opp.get('profit_percentage', 0):.4f}%")
            self.arbitrage_logger.info(f"    Amount: ${opp.get('potential_profit', 0):,.2f}")
    
    def log_portfolio_calculation(self, symbols: List[str], results: Dict[str, Any], log_level: str = "summary"):
        """Log portfolio calculation with configurable verbosity"""
        
        # Only log every 10th calculation to reduce verbosity (unless forced)
        if not hasattr(self, '_calc_counter'):
            self._calc_counter = 0
        self._calc_counter += 1
        
        # Summary mode: only log every 10th calculation or significant changes
        if log_level == "summary" and self._calc_counter % 10 != 0:
            return
            
        self.calc_logger.info("=" * 80)
        self.calc_logger.info(f"📊 PORTFOLIO CALCULATION")
        self.calc_logger.info("=" * 80)
        self.calc_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self.calc_logger.info(f"Symbols analyzed: {len(symbols)}")
        
        if log_level == "summary":
            # Only log summary information
            if "portfolio_analysis" in results:
                total_value = results.get("total_portfolio_value", 0)
                self.calc_logger.info(f"Total Portfolio Value: ${total_value:,.2f}")
                
                # Log only top 5 performers
                portfolio = results["portfolio_analysis"]
                sorted_cryptos = sorted(
                    portfolio.items(), 
                    key=lambda x: x[1].get('current_price', 0), 
                    reverse=True
                )[:5]
                
                self.calc_logger.info("Top 5 by Price:")
                for symbol, data in sorted_cryptos:
                    self.calc_logger.info(f"  {symbol}: ${data.get('current_price', 0):,.4f}")
        else:
            # Full detailed logging
            self.calc_logger.info(f"Symbols: {', '.join(symbols)}")
            
            if "portfolio_analysis" in results:
                portfolio = results["portfolio_analysis"]
                total_value = results.get("total_portfolio_value", 0)
                
                self.calc_logger.info(f"Total Portfolio Value: ${total_value:,.2f}")
                
                # Log individual symbol analysis
                for symbol, data in portfolio.items():
                    self.calc_logger.info(f"  {symbol}:")
                    self.calc_logger.info(f"    Price: ${data.get('current_price', 0):,.4f}")
                    self.calc_logger.info(f"    Value: ${data.get('value', 0):,.2f}")
                    self.calc_logger.info(f"    Market Cap: ${data.get('market_cap', 0):,.0f}")
                    self.calc_logger.info(f"    Volume 24h: ${data.get('volume_24h', 0):,.0f}")
                    if data.get('data_source'):
                        self.calc_logger.info(f"    Data Source: {data['data_source']}")
        
        # Log any errors
        if "error" in results:
            self.calc_logger.error(f"Portfolio calculation error: {results['error']}")
    
    def _schedule_cleanup(self):
        """Initialize cleanup tracking"""
        self.last_cleanup = datetime.now()
    
    def cleanup_old_logs(self, max_age_days: int = 7):
        """Archive and cleanup old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Find old log files
            log_pattern = f"{self.log_dir}/*.log"
            old_files = []
            
            for log_file in glob.glob(log_pattern):
                file_path = Path(log_file)
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    old_files.append(file_path)
            
            if old_files:
                # Archive old files
                archive_date = datetime.now().strftime("%Y%m%d")
                for old_file in old_files:
                    archive_name = f"{old_file.stem}_{archive_date}{old_file.suffix}"
                    archive_path = Path(self.log_dir) / "archive" / archive_name
                    
                    # Move to archive
                    old_file.rename(archive_path)
                    self.main_logger.info(f"Archived old log file: {old_file.name} -> {archive_name}")
                
                self.main_logger.info(f"Cleanup completed: {len(old_files)} files archived")
            
            # Update last cleanup time
            self.last_cleanup = datetime.now()
            
        except Exception as e:
            self.main_logger.error(f"Log cleanup failed: {e}")
    
    def should_cleanup(self) -> bool:
        """Check if daily cleanup is needed"""
        if not hasattr(self, 'last_cleanup'):
            return True
        
        # Cleanup once per day
        return (datetime.now() - self.last_cleanup).days >= 1
    
    def rotate_logs_if_needed(self):
        """Manually rotate large log files"""
        try:
            max_size = 5 * 1024 * 1024  # 5MB
            
            log_files = [
                f"{self.log_dir}/{self.component}_main.log",
                f"{self.log_dir}/{self.component}_calculations.log",
                f"{self.log_dir}/{self.component}_data.log",
                f"{self.log_dir}/{self.component}_metrics.log",
                f"{self.log_dir}/{self.component}_arbitrage.log"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file) and os.path.getsize(log_file) > max_size:
                    # Create backup
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{log_file}.{timestamp}"
                    os.rename(log_file, backup_name)
                    
                    # Move backup to archive
                    archive_path = f"{self.log_dir}/archive/{os.path.basename(backup_name)}"
                    os.rename(backup_name, archive_path)
                    
                    self.main_logger.info(f"Rotated large log file: {log_file}")
                    
        except Exception as e:
            if hasattr(self, 'main_logger'):
                self.main_logger.error(f"Log rotation failed: {e}")
    
    def log_crypto_metrics(self, symbol: str, metrics: Dict[str, Any], historical_data: Optional[pd.DataFrame] = None):
        """Log detailed crypto metrics calculation for debugging"""
        self.metrics_logger.info("=" * 80)
        self.metrics_logger.info(f"📈 CRYPTO METRICS: {symbol}")
        self.metrics_logger.info("=" * 80)
        self.metrics_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Log historical data info
        if historical_data is not None:
            self.metrics_logger.info(f"Historical Data Points: {len(historical_data)}")
            self.metrics_logger.info(f"Date Range: {historical_data.index[0]} to {historical_data.index[-1]}")
            self.metrics_logger.info(f"Price Range: ${historical_data['Close'].min():,.4f} - ${historical_data['Close'].max():,.4f}")
        
        # Log calculated metrics
        if "error" not in metrics:
            self.metrics_logger.info("CALCULATED METRICS:")
            self.metrics_logger.info(f"  Current Price: ${metrics.get('current_price', 0):,.4f}")
            self.metrics_logger.info(f"  Annual Return: {metrics.get('annual_return', 0):.2f}%")
            self.metrics_logger.info(f"  Volatility: {metrics.get('volatility', 0):.2f}%")
            self.metrics_logger.info(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
            self.metrics_logger.info(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.4f}")
            self.metrics_logger.info(f"  Calmar Ratio: {metrics.get('calmar_ratio', 0):.4f}")
            self.metrics_logger.info(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            self.metrics_logger.info(f"  VaR 95%: {metrics.get('var_95', 0):.2f}%")
            self.metrics_logger.info(f"  VaR 99%: {metrics.get('var_99', 0):.2f}%")
            self.metrics_logger.info(f"  CVaR 95%: {metrics.get('cvar_95', 0):.2f}%")
            self.metrics_logger.info(f"  Beta vs BTC: {metrics.get('beta_vs_btc', 0):.4f}")
            self.metrics_logger.info(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
            self.metrics_logger.info(f"  Data Source: {metrics.get('data_source', 'unknown')}")
            self.metrics_logger.info(f"  Period: {metrics.get('period', 'unknown')}")
        else:
            self.metrics_logger.error(f"Metrics calculation error: {metrics['error']}")
    
    def log_alert_decision(self, alert_type: str, symbol: str, decision: bool, reason: str, data: Dict[str, Any] = None):
        """Log alert decision making for debugging"""
        self.main_logger.info("=" * 60)
        self.main_logger.info(f"🚨 ALERT DECISION: {alert_type}")
        self.main_logger.info("=" * 60)
        self.main_logger.info(f"Symbol: {symbol}")
        self.main_logger.info(f"Decision: {'SEND' if decision else 'SKIP'}")
        self.main_logger.info(f"Reason: {reason}")
        if data:
            self.main_logger.info(f"Data: {json.dumps(data, indent=2, default=str)}")
    
    def log_performance_comparison(self, symbol: str, old_metrics: Dict, new_metrics: Dict):
        """Log performance comparison for change detection debugging"""
        self.calc_logger.info("=" * 80)
        self.calc_logger.info(f"📊 PERFORMANCE COMPARISON: {symbol}")
        self.calc_logger.info("=" * 80)
        
        # Compare key metrics
        key_metrics = ["sharpe_ratio", "annual_return", "volatility", "max_drawdown"]
        
        for metric in key_metrics:
            old_val = old_metrics.get(metric, 0)
            new_val = new_metrics.get(metric, 0)
            change = new_val - old_val
            change_pct = (change / old_val * 100) if old_val != 0 else 0
            
            self.calc_logger.info(f"  {metric}:")
            self.calc_logger.info(f"    Old: {old_val:.4f}")
            self.calc_logger.info(f"    New: {new_val:.4f}")
            self.calc_logger.info(f"    Change: {change:+.4f} ({change_pct:+.2f}%)")
    
    def log_database_operation(self, operation: str, table: str, data: Dict[str, Any], result: Any = None):
        """Log database operations for debugging"""
        self.data_logger.debug(f"DB_OP | {operation} | {table} | Result: {result}")
        if self.data_logger.isEnabledFor(logging.DEBUG):
            self.data_logger.debug(f"DB_DATA | {json.dumps(data, default=str)}")
    
    def log_cycle_summary(self, cycle_type: str, duration: float, stats: Dict[str, Any]):
        """Log cycle completion summary"""
        self.main_logger.info("=" * 60)
        self.main_logger.info(f"✅ {cycle_type.upper()} CYCLE COMPLETED")
        self.main_logger.info("=" * 60)
        self.main_logger.info(f"Duration: {duration:.2f} seconds")
        self.main_logger.info(f"Stats: {json.dumps(stats, indent=2, default=str)}")
    
    def log_error_with_context(self, error: Exception, context: str, data: Dict[str, Any] = None):
        """Log errors with full context for debugging"""
        self.main_logger.error("=" * 80)
        self.main_logger.error(f"❌ ERROR in {context}")
        self.main_logger.error("=" * 80)
        self.main_logger.error(f"Error: {type(error).__name__}: {str(error)}")
        if data:
            self.main_logger.error(f"Context Data: {json.dumps(data, indent=2, default=str)}")
        
        # Also log to calculation logger if it's calculation-related
        if "calculation" in context.lower() or "metric" in context.lower():
            self.calc_logger.error(f"CALC_ERROR | {context} | {str(error)}")
    
    def rotate_logs(self, max_size_mb: int = 100):
        """Rotate log files if they get too large"""
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'baseFilename'):
                filepath = handler.baseFilename
                if os.path.exists(filepath):
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        # Rotate by renaming with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        rotated_name = f"{filepath}.{timestamp}"
                        os.rename(filepath, rotated_name)
                        self.main_logger.info(f"Rotated log file: {filepath} -> {rotated_name}")


# Global production logger instance
production_logger = ProductionLogger()


def get_production_logger(component: str = "production") -> ProductionLogger:
    """Get a production logger instance for a specific component"""
    return ProductionLogger(component=component)