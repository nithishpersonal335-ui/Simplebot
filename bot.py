import requests
import time

# ===== YOUR DETAILS =====
BOT_TOKEN = "8285229070:AAGZQnCbjULqMUsZkmNMBSG9NCh3WlI2bNo"
CHAT_ID = "1207682165"

# ===== SEND MESSAGE =====
def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(url, params={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ===== EMA =====
def ema(prices, period):
    k = 2 / (period + 1)
    val = prices[0]
    for p in prices:
        val = p * k + val * (1 - k)
    return val

# ===== DATA =====
def get_prices():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=5m&range=1d"
        data = requests.get(url).json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c]
    except:
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

    if e9_prev < e15_prev and e9_now > e15_now:
        if last_signal != "BUY":
            send_msg("NIFTY EMA CROSS UP")
            last_signal = "BUY"

    elif e9_prev > e15_prev and e9_now < e15_now:
        if last_signal != "SELL":
            send_msg("NIFTY EMA CROSS DOWN")
            last_signal = "SELL"

print("Bot Started...")
send_msg("Bot running ✅")

while True:
    check()
    time.sleep(300)
