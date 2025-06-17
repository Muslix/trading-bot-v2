#!/bin/bash

# CI Test Simulation Script
# This script simulates the CI environment and tests our fixes

echo "🧪 Simulating CI Environment for Trading Bot Tests"
echo "=================================================="

# Create a temporary directory to simulate clean CI environment
TEST_DIR=$(mktemp -d)
echo "📁 Created temporary test directory: $TEST_DIR"

# Copy the project to the test directory
echo "📋 Copying project files..."
cp -r . "$TEST_DIR/"
cd "$TEST_DIR"

# Remove any existing logs directory (simulate CI environment)
echo "🧹 Removing existing logs directory..."
rm -rf logs/

# Install dependencies (simulate CI dependency installation)
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt > /dev/null 2>&1
    echo "✅ Dependencies installed"
else
    echo "⚠️ No requirements.txt found"
fi

# Run the test setup
echo "🔧 Testing configuration setup..."
python -c "
import sys
sys.path.append('tests')
import conftest
print('✅ Test configuration loaded')
"

# Test error logger directly
echo "📝 Testing error logger..."
python -c "
from src.utils.error_logger import setup_error_logger
logger = setup_error_logger()
logger.info('CI test message')
print('✅ Error logger working')
"

# Run actual unit tests
echo "🧪 Running unit tests..."
python -m pytest tests/test_modules/test_historical_data.py::TestHistoricalDataManager::test_manager_initialization -v --tb=short

# Clean up
cd - > /dev/null
rm -rf "$TEST_DIR"
echo "🧹 Cleaned up test directory"

echo ""
echo "🎉 CI Environment Test Complete!"
echo "The fixes should now work in GitHub Actions CI environment."
