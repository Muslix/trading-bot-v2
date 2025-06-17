# Makefile für Crypto Trading Bot v2.0
# Vereinfachte Version mit nur den wichtigsten Commands

.PHONY: help setup test run dev clean deploy security-check

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color

##@ Help & Info
help: ## 📋 Show all available commands
	@echo "$(CYAN)🚀 CRYPTO TRADING BOT v2.0$(NC)"
	@echo "$(CYAN)==============================$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Development
setup: ## 🔧 Install dependencies and setup environment
	@echo "$(BLUE)🔧 Setting up environment...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Setup completed!$(NC)"

secure-setup: ## 🔒 Interactive secure configuration setup
	@echo "$(BLUE)🔒 Starting secure setup...$(NC)"
	@chmod +x scripts/secure_setup.sh
	@./scripts/secure_setup.sh

test: ## 🧪 Run all tests
	@echo "$(GREEN)🧪 Running test suite...$(NC)"
	cd scripts && $(PYTHON) run_tests.py

test-quick: ## ⚡ Run quick tests only
	@echo "$(YELLOW)⚡ Running quick tests...$(NC)"
	$(PYTHON) -m pytest tests/test_modules/ -v

##@ Running the Bot
run: ## 🚀 Run the trading bot (single execution)
	@echo "$(GREEN)🚀 Starting Crypto Trading Bot...$(NC)"
	$(PYTHON) src/main.py

dev: ## 💻 Start in development mode
	@echo "$(YELLOW)💻 Starting in development mode...$(NC)"
	$(PYTHON) -u src/main.py

start: ## 🔄 Start 24/7 monitoring
	@echo "$(GREEN)🔄 Starting 24/7 monitoring...$(NC)"
	@echo "$(YELLOW)💡 Press Ctrl+C to stop$(NC)"
	$(PYTHON) src/start_bot.py

start-web: ## 🌐 Start web dashboard
	@echo "$(CYAN)🌐 Starting web dashboard...$(NC)"
	@echo "$(YELLOW)🔗 Dashboard: http://localhost:5000$(NC)"
	$(PYTHON) src/web_api.py

##@ System Control
status: ## 📊 Check bot status
	@echo "$(CYAN)📊 Bot Status:$(NC)"
	@if pgrep -f "src/start_bot.py" > /dev/null; then \
		echo "$(GREEN)✅ Bot is RUNNING (PID: $$(pgrep -f src/start_bot.py))$(NC)"; \
	else \
		echo "$(RED)❌ Bot is STOPPED$(NC)"; \
	fi
	@if pgrep -f "src/web_api.py" > /dev/null; then \
		echo "$(GREEN)✅ Web API is RUNNING (PID: $$(pgrep -f src/web_api.py))$(NC)"; \
	else \
		echo "$(RED)❌ Web API is STOPPED$(NC)"; \
	fi

stop: ## ⏹️ Stop all bot processes
	@echo "$(YELLOW)⏹️ Stopping bot processes...$(NC)"
	@pkill -f "src/start_bot.py" || echo "$(YELLOW)No bot process found$(NC)"
	@pkill -f "src/web_api.py" || echo "$(YELLOW)No web API process found$(NC)"
	@echo "$(GREEN)✅ All processes stopped$(NC)"

logs: ## 📄 Show bot logs
	@if [ -f bot.log ]; then \
		tail -50 bot.log; \
	else \
		echo "$(YELLOW)No log file found$(NC)"; \
	fi

##@ Docker & Containerization
docker-build: ## 🐳 Build Docker image
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	docker build -t muslix/crypto-trading-bot:latest .
	docker tag muslix/crypto-trading-bot:latest muslix/crypto-trading-bot:v2.0
	@echo "$(GREEN)✅ Docker image built successfully!$(NC)"

docker-run: ## 🚀 Run bot in Docker container
	@echo "$(GREEN)🚀 Starting bot in Docker container...$(NC)"
	docker-compose up -d crypto-bot
	@echo "$(CYAN)🔗 Web dashboard: http://localhost:5000$(NC)"

docker-stop: ## ⏹️ Stop Docker containers
	@echo "$(YELLOW)⏹️ Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## 📄 Show Docker container logs
	@echo "$(CYAN)📄 Container logs:$(NC)"
	docker-compose logs -f crypto-bot

docker-monitoring: ## 📊 Start with monitoring stack
	@echo "$(BLUE)📊 Starting with monitoring...$(NC)"
	docker-compose --profile monitoring up -d
	@echo "$(CYAN)🔗 Grafana: http://localhost:3000$(NC)"
	@echo "$(CYAN)🔗 Prometheus: http://localhost:9090$(NC)"
	@echo "$(CYAN)🔗 Bot Dashboard: http://localhost:5000$(NC)"

