#!/usr/bin/env python3
"""
Crypto Trading Bot 24/7 - Persistent Launcher
Startet das System persistent mit automatischer Chat ID Detection
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import project modules
try:
    from config.config import get_config
    from crypto_monitor_24_7 import CryptoMonitor24_7
    from src.modules.telegram_bot import crypto_bot
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class PersistentBotLauncher:
    """Persistent Bot Launcher mit Chat ID Setup"""

    def __init__(self):
        self.config = get_config()
        self.monitor = None
        self.running = False
        self.shutdown_requested = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutdown signal received ({signum})")
        self.shutdown_requested = True
        self.running = False

    async def setup_telegram_chat_id(self) -> bool:
        """Setup Telegram Chat ID wenn nicht vorhanden"""
        if self.config.telegram_chat_id:
            print("✅ Telegram Chat ID already configured")
            crypto_bot.set_chat_id(self.config.telegram_chat_id)
            return True

        print("🤖 TELEGRAM SETUP REQUIRED")
        print("=" * 40)
        print("📱 To receive alerts, you need to set up your Telegram Chat ID:")
        print("   1. Open Telegram and message @crypto_muslix_bot")
        print("   2. Send any message (e.g., /start)")
        print("   3. The bot will detect your Chat ID automatically")
        print("")

        # Versuche Chat ID automatisch zu erkennen
        print("🔍 Looking for your Chat ID...")

        for attempt in range(6):  # 30 seconds total
            try:
                chat_id = await crypto_bot.get_chat_id_from_updates()
                if chat_id:
                    print("✅ Found Chat ID: {chat_id}")

                    # Update .env file
                    self._update_env_file("TELEGRAM_CHAT_ID", chat_id)

                    # Set in bot
                    crypto_bot.set_chat_id(chat_id)

                    # Send welcome message
                    welcome_message = """
🎉 *SETUP COMPLETE!*

✅ Chat ID configured: `{chat_id}`
🤖 Bot is now ready for 24/7 monitoring!

📊 *Starting monitoring...*
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
                    await crypto_bot.send_message(welcome_message)
                    return True

            except Exception as e:
                print("⚠️ Error checking for Chat ID: {e}")

            print("⏳ Waiting... ({attempt + 1}/6)")
            await asyncio.sleep(5)

        print("❌ No Chat ID found. Please message @crypto_muslix_bot first.")
        print("💡 You can also manually add TELEGRAM_CHAT_ID to your .env file")

        # Ask user if they want to continue without Telegram
        try:
            response = input("\nContinue without Telegram alerts? (y/N): ").strip().lower()
            return response in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            return False

    def _update_env_file(self, key: str, value: str):
        """Update .env file with new value"""
        env_file = Path(__file__).parent / ".env"

        if not env_file.exists():
            print("⚠️ .env file not found")
            return

        try:
            # Read current content
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Update or add the key
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("{key}="):
                    lines[i] = "{key}={value}\n"
                    updated = True
                    break

            if not updated:
                lines.append("{key}={value}\n")

            # Write back
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(lines)

            print("✅ Updated .env file: {key}={value}")

        except Exception as e:
            print("❌ Error updating .env file: {e}")

    async def start_monitoring(self):
        """Starte das 24/7 Monitoring"""
        self.monitor = CryptoMonitor24_7()
        self.running = True

        print("🚀 STARTING 24/7 CRYPTO MONITORING")
        print("=" * 50)

        # Print configuration
        self.config.print_config_summary()

        print("\n📊 Monitor Configuration:")
        print("   • Arbitrage checks: every {self.config.arbitrage_check_interval}s")
        print("   • Performance analysis: every {self.config.performance_check_interval//60}min")
        print("   • Watchlist: {self.config.watchlist_symbols}")
        print("   • Exchanges: {self.config.exchanges}")

        print("\n🔄 Starting monitoring loop...")
        print("📱 Press Ctrl+C to stop gracefully")
        print("=" * 50)

        try:
            # Start the monitoring with configured chat ID
            await self.monitor.start_monitoring(self.config.telegram_chat_id)

        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
        except Exception as e:
            print("\n❌ Monitoring error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.running = False

    async def run(self):
        """Haupt-Einstiegspunkt"""
        print("🤖 CRYPTO TRADING BOT 24/7 - PERSISTENT LAUNCHER")
        print("=" * 60)
        print("⏰ Start time: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

        # 1. Setup Telegram
        if not await self.setup_telegram_chat_id():
            print("❌ Setup cancelled")
            return False

        # 2. Start monitoring
        await self.start_monitoring()

        print("\n⏰ Session ended: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        return True


def main():
    """Haupt-Einstiegspunkt"""
    try:
        launcher = PersistentBotLauncher()
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print("\n👋 Bot launcher stopped")
    except Exception as e:
        print("\n💥 Launcher error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
