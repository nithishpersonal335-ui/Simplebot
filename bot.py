import requests
import time
import threading
from flask import Flask

# ===== TELEGRAM =====
BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"

# ===== SEND MESSAGE =====
def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ===== EMA =====
def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

# ===== DATA =====
def get_prices():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d"
        data = requests.get(url, timeout=10).json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c]
    except Exception as e:
        print("Data error:", e)
        return []

last_signal = None

def check():
    global last_signal

    prices = get_prices()
    if len(prices) < 30:
        return

    e9_prev = ema(prices[-21:-1], 9)
    e15_prev = ema(prices[-21:-1], 15)

    e9_now = ema(prices[-20:], 9)
    e15_now = ema(prices[-20:], 15)

    if not all([e9_prev, e15_prev, e9_now, e15_now]):
        return

    if e9_prev < e15_prev and e9_now > e15_now:
        if last_signal != "BUY":
            send_msg("NIFTY BUY 🔼")
            last_signal = "BUY"

    elif e9_prev > e15_prev and e9_now < e15_now:
        if last_signal != "SELL":
            send_msg("NIFTY SELL 🔽")
            last_signal = "SELL"

# ===== BOT LOOP =====
def run_bot():
    print("Bot Started...")
    send_msg("Bot running ✅")

    while True:
        try:
            check()
            time.sleep(300)
        except Exception as e:
            print("Error:", e)
            time.sleep(60)

# ===== FLASK APP =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
