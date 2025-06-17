# Makefile für Crypto Trading Bot v2.0
# Alle wichtigen Befehle für Development, Testing und Deployment

.PHONY: help install test test-verbose test-coverage lint format clean run dev setup check all

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
PYTEST := $(PYTHON) -m pytest
COVERAGE := $(PYTHON) -m coverage

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

##@ Help
help: ## 📋 Zeige alle verfügbaren Befehle
	@echo "$(CYAN)🚀 CRYPTO TRADING BOT v2.0 - Makefile$(NC)"
	@echo "$(CYAN)===========================================$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(PURPLE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation
setup: ## 🔧 Komplettes Setup (Dependencies + Virtual Environment)
	@echo "$(YELLOW)🔧 Setting up Crypto Trading Bot...$(NC)"
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Setup completed!$(NC)"

install: ## 📦 Installiere nur Dependencies
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

install-dev: ## 🛠️ Installiere Development Dependencies
	@echo "$(BLUE)🛠️ Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 mypy isort
	@echo "$(GREEN)✅ Development dependencies installed!$(NC)"

# =============================================================================
# SECURE SETUP
# =============================================================================

.PHONY: secure-setup
secure-setup: ## 🔒 Interactive setup with secure credential management
	@echo "$(BLUE)🔒 Starting Secure Setup...$(NC)"
	@chmod +x scripts/secure_setup.sh
	@./scripts/secure_setup.sh
	@echo "$(GREEN)✅ Secure setup completed!$(NC)"

##@ Development
run: ## 🚀 Starte den Trading Bot (einmalig)
	@echo "$(GREEN)🚀 Starting Crypto Trading Bot (single run)...$(NC)"
	$(PYTHON) src/main.py

start: ## 🔄 Starte 24/7 Monitoring (persistent)
	@echo "$(GREEN)🔄 Starting 24/7 Crypto Monitoring...$(NC)"
	@echo "$(YELLOW)💡 Press Ctrl+C to stop gracefully$(NC)"
	$(PYTHON) src/start_bot.py

start-background: ## 🌙 Starte im Hintergrund
	@echo "$(GREEN)🌙 Starting bot in background...$(NC)"
	nohup $(PYTHON) src/start_bot.py > bot.log 2>&1 &
	@echo "$(GREEN)✅ Bot started in background$(NC)"
	@echo "$(YELLOW)📋 Check status: make status$(NC)"
	@echo "$(YELLOW)📄 View logs: tail -f bot.log$(NC)"

start-web: ## 🌐 Starte Web Dashboard
	@echo "$(CYAN)🌐 Starting web dashboard...$(NC)"
	@echo "$(YELLOW)🔗 Open: http://localhost:5000$(NC)"
	$(PYTHON) src/web_api.py

start-all: ## 🚀 Starte komplettes System (Web + Bot)
	@echo "$(GREEN)🚀 Starting complete system...$(NC)"
	@echo "$(CYAN)🌐 Starting web dashboard in background...$(NC)"
	nohup $(PYTHON) src/web_api.py > web.log 2>&1 &
	@sleep 3
	@echo "$(GREEN)🤖 Starting bot monitoring...$(NC)"
	$(PYTHON) src/start_bot.py

dev: ## 💻 Development Mode (mit Debugging)
	@echo "$(YELLOW)💻 Starting in development mode...$(NC)"
	$(PYTHON) -u src/main.py

demo: ## 🎯 Demo Mode (weniger Daten für schnelle Tests)
	@echo "$(CYAN)🎯 Starting demo mode...$(NC)"
	@echo "$(YELLOW)ℹ️ Demo verwendet weniger Daten für schnellere Ausführung$(NC)"
	$(PYTHON) src/main.py

##@ Testing
test: ## 🧪 Führe alle Tests aus
	@echo "$(GREEN)🧪 Running test suite...$(NC)"
	cd scripts && $(PYTHON) run_tests.py

test-verbose: ## 🔍 Tests mit detaillierter Ausgabe
	@echo "$(GREEN)🔍 Running tests with verbose output...$(NC)"
	$(PYTEST) tests/ -v --tb=short

test-fast: ## ⚡ Schnelle Tests (ohne Integration Tests)
	@echo "$(YELLOW)⚡ Running fast tests...$(NC)"
	$(PYTEST) tests/test_utils/ tests/test_modules/ -v

