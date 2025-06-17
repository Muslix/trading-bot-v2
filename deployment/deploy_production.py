"""
Production Deployment Script - Crypto Trading Bot 24/7
Komplettes Deployment für Produktions-Umgebung
"""

import subprocess
import sys
import os
import time
import json
import shutil
from datetime import datetime
from pathlib import Path


class ProductionDeployment:
    """Production Deployment Manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_log = []
        self.start_time = datetime.now()
        
    def log(self, message: str, level: str = "INFO"):
        """Logge Deployment-Schritte"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
    
    def check_requirements(self) -> bool:
        """Prüfe System-Anforderungen"""
        self.log("🔍 Checking system requirements...")
        
        # Python Version
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 8:
            self.log("❌ Python 3.8+ required", "ERROR")
            return False
        self.log(f"✅ Python {python_version.major}.{python_version.minor}")
        
        # Required packages
        required_packages = [
            'asyncio', 'telegram', 'flask', 'sqlite3', 
            'requests', 'pandas', 'numpy', 'yfinance'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                self.log(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                self.log(f"❌ {package} missing", "ERROR")
        
        if missing_packages:
            self.log(f"Install missing packages: pip install {' '.join(missing_packages)}", "ERROR")
            return False
        
        # File structure
        required_files = [
            'crypto_monitor_24_7.py',
            'web_api.py',
            'modules/telegram_bot.py',
            'modules/database.py',
            'modules/smart_alerts.py',
            'frontend/index.html'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                self.log(f"❌ Missing file: {file_path}", "ERROR")
                return False
            self.log(f"✅ {file_path}")
        
        return True
    
    def setup_production_config(self):
        """Setup Production-Konfiguration"""
        self.log("⚙️ Setting up production configuration...")
        
        # Load existing .env files if they exist (prioritize .env.local)
        import os
        from pathlib import Path
        
        env_local_path = Path(self.project_root).parent / ".env.local"
        env_path = Path(self.project_root).parent / ".env"
        
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # First try to load from .env.local (highest priority)
        if not telegram_token and env_local_path.exists():
            self.log("🔧 Loading configuration from .env.local")
            try:
                with open(env_local_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
                            telegram_token = line.strip().split('=', 1)[1]
                        elif line.strip().startswith('TELEGRAM_CHAT_ID='):
                            telegram_chat_id = line.strip().split('=', 1)[1]
            except Exception as e:
                self.log(f"⚠️ Warning: Could not read .env.local file: {e}")
        
        # Fallback to .env if no .env.local or missing values
        if (not telegram_token or not telegram_chat_id) and env_path.exists():
            self.log("🔧 Loading configuration from .env")
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if not telegram_token and line.strip().startswith('TELEGRAM_BOT_TOKEN='):
                            telegram_token = line.strip().split('=', 1)[1]
                        elif not telegram_chat_id and line.strip().startswith('TELEGRAM_CHAT_ID='):
                            telegram_chat_id = line.strip().split('=', 1)[1]
            except Exception as e:
                self.log(f"⚠️ Warning: Could not read .env file: {e}")
        
        # Validate credentials
        if telegram_token and telegram_token != "your_bot_token_here":
            self.log(f"✅ Telegram Bot Token loaded: {telegram_token[:10]}...")
        else:
            self.log("⚠️ No valid Telegram Bot Token found in environment")
            
        if telegram_chat_id and telegram_chat_id != "your_chat_id_here":
            self.log(f"✅ Telegram Chat ID loaded: {telegram_chat_id}")
        else:
            self.log("⚠️ No valid Telegram Chat ID found in environment")
        
        # Production config
        prod_config = {
            "BOT_TOKEN": telegram_token,
            "CHAT_ID": telegram_chat_id if telegram_chat_id else None,
            "DATABASE_PATH": "crypto_trading_bot_production.db",
            "WEB_PORT": int(os.getenv('WEB_PORT', '5000')),
            "WEB_HOST": os.getenv('WEB_HOST', '0.0.0.0'),
            "LOG_LEVEL": "INFO",
            "MONITORING_CONFIG": {
                "arbitrage_check_interval": int(os.getenv('ARBITRAGE_CHECK_INTERVAL', '30')),
                "performance_check_interval": int(os.getenv('PERFORMANCE_CHECK_INTERVAL', '600')),
                "daily_summary_hour": int(os.getenv('DAILY_SUMMARY_HOUR', '8')),
                "watchlist_symbols": os.getenv('WATCHLIST_SYMBOLS', 'BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,DOT/USDT').split(','),
                "analysis_crypto_count": int(os.getenv('ANALYSIS_CRYPTO_COUNT', '50'))
            },
            "ALERT_CONFIG": {
                "arbitrage_threshold": float(os.getenv('ARBITRAGE_THRESHOLD', '2.0')),
                "sharpe_change_threshold": float(os.getenv('SHARPE_CHANGE_THRESHOLD', '0.5')),
                "cooldown_minutes": 5
            }
        }
        
        # Speichere Config
        config_file = self.project_root / "production_config.json"
        with open(config_file, 'w') as f:
            json.dump(prod_config, f, indent=2)
        
        self.log(f"✅ Production config saved: {config_file}")
        return prod_config
    
    def create_systemd_service(self):
        """Erstelle systemd Service für Auto-Start"""
        self.log("🔧 Creating systemd service...")
        
        python_path = sys.executable
        project_path = str(self.project_root)
        
        service_content = f"""[Unit]
Description=Crypto Trading Bot 24/7
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'crypto')}
WorkingDirectory={project_path}
Environment=PYTHONPATH={project_path}
ExecStart={python_path} {project_path}/src/crypto_monitor_24_7.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.project_root / "crypto-trading-bot.service"
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        self.log(f"✅ Systemd service created: {service_file}")
        self.log("   To install: sudo cp crypto-trading-bot.service /etc/systemd/system/")
        self.log("   To enable: sudo systemctl enable crypto-trading-bot")
        self.log("   To start: sudo systemctl start crypto-trading-bot")
        
        return service_file
    
    def create_web_service(self):
        """Erstelle Web API Service"""
        self.log("🌐 Creating web API service...")
        
        python_path = sys.executable
        project_path = str(self.project_root)
        
        web_service_content = f"""[Unit]
Description=Crypto Trading Bot Web API
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'crypto')}
WorkingDirectory={project_path}
Environment=PYTHONPATH={project_path}
ExecStart={python_path} {project_path}/src/web_api.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        web_service_file = self.project_root / "crypto-web-api.service"
        with open(web_service_file, 'w') as f:
            f.write(web_service_content)
        
        self.log(f"✅ Web API service created: {web_service_file}")
        return web_service_file
    
    def create_startup_script(self):
        """Erstelle Startup-Script"""
        self.log("🚀 Creating startup script...")
        
        startup_script = f"""#!/bin/bash
# Crypto Trading Bot 24/7 - Production Startup Script

cd {self.project_root}

echo "🚀 Starting Crypto Trading Bot 24/7..."
echo "📅 $(date)"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Start Web API in background
echo "🌐 Starting Web API..."
python src/web_api.py &
WEB_PID=$!
echo "Web API PID: $WEB_PID"

# Wait a moment for web API to start
sleep 3

# Start main monitoring bot
echo "🤖 Starting main monitoring bot..."
python src/crypto_monitor_24_7.py

# Cleanup on exit
echo "🛑 Shutting down..."
kill $WEB_PID 2>/dev/null
echo "✅ Shutdown complete"
"""
        
        startup_file = self.project_root / "start_production.sh"
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod(startup_file, 0o755)
        
        self.log(f"✅ Startup script created: {startup_file}")
        return startup_file
    
    def create_monitoring_script(self):
        """Erstelle Monitoring-Script"""
        self.log("📊 Creating monitoring script...")
        
        monitor_script = f"""#!/bin/bash
# Crypto Trading Bot Monitoring Script

cd {self.project_root}

echo "📊 CRYPTO TRADING BOT STATUS REPORT"
echo "=================================="
echo "📅 $(date)"
echo ""

# Check if main process is running
if pgrep -f "crypto_monitor_24_7.py" > /dev/null; then
    echo "✅ Main Bot: RUNNING"
    echo "   PID: $(pgrep -f crypto_monitor_24_7.py)"
else
    echo "❌ Main Bot: STOPPED"
fi

# Check if web API is running  
if pgrep -f "web_api.py" > /dev/null; then
    echo "✅ Web API: RUNNING"
    echo "   PID: $(pgrep -f web_api.py)"
    echo "   URL: http://localhost:5000"
else
    echo "❌ Web API: STOPPED"
fi

# Check database
if [ -f "crypto_trading_bot_production.db" ]; then
    DB_SIZE=$(du -h crypto_trading_bot_production.db | cut -f1)
    echo "✅ Database: FOUND ($DB_SIZE)"
else
    echo "❌ Database: NOT FOUND"
fi

# Check recent activity
if [ -f "crypto_trading_bot_production.db" ]; then
    echo ""
    echo "📈 Recent Activity:"
    python -c "
import sqlite3
from datetime import datetime, timedelta
try:
    conn = sqlite3.connect('crypto_trading_bot_production.db')
    cursor = conn.cursor()
    
    # Recent alerts
    cursor.execute('SELECT COUNT(*) FROM arbitrage_alerts WHERE timestamp >= datetime(\"now\", \"-1 hour\")')
    alerts_1h = cursor.fetchone()[0]
    
    # Recent price updates
    cursor.execute('SELECT COUNT(*) FROM price_history WHERE timestamp >= datetime(\"now\", \"-1 hour\")')  
    prices_1h = cursor.fetchone()[0]
    
    print(f'   Alerts (last hour): {{alerts_1h}}')
    print(f'   Price updates (last hour): {{prices_1h}}')
    
    conn.close()
except:
    print('   Unable to query database')
"
fi

echo ""
echo "=================================="
"""
        
        monitor_file = self.project_root / "check_status.sh"
        with open(monitor_file, 'w') as f:
            f.write(monitor_script)
        
        os.chmod(monitor_file, 0o755)
        
        self.log(f"✅ Monitoring script created: {monitor_file}")
        return monitor_file
    
    def create_backup_script(self):
        """Erstelle Backup-Script"""
        self.log("💾 Creating backup script...")
        
        backup_script = f"""#!/bin/bash
# Crypto Trading Bot Backup Script

cd {self.project_root}

# Create backups directory
mkdir -p backups

# Backup database
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "crypto_trading_bot_production.db" ]; then
    cp crypto_trading_bot_production.db "backups/crypto_trading_bot_$TIMESTAMP.db"
    echo "✅ Database backed up: backups/crypto_trading_bot_$TIMESTAMP.db"
fi

# Backup configuration
if [ -f "production_config.json" ]; then
    cp production_config.json "backups/production_config_$TIMESTAMP.json" 
    echo "✅ Config backed up: backups/production_config_$TIMESTAMP.json"
fi

# Cleanup old backups (keep last 7 days)
find backups/ -name "*.db" -mtime +7 -delete
find backups/ -name "*.json" -mtime +7 -delete

echo "🧹 Old backups cleaned up"
echo "💾 Backup complete: $(date)"
"""
        
        backup_file = self.project_root / "backup_data.sh"
        with open(backup_file, 'w') as f:
            f.write(backup_script)
        
        os.chmod(backup_file, 0o755)
        
        self.log(f"✅ Backup script created: {backup_file}")
        return backup_file
    
    def create_readme(self):
        """Erstelle Production README"""
        self.log("📖 Creating production README...")
        
        readme_content = f"""# Crypto Trading Bot 24/7 - Production Deployment

## 🚀 Quick Start

### Manual Start
```bash
./start_production.sh
```

### Service Installation (Auto-start)
```bash
# Install systemd services
sudo cp crypto-trading-bot.service /etc/systemd/system/
sudo cp crypto-web-api.service /etc/systemd/system/

# Enable and start services
sudo systemctl enable crypto-trading-bot crypto-web-api
sudo systemctl start crypto-trading-bot crypto-web-api
```

## 📊 Monitoring

### Check Status
```bash
./check_status.sh
```

### View Logs
```bash
# Main bot logs
sudo journalctl -u crypto-trading-bot -f

# Web API logs  
sudo journalctl -u crypto-web-api -f
```

### Web Dashboard
- URL: http://localhost:5000
- Real-time monitoring dashboard
- API endpoints for integration

## 💾 Backup & Maintenance

### Create Backup
```bash
./backup_data.sh
```

### Database Location
- Production: `crypto_trading_bot_production.db`
- Backups: `backups/`

## 🔧 Configuration

### Telegram Bot Setup
1. Message @crypto_muslix_bot to get your chat ID
2. Update `production_config.json` with your chat ID
3. Restart the service

### Alert Configuration
Edit `production_config.json`:
```json
{{
  "ALERT_CONFIG": {{
    "arbitrage_threshold": 2.0,
    "sharpe_change_threshold": 0.5,
    "cooldown_minutes": 5
  }}
}}
```

## 📈 Features

### 24/7 Monitoring
- ✅ Arbitrage detection every 30 seconds
- ✅ Performance analysis every 10 minutes  
- ✅ Smart alerts with cooldown protection
- ✅ Daily summary reports at 8:00 AM

### Data Sources
- ✅ Real-time prices from Binance, Coinbase, Kraken
- ✅ Historical data from Yahoo Finance
- ✅ 100+ cryptocurrency analysis
- ✅ Advanced risk metrics (Sharpe, Sortino, VaR)

### Alerts
- 🚨 Arbitrage opportunities > 2%
- 📈 Performance changes > 0.5 Sharpe ratio
- 🌟 New top performers  
- 📊 Large price movements > 5%
- 🌅 Daily market summaries

## 🛠️ Troubleshooting

### Service Not Starting
```bash
# Check service status
sudo systemctl status crypto-trading-bot

# Check logs for errors
sudo journalctl -u crypto-trading-bot --since "10 minutes ago"
```

### Database Issues
```bash
# Check database file
ls -la crypto_trading_bot_production.db

# Restore from backup
cp backups/crypto_trading_bot_YYYYMMDD_HHMMSS.db crypto_trading_bot_production.db
```

### API Not Responding
```bash
# Check web service
sudo systemctl status crypto-web-api

# Test API endpoint
curl http://localhost:5000/api/dashboard-data
```

## 📞 Support

For issues or questions:
1. Check logs: `sudo journalctl -u crypto-trading-bot -f`
2. Run status check: `./check_status.sh`
3. Review configuration: `production_config.json`

---
**Deployment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version:** 2.0
**Status:** Production Ready ✅
"""
        
        readme_file = self.project_root / "PRODUCTION_README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        self.log(f"✅ Production README created: {readme_file}")
        return readme_file
    
    def deploy(self) -> bool:
        """Führe komplettes Deployment durch"""
        self.log("🚀 STARTING PRODUCTION DEPLOYMENT")
        self.log("=" * 50)
        
        # 1. Check Requirements
        if not self.check_requirements():
            self.log("❌ Requirements check failed", "ERROR")
            return False
        
        # 2. Setup Configuration
        config = self.setup_production_config()
        
        # 3. Create Services
        self.create_systemd_service()
        self.create_web_service()
        
        # 4. Create Scripts
        startup_script = self.create_startup_script()
        monitor_script = self.create_monitoring_script()
        backup_script = self.create_backup_script()
        
        # 5. Create Documentation
        readme = self.create_readme()
        
        # 6. Save Deployment Log
        self.save_deployment_log()
        
        self.log("=" * 50)
        self.log("🎉 PRODUCTION DEPLOYMENT COMPLETE!")
        
        duration = datetime.now() - self.start_time
        self.log(f"⏱️ Total deployment time: {duration.total_seconds():.1f} seconds")
        
        # Final Instructions
        self.print_final_instructions()
        
        return True
    
    def save_deployment_log(self):
        """Speichere Deployment-Log"""
        log_file = self.project_root / f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(log_file, 'w') as f:
            f.write("\\n".join(self.deployment_log))
        
        self.log(f"💾 Deployment log saved: {log_file}")
    
    def print_final_instructions(self):
        """Drucke finale Anweisungen"""
        self.log("")
        self.log("📋 NEXT STEPS:")
        self.log("=" * 30)
        self.log("1. Set up Telegram Bot:")
        self.log("   • Message @crypto_muslix_bot to get your chat ID")
        self.log("   • Update production_config.json with your chat ID")
        self.log("")
        self.log("2. Start the system:")
        self.log("   • Manual: ./start_production.sh") 
        self.log("   • Auto-start: Install systemd services (see README)")
        self.log("")
        self.log("3. Monitor the system:")
        self.log("   • Status: ./check_status.sh")
        self.log("   • Dashboard: http://localhost:5000")
        self.log("   • Logs: sudo journalctl -u crypto-trading-bot -f")
        self.log("")
        self.log("4. Schedule regular backups:")
        self.log("   • Add to crontab: 0 2 * * * /path/to/backup_data.sh")
        self.log("")
        self.log("📖 Read PRODUCTION_README.md for detailed instructions")
        self.log("🎯 System ready for 24/7 operation!")


def main():
    """Führe Production Deployment durch"""
    print("🚀 CRYPTO TRADING BOT 24/7 - PRODUCTION DEPLOYMENT")
    print("=" * 60)
    
    deployment = ProductionDeployment()
    
    try:
        success = deployment.deploy()
        
        if success:
            print("\\n🎉 Deployment successful!")
            print("📖 Check PRODUCTION_README.md for next steps")
        else:
            print("\\n❌ Deployment failed!")
            print("📋 Check deployment log for details")
            
    except Exception as e:
        print(f"\\n💥 Deployment error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()