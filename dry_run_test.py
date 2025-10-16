#!/usr/bin/env python3
"""
VIP InvestBot Dry Run Test
Shows you what messages would be sent without actually sending them
"""

import os
import sys
from investbot import VIPInvestBot, load_sent_alerts

def dry_run_test():
    print("🔍 VIP InvestBot Dry Run Test")
    print("=" * 50)
    print("This will show you what messages would be sent without actually sending them.")
    print()
    
    try:
        # Load previous alerts
        load_sent_alerts()
        
        # Create bot instance
        bot = VIPInvestBot()
        
        print("📊 Checking VIP trader filings...")
        new_filings = bot.check_vip_filings()
        
        print("📈 Checking price movements...")
        big_moves = bot.check_major_price_moves()
        
        print("\n" + "=" * 50)
        print("📋 DRY RUN RESULTS:")
        print("=" * 50)
        
        if new_filings:
            print(f"\n🚨 VIP FILINGS DETECTED: {len(new_filings)}")
            for filing in new_filings:
                print(f"   • {filing['trader']} - {filing['form']} on {filing['date']}")
            
            # Show what the message would look like
            alert_message = bot.format_vip_filing_alert(new_filings)
            print(f"\n📱 TELEGRAM MESSAGE THAT WOULD BE SENT:")
            print("-" * 50)
            print(alert_message)
            print("-" * 50)
        else:
            print("\n✅ No new VIP filings detected")
        
        if big_moves:
            print(f"\n📈 PRICE MOVEMENTS DETECTED: {len(big_moves)}")
            for move in big_moves:
                print(f"   • {move['ticker']} - {move['change_pct']:+.2f}% (${move['current_price']:.2f})")
            
            # Show what the message would look like
            alert_message = bot.format_price_movement_alert(big_moves)
            print(f"\n📱 TELEGRAM MESSAGE THAT WOULD BE SENT:")
            print("-" * 50)
            print(alert_message)
            print("-" * 50)
        else:
            print("\n✅ No significant price movements detected")
        
        if not new_filings and not big_moves:
            print("\n💤 Markets are calm - no alerts would be sent")
            print("📊 This is normal during quiet market periods")
        
        print(f"\n🎯 Total alerts that would be sent: {len(new_filings) + len(big_moves)}")
        
    except Exception as e:
        print(f"\n❌ Error during dry run: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = dry_run_test()
    sys.exit(0 if success else 1)
