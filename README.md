# 🚀 VIP InvestBot - Professional 24/7 Investment Monitoring

**Track the world's largest institutional money flows and legendary investors in real-time.**

## 🎯 What It Does

- **Monitors 48 VIP traders & institutions** (BlackRock, Vanguard, Buffett, etc.)
- **Tracks 40+ major stocks** for significant price movements
- **Sends news-style alerts** with individual stock prices
- **24/7 monitoring** with smart market session awareness
- **Stateful system** prevents duplicate alerts

## 📊 Coverage

### Institutional Players (20):
- BlackRock, Vanguard, Fidelity, State Street
- Carlyle Group, Blackstone, KKR, Apollo
- Temasek, GIC, Abu Dhabi Investment Authority
- And more...

### Legendary Investors (6):
- Warren Buffett & Charlie Munger
- Ray Dalio, Seth Klarman, Peter Lynch
- John Templeton

### Hedge Fund Legends (22):
- Michael Burry, Bill Ackman, David Tepper
- Renaissance Technologies, Citadel, Point72
- And more...

## 🚀 Quick Start

### 1. GitHub Actions Setup (Recommended)

1. **Fork this repository**
2. **Add secrets to your GitHub repository:**
   - Go to Settings → Secrets and variables → Actions
   - Add these secrets:
     - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
     - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
     - `FINNHUB_API_KEY`: Your Finnhub API key (free)

3. **Enable GitHub Actions:**
   - Go to Actions tab in your repository
   - Enable workflows if prompted

4. **That's it!** The bot will run automatically:
   - Every 15 minutes during market hours
   - Every hour during pre/after-market
   - Every 2 hours on weekends

### 2. Local Setup (Alternative)

```bash
# Clone the repository
git clone https://github.com/yourusername/InvestBot.git
cd InvestBot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export FINNHUB_API_KEY="your_finnhub_key"

# Run the bot
python investbot.py
```

## 🔧 API Keys Setup

### Telegram Bot (Free)
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create new bot with `/newbot`
3. Get your bot token
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

### Finnhub API (Free)
1. Go to [finnhub.io](https://finnhub.io)
2. Sign up for free account
3. Get your API key from dashboard
4. Free tier: 60 calls/minute (perfect for this bot)

## 📱 Alert Examples

```
📰 BREAKING: Warren Buffett's Q4 Moves Revealed

✅ BOUGHT:
• Chevron Corp: 120,000,000 shares @ $98.45
• Occidental Petroleum: 50,000,000 shares @ $58.20

❌ SOLD:
• Wells Fargo & Co: 100,000,000 shares @ $45.20

💰 Portfolio now worth $350,000,000,000

🎯 TRADING SIGNAL: Energy stocks likely to rally

📊 Full details: [WhaleWisdom](link)
```

## ⚙️ GitHub Actions Schedule

- **Market Hours**: Every 15 minutes (9:30 AM - 3:45 PM ET)
- **Pre/After Market**: Every hour (4 AM - 8 AM, 4 PM - 11 PM ET)
- **Weekends**: Every 2 hours
- **Manual Runs**: Available via GitHub Actions interface

## 🛠️ Customization

### Add More Traders
Edit `investbot.py` and add to the `vip_traders` dictionary:
```python
'New Trader': {
    'cik': '1234567', 
    'strategy': 'Investment strategy', 
    'company': 'Company Name', 
    'whale_link': 'https://whalewisdom.com/filer/...'
}
```

### Adjust Price Thresholds
Modify the `get_alert_threshold()` function to change when price alerts trigger.

### Change Schedule
Edit `.github/workflows/investbot.yml` to modify the cron schedule.

## 📊 Monitoring Stats

- **48 VIP traders & institutions** monitored
- **40+ major stocks** tracked for price movements
- **$50+ trillion** in combined assets under management
- **Global coverage** from US to Singapore to Abu Dhabi

## 🔒 Security

- All API keys stored as GitHub Secrets
- No sensitive data in code
- Stateful system prevents duplicate alerts
- Automatic log cleanup

## 📈 Performance

- **~30 seconds** per monitoring scan
- **No rate limit issues** with free APIs
- **24/7 uptime** via GitHub Actions
- **Professional-grade** institutional intelligence

## 🎯 Bottom Line

Get the same institutional intelligence that hedge funds and professional traders use - delivered directly to your phone via Telegram alerts!

**Track the smart money. Trade with confidence.**
