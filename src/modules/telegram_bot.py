"""
Telegram Bot Module - 24/7 Crypto Trading Bot Alerts
Sendet intelligente Alerts für Arbitrage und Performance-Updates
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import Bot
from telegram.constants import ParseMode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import os

# Import Config
import sys

from src.utils.decorators import async_log_performance

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from config.config import get_config

config = get_config()


class TelegramCryptoBot:
    """24/7 Crypto Trading Bot mit intelligenten Telegram Alerts"""

    def __init__(self, bot_token: str = None):
        # Use provided token or get from config
        if bot_token is None:
            bot_token = config.telegram_bot_token

        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.chat_id = config.telegram_chat_id
        self.alert_cooldowns = {}  # Spam-Protection
        self.last_alerts = {}  # Tracking für Alert-Häufigkeit

        # Alert-Konfiguration (from .env)
        self.alert_config = {
            "arbitrage_threshold": config.arbitrage_threshold,
            "sharpe_change_threshold": config.sharpe_change_threshold,
            "cooldown_minutes": config.alert_cooldown_minutes,
            "daily_summary_hour": config.daily_summary_hour,
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def set_chat_id(self, chat_id: str):
        """Setze die Chat ID für Nachrichten"""
        self.chat_id = chat_id
        self.logger.info(f"Chat ID gesetzt: {chat_id}")

    async def get_chat_id_from_updates(self) -> Optional[str]:
        """Hole Chat ID aus aktuellen Updates (für Setup)"""
        try:
            updates = await self.bot.get_updates()
            if updates:
                # Nimm die letzte Chat ID
                return str(updates[-1].message.chat.id)
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Chat ID: {e}")
            return None

    @async_log_performance
    async def send_message(self, message: str, parse_mode: str = ParseMode.MARKDOWN) -> bool:
        """Sende Nachricht an Telegram"""
        if not self.chat_id:
            self.logger.warning("Keine Chat ID gesetzt - Nachricht nicht gesendet")
            return False

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode=parse_mode)
            self.logger.info("Telegram Nachricht erfolgreich gesendet")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Telegram Nachricht: {e}")
            return False

    def _should_send_alert(self, alert_type: str, key: str = "") -> bool:
        """Prüfe ob Alert gesendet werden soll (Spam-Protection)"""
        alert_key = f"{alert_type}_{key}"
        now = datetime.now()

        if alert_key in self.alert_cooldowns:
            last_sent = self.alert_cooldowns[alert_key]
            cooldown_time = timedelta(minutes=self.alert_config["cooldown_minutes"])

            if now - last_sent < cooldown_time:
                return False

        self.alert_cooldowns[alert_key] = now
        return True

    @async_log_performance
    async def send_arbitrage_alert(self, opportunities: List[Dict]) -> bool:
        """Sende Arbitrage Alert"""
        if not opportunities:
            return False

        # Filtere nur große Arbitrage-Möglichkeiten (>2%)
        significant_opportunities = [
            opp
            for opp in opportunities
            if opp.get("profit_percentage", 0) >= self.alert_config["arbitrage_threshold"]
        ]

        if not significant_opportunities:
            return False

        # Spam-Protection: Pro Symbol nur alle 5 Minuten
        symbol = significant_opportunities[0].get("symbol", "UNKNOWN")
        if not self._should_send_alert("arbitrage", symbol):
            return False

        # Erstelle Alert-Nachricht
        best_opp = max(significant_opportunities, key=lambda x: x.get("profit_percentage", 0))

        message = f"""
🚨 *ARBITRAGE ALERT!* 🚨

💎 *{best_opp['symbol']}*
💰 *Profit: {best_opp['profit_percentage']:.1f}%*

📈 Kaufe auf: *{best_opp['buy_exchange']}* (${best_opp['buy_price']:.2f})
📉 Verkaufe auf: *{best_opp['sell_exchange']}* (${best_opp['sell_price']:.2f})

💵 Profit pro Einheit: *${best_opp.get('profit_per_unit', 0):.2f}*

⏰ {datetime.now().strftime('%H:%M:%S')}
"""

        return await self.send_message(message)

    @async_log_performance
    async def send_performance_alert(
        self, top_performers: List[tuple], timeframe: str = "24h"
    ) -> bool:
        """Sende Performance Update"""
        if not top_performers or len(top_performers) < 3:
            return False

        # Spam-Protection für Performance Updates
        if not self._should_send_alert("performance", timeframe):
            return False

        message = f"""
📊 *TOP PERFORMER UPDATE* ({timeframe})

"""

        for i, (symbol, metrics) in enumerate(top_performers[:5], 1):
            sharpe = metrics.get("sharpe_ratio", 0)
            returns = metrics.get("annual_return", 0)

            if sharpe > 1.0:  # Nur gute Performer
                emoji = "🚀" if i == 1 else "📈" if i <= 3 else "⭐"
                message += f"{emoji} *{i}. {symbol}*\n"
                message += f"   Sharpe: *{sharpe:.2f}* | Return: *{returns:.1f}%*\n\n"

        message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"

        return await self.send_message(message)

    @async_log_performance
    async def send_market_summary(self, market_data: Dict) -> bool:
        """Sende täglichen Markt-Summary"""
        total_opportunities = market_data.get("total_arbitrage_opportunities", 0)
        avg_profit = market_data.get("avg_arbitrage_profit", 0)
        top_crypto = market_data.get("best_performer", {})
        analyzed_coins = market_data.get("analyzed_coins", 0)

        message = f"""
