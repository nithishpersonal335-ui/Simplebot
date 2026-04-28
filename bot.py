import requests
import time
import threading
import pandas as pd
import yfinance as yf
from flask import Flask
from datetime import datetime
import pytz

# ===== CONFIG =====
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

SYMBOL = "^NSEI"   # NIFTY (change if needed)

app = Flask(__name__)

last_signal = None

# ===== TELEGRAM =====
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
        print("Sent:", text)
    except Exception as e:
        print("Error:", e)

# ===== MARKET TIME =====
def is_market_open():
    india = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india)

    start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return start <= now <= end

# ===== SIGNAL LOGIC =====
def check_signal():
    global last_signal

    data = yf.download(SYMBOL, interval="5m", period="1d")

    if data is None or len(data) < 20:
        return

    # EMA
    data["EMA9"] = data["Close"].ewm(span=9).mean()
    data["EMA15"] = data["Close"].ewm(span=15).mean()

    # USE CLOSED CANDLES ONLY
    last = data.iloc[-2]
    prev = data.iloc[-3]

    signal = None

    # BUY
    if prev["EMA9"] < prev["EMA15"] and last["EMA9"] > last["EMA15"]:
        signal = "BUY 📈"

    # SELL
    elif prev["EMA9"] > prev["EMA15"] and last["EMA9"] < last["EMA15"]:
        signal = "SELL 📉"

    # SEND ONLY NEW SIGNAL
    if signal and signal != last_signal:
        last_signal = signal
        send_message(f"NIFTY {signal} (5m EMA 9/15 crossover)")

# ===== LOOP =====
def run_bot():
    send_message("Bot Started ✅")

    while True:
        if is_market_open():
            check_signal()
        else:
            print("Market Closed")

        time.sleep(60)   # check every 1 min

# ===== FLASK =====
@app.route('/')
def home():
    return "Bot Running ✅"

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
