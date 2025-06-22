#!/bin/bash
# Update Dependencies Script
# Updates all dependencies to their latest compatible versions

set -e

echo "🔄 UPDATING DEPENDENCIES TO LATEST VERSIONS"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 1. Upgrading pip and setuptools...${NC}"
python3 -m pip install --upgrade pip setuptools wheel

echo ""
echo -e "${BLUE}📦 2. Installing/upgrading production dependencies...${NC}"
pip install --upgrade -r requirements.txt

echo ""
echo -e "${BLUE}📦 3. Installing/upgrading development dependencies...${NC}"
pip install --upgrade -r requirements-dev.txt

echo ""
echo -e "${BLUE}🔍 4. Running security scan on updated dependencies...${NC}"
if command -v safety &> /dev/null; then
    safety scan --output text || echo -e "${YELLOW}⚠️ Safety scan found some issues (check output above)${NC}"
else
    echo -e "${YELLOW}⚠️ Safety not installed, installing...${NC}"
    pip install safety
    safety scan --output text || echo -e "${YELLOW}⚠️ Safety scan found some issues (check output above)${NC}"
fi

echo ""
echo -e "${BLUE}🧪 5. Running quick test to verify dependencies work...${NC}"
python3 -c "
import pytest
import pandas as pd
import numpy as np
import requests
import flask
import ccxt
print('✅ All critical dependencies imported successfully!')
"

echo ""
echo -e "${GREEN}✅ DEPENDENCY UPDATE COMPLETED!${NC}"
echo -e "${GREEN}🚀 All dependencies updated to latest compatible versions${NC}"
echo ""
echo -e "${BLUE}💡 Recommended next steps:${NC}"
echo "   1. Run tests: make test"
echo "   2. Check for any breaking changes in logs above"
echo "   3. Commit updated dependencies if tests pass"
echo ""
echo -e "${YELLOW}📋 To freeze current versions run:${NC}"
echo "   pip freeze > requirements-frozen.txt"
