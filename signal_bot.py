import telebot
import yfinance as yf
import pandas as pd
import ta
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# 1. Telegram Settings
TELEGRAM_TOKEN = '8807084061:AAF6BQTkW-AQ3XGpQI4eMDLmPbIhYT8_r2o'
CHAT_IDS = ['1375185299', '-1003642812085']
bot = telebot.TeleBot(TELEGRAM_TOKEN)

pairs = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X',
    'EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'EURCAD=X', 'AUDCAD=X', 'CADJPY=X', 'CHFJPY=X'
]

def fetch_market_signal():
    print("Scanning markets for manual request...")
    for pair in pairs:
        try:
            df = yf.download(pair, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 50:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close_prices = df['Close'].squeeze()
            high_prices = df['High'].squeeze()
            low_prices = df['Low'].squeeze()

            # Strategy Indicators (SMA 5, 8, 13 + PSAR + ADX 7)
            df['SMA_5'] = ta.trend.sma_indicator(close_prices, window=5)
            df['SMA_8'] = ta.trend.sma_indicator(close_prices, window=8)
            df['SMA_13'] = ta.trend.sma_indicator(close_prices, window=13)
            
            psar_indicator = ta.trend.PSARIndicator(high=high_prices, low=low_prices, close=close_prices, step=0.03, max_step=0.3)
            df['PSAR'] = psar_indicator.psar()
            
            adx_indicator = ta.trend.ADXIndicator(high=high_prices, low=low_prices, close=close_prices, window=7)
            df['ADX_7'] = adx_indicator.adx()
            df['DMP_7'] = adx_indicator.adx_pos()
            df['DMN_7'] = adx_indicator.adx_neg()

            sma_5 = float(df['SMA_5'].iloc[-1])
            sma_8 = float(df['SMA_8'].iloc[-1])
            sma_13 = float(df['SMA_13'].iloc[-1])
            
            current_close = float(close_prices.iloc[-1])
            current_psar = float(df['PSAR'].iloc[-1])
            
            dmp = float(df['DMP_7'].iloc[-1])
            dmn = float(df['DMN_7'].iloc[-1])
            adx_val = float(df['ADX_7'].iloc[-1])

            direction = None
            logic_text = ""
            
            # Strategy Rules
            if sma_5 > sma_8 > sma_13 and current_close > current_psar and dmp > dmn and adx_val > 15:
                direction = "🟢 CALL (UP)"
                logic_text = "SMA Uptrend + PSAR Support + ADX Up"
                
            elif sma_5 < sma_8 < sma_13 and current_close < current_psar and dmn > dmp and adx_val > 15:
                direction = "🔴 PUT (DOWN)"
                logic_text = "SMA Downtrend + PSAR Resistance + ADX Down"

            if direction:
                pair_name = pair.replace('=X', '')
                message = (
                    f"🦅 **EAGLE TRADING ZONE - INSTANT SIGNAL** 🦅\n\n"
                    f"📌 **Pair:** {pair_name}\n"
                    f"⏳ **Expiry:** 1 Minute\n"
                    f"📈 **Direction:** {direction}\n\n"
                    f"⚡ **Logic:** {logic_text}\n"
                    f"⚠️ *Requested manually via Telegram command.*"
                )
                return message
        except Exception as e:
            continue
            
    return "⚠️ Hazzar pairs scan kiye gaye, lekin abhi koi strong setup nahi mila. Thodi der baad dubara `/signal` try karein!"

# Telegram Command Handler
@bot.message_handler(commands=['signal', 'new'])
def send_manual_signal(message):
    bot.send_message(message.chat.id, "🔍 Scanning high-volume markets for your setup...", parse_mode='Markdown')
    signal_result = fetch_market_signal()
    for chat_id in CHAT_IDS:
        try:
            bot.send_message(chat_id, signal_result, parse_mode='Markdown')
        except:
            pass

# 2. Bot Polling in Background Thread
def run_bot():
    print("Eagle Trading Zone Command Bot Started! Send /signal on Telegram.")
    bot.infinity_polling()

# 3. HTTP Server to keep alive on hosting platforms
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Eagle Trading Zone Command Bot is Running 24/7!")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()
