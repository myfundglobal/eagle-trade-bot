import telebot
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import time
from datetime import datetime, timedelta

# Aapka Telegram Token aur Chat ID
TELEGRAM_TOKEN = '8807084061:AAF6BQTkW-AQ3XGpQI4eMDLmPbIhYT8_r2o'
CHAT_ID = '1375185299'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 15 Major Forex Pairs
pairs = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X',
    'EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'EURCAD=X', 'AUDCAD=X', 'CADJPY=X', 'CHFJPY=X'
]

# SPAM BLOCKER: Ek signal aane ke baad us pair par agle 3 minute tak koi signal nahi aayega
last_signal_time = {}
COOLDOWN_MINUTES = 3 

def get_signal(pair):
    try:
        # 1-minute data for YouTube Strategy
        df = yf.download(pair, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 50:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # YouTube Strategy Indicators (SMAs, PSAR, ADX)
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
        
        # LOGIC
        if sma_5 > sma_8 > sma_13 and psar_val < curr_close and dmp > dmn and adx_val > 20:
            direction = "🟢 CALL (UP)"
            logic_text = "SMA Uptrend + Parabolic SAR Support + ADX Upward Trend"
            
        elif sma_5 < sma_8 < sma_13 and psar_val > curr_close and dmn > dmp and adx_val > 20:
            direction = "🔴 PUT (DOWN)"
            logic_text = "SMA Downtrend + Parabolic SAR Resistance + ADX Downward Trend"

        # Signal Output Generation with Anti-Spam Check
        if direction:
            now = datetime.now()
            
            # Anti-Spam Check
            if pair in last_signal_time:
                time_since_last = now - last_signal_time[pair]
                if time_since_last < timedelta(minutes=COOLDOWN_MINUTES):
                    return None 
                    
            # Update last signal time
            last_signal_time[pair] = now
            
            entry_time = now.strftime("%I:%M %p")
            exit_time = (now + timedelta(minutes=1)).strftime("%I:%M %p") # 1 Min exact
            
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

print("Eagle Trading Zone 1-Min YouTube Bot (Anti-Spam Active) Started!")

while True:
    for pair in pairs:
        signal_msg = get_signal(pair)
        if signal_msg:
            try:
                bot.send_message(CHAT_ID, signal_msg, parse_mode='Markdown')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 1-Min Signal sent for {pair}")
                time.sleep(2) 
            except Exception:
                pass
    
    time.sleep(60)