# 🤖 Crypto Trading Bot v2.0

[![CI/CD Pipeline](https://github.com/Muslix/trading-bot-v2/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Muslix/trading-bot-v2/actions/workflows/ci-cd.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/muslix/crypto-trading-bot)
[![Security](https://img.shields.io/badge/security-audited-green.svg)](#security)
[![One-Click Setup](https://img.shields.io/badge/setup-one--click-green.svg)](#quick-start)

Ein fortschrittlicher, vollautomatischer Kryptowährungs-Trading-Bot mit **intelligenten ML-basierten Alerts**, **Enhanced Visualizations** und **One-Click Setup**.

## 🚀 Quick Start (< 5 Minuten!)

### Option 1: One-Click Installation
```bash
# Clone repository
git clone https://github.com/your-username/trading_bot_v2.git
cd trading_bot_v2

# Run one-click installer
./install.sh

# Start trading bot
./start.sh
```

### Option 2: Python Setup Script
```bash
# Run interactive setup
python3 setup.py

# Start the bot
./start.sh
```

**That's it!** 🎉 Your dashboard will be available at http://localhost:5000

## 📊 Dashboard Preview
- **Live Prices**: 25 cryptocurrencies with real-time updates
- **Smart Arbitrage**: ML-filtered opportunities with execution analysis  
- **Enhanced Charts**: Interactive heatmaps, correlation matrices, risk/return plots
- **Mobile Ready**: Responsive design for all devices

## ✨ Features

### 🚀 Core Trading Features
- **Echtzeitüberwachung** von Kryptowährungspreisen
- **Arbitrage-Erkennung** zwischen verschiedenen Börsen
- **Portfolio-Analyse** mit paralleler Verarbeitung
- **Intelligente Alerts** über Telegram
- **Historische Datenanalyse** für bessere Entscheidungen

### 🌐 Web Dashboard
- **Live-Dashboard** mit Echtzeitdaten
- **Interaktive Charts** für Preisverläufe
- **Portfolio-Übersicht** mit Performance-Metriken
- **Alert-Management** direkt im Browser
- **API-Zugang** für externe Integrationen

### 🔒 Sicherheit & Compliance
- **Umfassende Sicherheitsaudits** in CI/CD
- **Verschlüsselte Konfiguration** über Umgebungsvariablen
- **Keine Hardcoded Secrets** im Code
- **Automated Security Scanning** mit jeder Code-Änderung

### � Monitoring & Observability
- **Prometheus Metrics** für detailliertes Monitoring
- **Grafana Dashboards** für Visualisierung
- **Health Checks** und Uptime-Überwachung
- **Strukturierte Logs** für bessere Debugging

## 🚀 Quick Start

### 1. Repository klonen
```bash
git clone https://github.com/Muslix/trading-bot-v2.git
cd trading-bot-v2
```

### 2. Mit Docker (Empfohlen)
```bash
# Umgebungsvariablen konfigurieren
cp .env.example .env
# Bearbeite .env mit deinen API-Keys

# Bot mit Monitoring starten
make docker-monitoring
```

### 3. Manuelle Installation
```bash
# Dependencies installieren
make setup

# Sichere Konfiguration
make secure-setup

# Tests ausführen
make test

# Bot starten
make run
```

## 📋 Verfügbare Commands

### 🔧 Setup & Development
```bash
make setup          # Dependencies installieren
make secure-setup    # Interaktive Konfiguration
make test           # Alle Tests ausführen
make run            # Bot einmal ausführen
make dev            # Development-Modus
make start          # 24/7 Monitoring starten
```

### 🐳 Docker Commands
```bash
make docker-build      # Docker Image bauen
make docker-run        # Bot in Container starten
make docker-monitoring # Mit Prometheus/Grafana
make docker-logs       # Container Logs anzeigen
make docker-stop       # Container stoppen
```

### 🔒 Sicherheit
```bash
make security-check   # Schnelle Sicherheitsprüfung
make security-audit   # Umfassende Security-Analyse
```

### 🚀 Production
```bash
make deploy             # Production Deployment
make production-start   # Production Services starten
make production-status  # Status prüfen
```

## 🧪 Testing

### Run All Tests
```bash
cd scripts/
python3 run_tests.py
```

### Individual Tests
```bash
cd scripts/
python3 test_telegram.py      # Test Telegram integration
python3 test_24_7_monitor.py  # Test monitoring system
python3 test_web_api.py       # Test API endpoints
```

### 24h Full System Test
```bash
cd scripts/
python3 run_24h_test.py       # Complete system test
```

## 📈 Performance

### Arbitrage Detection
- **Real-time**: 30-second intervals
- **Multi-Exchange**: 3 major exchanges
- **Filtering**: Only profitable opportunities (≥1.5%)
- **Storage**: SQLite for historical analysis

### Portfolio Analysis
- **Historical Data**: 2 years of price data
- **Metrics**: Sharpe, Sortino, Calmar ratios
- **Updates**: Every 10 minutes
- **Coverage**: 50+ top cryptocurrencies

## 🔧 Advanced Usage

### Custom Scripts
```bash
# Run scripts overview
cd scripts/
./README.sh
```

### Database Queries
```bash
sqlite3 crypto_trading_bot.db
SELECT * FROM arbitrage_alerts WHERE profit_percentage >= 2.0;
```

### API Integration
```bash
curl http://localhost:5000/api/arbitrage-alerts
curl http://localhost:5000/api/dashboard-data
curl http://localhost:5000/api/live-prices
```

## 🛠️ Architecture

### Core Components
1. **Monitor System** (`crypto_monitor_24_7.py`)
   - Orchestrates all monitoring activities
   - Manages intervals and scheduling
   - Handles error recovery

2. **Alert Engine** (`modules/smart_alerts.py`)
   - Intelligent filtering and prioritization
   - Anti-spam mechanisms
   - Multi-channel notifications

3. **Data Layer** (`modules/database.py`)
   - SQLite storage for all data
   - Performance optimized queries
   - Data retention management

4. **Web Interface** (`web_api.py` + `frontend/`)
   - RESTful API endpoints
   - Real-time dashboard
   - Historical data visualization

## 📊 Monitoring Dashboard

Das Web-Dashboard zeigt:
- **Live Prices** von allen Börsen
- **Recent Alerts** (nur profitable ≥1.0%)
- **Top Performers** nach Sharpe Ratio
- **Bot Status** und Uptime
- **Charts** für Performance-Trends

## 🔄 Recent Improvements

### ✅ Project Structure
- Moved test scripts to `/scripts/` folder
- Better organization of utility scripts
- Added scripts overview (`scripts/README.sh`)

### ✅ Alert System Fixes
- Fixed 0% profit alerts spam
- Consistent `profit_percentage` key usage
- Improved threshold filtering (1.5% minimum)

### ✅ Frontend Improvements  
- Better error handling and logging
- Automatic data refresh on page load
- Fixed Recent Alerts display issues
- Added debug console output

### ✅ Configuration
- Centralized `.env` configuration
- Flexible thresholds and intervals
- Environment-based settings

## 🆕 Neueste Verbesserungen (v2.1)

### ✅ **Duplikate-Problem behoben**
- **Symbol-Normalisierung**: Automatische Bereinigung von BTC/BTC-USD/BTCUSD etc.
- **Intelligente Aggregation**: Duplikate werden durch Durchschnittsbildung zusammengefasst
- **API-Verbesserung**: `/api/performance-data` zeigt jetzt bereinigte Daten

### ✅ **Frontend Auto-Refresh**
- **5-Sekunden Updates**: Dashboard aktualisiert sich automatisch alle 5 Sekunden
- **Live-Daten**: Echtzeitanzeige der neuesten Arbitrage-Opportunities
- **Bessere UX**: Keine manuellen Refreshs mehr nötig

### ✅ **Erweiterte Coin-Analyse**
- **Top 100 Coins**: Analyse von 100 statt 50 Cryptocurrencies
- **Mehr Abdeckung**: Umfassendere Marktanalyse
- **Bessere Performance**: Optimierte Datenverarbeitung

### ✅ **Telegram Integration**
- **Chat ID Setup**: Automatische Chat ID Erkennung bei Setup
- **Sofortige Alerts**: Direkte Benachrichtigungen bei Arbitrage-Opportunities
- **Smart Filtering**: Nur profitable Alerts (≥1.5%) werden gesendet

### 🔧 **Konfiguration (.env Updates)**
```env
# Neue Einstellungen
TELEGRAM_CHAT_ID=YOUR_CHAT_ID       # Ihre Chat ID (siehe Setup)
ANALYSIS_CRYPTO_COUNT=100           # Analysiere 100 Coins
ARBITRAGE_THRESHOLD=1.5             # 1.5% minimum profit
```

### 📊 **API Verbesserungen**
```bash
# Neue API Features
GET /api/performance-data           # Mit Duplikate-Bereinigung
    - original_count: Ursprüngliche Anzahl
    - count: Nach Bereinigung  
    - duplicates_removed: Entfernte Duplikate

# Live-Testing
curl http://localhost:5000/api/performance-data
```

### 🛠️ **Symbol-Normalisierung**
```python
# Neue Utility
from utils.symbol_normalizer import normalize_crypto_symbol

normalize_crypto_symbol('BTC-USD')   # -> 'BTC'
normalize_crypto_symbol('XRPUSD')    # -> 'XRP'  
normalize_crypto_symbol('ETH-USDT')  # -> 'ETH'
```

---

## 🚨 Troubleshooting

### No Recent Alerts Showing
1. Check Web API: `curl http://localhost:5000/api/arbitrage-alerts`
2. Verify database: `sqlite3 crypto_trading_bot.db "SELECT COUNT(*) FROM arbitrage_alerts;"`
3. Check browser console for errors

### Bot Not Sending Telegram Alerts
1. Verify `TELEGRAM_BOT_TOKEN` in `.env`
2. Set `TELEGRAM_CHAT_ID` in `.env`
3. Test with: `cd scripts/ && python3 test_telegram.py`

### High CPU Usage
1. Increase `ARBITRAGE_CHECK_INTERVAL` (e.g., 60 seconds)
2. Reduce `ANALYSIS_CRYPTO_COUNT`
3. Limit `WATCHLIST_SYMBOLS`

## 📝 Contributing

1. Tests für neue Features hinzufügen
2. Dokumentation aktualisieren
3. Code-Style: PEP 8 befolgen
4. Pull Requests willkommen!

## 📄 License

MIT License - Siehe LICENSE Datei

---

**Status**: ✅ Production Ready | 📈 Actively Maintained | 🚀 High Performance

*Last Updated: June 16, 2025*

## 🔐 Security & Configuration

### Environment Setup
1. **Copy the template**: `cp .env.template .env`
2. **Configure your credentials** (never commit .env to git):
   ```bash
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   TELEGRAM_CHAT_ID=your_actual_chat_id
   
   # Exchange API Keys (if using live trading)
   BINANCE_API_KEY=your_actual_api_key
   BINANCE_SECRET_KEY=your_actual_secret_key
   ```

### Security Best Practices
- ✅ All sensitive files are gitignored (`.env`, `*token*`, `*secret*`)
- ✅ Use environment variables for all credentials
- ✅ Run security audit: `./scripts/security_audit.sh`
- ✅ Regular dependency updates with `make update-deps`
- ✅ File permissions are automatically secured
- ⚠️ **Never commit real API keys to version control**

### Security Audit
```bash
# Run comprehensive security check
./scripts/security_audit.sh

# Expected output: "✅ Security audit passed!"
```