test-telegram: ## � Teste Telegram Bot
	@echo "$(CYAN)� Testing Telegram Bot...$(NC)"
	cd scripts && $(PYTHON) test_telegram.py

test-monitor: ## � Teste 24/7 Monitor System
	@echo "$(BLUE)� Testing Monitor System...$(NC)"
	cd scripts && $(PYTHON) test_24_7_monitor.py

test-api: ## 🌐 Teste Web API
	@echo "$(GREEN)🌐 Testing Web API...$(NC)"
	cd scripts && $(PYTHON) test_web_api.py

test-24h: ## ⏰ 24h Volltest
	@echo "$(PURPLE)⏰ Running 24h full system test...$(NC)"
	cd scripts && $(PYTHON) run_24h_test.py

test-duplicates: ## 🧪 Teste Duplikate-Vermeidung
	@echo "$(YELLOW)🧪 Testing duplicate prevention logic...$(NC)"
	$(PYTHON) scripts/test_duplicate_prevention.py

test-coin-coverage: ## 🧪 Teste Coin Coverage (alle konfigurierten Coins)
	@echo "$(YELLOW)🧪 Testing coin coverage...$(NC)"
	$(PYTHON) tests/test_coin_coverage.py

test-duplicate-prevention: ## 🧪 Teste Duplikate-Vermeidung
	@echo "$(YELLOW)🧪 Testing duplicate prevention...$(NC)"
	$(PYTHON) tests/test_duplicate_prevention.py

test-system: ## 🧪 Umfassende System-Tests (Coverage + Duplikate)
	@echo "$(YELLOW)🧪 Running comprehensive system tests...$(NC)"
	$(PYTHON) tests/test_coin_coverage.py && $(PYTHON) tests/test_duplicate_prevention.py
	@echo "$(GREEN)✅ All system tests completed!$(NC)"

##@ Code Quality
lint: ## 🔍 Code Linting (flake8)
	@echo "$(BLUE)🔍 Running code linting...$(NC)"
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/modules/ src/utils/ src/main.py --max-line-length=100 --ignore=E203,W503; \
		echo "$(GREEN)✅ Linting completed!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ flake8 not installed. Run: make install-dev$(NC)"; \
	fi

format: ## 🎨 Code Formatting (black)
	@echo "$(PURPLE)🎨 Formatting code...$(NC)"
	@if command -v black >/dev/null 2>&1; then \
		black src/modules/ src/utils/ src/main.py tests/ --line-length=100; \
		echo "$(GREEN)✅ Code formatted!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ black not installed. Run: make install-dev$(NC)"; \
	fi

type-check: ## 🔎 Type Checking (mypy)
	@echo "$(CYAN)🔎 Running type checks...$(NC)"
	@if command -v mypy >/dev/null 2>&1; then \
		mypy src/modules/ src/utils/ src/main.py --ignore-missing-imports; \
		echo "$(GREEN)✅ Type checking completed!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ mypy not installed. Run: make install-dev$(NC)"; \
	fi

sort-imports: ## 📐 Sort Imports (isort)
	@echo "$(BLUE)📐 Sorting imports...$(NC)"
	@if command -v isort >/dev/null 2>&1; then \
		isort src/modules/ src/utils/ src/main.py tests/ --profile black; \
		echo "$(GREEN)✅ Imports sorted!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ isort not installed. Run: make install-dev$(NC)"; \
	fi

##@ Quality Assurance
check: ## ✅ Komplette Code-Qualitätsprüfung
	@echo "$(CYAN)✅ Running complete quality check...$(NC)"
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test-fast
	@echo "$(GREEN)🎉 Quality check completed!$(NC)"

check-all: ## 🎯 Vollständige Qualitätsprüfung (mit Coverage)
	@echo "$(PURPLE)🎯 Running comprehensive quality check...$(NC)"
	@$(MAKE) format
	@$(MAKE) sort-imports
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test-coverage
	@echo "$(GREEN)🎉 Comprehensive check completed!$(NC)"

