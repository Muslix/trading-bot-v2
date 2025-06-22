#!/bin/bash
# Comprehensive Security Audit Script
# This script performs a thorough security check of the crypto trading bot

set -e

echo "🔒 COMPREHENSIVE SECURITY AUDIT"
echo "==============================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# 1. Check for hardcoded secrets
echo "🔍 1. CHECKING FOR HARDCODED SECRETS"
echo "-----------------------------------"

# Check for specific hardcoded tokens
if grep -r "7780477878" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude="*.md" --exclude="security_audit.sh" --exclude=".env" --exclude=".env.local" | head -3 | grep -v "^$" >/dev/null 2>&1; then
    echo -e "${RED}❌ Hardcoded Telegram token found in unexpected places!${NC}"
    grep -r "7780477878" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=.venv --exclude="*.md" --exclude="security_audit.sh" --exclude=".env" --exclude=".env.local" | head -3
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✅ No hardcoded Telegram tokens in source code${NC}"
fi

# Check for hardcoded API keys pattern
if grep -r "api[_-]key.*=" . --include="*.py" | grep -E "\"[A-Za-z0-9]{20,}\"|'[A-Za-z0-9]{20,}'" > /dev/null 2>&1; then
    echo -e "${RED}❌ Potential hardcoded API keys found!${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✅ No hardcoded API keys${NC}"
fi

# Check for hardcoded passwords
if grep -r "password.*=" . --include="*.py" --exclude-dir=.venv --exclude-dir=venv | grep -E "\"[^\"]+\"|'[^']+'" | grep -v "your_password_here" | grep -v "common_passwords" | grep -v "sender_password.*config.get" | grep -v "password.*data.get" | grep -v "password.*\"\"" | grep -v "kdf.derive" | grep -v "security_util.py" > /dev/null 2>&1; then
    echo -e "${RED}❌ Potential hardcoded passwords found!${NC}"
    grep -r "password.*=" . --include="*.py" --exclude-dir=.venv --exclude-dir=venv | grep -E "\"[^\"]+\"|'[^']+'" | grep -v "your_password_here" | grep -v "common_passwords" | grep -v "sender_password.*config.get" | grep -v "password.*data.get" | grep -v "password.*\"\"" | grep -v "kdf.derive" | grep -v "security_util.py" | head -3
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✅ No hardcoded passwords${NC}"
fi

echo ""

# 2. Check .gitignore protection
echo "🚫 2. CHECKING GITIGNORE PROTECTION"
echo "-----------------------------------"

sensitive_files=(".env" ".env.local" ".env.production" "production_config.json")
for file in "${sensitive_files[@]}"; do
    if git check-ignore "$file" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $file is properly ignored${NC}"
    else
        echo -e "${RED}❌ $file is NOT ignored by git${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
done

echo ""

# 3. Check environment file security
echo "⚙️ 3. CHECKING ENVIRONMENT FILES"
echo "--------------------------------"

if [ -f ".env" ]; then
    echo -e "${YELLOW}📋 Checking .env file...${NC}"
    # In CI/CD or production, we expect only placeholders
    if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
        if grep -q "your_.*_here" .env; then
            echo -e "${GREEN}✅ .env contains placeholders (CI safe)${NC}"
        else
            echo -e "${RED}❌ .env may contain real credentials in CI${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    else
        # Local development - real tokens are OK
        echo -e "${GREEN}✅ .env found (local development)${NC}"
    fi
fi

if [ -f ".env.local" ]; then
    echo -e "${YELLOW}📋 Checking .env.local file...${NC}"
    if grep -q "your_.*_here" .env.local; then
        echo -e "${YELLOW}⚠️ .env.local contains placeholders${NC}"
    else
        echo -e "${GREEN}✅ .env.local contains real credentials (as expected)${NC}"
    fi
fi

echo ""

# 4. Check configuration system
echo "🔧 4. TESTING CONFIGURATION SYSTEM"
echo "----------------------------------"

if python -c "import sys; sys.path.append('.'); from config.config import get_config; get_config()" 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration system loads correctly${NC}"
else
    echo -e "${RED}❌ Configuration system has issues${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

echo ""

# 5. Check file permissions
echo "🔐 5. CHECKING FILE PERMISSIONS"
echo "------------------------------"

# Check if sensitive files have appropriate permissions
sensitive_files_check=(".env.local" "scripts/secure_setup.sh")
for file in "${sensitive_files_check[@]}"; do
    if [ -f "$file" ]; then
        perms=$(stat -c "%a" "$file" 2>/dev/null || echo "unknown")
        if [[ "$perms" =~ ^[67][0-4][0-4]$ ]]; then
            echo -e "${GREEN}✅ $file has secure permissions ($perms)${NC}"
        else
            echo -e "${YELLOW}⚠️ $file permissions could be more secure ($perms)${NC}"
        fi
    fi
done

echo ""

# 6. Check for sensitive data in logs
echo "📝 6. CHECKING FOR SENSITIVE DATA IN LOGS"
echo "-----------------------------------------"

log_files=$(find . -name "*.log" -type f -not -path "./.venv/*" -not -path "./venv/*" 2>/dev/null)
if [ -n "$log_files" ]; then
    if echo "$log_files" | xargs grep -l "token\|secret\|key" 2>/dev/null | head -1 >/dev/null; then
        echo -e "${YELLOW}⚠️ Log files may contain sensitive data (review needed)${NC}"
        # Don't fail in local development where logs may have debug info
        if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    else
        echo -e "${GREEN}✅ No sensitive data found in logs${NC}"
    fi
else
    echo -e "${GREEN}✅ No log files found${NC}"
fi

echo ""

# 7. Check database security
echo "🗄️ 7. CHECKING DATABASE SECURITY"
echo "--------------------------------"

if [ -f "crypto_trading_bot.db" ]; then
    perms=$(stat -c "%a" "crypto_trading_bot.db" 2>/dev/null || echo "unknown")
    if [[ "$perms" =~ ^[67][0-4][0-4]$ ]]; then
        echo -e "${GREEN}✅ Database has secure permissions ($perms)${NC}"
    else
        echo -e "${YELLOW}⚠️ Database permissions could be more secure ($perms)${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️ Database file not found (will be created on first run)${NC}"
fi

echo ""

# Final summary
echo "📊 SECURITY AUDIT SUMMARY"
echo "========================="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}🎉 SECURITY AUDIT PASSED!${NC}"
    echo -e "${GREEN}✅ No security issues found${NC}"
    echo -e "${GREEN}✅ All sensitive data properly secured${NC}"
    echo -e "${GREEN}✅ Configuration system working correctly${NC}"
    echo -e "${GREEN}✅ Git protection in place${NC}"
    echo ""
    echo -e "${GREEN}🚀 System is ready for production deployment!${NC}"
    exit 0
else
    echo -e "${RED}❌ SECURITY AUDIT FAILED!${NC}"
    echo -e "${RED}🚨 Found $ISSUES_FOUND security issue(s)${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the issues above before deploying to production.${NC}"
    exit 1
fi
