#!/bin/bash
# Crypto Trading Bot Monitoring Script

cd /home/muslix/trading_bot_v2

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
    cursor.execute('SELECT COUNT(*) FROM arbitrage_alerts WHERE timestamp >= datetime("now", "-1 hour")')
    alerts_1h = cursor.fetchone()[0]
    
    # Recent price updates
    cursor.execute('SELECT COUNT(*) FROM price_history WHERE timestamp >= datetime("now", "-1 hour")')  
    prices_1h = cursor.fetchone()[0]
    
    print(f'   Alerts (last hour): {alerts_1h}')
    print(f'   Price updates (last hour): {prices_1h}')
    
    conn.close()
except:
    print('   Unable to query database')
"
fi

echo ""
echo "=================================="