docker-clean: ## 🧹 Clean Docker resources
	@echo "$(YELLOW)🧹 Cleaning Docker resources...$(NC)"
	docker-compose down -v
	docker system prune -f
	@echo "$(GREEN)✅ Docker cleanup completed!$(NC)"

##@ Production
deploy: ## 🚀 Deploy to production
	@echo "$(GREEN)🚀 Deploying to production...$(NC)"
	cd deployment && $(PYTHON) deploy_production.py

production-start: ## 🔄 Start production services
	@echo "$(GREEN)🔄 Starting production services...$(NC)"
	@echo "$(BLUE)🔧 Loading environment configuration...$(NC)"
	@if [ -f ".env.local" ]; then \
		echo "$(GREEN)✅ Using .env.local configuration$(NC)"; \
	elif [ -f ".env" ]; then \
		echo "$(GREEN)✅ Using .env configuration$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ No .env file found$(NC)"; \
	fi
	@chmod +x deployment/start_production.sh
	@bash deployment/start_production.sh

production-stop: ## ⏹️ Stop production services
	@echo "$(YELLOW)⏹️ Stopping production services...$(NC)"
	@sudo systemctl stop crypto-trading-bot.service crypto-web-api.service 2>/dev/null || true

production-status: ## 📊 Check production status
	@echo "$(CYAN)📊 Production Status:$(NC)"
	@echo "$(BLUE)🤖 Trading Bot:$(NC)"
	@sudo systemctl is-active crypto-trading-bot.service > /dev/null && echo "$(GREEN)✅ RUNNING$(NC)" || echo "$(RED)❌ STOPPED$(NC)"
	@echo "$(BLUE)🌐 Web API:$(NC)"
	@sudo systemctl is-active crypto-web-api.service > /dev/null && echo "$(GREEN)✅ RUNNING$(NC)" || echo "$(RED)❌ STOPPED$(NC)"

##@ Security & Quality
security-check: ## 🔍 Check for security issues
	@echo "$(BLUE)🔍 Running security check...$(NC)"
	@FOUND=0; \
	if grep -r "BOT_TOKEN.*=" src/ --include="*.py" | grep -E "\"[^\"]+\"|'[^']+'" > /dev/null 2>&1; then \
		echo "$(RED)❌ Hardcoded secrets found!$(NC)"; \
		exit 1; \
	fi; \
	if git check-ignore .env.local > /dev/null 2>&1; then \
		echo "$(GREEN)✅ Security check passed!$(NC)"; \
	else \
		echo "$(RED)❌ Sensitive files not protected$(NC)"; \
		exit 1; \
	fi

security-audit: ## 🔒 Comprehensive security audit
	@echo "$(BLUE)🔒 Running security audit...$(NC)"
	@chmod +x scripts/security_audit.sh
	@./scripts/security_audit.sh

##@ Maintenance
clean: ## 🧹 Clean temporary files
	@echo "$(YELLOW)🧹 Cleaning temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage dist/ build/
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

##@ Quick Actions
quick-start: ## ⚡ Quick start for new users
	@echo "$(GREEN)⚡ Quick Start Guide:$(NC)"
	@echo "$(YELLOW)1.$(NC) make setup          # Install dependencies"
	@echo "$(YELLOW)2.$(NC) make secure-setup   # Configure credentials"
	@echo "$(YELLOW)3.$(NC) make test           # Run tests"
	@echo "$(YELLOW)4.$(NC) make run            # Start the bot"
	@echo "$(YELLOW)5.$(NC) make start-web      # Open dashboard"

all: ## 🎯 Full workflow (setup -> test -> run)
	@$(MAKE) setup
	@$(MAKE) test
	@$(MAKE) run

# =============================================================================
# CODE QUALITY & TESTING
# =============================================================================

# Pre-commit checks - run before every commit
pre-commit:
	@echo "🔍 Running pre-commit checks..."
	@~/.local/bin/flake8 src/ tests/ --max-line-length=120 --ignore=E203,W503,F401,E501,F541,W291,E402,E722,F841 --count
	@python -m pytest tests/test_modules/ -x --tb=short
	@python -m pytest tests/test_integration.py -x --tb=short
	@echo "✅ All checks passed! Ready to commit."

# Quick pre-commit (skip integration tests for speed)
pre-commit-quick:
	@echo "🔍 Running quick pre-commit checks..."
	@~/.local/bin/flake8 src/ tests/ --max-line-length=120 --ignore=E203,W503,F401,E501,F541,W291,E402,E722,F841 --count
	@python -m pytest tests/test_integration.py -x --tb=short
	@echo "✅ Quick checks passed!"

# Full test suite
test-all:
	@python -m pytest tests/ -v --tb=short
