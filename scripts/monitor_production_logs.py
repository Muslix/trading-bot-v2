#!/usr/bin/env python3
"""
Production Log Monitor - Monitor and analyze production logs in real-time
Provides insights into bot performance, calculations, and data quality
"""

import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class ProductionLogMonitor:
    """Monitor production logs for insights and issues"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_files = {}
        self.stats = {
            "arbitrage_opportunities": 0,
            "performance_analyses": 0,
            "alerts_sent": 0,
            "errors": 0,
            "data_points_collected": 0,
            "last_arbitrage_opportunity": None,
            "last_performance_check": None,
            "session_start": datetime.now()
        }
        
    def find_log_files(self):
        """Find all production log files"""
        if not self.log_dir.exists():
            print(f"❌ Log directory {self.log_dir} does not exist!")
            return
            
        log_patterns = [
            "*_main.log",
            "*_calculations.log", 
            "*_data.log",
            "*_metrics.log",
            "*_arbitrage.log"
        ]
        
        for pattern in log_patterns:
            files = list(self.log_dir.glob(pattern))
            for file in files:
                log_type = file.stem.split('_')[-1]
                self.log_files[log_type] = file
                
        print(f"📁 Found {len(self.log_files)} log files:")
        for log_type, file in self.log_files.items():
            print(f"   {log_type}: {file}")
    
    def tail_logs(self, lines: int = 50):
        """Show recent log entries"""
        print("📄 Recent Log Entries:")
        print("=" * 80)
        
        for log_type, file in self.log_files.items():
            if file.exists():
                print(f"\n🔍 {log_type.upper()} LOG ({file}):")
                print("-" * 60)
                
                try:
                    with open(file, 'r') as f:
                        content = f.readlines()
                        recent_lines = content[-lines:] if len(content) > lines else content
                        
                        for line in recent_lines:
                            print(line.rstrip())
                            
                except Exception as e:
                    print(f"❌ Error reading {file}: {e}")
    
    def analyze_arbitrage_logs(self):
        """Analyze arbitrage calculation logs"""
        arbitrage_file = self.log_files.get('arbitrage')
        if not arbitrage_file or not arbitrage_file.exists():
            print("⚠️ No arbitrage log file found")
            return
            
        print("\n🔍 ARBITRAGE ANALYSIS:")
        print("=" * 60)
        
        opportunities = []
        symbols_analyzed = set()
        
        try:
            with open(arbitrage_file, 'r') as f:
                content = f.read()
                
                # Extract arbitrage opportunities
                opp_pattern = r'ARBITRAGE CALCULATION: (\w+).*?Profit: ([\d.]+)%'
                matches = re.findall(opp_pattern, content, re.DOTALL)
                
                for symbol, profit in matches:
                    symbols_analyzed.add(symbol)
                    profit_pct = float(profit)
                    if profit_pct >= 1.0:  # Only significant opportunities
                        opportunities.append((symbol, profit_pct))
                        
        except Exception as e:
            print(f"❌ Error analyzing arbitrage logs: {e}")
            return
            
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"📊 Symbols Analyzed: {len(symbols_analyzed)}")
        print(f"🎯 Opportunities Found: {len(opportunities)}")
        
        if opportunities:
            print("\n🏆 Top Arbitrage Opportunities:")
            for i, (symbol, profit) in enumerate(opportunities[:10]):
                print(f"   {i+1}. {symbol}: {profit:.2f}%")
        
        self.stats["arbitrage_opportunities"] = len(opportunities)
        
    def analyze_metrics_logs(self):
        """Analyze crypto metrics calculation logs"""
        metrics_file = self.log_files.get('metrics')
        if not metrics_file or not metrics_file.exists():
            print("⚠️ No metrics log file found")
            return
            
        print("\n📈 METRICS ANALYSIS:")
        print("=" * 60)
        
        metrics_data = []
        
        try:
            with open(metrics_file, 'r') as f:
                content = f.read()
                
                # Extract metrics calculations
                metric_pattern = r'CRYPTO METRICS: (\w+).*?Sharpe Ratio: ([\d.-]+).*?Annual Return: ([\d.-]+)%.*?Volatility: ([\d.-]+)%'
                matches = re.findall(metric_pattern, content, re.DOTALL)
                
                for symbol, sharpe, return_pct, volatility in matches:
                    metrics_data.append({
                        'symbol': symbol,
                        'sharpe_ratio': float(sharpe),
                        'annual_return': float(return_pct),
                        'volatility': float(volatility)
                    })
                    
        except Exception as e:
            print(f"❌ Error analyzing metrics logs: {e}")
            return
            
        if metrics_data:
            # Sort by Sharpe ratio
            metrics_data.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            
            print(f"📊 Metrics Calculated: {len(metrics_data)}")
            print("\n🏆 Top Performers (by Sharpe Ratio):")
            
            for i, data in enumerate(metrics_data[:10]):
                print(f"   {i+1}. {data['symbol']}: Sharpe {data['sharpe_ratio']:.3f}, "
                      f"Return {data['annual_return']:.1f}%, Vol {data['volatility']:.1f}%")
                      
            # Calculate averages
            avg_sharpe = sum(d['sharpe_ratio'] for d in metrics_data) / len(metrics_data)
            avg_return = sum(d['annual_return'] for d in metrics_data) / len(metrics_data)
            avg_vol = sum(d['volatility'] for d in metrics_data) / len(metrics_data)
            
            print(f"\n📊 Averages:")
            print(f"   Sharpe Ratio: {avg_sharpe:.3f}")
            print(f"   Annual Return: {avg_return:.1f}%")
            print(f"   Volatility: {avg_vol:.1f}%")
            
        self.stats["performance_analyses"] = len(metrics_data)
    
    def analyze_data_quality(self):
        """Analyze data quality from data logs"""
        data_file = self.log_files.get('data')
        if not data_file or not data_file.exists():
            print("⚠️ No data log file found")
            return
            
        print("\n📊 DATA QUALITY ANALYSIS:")
        print("=" * 60)
        
        price_data = []
        data_sources = set()
        
        try:
            with open(data_file, 'r') as f:
                lines = f.readlines()
                
                for line in lines:
                    if 'PRICE_DATA' in line:
                        # Parse: PRICE_DATA | SYMBOL | EXCHANGE | $PRICE | TIMESTAMP
                        parts = line.split('|')
                        if len(parts) >= 5:
                            symbol = parts[1].strip()
                            exchange = parts[2].strip()
                            price_str = parts[3].strip().replace('$', '').replace(',', '')
                            
                            try:
                                price = float(price_str)
                                price_data.append({
                                    'symbol': symbol,
                                    'exchange': exchange,
                                    'price': price
                                })
                                data_sources.add(exchange)
                            except ValueError:
                                continue
                                
        except Exception as e:
            print(f"❌ Error analyzing data logs: {e}")
            return
            
        if price_data:
            print(f"📊 Price Data Points: {len(price_data)}")
            print(f"🌐 Data Sources: {len(data_sources)} ({', '.join(data_sources)})")
            
            # Group by symbol
            symbols = {}
            for data in price_data:
                symbol = data['symbol']
                if symbol not in symbols:
                    symbols[symbol] = []
                symbols[symbol].append(data)
            
            print(f"💰 Symbols Tracked: {len(symbols)}")
            
            # Show price ranges for each symbol
            print("\n💲 Price Ranges:")
            for symbol, data_points in list(symbols.items())[:10]:  # Show top 10
                prices = [d['price'] for d in data_points]
                min_price = min(prices)
                max_price = max(prices)
                spread = ((max_price - min_price) / min_price) * 100
                
                print(f"   {symbol}: ${min_price:,.2f} - ${max_price:,.2f} "
                      f"(spread: {spread:.2f}%)")
                      
        self.stats["data_points_collected"] = len(price_data)
    
    def analyze_errors(self):
        """Analyze errors from all log files"""
        print("\n❌ ERROR ANALYSIS:")
        print("=" * 60)
        
        errors = []
        
        for log_type, file in self.log_files.items():
            if not file.exists():
                continue
                
            try:
                with open(file, 'r') as f:
                    lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if 'ERROR' in line or 'Exception' in line:
                            errors.append({
                                'file': log_type,
                                'line_num': i + 1,
                                'content': line.strip(),
                                'timestamp': self._extract_timestamp(line)
                            })
                            
            except Exception as e:
                print(f"❌ Error reading {file}: {e}")
                
        if errors:
            print(f"🔍 Total Errors Found: {len(errors)}")
            
            # Group by error type
            error_types = {}
            for error in errors:
                error_type = self._classify_error(error['content'])
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(error)
            
            print("\n📊 Error Types:")
            for error_type, error_list in error_types.items():
                print(f"   {error_type}: {len(error_list)} occurrences")
                
            # Show recent errors
            recent_errors = sorted(errors, key=lambda x: x['timestamp'] or datetime.min, reverse=True)[:5]
            print("\n🕐 Recent Errors:")
            for error in recent_errors:
                print(f"   [{error['file']}] {error['content'][:100]}...")
        else:
            print("✅ No errors found!")
            
        self.stats["errors"] = len(errors)
    
    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line"""
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        match = re.search(timestamp_pattern, line)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        return None
    
    def _classify_error(self, error_content: str) -> str:
        """Classify error by type"""
        error_content_lower = error_content.lower()
        
        if 'import' in error_content_lower or 'module' in error_content_lower:
            return 'Import Error'
        elif 'connection' in error_content_lower or 'timeout' in error_content_lower:
            return 'Connection Error'
        elif 'calculation' in error_content_lower or 'metric' in error_content_lower:
            return 'Calculation Error'
        elif 'database' in error_content_lower or 'db' in error_content_lower:
            return 'Database Error'
        elif 'telegram' in error_content_lower or 'bot' in error_content_lower:
            return 'Telegram Error'
        else:
            return 'Other Error'
    
    def print_summary(self):
        """Print overall summary"""
        print("\n" + "=" * 80)
        print("📊 PRODUCTION LOG SUMMARY")
        print("=" * 80)
        
        uptime = datetime.now() - self.stats["session_start"]
        
        print(f"⏱️  Session Duration: {str(uptime).split('.')[0]}")
        print(f"🎯 Arbitrage Opportunities: {self.stats['arbitrage_opportunities']}")
        print(f"📈 Performance Analyses: {self.stats['performance_analyses']}")
        print(f"📊 Data Points Collected: {self.stats['data_points_collected']}")
        print(f"❌ Errors Found: {self.stats['errors']}")
        
        if self.stats['errors'] == 0:
            print("✅ No errors detected - system running smoothly!")
        else:
            print("⚠️  Check errors above for issues that need attention")
    
    def watch_logs(self, interval: int = 30):
        """Watch logs in real-time"""
        print(f"👀 Watching logs (updating every {interval} seconds)...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print("🔄 REAL-TIME PRODUCTION LOG MONITOR")
                print("=" * 80)
                print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.analyze_arbitrage_logs()
                self.analyze_metrics_logs() 
                self.analyze_data_quality()
                self.analyze_errors()
                self.print_summary()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped!")


def main():
    parser = argparse.ArgumentParser(description='Monitor production logs')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    parser.add_argument('--tail', type=int, help='Show last N lines from logs')
    parser.add_argument('--watch', action='store_true', help='Watch logs in real-time')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval in seconds')
    
    args = parser.parse_args()
    
    monitor = ProductionLogMonitor(args.log_dir)
    monitor.find_log_files()
    
    if args.tail:
        monitor.tail_logs(args.tail)
    elif args.watch:
        monitor.watch_logs(args.interval)
    else:
        # Run full analysis
        monitor.analyze_arbitrage_logs()
        monitor.analyze_metrics_logs()
        monitor.analyze_data_quality()
        monitor.analyze_errors()
        monitor.print_summary()


if __name__ == "__main__":
    main()