##@ System Control
status: ## 📊 Zeige Bot Status
	@echo "$(CYAN)📊 Checking bot status...$(NC)"
	@if pgrep -f "src/start_bot.py" > /dev/null; then \
		echo "$(GREEN)✅ Bot is RUNNING$(NC)"; \
		echo "$(YELLOW)   PID: $$(pgrep -f src/start_bot.py)$(NC)"; \
	else \
		echo "$(RED)❌ Bot is STOPPED$(NC)"; \
	fi
	@if pgrep -f "src/web_api.py" > /dev/null; then \
		echo "$(GREEN)✅ Web API is RUNNING$(NC)"; \
		echo "$(YELLOW)   PID: $$(pgrep -f src/web_api.py)$(NC)"; \
		echo "$(YELLOW)   URL: http://localhost:5000$(NC)"; \
	else \
		echo "$(RED)❌ Web API is STOPPED$(NC)"; \
	fi

stop: ## ⏹️ Stoppe alle Bot-Prozesse
	@echo "$(YELLOW)⏹️ Stopping bot processes...$(NC)"
	@pkill -f "src/start_bot.py" || echo "$(YELLOW)No bot process found$(NC)"
	@pkill -f "src/web_api.py" || echo "$(YELLOW)No web API process found$(NC)"
	@echo "$(GREEN)✅ All processes stopped$(NC)"

restart: ## 🔄 Neustart des Bots
	@echo "$(YELLOW)🔄 Restarting bot...$(NC)"
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start-background

logs: ## 📄 Zeige Bot Logs
	@echo "$(CYAN)📄 Bot Logs (last 50 lines):$(NC)"
	@if [ -f bot.log ]; then \
		tail -50 bot.log; \
	else \
		echo "$(YELLOW)No log file found. Start bot with 'make start-background'$(NC)"; \
	fi

logs-live: ## 📺 Live Bot Logs
	@echo "$(CYAN)📺 Live Bot Logs (Press Ctrl+C to exit):$(NC)"
	@if [ -f bot.log ]; then \
		tail -f bot.log; \
	else \
		echo "$(YELLOW)No log file found. Start bot with 'make start-background'$(NC)"; \
	fi

web-logs: ## 🌐 Zeige Web API Logs
	@echo "$(CYAN)🌐 Web API Logs (last 50 lines):$(NC)"
	@if [ -f web.log ]; then \
		tail -50 web.log; \
	else \
		echo "$(YELLOW)No web log file found$(NC)"; \
	fi

##@ Maintenance
clean: ## 🧹 Cleaning temporäre Dateien
	@echo "$(YELLOW)🧹 Cleaning temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

clean-all: ## 🗑️ Tiefe Reinigung (inkl. Dependencies)
	@echo "$(RED)🗑️ Deep cleaning...$(NC)"
	@$(MAKE) clean
	@echo "$(YELLOW)⚠️ Note: Virtual environment not removed automatically$(NC)"
	@echo "$(GREEN)✅ Deep cleanup completed!$(NC)"

##@ Monitoring & Analysis
benchmark: ## 📈 Performance Benchmarks
	@echo "$(CYAN)📈 Running performance benchmarks...$(NC)"
	@echo "$(BLUE)🔍 Portfolio Analysis Benchmark:$(NC)"
	@time $(PYTHON) -c "from src.modules.portfolio_analyzer import analyze_crypto_portfolio_parallel, get_top_cryptocurrencies; analyze_crypto_portfolio_parallel(get_top_cryptocurrencies(50))"
	@echo "$(BLUE)⚡ Price Monitor Benchmark:$(NC)"
	@time $(PYTHON) -c "import asyncio; from src.modules.price_monitor import monitor_multi_exchange_prices; asyncio.run(monitor_multi_exchange_prices('BTC/USDT'))"

stats: ## 📊 Projekt-Statistiken
	@echo "$(CYAN)📊 Project Statistics$(NC)"
	@echo "$(CYAN)==================$(NC)"
	@echo "$(BLUE)📁 Total Python files:$(NC) $$(find . -name '*.py' | wc -l)"
	@echo "$(BLUE)📝 Lines of code:$(NC) $$(find . -name '*.py' -exec cat {} \; | wc -l)"
	@echo "$(BLUE)🧪 Test files:$(NC) $$(find tests/ -name 'test_*.py' | wc -l)"
	@echo "$(BLUE)🎯 Total tests:$(NC) $$($(PYTEST) tests/ --collect-only -q 2>/dev/null | grep '<Module' | wc -l)"
	@echo "$(BLUE)📦 Modules:$(NC) $$(find src/modules/ -name '*.py' | grep -v __init__ | wc -l)"
	@echo "$(BLUE)🛠️ Utils:$(NC) $$(find src/utils/ -name '*.py' | grep -v __init__ | wc -l)"

