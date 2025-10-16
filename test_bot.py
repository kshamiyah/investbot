#!/usr/bin/env python3
"""
VIP InvestBot Test Script
Run this to test your bot locally and see what messages you'd receive
"""

import os
import sys
from investbot import VIPInvestBot, load_sent_alerts, save_sent_alerts

def test_bot():
    print("🧪 Testing VIP InvestBot...")
    print("=" * 50)
    
    # Check if environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'FINNHUB_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Set them with:")
        for var in missing_vars:
            print(f"   export {var}='your_value_here'")
        return False
    
    print("✅ All environment variables found!")
    print("\n🚀 Starting InvestBot test...")
    
    try:
        # Load previous alerts
        load_sent_alerts()
        
        # Create bot instance
        bot = VIPInvestBot()
        
        # Run monitoring
        alerts_sent = bot.run_vip_monitoring()
        
        # Save alerts
        save_sent_alerts()
        
        if alerts_sent > 0:
            print(f"\n🚨 SUCCESS: Sent {alerts_sent} new alerts!")
            print("📱 Check your Telegram for the messages!")
        else:
            print("\n✅ SUCCESS: No new alerts to send.")
            print("💡 This means either:")
            print("   - No new VIP filings detected")
            print("   - No significant price movements")
            print("   - Markets are calm (which is normal)")
        
        print("\n🎯 Test complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_bot()
    sys.exit(0 if success else 1)
