#!/bin/bash
# Crypto Trading Bot Backup Script

cd /home/muslix/trading_bot_v2

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