dependencies: ## 📋 Zeige installierte Dependencies
	@echo "$(CYAN)📋 Installed Dependencies$(NC)"
	@echo "$(CYAN)========================$(NC)"
	$(PIP) list | grep -E "(pytest|numpy|pandas|ccxt|yfinance)"

##@ Workflows
all: ## 🎯 Kompletter Workflow (Setup -> Tests -> Quality)
	@echo "$(PURPLE)🎯 Running complete workflow...$(NC)"
	@$(MAKE) setup
	@$(MAKE) test
	@$(MAKE) check
	@echo "$(GREEN)🎉 Complete workflow finished!$(NC)"

ci: ## 🔄 CI/CD Pipeline
	@echo "$(BLUE)🔄 Running CI/CD pipeline...$(NC)"
	@$(MAKE) install
	@$(MAKE) test-coverage
	@$(MAKE) lint
	@echo "$(GREEN)✅ CI/CD pipeline completed!$(NC)"

quick-start: ## ⚡ Schnellstart für neue Entwickler
	@echo "$(GREEN)⚡ Quick Start for Crypto Trading Bot$(NC)"
	@echo "$(GREEN)=====================================$(NC)"
	@echo "$(YELLOW)1. Installing dependencies...$(NC)"
	@$(MAKE) install
	@echo "$(YELLOW)2. Running tests...$(NC)"
	@$(MAKE) test-fast
	@echo "$(YELLOW)3. Starting bot...$(NC)"
	@$(MAKE) run
	@echo "$(GREEN)🎉 Quick start completed!$(NC)"

##@ Documentation
docs: ## 📚 Zeige Projekt-Dokumentation
	@echo "$(CYAN)📚 Crypto Trading Bot v2.0 Documentation$(NC)"
	@echo "$(CYAN)=========================================$(NC)"
	@echo ""
	@echo "$(GREEN)🎯 Projekt-Übersicht:$(NC)"
	@echo "  Ein modularer Crypto Trading Bot mit drei Python-Konzepten:"
	@echo "  • $(BLUE)Multiprocessing$(NC): Portfolio-Analyse für 50-100 Kryptowährungen"
	@echo "  • $(BLUE)Async/IO$(NC): Live-Preise von mehreren Börsen gleichzeitig"
	@echo "  • $(BLUE)Decorators$(NC): Automatisches Logging und Performance-Tracking"
	@echo ""
	@echo "$(GREEN)📁 Projekt-Struktur:$(NC)"
	@echo "  • $(YELLOW)main.py$(NC)              - Haupt-Entry-Point"
	@echo "  • $(YELLOW)modules/$(NC)             - Kern-Module (Portfolio, Price Monitor, Arbitrage)"
	@echo "  • $(YELLOW)utils/$(NC)               - Hilfsfunktionen (Decorators)"
	@echo "  • $(YELLOW)tests/$(NC)               - Umfassende Test-Suite"
	@echo ""
	@echo "$(GREEN)🚀 Schnellstart:$(NC)"
	@echo "  make quick-start    # Alles installieren und starten"
	@echo "  make run           # Trading Bot ausführen"
	@echo "  make test          # Tests ausführen"
	@echo ""
	@echo "$(GREEN)📖 Weitere Befehle:$(NC)"
	@echo "  make help          # Alle verfügbaren Befehle anzeigen"

version: ## 🏷️ Zeige Version und System-Info
	@echo "$(CYAN)🏷️ Version Information$(NC)"
	@echo "$(CYAN)=====================$(NC)"
	@echo "$(BLUE)🤖 Crypto Trading Bot:$(NC) v2.0"
	@echo "$(BLUE)🐍 Python Version:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)📦 Pip Version:$(NC) $$($(PIP) --version)"
	@echo "$(BLUE)🧪 Pytest Version:$(NC) $$($(PYTEST) --version | head -1)"
	@echo "$(BLUE)💻 System:$(NC) $$(uname -s) $$(uname -r)"
	@echo "$(BLUE)📅 Date:$(NC) $$(date)"

