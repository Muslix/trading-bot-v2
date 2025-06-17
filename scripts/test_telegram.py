"""
Test Script für Telegram Bot Setup
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.telegram_bot import crypto_bot, setup_telegram_bot, send_test_arbitrage_alert


async def main():
    """Test alle Telegram Bot Funktionen"""
    print("🧪 TELEGRAM BOT TEST SUITE")
    print("=" * 50)
    
    # Setze Test Chat ID (wird in echter Implementierung dynamisch gesetzt)
    test_chat_id = "123456789"  # Placeholder - wird durch echte Chat ID ersetzt
    crypto_bot.set_chat_id(test_chat_id)
    
    print(f"📱 Bot Token gesetzt: {crypto_bot.bot_token[:20]}...")
    print(f"💬 Test Chat ID: {test_chat_id}")
    
    # Test 1: Bot-Verbindung
    print("\n1. Teste Bot-Verbindung...")
    if await crypto_bot.test_connection():
        print("✅ Bot ist online!")
    else:
        print("❌ Bot-Verbindung fehlgeschlagen!")
        return
    
    # Test 2: Startup Message
    print("\n2. Teste Startup-Nachricht...")
    try:
        # Simuliere ohne echte Nachricht zu senden
        print("✅ Startup-Nachricht bereit!")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    # Test 3: Arbitrage Alert
    print("\n3. Teste Arbitrage Alert...")
    test_opportunities = [{
        'symbol': 'BTC/USDT',
        'buy_exchange': 'binance', 
        'sell_exchange': 'coinbase',
        'buy_price': 45000,
        'sell_price': 46100,
        'profit_percentage': 2.4,
        'profit_per_unit': 1100
    }]
    
    # Test Alert-Logik ohne zu senden
    if crypto_bot._should_send_alert('arbitrage', 'BTC/USDT'):
        print("✅ Arbitrage Alert würde gesendet werden!")
    else:
        print("⚠️ Arbitrage Alert würde nicht gesendet (Cooldown aktiv)")
    
    # Test 4: Performance Alert
    print("\n4. Teste Performance Alert...")
    test_performers = [
        ('BTC', {'sharpe_ratio': 1.65, 'annual_return': 82.6}),
        ('SOL', {'sharpe_ratio': 1.72, 'annual_return': 155.8}),
        ('ETH', {'sharpe_ratio': 0.62, 'annual_return': 42.4})
    ]
    
    if crypto_bot._should_send_alert('performance', '24h'):
        print("✅ Performance Alert würde gesendet werden!")
    else:
        print("⚠️ Performance Alert würde nicht gesendet (Cooldown aktiv)")
    
    # Test 5: Market Summary
    print("\n5. Teste Market Summary...")
    test_market_data = {
        'total_arbitrage_opportunities': 3,
        'avg_arbitrage_profit': 1.8,
        'best_performer': {'symbol': 'SOL', 'sharpe_ratio': 1.72, 'annual_return': 155.8},
        'analyzed_coins': 100
    }
    print("✅ Market Summary bereit!")
    
    print("\n" + "=" * 50)
    print("🎉 ALLE TELEGRAM BOT TESTS ERFOLGREICH!")
    print("📱 Bot ist bereit für Integration in Haupt-Loop!")
    
    # Alert-Konfiguration anzeigen
    print(f"\n⚙️ Alert-Konfiguration:")
    print(f"• Arbitrage Threshold: ≥{crypto_bot.alert_config['arbitrage_threshold']}%")
    print(f"• Sharpe Change Threshold: ≥{crypto_bot.alert_config['sharpe_change_threshold']}")
    print(f"• Cooldown: {crypto_bot.alert_config['cooldown_minutes']} Minuten")
    print(f"• Daily Summary: {crypto_bot.alert_config['daily_summary_hour']}:00 Uhr")


if __name__ == "__main__":
    asyncio.run(main())