import requests
import pandas as pd
import time
from datetime import datetime
import pytz
from flask import Flask
import threading

# ================= CONFIG =================
BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"
SYMBOL = "^NSEI"
# =========================================

app = Flask(__name__)

last_signal_time = None

# ===== TELEGRAM =====
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
        print("Sent:", text)
    except Exception as e:
        print("Error:", e)

# ===== MARKET TIME =====
def is_market_open():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return start <= now <= end

# ===== FETCH DATA =====
def get_data():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=5m&range=1d"
    res = requests.get(url).json()

    closes = res['chart']['result'][0]['indicators']['quote'][0]['close']
    df = pd.DataFrame(closes, columns=["close"])
    df.dropna(inplace=True)

    return df

# ===== SIGNAL LOGIC =====
def check_signal():
    global last_signal_time

    df = get_data()

    if len(df) < 20:
        return

    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema15"] = df["close"].ewm(span=15).mean()

    # CLOSED candles
    prev = df.iloc[-3]
    curr = df.iloc[-2]

    candle_id = len(df)

    if last_signal_time == candle_id:
        return

    signal = None

    if prev["ema9"] < prev["ema15"] and curr["ema9"] > curr["ema15"]:
        signal = "BUY 📈"

    elif prev["ema9"] > prev["ema15"] and curr["ema9"] < curr["ema15"]:
        signal = "SELL 📉"

    if signal:
        last_signal_time = candle_id
        send_message(f"NIFTY {signal}")

# ===== WAIT FOR NEXT 5 MIN CANDLE =====
def wait_for_next_candle():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    seconds = (5 - now.minute % 5) * 60 - now.second
    if seconds <= 0:
        seconds = 300

    print(f"Waiting {seconds} sec...")
    time.sleep(seconds + 2)

# ===== BOT LOOP =====
def run_bot():
    send_message("Bot Started ✅")

    while True:
        if is_market_open():
            wait_for_next_candle()
            check_signal()
        else:
            print("Market Closed")
            time.sleep(60)

# ===== FLASK =====
@app.route('/')
def home():
    return "Bot Running ✅"

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
