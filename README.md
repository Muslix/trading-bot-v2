# 🤖 Crypto Trading Bot 24/7 - Advanced Multi-Exchange Arbitrage System

Ein intelligenter Kryptowährungs-Trading-Bot mit 24/7-Überwachung, Arbitrage-Erkennung und automatischen Alerts.

## 📁 Projektstruktur

```
crypto_trading_bot_v2/                 # Hauptprojektverzeichnis
├── 📂 modules/                        # Kernmodule
│   ├── 🔍 arbitrage_detector.py       # Arbitrage-Erkennung
│   ├── 💾 database.py                 # SQLite Database Management
│   ├── 📊 historical_data.py          # Historische Datenanalyse
│   ├── 📈 portfolio_analyzer.py       # Portfolio Performance Analyse
│   ├── 💲 price_monitor.py            # Preisüberwachung (Legacy)
│   ├── 💲 real_price_monitor.py       # Echte Multi-Exchange Preise
│   ├── 🚨 smart_alerts.py             # Intelligentes Alert-System
│   └── 📱 telegram_bot.py             # Telegram Notifications
├── 📂 utils/                          # Hilfsfunktionen
│   └── ⚡ decorators.py               # Performance & Logging Decorators
├── 📂 tests/                          # Unit Tests
│   ├── test_integration.py            # Integrationstests
│   └── 📂 test_modules/               # Modul-spezifische Tests
├── 📂 scripts/                        # 🆕 Test & Utility Scripts
│   ├── test_telegram.py               # Telegram Bot Tests
│   ├── test_24_7_monitor.py           # Monitor System Tests
│   ├── test_web_api.py                # Web API Tests
│   ├── run_24h_test.py                # 24h Volltest
│   ├── run_tests.py                   # Unit Test Runner
│   └── README.sh                      # Scripts Übersicht
├── 📂 frontend/                       # Web Dashboard
│   └── index.html                     # Vue.js Dashboard
├── 📄 main.py                         # Haupt-Analysetool
├── 🔄 crypto_monitor_24_7.py          # 24/7 Monitoring System
├── 🌐 web_api.py                      # Flask Web API
├── ⚙️ config.py                       # Konfigurationslader
├── 🚀 start_bot.py                    # Bot Starter
├── 📊 crypto_trading_bot.db           # SQLite Database
└── 🔧 requirements.txt                # Python Dependencies
```

## 🚀 Features

### 🔍 Multi-Exchange Arbitrage Detection
- **Echte Preisdaten** von Binance, Coinbase, Kraken
- **Intelligent Filtering**: Nur Opportunities ≥ 1.5% Profit
- **Anti-Spam**: Cooldown-basierte Alert-Kontrolle
- **Database Storage**: Alle Arbitrage-Opportunities gespeichert

### 📊 Advanced Portfolio Analysis
- **100+ Cryptocurrencies** historische Datenanalyse
- **Sharpe Ratio, Sortino, Calmar** Berechnung
- **Top Performer Tracking** mit Performance-Alerts
- **2 Jahre historische Daten** für präzise Metriken

### 🚨 Smart Alert System
- **Telegram Integration** für sofortige Benachrichtigungen
- **Threshold-basierte Alerts**: 
  - Arbitrage ≥ 1.5%
  - Sharpe Ratio Änderungen ≥ 0.5
- **Cooldown Management**: Anti-Spam Mechanismus
- **Prioritäts-basierte Alerts**: High/Medium/Low

### 🌐 Real-time Web Dashboard
- **Vue.js Frontend** mit Live-Updates
- **Chart.js Visualisierung**
- **Bootstrap UI** mit modernem Design
- **Auto-Refresh** alle 30 Sekunden

## ⚙️ Konfiguration (.env)

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Alert Thresholds
ARBITRAGE_THRESHOLD=1.5              # Minimum 1.5% profit
SHARPE_CHANGE_THRESHOLD=0.5          # Sharpe ratio change alert
ALERT_COOLDOWN_MINUTES=10            # Anti-spam cooldown

# Monitoring Intervals
ARBITRAGE_CHECK_INTERVAL=30          # Check every 30 seconds
PERFORMANCE_CHECK_INTERVAL=600       # Check every 10 minutes

# Watchlist
WATCHLIST_SYMBOLS=BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,DOT/USDT
EXCHANGES=binance,coinbase,kraken
```

## 🏃‍♂️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Konfiguration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start 24/7 Monitoring
```bash
python3 crypto_monitor_24_7.py
```

### 4. Start Web Dashboard
```bash
python3 web_api.py
# Visit: http://localhost:5000
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
- **Vorkonfigurierte Chat ID**: `283812226` bereits eingetragen
- **Sofortige Alerts**: Direkte Benachrichtigungen bei Arbitrage-Opportunities
- **Smart Filtering**: Nur profitable Alerts (≥1.5%) werden gesendet

### 🔧 **Konfiguration (.env Updates)**
```env
# Neue Einstellungen
TELEGRAM_CHAT_ID=283812226          # Ihre Chat ID
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
