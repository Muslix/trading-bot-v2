#!/bin/bash
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
