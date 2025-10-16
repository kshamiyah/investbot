#!/usr/bin/env python3
"""
VIP InvestBot Setup Script
Helps you configure the bot for GitHub Actions
"""

import os
import sys

def main():
    print("🚀 VIP InvestBot Setup")
    print("=" * 50)
    
    print("\n📋 Required Environment Variables:")
    print("1. TELEGRAM_BOT_TOKEN - Your Telegram bot token")
    print("2. TELEGRAM_CHAT_ID - Your Telegram chat ID") 
    print("3. FINNHUB_API_KEY - Your Finnhub API key")
    
    print("\n🔧 GitHub Actions Setup:")
    print("1. Go to your GitHub repository")
    print("2. Click Settings → Secrets and variables → Actions")
    print("3. Add the three secrets above")
    print("4. Go to Actions tab and enable workflows")
    
    print("\n📱 Telegram Bot Setup:")
    print("1. Message @BotFather on Telegram")
    print("2. Create new bot with /newbot")
    print("3. Get your chat ID from @userinfobot")
    
    print("\n🔑 Finnhub API Setup:")
    print("1. Go to https://finnhub.io")
    print("2. Sign up for free account")
    print("3. Get API key from dashboard")
    
    print("\n✅ Once configured, the bot will run automatically!")
    print("📊 Monitoring 48 VIP traders & 40+ major stocks")
    print("🎯 24/7 institutional intelligence delivered to your phone")

if __name__ == "__main__":
    main()
