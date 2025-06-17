"""
Configuration Management - Load settings from .env file
Sichere Verwaltung aller Konfigurationsparameter
"""

import os
import logging
from typing import List, Optional
from pathlib import Path


class Config:
    """Configuration Manager für Environment Variables"""
    
    def __init__(self):
        self.load_env_file()
        self._validate_config()
    
    def load_env_file(self, env_file: str = None):
        """Lade .env Datei - bevorzuge .env.local für lokale Entwicklung"""
        if env_file is None:
            # Prüfe zunächst auf .env.local (für lokale Entwicklung)
            local_env = os.path.join(os.path.dirname(__file__), "..", ".env.local")
            if os.path.exists(local_env):
                env_file = local_env
                print("🔧 Using local development configuration (.env.local)")
            else:
                # Fallback auf .env
                env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        
        env_path = Path(env_file)
        
        if not env_path.exists():
            print(f"⚠️ .env file not found: {env_path}")
            print("📝 Please copy .env.example to .env and configure your settings")
            print("💡 For local development, you can use .env.local")
            return
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set environment variable
                        os.environ[key] = value
            
            print(f"✅ Loaded configuration from {env_path}")
            
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")
    
    def _validate_config(self):
        """Validiere kritische Konfiguration"""
        required_vars = ['TELEGRAM_BOT_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            if not self.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("📝 Please configure these in your .env file")
    
    def get(self, key: str, default: str = None) -> Optional[str]:
        """Hole Environment Variable"""
        return os.getenv(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Hole Integer Environment Variable"""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Hole Float Environment Variable"""
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Hole Boolean Environment Variable"""
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_list(self, key: str, default: List[str] = None) -> List[str]:
        """Hole List Environment Variable (comma-separated)"""
        if default is None:
            default = []
        
        value = self.get(key)
        if not value:
            return default
        
        return [item.strip() for item in value.split(',') if item.strip()]
    
    # =============================================================================
    # TELEGRAM CONFIGURATION
    # =============================================================================
    @property
    def telegram_bot_token(self) -> str:
        return self.get('TELEGRAM_BOT_TOKEN', '')
    
    @property
    def telegram_chat_id(self) -> Optional[str]:
        chat_id = self.get('TELEGRAM_CHAT_ID')
        return chat_id if chat_id else None
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    @property
    def database_path(self) -> str:
        return self.get('DATABASE_PATH', 'crypto_trading_bot.db')
    
    # =============================================================================
    # WEB API CONFIGURATION
    # =============================================================================
    @property
    def web_host(self) -> str:
        return self.get('WEB_HOST', '127.0.0.1')
    
    @property
    def web_port(self) -> int:
        return self.get_int('WEB_PORT', 5000)
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    @property
    def arbitrage_check_interval(self) -> int:
        return self.get_int('ARBITRAGE_CHECK_INTERVAL', 30)
    
    @property
    def performance_check_interval(self) -> int:
        return self.get_int('PERFORMANCE_CHECK_INTERVAL', 600)
    
    @property
    def daily_summary_hour(self) -> int:
        return self.get_int('DAILY_SUMMARY_HOUR', 8)
    
    @property
    def analysis_crypto_count(self) -> int:
        return self.get_int('ANALYSIS_CRYPTO_COUNT', 50)
    
    # =============================================================================
    # ALERT CONFIGURATION
    # =============================================================================
    @property
    def arbitrage_threshold(self) -> float:
        return self.get_float('ARBITRAGE_THRESHOLD', 2.0)
    
    @property
    def sharpe_change_threshold(self) -> float:
        return self.get_float('SHARPE_CHANGE_THRESHOLD', 0.5)
    
    @property
    def alert_cooldown_minutes(self) -> int:
        return self.get_int('ALERT_COOLDOWN_MINUTES', 5)
    
    # =============================================================================
    # WATCHLIST CONFIGURATION
    # =============================================================================
    @property
    def watchlist_symbols(self) -> List[str]:
        return self.get_list('WATCHLIST_SYMBOLS', ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'])
    
    @property
    def exchanges(self) -> List[str]:
        return self.get_list('EXCHANGES', ['binance', 'coinbase', 'kraken'])
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    @property
    def log_level(self) -> str:
        return self.get('LOG_LEVEL', 'INFO')
    
    @property
    def log_file(self) -> Optional[str]:
        log_file = self.get('LOG_FILE')
        return log_file if log_file else None
    
    # =============================================================================
    # DEBUG CONFIGURATION
    # =============================================================================
    @property
    def debug_mode(self) -> bool:
        return self.get_bool('DEBUG_MODE', False)
    
    @property
    def test_mode(self) -> bool:
        return self.get_bool('TEST_MODE', False)
    
    def print_config_summary(self):
        """Drucke Konfigurations-Übersicht (ohne sensitive Daten)"""
        print("⚙️ CONFIGURATION SUMMARY")
        print("=" * 40)
        print(f"📊 Database: {self.database_path}")
        print(f"🌐 Web API: {self.web_host}:{self.web_port}")
        print(f"🔄 Arbitrage Check: every {self.arbitrage_check_interval}s")
        print(f"📈 Performance Check: every {self.performance_check_interval//60}min")
        print(f"🚨 Arbitrage Threshold: {self.arbitrage_threshold}%")
        print(f"📱 Watchlist: {len(self.watchlist_symbols)} symbols")
        print(f"🏦 Exchanges: {len(self.exchanges)} exchanges")
        print(f"🪵 Log Level: {self.log_level}")
        print(f"🐛 Debug Mode: {self.debug_mode}")
        print(f"🧪 Test Mode: {self.test_mode}")
        
        # Telegram status (without showing token)
        if self.telegram_bot_token:
            if self.telegram_chat_id:
                print("✅ Telegram: Configured with Chat ID")
            else:
                print("⚠️ Telegram: Bot token set, but no Chat ID")
        else:
            print("❌ Telegram: Not configured")
        
        print("=" * 40)


# Global config instance
config = Config()


def get_config() -> Config:
    """Hole globale Config-Instanz"""
    return config


if __name__ == "__main__":
    # Test configuration loading
    print("🧪 TESTING CONFIGURATION LOADING")
    print("=" * 50)
    
    test_config = Config()
    test_config.print_config_summary()
    
    print("\n✅ Configuration test complete!")