# VIP InvestBot - Professional 24/7 Investment Monitoring (STATEFUL - NO REPEATS)
# Only sends alerts for REAL events + daily summary if calm
# Updated: January 2025 - Clean version without debug lines
# Cursor Git integration test

import requests
import json
from datetime import datetime, timedelta, date
import pytz
import os
import time
import schedule
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Tuple
import finnhub

# --- STATE MANAGEMENT ---
STATE_FILE = "sent_alerts.log"
sent_alerts_cache = set()

def load_sent_alerts():
    """Load the log of sent alerts from the state file into memory."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                for line in f:
                    sent_alerts_cache.add(line.strip())
        print(f"✅ Loaded {len(sent_alerts_cache)} previously sent alerts from {STATE_FILE}.")
    except Exception as e:
        print(f"⚠️ Could not load state file: {e}")

def save_sent_alerts():
    """Save the in-memory cache of sent alerts back to the state file."""
    try:
        with open(STATE_FILE, 'w') as f:
            for alert_key in sorted(list(sent_alerts_cache)):
                f.write(f"{alert_key}\n")
        print(f"✅ Saved {len(sent_alerts_cache)} alert keys to {STATE_FILE}.")
    except Exception as e:
        print(f"❌ Failed to save state file: {e}")

def has_alert_been_sent(alert_key: str) -> bool:
    """Check if a specific alert has already been sent."""
    return alert_key in sent_alerts_cache

def mark_alert_as_sent(alert_key: str):
    """Add a new alert key to our in-memory cache."""
    sent_alerts_cache.add(alert_key)

class MarketHours:
    """Handle market hours and trading sessions"""
    
    def __init__(self):
        self.eastern = pytz.timezone('US/Eastern')
        
        # Market holidays 2025
        self.market_holidays = [
            datetime(2025, 1, 1),   # New Year's Day
            datetime(2025, 1, 20),  # Martin Luther King Jr. Day
            datetime(2025, 2, 17),  # Presidents' Day
            datetime(2025, 4, 18),  # Good Friday
            datetime(2025, 5, 26),  # Memorial Day
            datetime(2025, 6, 19),  # Juneteenth
            datetime(2025, 7, 4),   # Independence Day
            datetime(2025, 9, 1),   # Labor Day
            datetime(2025, 11, 27), # Thanksgiving
            datetime(2025, 12, 25), # Christmas
        ]
    
    def get_current_time_eastern(self) -> datetime:
        """Get current time in Eastern timezone"""
        return datetime.now(self.eastern)
    
    def is_market_holiday(self, date: datetime = None) -> bool:
        """Check if given date is a market holiday"""
        if date is None:
            date = self.get_current_time_eastern()
        return date.date() in [holiday.date() for holiday in self.market_holidays]
    
    def is_weekend(self, date: datetime = None) -> bool:
        """Check if given date is weekend"""
        if date is None:
            date = self.get_current_time_eastern()
        return date.weekday() >= 5  # Saturday = 5, Sunday = 6
    
    def get_market_session(self, dt: datetime = None) -> str:
        """Determine current market session"""
        if dt is None:
            dt = self.get_current_time_eastern()
        
        if self.is_weekend(dt) or self.is_market_holiday(dt):
            return 'closed'
        
        time_only = dt.time()
        
        if time_only < datetime.strptime('04:00', '%H:%M').time():
            return 'closed'
        elif time_only < datetime.strptime('09:30', '%H:%M').time():
            return 'pre_market'
        elif time_only < datetime.strptime('16:00', '%H:%M').time():
            return 'regular'
        elif time_only < datetime.strptime('20:00', '%H:%M').time():
            return 'after_hours'
        else:
            return 'closed'
    
    def get_session_emoji(self) -> str:
        """Get emoji for current market session"""
        session = self.get_market_session()
        emojis = {
            'closed': '🌙',
            'pre_market': '🌅',
            'regular': '📈',
            'after_hours': '🌆'
        }
        return emojis.get(session, '❓')
    
    def is_end_of_trading_day(self) -> bool:
        """Check if it's time for daily summary"""
        now = self.get_current_time_eastern()
        if self.is_weekend(now) or self.is_market_holiday(now):
            return False
        return now.time() >= datetime.strptime('16:30', '%H:%M').time() and now.time() <= datetime.strptime('17:00', '%H:%M').time()

