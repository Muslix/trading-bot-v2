#!/usr/bin/env python3
"""
Production Logging Setup - Prepare logging infrastructure for production deployment
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def setup_log_directories():
    """Create necessary log directories"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create subdirectories for different log types
    subdirs = ["archive", "errors", "debug"]
    for subdir in subdirs:
        (log_dir / subdir).mkdir(exist_ok=True)
    
    print(f"✅ Created log directories in {log_dir}")
    return log_dir


def create_log_rotation_config():
    """Create logrotate configuration"""
    log_dir = project_root / "logs"
    config_content = f"""# Crypto Trading Bot Log Rotation
{log_dir}/*.log {{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 {os.getuid()} {os.getgid()}
    postrotate
        # Signal the application to reopen log files if needed
        echo "Log rotated at $(date)" >> {log_dir}/rotation.log
    endscript
}}

{log_dir}/*.debug {{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 {os.getuid()} {os.getgid()}
}}
"""
    
    config_file = project_root / "logrotate.conf"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Created log rotation config: {config_file}")
    return config_file


def create_production_env_template():
    """Create production environment template with logging settings"""
    env_template = """# Production Environment Configuration for Crypto Trading Bot

# Environment
ENVIRONMENT=production

# Telegram Configuration (REQUIRED)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_ROTATION_SIZE_MB=100
LOG_RETENTION_DAYS=30

# Monitoring Configuration
ARBITRAGE_CHECK_INTERVAL=30
PERFORMANCE_CHECK_INTERVAL=600
DAILY_SUMMARY_HOUR=8

# Trading Configuration
WATCHLIST_SYMBOLS=BTC,ETH,BNB,ADA,DOT,XRP,LTC,LINK
ANALYSIS_CRYPTO_COUNT=100
EXCHANGES=binance,coinbase,kraken

# Database Configuration
DATABASE_URL=sqlite:///trading_bot.db
DATABASE_BACKUP_INTERVAL=3600

# Security Configuration
API_RATE_LIMIT=100
MAX_POSITION_SIZE=1000
ENABLE_PAPER_TRADING=true

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=300

# Alert Configuration
ARBITRAGE_THRESHOLD=1.5
SHARPE_CHANGE_THRESHOLD=0.5
ALERT_COOLDOWN_MINUTES=15

# Production Debugging
PRODUCTION_LOGGING=true
DEBUG_CALCULATIONS=true
LOG_DATA_SOURCES=true
LOG_PRICE_DATA=true
LOG_METRICS_CALCULATION=true
"""
    
    env_file = project_root / ".env.production"
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created production environment template: {env_file}")
    print("   Please edit this file with your actual configuration values")
    return env_file


