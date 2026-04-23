import requests
import time
import threading
from flask import Flask

# ===== TELEGRAM =====
BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"

# ===== YOUR APP URL (IMPORTANT) =====
APP_URL = "https://simplebot-production-11a0.up.railway.app"

# ===== SEND TELEGRAM MESSAGE =====
def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ===== EMA CALCULATION =====
def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

# ===== FETCH DATA (FIXED) =====
def get_prices():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            print("API error:", r.status_code)
            return []

        data = r.json()

        if not data.get("chart") or not data["chart"].get("result"):
            print("Invalid data")
            return []

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]

    except Exception as e:
        print("Data error:", e)
        return []

# ===== SIGNAL MEMORY =====
last_signal = None

# ===== CHECK SIGNAL =====
def check():
    global last_signal

    prices = get_prices()

    if len(prices) < 10:
        print("Not enough data")
        return

    ema9_prev = ema(prices[-21:-1], 9)
    ema15_prev = ema(prices[-21:-1], 15)

    ema9_now = ema(prices[-20:], 9)
    ema15_now = ema(prices[-20:], 15)

    if not all([ema9_prev, ema15_prev, ema9_now, ema15_now]):
        return

    # BUY
    if ema9_prev < ema15_prev and ema9_now > ema15_now:
        if last_signal != "BUY":
            send_msg("NIFTY BUY 🔼")
            print("BUY signal")
            last_signal = "BUY"

    # SELL
    elif ema9_prev > ema15_prev and ema9_now < ema15_now:
        if last_signal != "SELL":
            send_msg("NIFTY SELL 🔽")
            print("SELL signal")
            last_signal = "SELL"

# ===== BOT LOOP =====
def run_bot():
    print("Bot Started...")
    send_msg("Bot running on cloud ✅")

    while True:
        try:
            check()

            # 🔥 SELF PING (keeps Railway alive)
            try:
                requests.get(APP_URL, timeout=5)
                print("Self ping success")
            except:
                print("Self ping failed")

            time.sleep(300)  # every 5 mins

        except Exception as e:
            print("Error:", e)
            time.sleep(60)

# ===== FLASK SERVER =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
