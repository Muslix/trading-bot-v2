#!/usr/bin/env python3
"""
Telegram Bot Test Script
"""
import sys
import os

# Add paths
sys.path.append(".")
sys.path.append("src/")
sys.path.append("modules/")

try:
    from src.modules.telegram_bot import TelegramCryptoBot
    import asyncio

    async def test_telegram():
        # Initialize bot
        bot = TelegramCryptoBot()

        message = """🚀 CRYPTO TRADING BOT v2.0 - TEST MESSAGE

✅ Bot erfolgreich gestartet!
📊 Alle Systeme online
🔗 Dashboard: http://localhost:5000
🤖 24/7 Monitoring aktiv
💰 Arbitrage Detection läuft

Dein Trading Bot ist bereit! 🎉"""

        # Test connection first
        if await bot.test_connection():
            print("✅ Telegram Bot Verbindung erfolgreich!")
            result = await bot.send_message(message)
            print(f"📱 Nachricht gesendet: {result}")
        else:
            print("❌ Telegram Bot Verbindung fehlgeschlagen")

    # Run async function
    asyncio.run(test_telegram())

except Exception as e:
    print(f"❌ Telegram Fehler: {e}")
    import traceback

    traceback.print_exc()
