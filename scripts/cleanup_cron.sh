#!/bin/bash
"""
Automatic Database Cleanup Cron Job
Bereinigt automatisch die Database um Spam zu reduzieren
"""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Log file
LOG_FILE="cleanup_cron.log"

# Add timestamp to log
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting automatic database cleanup" >> "$LOG_FILE"

# Run cleanup
python3 cleanup_db.py --zero-profit --duplicates >> "$LOG_FILE" 2>&1

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup completed" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

# Keep log file size manageable (keep last 1000 lines)
tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
