#!/bin/bash

# Frontend startup script for Crypto Trading Bot
# Starts the web API server with the working frontend

echo "🚀 Starting Crypto Trading Bot Frontend..."

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Kill any existing web API processes
echo "🛑 Stopping any existing web API processes..."
pkill -f web_api_simple || echo "No existing processes found"

# Wait a moment for cleanup
sleep 2

# Start the simple web API in the background
echo "🌐 Starting Simple Web API server..."
python src/web_api_simple.py > logs/frontend.log 2>&1 &

# Get the process ID
API_PID=$!
echo "📝 Web API started with PID: $API_PID"

# Wait a moment for startup
sleep 3

# Check if the server is running
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Web API server is running successfully!"
    echo "🔗 Frontend available at: http://localhost:5000"
    echo "🔗 API health check: http://localhost:5000/health"
    echo "📊 Dashboard API: http://localhost:5000/api/dashboard-data"
    echo "💰 Live Prices: http://localhost:5000/api/live-prices"
    echo "📈 Performance Data: http://localhost:5000/api/performance-data"
    echo ""
    echo "🔍 Features available:"
    echo "   • 📊 Dashboard with live data (25 live prices, 70 performance coins)"
    echo "   • 🔄 Real-time WebSocket updates (with state persistence)"
    echo "   • 🏊 DeFi Pools Analysis"
    echo "   • 🤖 AI/ML Sentiment & Predictions"
    echo "   • 📋 Strategy Sharing Platform"
    echo "   • 🔔 Notification System"
    echo ""
    echo "📝 Logs are being written to: logs/frontend.log"
    echo "🛑 To stop the server, run: pkill -f web_api_simple"
else
    echo "❌ Web API server failed to start"
    echo "📝 Check logs/frontend.log for details"
    exit 1
fi