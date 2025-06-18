#!/bin/bash
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
    find "$LOG_DIR" -name "*.log" -exec ls -lh {} \; | awk '{print "   " $9 ": " $5}'
    
    # Check for recent errors
    ERROR_COUNT=$(find "$LOG_DIR" -name "*.log" -mtime -1 -exec grep -c "ERROR" {} \; | awk '{sum+=$1} END {print sum+0}')
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
