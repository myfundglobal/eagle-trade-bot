import telebot
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import time
from datetime import datetime, timedelta
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render Free Web Service ko active rakhne ke liye dummy HTTP server
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Eagle Trading Zone Bot is Running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Server ko background me start karna
t = threading.Thread(target=run_server)
t.daemon = True
t.start()

# Aapka Telegram Token aur Chat ID
TELEGRAM_TOKEN = '8807084061:AAF6BQTkW-AQ3XGpQI4eMDLmPbIhYT8_r2o'
CHAT_ID = '1375185299'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

pairs = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X',
    'EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'EURCAD=X', 'AUDCAD=X', 'CADJPY=X', 'CHFJPY=X'
]

last_signal_time = {}
COOLDOWN_MINUTES = 3 

def get_signal(pair):
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 50:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['SMA_5'] = ta.sma(df['Close'], length=5)
        df['SMA_8'] = ta.sma(df['Close'], length=8)
        df['SMA_13'] = ta.sma(df['Close'], length=13)
        
        psar = ta.psar(df['High'], df['Low'], df['Close'], step=0.03, max_step=0.3)
        
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=7)
        df['ADX_7'] = adx['ADX_7']
        df['DMP_7'] = adx['DMP_7'] 
        df['DMN_7'] = adx['DMN_7'] 

        sma_5 = df['SMA_5'].iloc[-1]
        sma_8 = df['SMA_8'].iloc[-1]
        sma_13 = df['SMA_13'].iloc[-1]
        psar_val = psar.iloc[-1, 0]
        curr_close = df['Close'].iloc[-1]
        dmp = df['DMP_7'].iloc[-1]
        dmn = df['DMN_7'].iloc[-1]
        adx_val = df['ADX_7'].iloc[-1]

        direction = None
        logic_text = ""
        
        if sma_5 > sma_8 > sma_13 and psar_val < curr_close and dmp > dmn and adx_val > 20:
            direction = "🟢 CALL (UP)"
            logic_text = "SMA Uptrend + Parabolic SAR Support + ADX Upward Trend"
            
        elif sma_5 < sma_8 < sma_13 and psar_val > curr_close and dmn > dmp and adx_val > 20:
            direction = "🔴 PUT (DOWN)"
            logic_text = "SMA Downtrend + Parabolic SAR Resistance + ADX Downward Trend"

        if direction:
            now = datetime.now()
            if pair in last_signal_time:
                time_since_last = now - last_signal_time[pair]
                if time_since_last < timedelta(minutes=COOLDOWN_MINUTES):
                    return None 
                    
            last_signal_time[pair] = now
            entry_time = now.strftime("%I:%M %p")
            exit_time = (now + timedelta(minutes=1)).strftime("%I:%M %p")
            
            message = (
                f"🦅 **EAGLE TRADING ZONE - 1 MIN SIGNAL** 🦅\n\n"
                f"📌 **Pair:** {pair.replace('=X', '')}\n"
                f"🕒 **Entry Time:** {entry_time}\n"
                f"⏳ **Exit Time:** {exit_time} (1 Min Trade)\n"
                f"📈 **Direction:** {direction}\n\n"
                f"⚡ **Logic:** {logic_text}\n"
                f"⚠️ *Wait for perfect entry. Use 1-Step MTG if required.*"
            )
            return message
    except Exception:
        return None
    return None

print("Eagle Trading Zone Free Web Service Bot Started!")

while True:
    for pair in pairs:
        signal_msg = get_signal(pair)
        if signal_msg:
            try:
                bot.send_message(CHAT_ID, signal_msg, parse_mode='Markdown')
                time.sleep(2) 
            except Exception:
                pass
    time.sleep(60)
