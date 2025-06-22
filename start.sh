#!/bin/bash
# Crypto Trading Bot v2.0 - Quick Start Script

echo "🚀 Starting Crypto Trading Bot v2.0..."

# Change to project directory
cd "$(dirname "$0")"

# Check if setup has been run
if [ ! -f ".env.local" ]; then
    echo "⚠️ Setup not completed. Running one-click setup..."
    python3 setup.py
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "❌ Setup failed. Please check the errors above."
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables
if [ -f ".env.local" ]; then
    echo "🔧 Loading environment configuration..."
    export $(cat .env.local | grep -v '^#' | grep -v '^$' | xargs)
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, requests, numpy, pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the web API
echo "🌐 Starting web dashboard..."
python3 src/web_api_simple.py &
WEB_PID=$!

# Wait a moment for web server to start
sleep 2

# Start the monitoring system (optional)
if [ "$1" = "--with-monitor" ]; then
    echo "📊 Starting 24/7 monitoring..."
    python3 src/crypto_monitor_24_7.py &
    MONITOR_PID=$!
fi

echo ""
echo "✅ Crypto Trading Bot started successfully!"
echo "📊 Dashboard: http://localhost:5000"
echo "📱 Mobile Access: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "🛑 Press Ctrl+C to stop"

# Function to handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ ! -z "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null
    fi
    if [ ! -z "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null
    fi
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handling
trap cleanup INT TERM

# Wait for processes
if [ ! -z "$MONITOR_PID" ]; then
    wait $WEB_PID $MONITOR_PID
else
    wait $WEB_PID
fi