##@ Targets mit Abhängigkeiten
.PHONY: test-and-run
test-and-run: test ## 🧪🚀 Tests ausführen und dann Bot starten
	@$(MAKE) run

##@ Database Management
cleanup-db: ## 🧹 Bereinige die Database (Zero-Profit Alerts)
	@echo "$(YELLOW)🧹 Cleaning up database...$(NC)"
	$(PYTHON) scripts/cleanup_db.py --zero-profit --duplicates
	@echo "$(GREEN)✅ Database cleaned!$(NC)"

cleanup-db-full: ## 🧹 Vollständige Database-Bereinigung 
	@echo "$(YELLOW)🧹 Full database cleanup...$(NC)"
	$(PYTHON) scripts/cleanup_db.py --all
	@echo "$(GREEN)✅ Full database cleanup completed!$(NC)"

db-stats: ## 📊 Zeige Database-Statistiken
	@echo "$(BLUE)📊 Database Statistics:$(NC)"
	$(PYTHON) scripts/cleanup_db.py --stats

cleanup-preview: ## 👀 Zeige Vorschau der Duplikate-Bereinigung
	@echo "$(YELLOW)👀 Showing duplicate alerts cleanup preview...$(NC)"
	$(PYTHON) scripts/cleanup_duplicate_alerts.py --preview

cleanup-duplicates: ## 🧹 Bereinige doppelte Arbitrage Alerts
	@echo "$(RED)🧹 Cleaning up duplicate arbitrage alerts...$(NC)"
	$(PYTHON) scripts/cleanup_duplicate_alerts.py --cleanup
	@echo "$(GREEN)✅ Database cleanup completed!$(NC)"

##@ Production Deployment
deploy: ## 🚀 Production Deployment (komplett)
	@echo "$(GREEN)🚀 Starting production deployment...$(NC)"
	@echo "$(YELLOW)⚠️ This will deploy the bot to production environment$(NC)"
	cd deployment && $(PYTHON) deploy_production.py
	@echo "$(GREEN)✅ Production deployment completed!$(NC)"

production-start: ## 🔄 Starte Production Bot
	@echo "$(GREEN)🔄 Starting production bot...$(NC)"
	bash deployment/start_production.sh

production-stop: ## ⏹️ Stoppe Production Services
	@echo "$(YELLOW)⏹️ Stopping production services...$(NC)"
	@sudo systemctl stop crypto-trading-bot.service || echo "$(YELLOW)Bot service not running$(NC)"
	@sudo systemctl stop crypto-web-api.service || echo "$(YELLOW)Web API service not running$(NC)"
	@echo "$(GREEN)✅ Production services stopped$(NC)"

production-status: ## 📊 Production Status
	@echo "$(CYAN)📊 Production Status$(NC)"
	@echo "$(CYAN)==================$(NC)"
	@echo "$(BLUE)🤖 Trading Bot Service:$(NC)"
	@sudo systemctl is-active crypto-trading-bot.service && echo "$(GREEN)✅ RUNNING$(NC)" || echo "$(RED)❌ STOPPED$(NC)"
	@echo "$(BLUE)🌐 Web API Service:$(NC)"
	@sudo systemctl is-active crypto-web-api.service && echo "$(GREEN)✅ RUNNING$(NC)" || echo "$(RED)❌ STOPPED$(NC)"
	@echo ""
	@echo "$(BLUE)🔍 Process Status:$(NC)"
	@if pgrep -f "src/crypto_monitor_24_7.py" > /dev/null; then \
		echo "$(GREEN)✅ Bot Monitor is RUNNING (PID: $$(pgrep -f src/crypto_monitor_24_7.py))$(NC)"; \
	else \
		echo "$(RED)❌ Bot Monitor is STOPPED$(NC)"; \
	fi
	@if pgrep -f "src/web_api.py" > /dev/null; then \
		echo "$(GREEN)✅ Web API is RUNNING (PID: $$(pgrep -f src/web_api.py))$(NC)"; \
		echo "$(YELLOW)   URL: http://localhost:5000$(NC)"; \
	else \
		echo "$(RED)❌ Web API is STOPPED$(NC)"; \
	fi

