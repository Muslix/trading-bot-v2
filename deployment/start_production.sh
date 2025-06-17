#!/bin/bash
# Crypto Trading Bot 24/7 - Production Startup Script

# Get the script directory and go to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🚀 Starting Crypto Trading Bot 24/7..."
echo "📅 $(date)"
echo "📁 Working Directory: $(pwd)"

# Load environment variables from .env files
echo "🔧 Loading environment configuration..."
if [ -f ".env.local" ]; then
    echo "✅ Loading .env.local (local development)"
    export $(grep -v '^#' .env.local | xargs)
elif [ -f ".env" ]; then
    echo "✅ Loading .env (default configuration)"
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ No .env file found, using system environment"
fi

# Verify critical environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set!"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ TELEGRAM_CHAT_ID not set!"
    exit 1
fi

echo "✅ Telegram Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "✅ Telegram Chat ID: $TELEGRAM_CHAT_ID"

# Set Python path to include the project root
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import flask, telegram" 2>/dev/null || {
    echo "📦 Installing missing dependencies..."
    python3 -m pip install --user flask python-telegram-bot
}

# Start Web API in background
echo "🌐 Starting Web API..."
python3 src/web_api.py &
WEB_PID=$!
echo "Web API PID: $WEB_PID"

# Wait a moment for web API to start
sleep 3

# Start main monitoring bot
echo "🤖 Starting main monitoring bot..."
python3 src/crypto_monitor_24_7.py

# Cleanup on exit
echo "🛑 Shutting down..."
kill $WEB_PID 2>/dev/null
echo "✅ Shutdown complete"