🌅 *TÄGLICHER MARKT-REPORT*

📊 *Markt-Übersicht:*
• Analysierte Coins: *{analyzed_coins}*
• Arbitrage-Möglichkeiten: *{total_opportunities}*
• Durchschnittlicher Profit: *{avg_profit:.1f}%*

🏆 *Bester Performer:*
• Symbol: *{top_crypto.get('symbol', 'N/A')}*
• Sharpe Ratio: *{top_crypto.get('sharpe_ratio', 0):.2f}*
• Return: *{top_crypto.get('annual_return', 0):.1f}%*

📈 Bot läuft stabil 24/7
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

        return await self.send_message(message)

    @async_log_performance
    async def send_startup_message(self) -> bool:
        """Sende Bot-Start Nachricht"""
        message = f"""
🤖 *CRYPTO TRADING BOT GESTARTET!*

✅ *Aktive Features:*
• 24/7 Arbitrage Monitoring
• Real-time Preise von 3 Börsen
• Portfolio-Analyse (100+ Coins)
• Smart Alert System

⚙️ *Alert-Einstellungen:*
• Arbitrage Threshold: ≥{self.alert_config['arbitrage_threshold']}%
• Sharpe Change Alert: ≥{self.alert_config['sharpe_change_threshold']}
• Cooldown: {self.alert_config['cooldown_minutes']} Minuten

📊 *Monitoring startet...*
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""

        return await self.send_message(message)

    @async_log_performance
    async def send_error_alert(self, error_msg: str, module: str = "") -> bool:
        """Sende Error Alert"""
        # Nur kritische Errors senden (nicht spammen)
        if not self._should_send_alert("error", module):
            return False

        message = f"""
⚠️ *BOT ERROR ALERT*

🔧 Module: *{module or 'Unknown'}*
❌ Error: `{error_msg[:200]}...` 

🔄 Bot versucht automatisch weiterzulaufen...
⏰ {datetime.now().strftime('%H:%M:%S')}
"""

        return await self.send_message(message)

    async def test_connection(self) -> bool:
        """Teste Bot-Verbindung"""
        try:
            bot_info = await self.bot.get_me()
            self.logger.info(f"Bot verbunden: @{bot_info.username}")

            test_message = f"""
🧪 *TEST NACHRICHT*

✅ Bot ist online und bereit!
🤖 Username: @{bot_info.username}
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Schreibe /start um zu beginnen.
"""

            if self.chat_id:
                await self.send_message(test_message)

            return True

        except Exception as e:
            self.logger.error(f"Bot-Verbindungstest fehlgeschlagen: {e}")
            return False


# Global Bot Instance
crypto_bot = TelegramCryptoBot()


async def setup_telegram_bot() -> bool:
    """Setup und Test des Telegram Bots"""
    print("🤖 TELEGRAM BOT SETUP")
    print("=" * 50)

    # 1. Bot-Verbindung testen
    print("1. Teste Bot-Verbindung...")
    if not await crypto_bot.test_connection():
        print("❌ Bot-Verbindung fehlgeschlagen!")
        return False
    print("✅ Bot-Verbindung erfolgreich!")

    # 2. Chat ID ermitteln
    print("\n2. Ermittle Chat ID...")
    chat_id = await crypto_bot.get_chat_id_from_updates()

    if chat_id:
        crypto_bot.set_chat_id(chat_id)
        print(f"✅ Chat ID gefunden: {chat_id}")
    else:
        print("⚠️ Keine Chat ID gefunden.")
        print("💡 Schreibe eine Nachricht an @crypto_muslix_bot und führe das Setup erneut aus.")
        return False

    # 3. Test-Nachricht senden
    print("\n3. Sende Test-Nachricht...")
    if await crypto_bot.send_startup_message():
        print("✅ Test-Nachricht gesendet!")
    else:
        print("❌ Fehler beim Senden der Test-Nachricht!")
        return False

    print("\n" + "=" * 50)
    print("🎉 TELEGRAM BOT SETUP ERFOLGREICH!")
    print(f"📱 Bot: @crypto_muslix_bot")
    print(f"💬 Chat ID: {chat_id}")
    print("🚀 Bot ist bereit für 24/7 Monitoring!")

    return True


async def send_test_arbitrage_alert():
    """Teste Arbitrage Alert (für Demo)"""
    test_opportunities = [
        {
            "symbol": "BTC/USDT",
            "buy_exchange": "binance",
            "sell_exchange": "coinbase",
            "buy_price": 45000,
            "sell_price": 46000,
            "profit_percentage": 2.2,
            "profit_per_unit": 1000,
        }
    ]

    return await crypto_bot.send_arbitrage_alert(test_opportunities)


# Create bot instance with secure configuration
crypto_bot = TelegramCryptoBot()


if __name__ == "__main__":
    # Setup und Test
    asyncio.run(setup_telegram_bot())