def create_monitoring_scripts():
    """Create monitoring and management scripts"""
    
    # Health check script
    health_check_script = project_root / "scripts" / "health_check.sh"
    health_check_content = """#!/bin/bash
# Health check script for production monitoring

LOG_DIR="${1:-logs}"
ALERT_THRESHOLD_ERRORS=10

echo "🔍 CRYPTO TRADING BOT HEALTH CHECK"
echo "=================================="
echo "Time: $(date)"
echo

# Check if bot is running
if pgrep -f "crypto_monitor_24_7.py" > /dev/null; then
    echo "✅ Bot is RUNNING (PID: $(pgrep -f crypto_monitor_24_7.py))"
else
    echo "❌ Bot is NOT RUNNING"
    exit 1
fi

# Check log directory
if [ -d "$LOG_DIR" ]; then
    echo "✅ Log directory exists: $LOG_DIR"
    
    # Check log file sizes
    echo "📁 Log file sizes:"
    find "$LOG_DIR" -name "*.log" -exec ls -lh {} \\; | awk '{print "   " $9 ": " $5}'
    
    # Check for recent errors
    ERROR_COUNT=$(find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -c "ERROR" {} \\; | awk '{sum+=$1} END {print sum+0}')
    echo "❌ Errors in last 24h: $ERROR_COUNT"
    
    if [ "$ERROR_COUNT" -gt "$ALERT_THRESHOLD_ERRORS" ]; then
        echo "⚠️  WARNING: High error count detected!"
        exit 2
    fi
else
    echo "❌ Log directory not found: $LOG_DIR"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df "$LOG_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
echo "💾 Disk usage: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️  WARNING: Low disk space!"
    exit 3
fi

echo "✅ Health check passed!"
"""
    
    with open(health_check_script, 'w') as f:
        f.write(health_check_content)
    
    os.chmod(health_check_script, 0o755)
    print(f"✅ Created health check script: {health_check_script}")
    
    # Log cleanup script
    cleanup_script = project_root / "scripts" / "cleanup_logs.sh"
    cleanup_content = """#!/bin/bash
# Log cleanup script

LOG_DIR="${1:-logs}"
RETENTION_DAYS="${2:-30}"

echo "🧹 CLEANING OLD LOG FILES"
echo "========================"
echo "Log directory: $LOG_DIR"
echo "Retention: $RETENTION_DAYS days"
echo

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Log directory not found: $LOG_DIR"
    exit 1
fi

# Move old logs to archive
ARCHIVE_DIR="$LOG_DIR/archive"
mkdir -p "$ARCHIVE_DIR"

# Find and archive old log files
OLD_LOGS=$(find "$LOG_DIR" -name "*.log" -mtime +7 -not -path "$ARCHIVE_DIR/*")

if [ -n "$OLD_LOGS" ]; then
    echo "📦 Archiving old log files..."
    echo "$OLD_LOGS" | while read -r file; do
        if [ -f "$file" ]; then
            gzip "$file"
            mv "$file.gz" "$ARCHIVE_DIR/"
            echo "   Archived: $(basename "$file")"
        fi
    done
else
    echo "✅ No old log files to archive"
fi

# Delete very old archived logs
DELETED=$(find "$ARCHIVE_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "🗑️  Deleted $DELETED very old log files"
else
    echo "✅ No very old log files to delete"
fi

echo "✅ Log cleanup completed!"
"""
    
    with open(cleanup_script, 'w') as f:
        f.write(cleanup_content)
    
    os.chmod(cleanup_script, 0o755)
    print(f"✅ Created log cleanup script: {cleanup_script}")


def create_systemd_service():
    """Create systemd service file for production deployment"""
    service_content = f"""[Unit]
Description=Crypto Trading Bot 24/7 Monitor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={project_root}
Environment=PYTHONPATH={project_root}
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 {project_root}/src/crypto_monitor_24_7.py
Restart=always
RestartSec=10
StandardOutput=append:{project_root}/logs/systemd.log
StandardError=append:{project_root}/logs/systemd_error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths={project_root}

[Install]
WantedBy=multi-user.target
"""
    
    service_file = project_root / "crypto-trading-bot.service"
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service file: {service_file}")
    print("   To install: sudo cp crypto-trading-bot.service /etc/systemd/system/")
    print("   To enable: sudo systemctl enable crypto-trading-bot")
    print("   To start: sudo systemctl start crypto-trading-bot")
    return service_file