production-restart: ## 🔄 Neustart Production Services
	@echo "$(YELLOW)🔄 Restarting production services...$(NC)"
	@$(MAKE) production-stop
	@sleep 3
	@$(MAKE) production-start
	@echo "$(GREEN)✅ Production services restarted$(NC)"

production-logs: ## 📄 Production Logs
	@echo "$(CYAN)📄 Production Logs$(NC)"
	@echo "$(CYAN)==================$(NC)"
	@echo "$(BLUE)🤖 Trading Bot Logs:$(NC)"
	@sudo journalctl -u crypto-trading-bot.service --no-pager -n 50
	@echo ""
	@echo "$(BLUE)🌐 Web API Logs:$(NC)"
	@sudo journalctl -u crypto-web-api.service --no-pager -n 50

production-logs-live: ## 📺 Live Production Logs
	@echo "$(CYAN)📺 Live Production Logs (Press Ctrl+C to exit)$(NC)"
	@echo "$(YELLOW)Following both services...$(NC)"
	@sudo journalctl -u crypto-trading-bot.service -u crypto-web-api.service -f

install-services: ## 🔧 Installiere systemd Services
	@echo "$(BLUE)🔧 Installing systemd services...$(NC)"
	@if [ -f deployment/crypto-trading-bot.service ]; then \
		sudo cp deployment/crypto-trading-bot.service /etc/systemd/system/; \
		echo "$(GREEN)✅ Bot service installed$(NC)"; \
	fi
	@if [ -f deployment/crypto-web-api.service ]; then \
		sudo cp deployment/crypto-web-api.service /etc/systemd/system/; \
		echo "$(GREEN)✅ Web API service installed$(NC)"; \
	fi
	@sudo systemctl daemon-reload
	@sudo systemctl enable crypto-trading-bot.service
	@sudo systemctl enable crypto-web-api.service
	@echo "$(GREEN)✅ Services installed and enabled$(NC)"

remove-services: ## 🗑️ Entferne systemd Services
	@echo "$(RED)🗑️ Removing systemd services...$(NC)"
	@sudo systemctl stop crypto-trading-bot.service crypto-web-api.service 2>/dev/null || true
	@sudo systemctl disable crypto-trading-bot.service crypto-web-api.service 2>/dev/null || true
	@sudo rm -f /etc/systemd/system/crypto-trading-bot.service
	@sudo rm -f /etc/systemd/system/crypto-web-api.service
	@sudo systemctl daemon-reload
	@echo "$(GREEN)✅ Services removed$(NC)"

.PHONY: security-check
security-check: ## 🔍 Check for hardcoded secrets and security issues
	@echo "$(BLUE)🔍 Running Security Check...$(NC)"
	@echo "$(YELLOW)Checking for hardcoded tokens...$(NC)"
	@FOUND=0; \
	if grep -r "BOT_TOKEN.*=" src/ --include="*.py" | grep -E "\"[^\"]+\"|'[^']+'" > /dev/null 2>&1; then \
		echo "$(RED)❌ Hardcoded BOT_TOKEN assignment found!$(NC)"; \
		FOUND=1; \
	fi; \
	if [ $$FOUND -eq 0 ]; then \
		echo "$(GREEN)✅ No hardcoded secrets found$(NC)"; \
	else \
		exit 1; \
	fi
	@echo "$(YELLOW)Checking .gitignore protection...$(NC)"
	@if git check-ignore .env.local > /dev/null 2>&1; then \
		echo "$(GREEN)✅ Sensitive files properly ignored$(NC)"; \
	else \
		echo "$(RED)❌ Sensitive files not properly protected$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🔒 Security check passed!$(NC)"

.PHONY: test-config
test-config: ## 🧪 Test configuration loading
	@echo "$(BLUE)🧪 Testing Configuration...$(NC)"
	@python -c "import sys; sys.path.append('.'); from config.config import get_config; c=get_config(); print('✅ Config loaded successfully')"

.PHONY: security-audit
security-audit: ## 🔒 Comprehensive security audit
	@echo "$(BLUE)🔒 Running Full Security Audit...$(NC)"
	@chmod +x scripts/security_audit.sh
	@./scripts/security_audit.sh