class VIPInvestBot:
    def __init__(self):
        self.market = MarketHours()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.daily_summary_sent_key = f"summary-{date.today().strftime('%Y-%m-%d')}"

        self.headers = {
            'User-Agent': 'VIPInvestBot Professional',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        
        # VIP Traders Database
        self.vip_traders = {
            'Warren Buffett': {'cik': '1067983', 'strategy': 'Long-term value investing', 'company': 'Berkshire Hathaway', 'whale_link': 'https://whalewisdom.com/filer/berkshire-hathaway-inc'},
            'Charlie Munger': {'cik': '1067983', 'strategy': 'Value investing & mental models', 'company': 'Berkshire Hathaway', 'whale_link': 'https://whalewisdom.com/filer/berkshire-hathaway-inc'},
            'Ray Dalio': {'cik': '1350694', 'strategy': 'All-weather portfolio', 'company': 'Bridgewater Associates', 'whale_link': 'https://whalewisdom.com/filer/bridgewater-associates-lp'},
            'Seth Klarman': {'cik': '1040273', 'strategy': 'Deep value investing', 'company': 'Baupost Group', 'whale_link': 'https://whalewisdom.com/filer/baupost-group-llc'},
            'Peter Lynch': {'cik': '1040273', 'strategy': 'Growth at reasonable price', 'company': 'Fidelity Magellan Fund', 'whale_link': 'https://whalewisdom.com/filer/fidelity-management-research-company'},
            'John Templeton': {'cik': '1040273', 'strategy': 'Global value investing', 'company': 'Templeton Funds', 'whale_link': 'https://whalewisdom.com/filer/templeton-global-advisors-limited'},
            'Michael Burry': {'cik': '1649339', 'strategy': 'Contrarian deep-value bets', 'company': 'Scion Asset Management', 'whale_link': 'https://whalewisdom.com/filer/scion-asset-management-llc'},
            'Bill Ackman': {'cik': '1336528', 'strategy': 'Activist investing', 'company': 'Pershing Square', 'whale_link': 'https://whalewisdom.com/filer/pershing-square-capital-management-l-p'},
            'David Tepper': {'cik': '1040273', 'strategy': 'Macro and distressed investing', 'company': 'Appaloosa Management', 'whale_link': 'https://whalewisdom.com/filer/appaloosa-management-lp'},
            'Renaissance Technologies': {'cik': '1037389', 'strategy': 'Quantitative investing', 'company': 'Renaissance Technologies', 'whale_link': 'https://whalewisdom.com/filer/renaissance-technologies-llc'},
            'Carl Icahn': {'cik': '1336528', 'strategy': 'Activist investing', 'company': 'Icahn Enterprises', 'whale_link': 'https://whalewisdom.com/filer/icahn-enterprises-l-p'},
            'Paul Tudor Jones': {'cik': '1040273', 'strategy': 'Macro trading', 'company': 'Tudor Investment Corp', 'whale_link': 'https://whalewisdom.com/filer/tudor-investment-corporation'},
            'Stanley Druckenmiller': {'cik': '1040273', 'strategy': 'Macro and growth investing', 'company': 'Duquesne Family Office', 'whale_link': 'https://whalewisdom.com/filer/duquesne-family-office-llc'},
            'George Soros': {'cik': '1040273', 'strategy': 'Macro and currency trading', 'company': 'Soros Fund Management', 'whale_link': 'https://whalewisdom.com/filer/soros-fund-management-llc'},
            'Chase Coleman': {'cik': '1040273', 'strategy': 'Growth investing', 'company': 'Tiger Global Management', 'whale_link': 'https://whalewisdom.com/filer/tiger-global-management-llc'},
            'Steve Cohen': {'cik': '1040273', 'strategy': 'Quantitative and fundamental', 'company': 'Point72 Asset Management', 'whale_link': 'https://whalewisdom.com/filer/point72-asset-management-l-p'},
            'Ken Griffin': {'cik': '1040273', 'strategy': 'Quantitative trading', 'company': 'Citadel', 'whale_link': 'https://whalewisdom.com/filer/citadel-advisors-llc'},
            'David Einhorn': {'cik': '1040273', 'strategy': 'Value and activist investing', 'company': 'Greenlight Capital', 'whale_link': 'https://whalewisdom.com/filer/greenlight-capital-inc'},
            'Howard Marks': {'cik': '1040273', 'strategy': 'Distressed and credit investing', 'company': 'Oaktree Capital', 'whale_link': 'https://whalewisdom.com/filer/oaktree-capital-management-l-p'},
            'Leon Cooperman': {'cik': '1040273', 'strategy': 'Value investing', 'company': 'Omega Advisors', 'whale_link': 'https://whalewisdom.com/filer/omega-advisors-inc'},
            'Mohnish Pabrai': {'cik': '1040273', 'strategy': 'Value investing', 'company': 'Pabrai Investment Funds', 'whale_link': 'https://whalewisdom.com/filer/pabrai-investment-funds'},
            'Joel Greenblatt': {'cik': '1040273', 'strategy': 'Value and special situations', 'company': 'Gotham Asset Management', 'whale_link': 'https://whalewisdom.com/filer/gotham-asset-management-llc'},
            'Prem Watsa': {'cik': '1040273', 'strategy': 'Value and insurance investing', 'company': 'Fairfax Financial', 'whale_link': 'https://whalewisdom.com/filer/fairfax-financial-holdings-ltd'},
            'BlackRock': {'cik': '1364742', 'strategy': 'Global asset management', 'company': 'BlackRock Inc', 'whale_link': 'https://whalewisdom.com/filer/blackrock-inc'},
            'Vanguard Group': {'cik': '1040273', 'strategy': 'Index fund investing', 'company': 'Vanguard Group', 'whale_link': 'https://whalewisdom.com/filer/vanguard-group-inc'},
            'Fidelity Investments': {'cik': '1040273', 'strategy': 'Active and passive management', 'company': 'Fidelity Management', 'whale_link': 'https://whalewisdom.com/filer/fidelity-management-research-company'},
            'State Street Global Advisors': {'cik': '1040273', 'strategy': 'ETF and index investing', 'company': 'State Street Corp', 'whale_link': 'https://whalewisdom.com/filer/state-street-corporation'},
            'The Carlyle Group': {'cik': '1040273', 'strategy': 'Private equity', 'company': 'Carlyle Group', 'whale_link': 'https://whalewisdom.com/filer/carlyle-group-inc'},
            'Allianz Global Investors': {'cik': '1040273', 'strategy': 'Global asset management', 'company': 'Allianz Global Investors', 'whale_link': 'https://whalewisdom.com/filer/allianz-global-investors-us-llc'},
            'PIMCO': {'cik': '1040273', 'strategy': 'Fixed income investing', 'company': 'Pacific Investment Management', 'whale_link': 'https://whalewisdom.com/filer/pacific-investment-management-company-llc'},
            'Amundi': {'cik': '1040273', 'strategy': 'European asset management', 'company': 'Amundi Asset Management', 'whale_link': 'https://whalewisdom.com/filer/amundi-asset-management'},
            'Blackstone': {'cik': '1040273', 'strategy': 'Alternative investments', 'company': 'Blackstone Group', 'whale_link': 'https://whalewisdom.com/filer/blackstone-group-inc'},
            'KKR': {'cik': '1040273', 'strategy': 'Private equity and credit', 'company': 'KKR & Co', 'whale_link': 'https://whalewisdom.com/filer/kkr-co-inc'},
            'Apollo Global Management': {'cik': '1040273', 'strategy': 'Alternative investments', 'company': 'Apollo Global Management', 'whale_link': 'https://whalewisdom.com/filer/apollo-global-management-inc'},
            'CVC Capital Partners': {'cik': '1040273', 'strategy': 'Private equity', 'company': 'CVC Capital Partners', 'whale_link': 'https://whalewisdom.com/filer/cvc-capital-partners'},
            'TPG': {'cik': '1040273', 'strategy': 'Private equity and growth', 'company': 'TPG Inc', 'whale_link': 'https://whalewisdom.com/filer/tpg-inc'},
            'Thoma Bravo': {'cik': '1040273', 'strategy': 'Software private equity', 'company': 'Thoma Bravo', 'whale_link': 'https://whalewisdom.com/filer/thoma-bravo-llc'},
            'Warburg Pincus': {'cik': '1040273', 'strategy': 'Growth private equity', 'company': 'Warburg Pincus', 'whale_link': 'https://whalewisdom.com/filer/warburg-pincus-llc'},
            'AlpInvest Partners': {'cik': '1040273', 'strategy': 'Private equity fund of funds', 'company': 'AlpInvest Partners', 'whale_link': 'https://whalewisdom.com/filer/alpinvest-partners'},
            'Temasek Holdings': {'cik': '1040273', 'strategy': 'Sovereign wealth fund', 'company': 'Temasek Holdings', 'whale_link': 'https://whalewisdom.com/filer/temasek-holdings-private-limited'},
            'GIC': {'cik': '1040273', 'strategy': 'Sovereign wealth fund', 'company': 'Government of Singapore Investment Corp', 'whale_link': 'https://whalewisdom.com/filer/government-of-singapore-investment-corporation'},
            'CPP Investments': {'cik': '1040273', 'strategy': 'Pension fund investing', 'company': 'Canada Pension Plan Investment Board', 'whale_link': 'https://whalewisdom.com/filer/canada-pension-plan-investment-board'},
            'Mubadala Investment Company': {'cik': '1040273', 'strategy': 'Sovereign wealth fund', 'company': 'Mubadala Investment Company', 'whale_link': 'https://whalewisdom.com/filer/mubadala-investment-company'},
            'Abu Dhabi Investment Authority': {'cik': '1040273', 'strategy': 'Sovereign wealth fund', 'company': 'Abu Dhabi Investment Authority', 'whale_link': 'https://whalewisdom.com/filer/abu-dhabi-investment-authority'}
        }
        
        session = self.market.get_market_session()
        session_emoji = self.market.get_session_emoji()
        
        print(f"🤖 VIP InvestBot starting - {datetime.now()}")
        print(f"{session_emoji} Market Status: {session.upper()}")
        print(f"📊 24/7 PRICE MONITORING: ACTIVE (STATEFUL - NO REPEATS)")
        print(f"👥 Monitoring {len(self.vip_traders)} VIP traders & institutions")
        print(f"🏛️ Institutional Players: BlackRock, Vanguard, Fidelity, State Street, etc.")
        print(f"👑 Legendary Investors: Buffett, Munger, Dalio, Lynch, Templeton, etc.")
        print(f"📈 Price movements: ENABLED (40+ major stocks)")
        print(f"📅 Earnings calendar: DISABLED (reduced notifications)")
    
    def send_telegram_alert(self, message, urgency="HIGH"):
        if not self.bot_token or not self.chat_id:
            print("❌ Missing Telegram credentials")
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            urgency_icons = {"CRITICAL": "🚨🚨🚨", "HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "📊"}
            session_emoji = self.market.get_session_emoji()
            session = self.market.get_market_session()
            icon = urgency_icons.get(urgency, "📊")
            formatted_message = f"{icon} *VIP InvestBot Alert* {session_emoji}\n"
            formatted_message += f"_{session.replace('_', ' ').title()} Session_\n\n{message}"
            data = {'chat_id': self.chat_id, 'text': formatted_message, 'parse_mode': 'Markdown', 'disable_web_page_preview': False}
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ {urgency} alert sent to Telegram successfully!")
                return True
            else:
                print(f"❌ Telegram API error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
            return False

    def get_company_name(self, ticker):
        company_names = {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corporation', 'GOOGL': 'Alphabet Inc.', 'GOOG': 'Alphabet Inc.', 'AMZN': 'Amazon.com Inc.', 'TSLA': 'Tesla Inc.', 'NVDA': 'NVIDIA Corporation', 'META': 'Meta Platforms Inc.', 'BRK-B': 'Berkshire Hathaway', 'JPM': 'JPMorgan Chase & Co.', 'JNJ': 'Johnson & Johnson', 'PG': 'Procter & Gamble', 'HD': 'The Home Depot', 'BAC': 'Bank of America', 'UNH': 'UnitedHealth Group', 'V': 'Visa Inc.', 'MA': 'Mastercard Inc.', 'WMT': 'Walmart Inc.', 'DIS': 'The Walt Disney Company', 'NFLX': 'Netflix Inc.', 'CRM': 'Salesforce Inc.', 'ADBE': 'Adobe Inc.', 'ORCL': 'Oracle Corporation', 'CSCO': 'Cisco Systems', 'INTC': 'Intel Corporation', 'AMD': 'Advanced Micro Devices', 'QCOM': 'QUALCOMM Inc.', 'TXN': 'Texas Instruments', 'AVGO': 'Broadcom Inc.', 'HON': 'Honeywell International', 'CAT': 'Caterpillar Inc.', 'BA': 'The Boeing Company', 'GE': 'General Electric', 'MMM': '3M Company', 'KO': 'The Coca-Cola Company', 'PEP': 'PepsiCo Inc.', 'MCD': 'McDonald\'s Corporation', 'NKE': 'NIKE Inc.', 'SBUX': 'Starbucks Corporation'
        }
        return company_names.get(ticker, f"{ticker} Inc.")
    
    def get_stock_price(self, ticker):
        """Get current stock price using Finnhub API"""
        try:
            FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
            if not FINNHUB_API_KEY:
                return None
                
            finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            quote = finnhub_client.quote(ticker)
            
            if quote and 'c' in quote:
                return quote['c']
            return None
        except Exception as e:
            print(f"❌ Error getting price for {ticker}: {e}")
            return None
    
    def get_ticker_from_company_name(self, company_name):
        """Convert company name to ticker symbol"""
        ticker_mapping = {
            'Apple Inc.': 'AAPL', 'Microsoft Corporation': 'MSFT', 'Alphabet Inc.': 'GOOGL',
            'Amazon.com Inc.': 'AMZN', 'Tesla Inc.': 'TSLA', 'NVIDIA Corporation': 'NVDA',
            'Meta Platforms Inc.': 'META', 'Berkshire Hathaway': 'BRK-B', 'JPMorgan Chase & Co.': 'JPM',
            'Johnson & Johnson': 'JNJ', 'Procter & Gamble': 'PG', 'The Home Depot': 'HD',
            'Bank of America': 'BAC', 'UnitedHealth Group': 'UNH', 'Visa Inc.': 'V',
            'Mastercard Inc.': 'MA', 'Walmart Inc.': 'WMT', 'The Walt Disney Company': 'DIS',
            'Netflix Inc.': 'NFLX', 'Salesforce Inc.': 'CRM', 'Adobe Inc.': 'ADBE',
            'Oracle Corporation': 'ORCL', 'Cisco Systems': 'CSCO', 'Intel Corporation': 'INTC',
            'Advanced Micro Devices': 'AMD', 'QUALCOMM Inc.': 'QCOM', 'Texas Instruments': 'TXN',
            'Broadcom Inc.': 'AVGO', 'Honeywell International': 'HON', 'Caterpillar Inc.': 'CAT',
            'The Boeing Company': 'BA', 'General Electric': 'GE', '3M Company': 'MMM',
            'The Coca-Cola Company': 'KO', 'PepsiCo Inc.': 'PEP', 'McDonald\'s Corporation': 'MCD',
            'NIKE Inc.': 'NKE', 'Starbucks Corporation': 'SBUX', 'Chevron Corp': 'CVX',
            'Occidental Petroleum': 'OXY', 'Activision Blizzard': 'ATVI', 'Wells Fargo & Co': 'WFC',
            'Verizon Communications': 'VZ', 'Exxon Mobil': 'XOM', 'ConocoPhillips': 'COP'
        }
        return ticker_mapping.get(company_name, None)
    
    def get_alert_threshold(self, ticker):
        large_cap_stable = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'BRK-B', 'JPM', 'V', 'MA', 'UNH', 'JNJ', 'PG', 'HD', 'PFE', 'KO', 'PEP', 'WMT', 'MCD']
        high_volatility = ['TSLA', 'NVDA', 'AMD', 'ROKU', 'ZM', 'PTON', 'SNAP', 'UBER', 'COIN', 'HOOD', 'RIVN', 'LCID', 'NIO', 'XPEV', 'PLTR']
        base_threshold = 3.5 if ticker in large_cap_stable else 6.0 if ticker in high_volatility else 4.5
        session = self.market.get_market_session()
        if session == 'closed': return base_threshold * 2.0
        elif session == 'pre_market': return base_threshold * 1.3
        elif session == 'after_hours': return base_threshold * 1.1
        else: return base_threshold
    
    def check_vip_filings(self):
        print("🔍 Checking VIP trader SEC filings...")
        new_filings = []
        for trader_name, info in self.vip_traders.items():
            try:
                filings_url = f"https://data.sec.gov/submissions/CIK{info['cik'].zfill(10)}.json"
                response = requests.get(filings_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    recent_filings = data.get('filings', {}).get('recent', {})
                    cutoff_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                    for i, form in enumerate(recent_filings.get('form', [])):
                        filing_date = recent_filings.get('filingDate', [])[i]
                        if form in ['13F-HR', '13F-NT', '4', 'SC 13G', 'SC 13D', '8-K'] and filing_date >= cutoff_date:
                            alert_key = f"file-{info['cik']}-{recent_filings.get('accessionNumber', [])[i]}"
                            if not has_alert_been_sent(alert_key):
                                filing_info = {
                                    'trader': trader_name, 
                                    'company': info['company'], 
                                    'form': form, 
                                    'date': filing_date, 
                                    'strategy': info['strategy'], 
                                    'whale_link': info['whale_link'], 
                                    'accession_number': recent_filings.get('accessionNumber', [])[i], 
                                    'cik': info['cik'], 
                                    'alert_key': alert_key
                                }
                                new_filings.append(filing_info)
                                print(f"🆕 NEW FILING: {trader_name} filed {form} on {filing_date}. Queued.")
                time.sleep(0.4)
            except Exception as e:
                print(f"❌ Error checking {trader_name}: {e}")
        return new_filings

    def check_major_price_moves(self):
        """Check for significant price movements using Finnhub API"""
        print("📈 Checking price movements 24/7...")
        FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
        if not FINNHUB_API_KEY:
            print("❌❌ ERROR: FINNHUB_API_KEY not found.")
            return []

        major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'V', 'MA', 'UNH', 'JNJ', 'PG', 'HD', 'BAC', 'WMT', 'DIS', 'NFLX', 'CRM', 'ADBE', 'ORCL', 'CSCO', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO', 'HON', 'CAT', 'BA', 'GE', 'MMM', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX']
        
        new_price_moves = []
        
        try:
            finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            
            for ticker in major_tickers:
                try:
                    quote = finnhub_client.quote(ticker)
                    if quote and 'c' in quote and 'pc' in quote:
                        current_price = quote['c']
                        previous_close = quote['pc']
                        
                        if current_price and previous_close and previous_close > 0:
                            price_change_pct = ((current_price - previous_close) / previous_close) * 100
                            threshold = self.get_alert_threshold(ticker)
                            
                            if abs(price_change_pct) >= threshold:
                                alert_key = f"price-{ticker}-{datetime.now().strftime('%Y-%m-%d-%H')}"
                                
                                if not has_alert_been_sent(alert_key):
                                    move_info = {
                                        'ticker': ticker,
                                        'company_name': self.get_company_name(ticker),
                                        'current_price': current_price,
                                        'previous_close': previous_close,
                                        'change_pct': price_change_pct,
                                        'change_amount': current_price - previous_close,
                                        'alert_key': alert_key,
                                        'threshold': threshold
                                    }
                                    new_price_moves.append(move_info)
                                    print(f"🆕 NEW PRICE MOVE: {ticker} {price_change_pct:+.2f}% (threshold: {threshold}%). Queued.")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Error checking {ticker}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌❌ ERROR in check_major_price_moves: {e}")
            return []
            
        return new_price_moves
    
    def format_vip_filing_alert(self, filings):
        """Format VIP filing alerts in news-style"""
        if len(filings) > 1:
            header = f"📰 *BREAKING: {len(filings)} VIP TRADERS MAKE MAJOR MOVES*"
        else:
            filing = filings[0]
            header = f"📰 *BREAKING: {filing['trader']}'s Q4 Moves Revealed*"
        
        message = f"{header}\n\n"
        
        for filing in filings:
            message += f"👤 *{filing['trader']}*\n🏢 {filing['company']}\n📄 {filing['form']} filed on {filing['date']}\n🎯 Strategy: _{filing['strategy']}_\n\n"
            message += f"🔗 *Analysis:*\n🐋 [WhaleWisdom]({filing['whale_link']})\n📊 [QuiverQuant](https://www.quiverquant.com/sources/institutions)\n\n"
            message += "─────────────────\n\n"
        
        return message

    def format_price_movement_alert(self, moves):
        """Format price movement alerts"""
        if not moves:
            return None
            
        header = f"📈 *{len(moves)} MAJOR PRICE MOVEMENTS DETECTED!*" if len(moves) > 1 else f"📈 *MAJOR PRICE MOVEMENT DETECTED!*"
        message = f"{header}\n\n"
        
        moves.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        
        for move in moves:
            direction = "🚀" if move['change_pct'] > 0 else "📉"
            urgency = "🚨🚨🚨" if abs(move['change_pct']) >= 10 else "🚨" if abs(move['change_pct']) >= 5 else "⚠️"
            
            message += f"{urgency} {direction} *{move['ticker']}* - {move['company_name']}\n"
            message += f"💰 Price: ${move['current_price']:.2f} (was ${move['previous_close']:.2f})\n"
            message += f"📊 Change: {move['change_pct']:+.2f}% (${move['change_amount']:+.2f})\n"
            message += f"🎯 Threshold: {move['threshold']:.1f}%\n\n"
        
        return message

    def send_daily_summary(self):
        if has_alert_been_sent(self.daily_summary_sent_key):
            return False
        if not self.market.is_end_of_trading_day():
            return False
        eastern_time = self.market.get_current_time_eastern()
        date_str = eastern_time.strftime('%B %d, %Y')
        summary_message = f"🌙 *End of Day Summary - {date_str}*\n\n✅ *Markets Calm Today*\n\n🔍 *Daily Scan Results:*\n• VIP trader filings: None\n• Major price movements: None detected\n\n📊 *Monitoring Stats:*\n• VIP traders & institutions monitored: {len(self.vip_traders)}\n• Major stocks tracked: 40+ S&P 500 leaders\n\n💤 *Rest easy - your VIP InvestBot is watching 24/7*"
        success = self.send_telegram_alert(summary_message, "LOW")
        if success:
            mark_alert_as_sent(self.daily_summary_sent_key)
            print("📊 Daily summary sent and logged.")
        return success
    
    def run_vip_monitoring(self):
        session = self.market.get_market_session()
        print(f"🎯 Running STATEFUL monitoring scan - {datetime.now()}")
        print(f"({session.upper()})")
        alerts_sent_this_run = 0
        
        # Check 1: VIP Trader Filings
        new_filings = self.check_vip_filings()
        if new_filings:
            alert_message = self.format_vip_filing_alert(new_filings)
            if self.send_telegram_alert(alert_message, "CRITICAL"):
                for filing in new_filings: mark_alert_as_sent(filing['alert_key'])
                alerts_sent_this_run += 1
        
        # Check 2: Price Movements
        big_moves = self.check_major_price_moves()
        if big_moves:
            alert_message = self.format_price_movement_alert(big_moves)
            if alert_message:
                max_move = max([abs(move['change_pct']) for move in big_moves])
                urgency = "CRITICAL" if max_move >= 10 else "HIGH" if max_move >= 5 else "MEDIUM"
                if self.send_telegram_alert(alert_message, urgency):
                    for move in big_moves: mark_alert_as_sent(move['alert_key'])
                    alerts_sent_this_run += 1
        
        # Check 3: Send daily summary if no alerts were sent
        if alerts_sent_this_run == 0:
            self.send_daily_summary()
            
        return alerts_sent_this_run

# --- Main execution ---
if __name__ == "__main__":
    print("🚀 Starting VIP InvestBot - STATEFUL VERSION...")
    load_sent_alerts()
    bot = VIPInvestBot()
    alerts_sent = bot.run_vip_monitoring()
    save_sent_alerts()
    if alerts_sent > 0:
        print(f"🚨 SUCCESS: Sent {alerts_sent} new, unique alerts!")
    else:
        print("✅ SUCCESS: Monitoring complete, no new alerts to send.")
    print("🎯 VIP InvestBot execution complete!")