def create_production_readme():
    """Create production deployment README"""
    readme_content = """# 🚀 PRODUCTION DEPLOYMENT GUIDE

## Quick Start

1. **Setup Production Environment**
   ```bash
   # Copy and configure production environment
   cp .env.production .env.local
   nano .env.local  # Add your API keys and settings
   ```

2. **Start Production Services**
   ```bash
   make production-start
   ```

3. **Monitor Logs**
   ```bash
   # Real-time monitoring
   python3 scripts/monitor_production_logs.py --watch
   
   # View recent logs
   python3 scripts/monitor_production_logs.py --tail 100
   
   # Analyze logs
   python3 scripts/monitor_production_logs.py
   ```

## Log Files Structure

- `logs/crypto_monitor_main.log` - Main application events
- `logs/crypto_monitor_calculations.log` - Detailed calculation debugging
- `logs/crypto_monitor_data.log` - Data source and price information
- `logs/crypto_monitor_metrics.log` - Performance metrics calculation
- `logs/crypto_monitor_arbitrage.log` - Arbitrage opportunity analysis

## Production Features

### Enhanced Logging
- **Calculation Debugging**: All financial calculations logged with inputs/outputs
- **Data Source Tracking**: Price data from all exchanges logged
- **Performance Monitoring**: Detailed metrics calculation logging
- **Error Context**: Full error context with relevant data

### Real-time Monitoring
```bash
# Watch logs in real-time
python3 scripts/monitor_production_logs.py --watch

# Health check
bash scripts/health_check.sh

# Log cleanup
bash scripts/cleanup_logs.sh
```

### Systemd Service (Optional)
```bash
# Install service
sudo cp crypto-trading-bot.service /etc/systemd/system/
sudo systemctl enable crypto-trading-bot
sudo systemctl start crypto-trading-bot

# Monitor service
sudo systemctl status crypto-trading-bot
sudo journalctl -u crypto-trading-bot -f
```

## Configuration

### Environment Variables
See `.env.production` for all available configuration options.

Key production settings:
- `PRODUCTION_LOGGING=true` - Enable detailed production logging
- `DEBUG_CALCULATIONS=true` - Log all calculation steps
- `LOG_DATA_SOURCES=true` - Log price data from exchanges
- `LOG_LEVEL=INFO` - Set appropriate log level

### Log Rotation
Logs are automatically rotated to prevent disk space issues:
- Daily rotation for main logs
- 30-day retention for compressed logs
- 7-day retention for debug logs

## Monitoring Commands

```bash
# Check bot status
make production-status

# View logs
make logs

# Monitor in real-time
python3 scripts/monitor_production_logs.py --watch

# Analyze performance
python3 scripts/monitor_production_logs.py

# Health check
bash scripts/health_check.sh
```

## Troubleshooting

### High Memory Usage
Check log file sizes and enable log rotation:
```bash
bash scripts/cleanup_logs.sh
```

### Missing Calculations
Check calculation logs:
```bash
tail -f logs/crypto_monitor_calculations.log
```

### Data Source Issues
Check data logs:
```bash
tail -f logs/crypto_monitor_data.log
```

### Alert Problems
Check main logs:
```bash
tail -f logs/crypto_monitor_main.log
```

## Security Notes

- Keep `.env.local` secure and never commit it
- Use systemd service for production (includes security settings)
- Monitor logs for any suspicious activity
- Regular health checks recommended

## Performance Tips

- Monitor log file sizes regularly
- Use log rotation to prevent disk space issues
- Set appropriate log levels (INFO for production)
- Monitor system resources during peak trading hours
"""
    
    readme_file = project_root / "PRODUCTION_README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Created production README: {readme_file}")
    return readme_file


def main():
    print("🚀 SETTING UP PRODUCTION LOGGING")
    print("=" * 50)
    
    # Setup log infrastructure
    log_dir = setup_log_directories()
    
    # Create configuration files
    env_file = create_production_env_template()
    config_file = create_log_rotation_config()
    
    # Create monitoring scripts
    create_monitoring_scripts()
    
    # Create systemd service
    service_file = create_systemd_service()
    
    # Create documentation
    readme_file = create_production_readme()
    
    print("\n✅ PRODUCTION LOGGING SETUP COMPLETE!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Edit .env.production with your actual configuration")
    print("2. Copy .env.production to .env.local")
    print("3. Run: make production-start")
    print("4. Monitor: python3 scripts/monitor_production_logs.py --watch")
    print(f"\n📖 See {readme_file} for detailed instructions")


if __name__ == "__main__":
    main()